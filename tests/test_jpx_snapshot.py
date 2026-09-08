import json
from pathlib import Path

import pytest

from wa_commons.identity import jpx_snapshot
from wa_commons.identity.jpx_snapshot import build_pilot, domestic_company_rows, read_jpx_rows


HEADER = "日付,コード,銘柄名,市場・商品区分,33業種コード,33業種区分,17業種コード,17業種区分,規模コード,規模区分"


def _write_fixture(path: Path) -> None:
    lines = [HEADER]
    # Mixed non-company rows that must be ignored.
    lines.append("20260430,1305,TEST ETF,ETF・ETN,-,-,-,-,-,-")
    lines.append("20260430,131A,TEST PRO,PRO Market,5250,情報・通信業,10,情報通信・サービスその他,-,-")
    for i in range(1, 106):
        code = 2000 + i
        market = "プライム（内国株式）" if i % 2 else "スタンダード（内国株式）"
        lines.append(f"20260430,{code},テスト企業{i},{market},2050,建設業,3,建設・資材,-,-")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def _universe_rows() -> list[str]:
    return [
        "20260831,1003,成長テスト,グロース（内国株式）,5250,情報・通信業,10,情報通信・サービスその他,-,-",
        "20260831,1001,主要テスト,プライム（内国株式）,2050,建設業,3,建設・資材,-,-",
        "20260831,1002,標準テスト,スタンダード（内国株式）,3050,卸売業,9,商社・卸売,-,-",
        "20260831,1305,ETF TEST,ETF・ETN,-,-,-,-,-,-",
        "20260831,8951,REIT TEST,不動産投資信託（REIT）,-,-,-,-,-,-",
        "20260831,131A,PRO TEST,PRO Market,5250,情報・通信業,10,情報通信・サービスその他,-,-",
        "20260831,200A,FOREIGN TEST,プライム（外国株式）,5250,情報・通信業,10,情報通信・サービスその他,-,-",
    ]


def _write_universe_fixture(path: Path, rows: list[str] | None = None) -> None:
    path.write_text(
        "\n".join([HEADER, *(rows if rows is not None else _universe_rows())]) + "\n",
        encoding="utf-8-sig",
    )


def _build_fixture_universe(path: Path) -> dict:
    return jpx_snapshot.build_universe(
        path,
        snapshot="2026-08-31",
        source_url="https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
        retrieved_at="2026-09-08T00:00:00Z",
    )


def _semantic_projection(payload: dict) -> list[dict[str, str]]:
    return [
        {
            "entity_id": row["entity_id"],
            "security_code": row["security_code"],
            "canonical_name": row["canonical_name"],
            "market_segment": row["market_segment"],
        }
        for row in payload["entities"]
    ]


def test_domestic_filter_excludes_etf_and_pro_market(tmp_path):
    fixture = tmp_path / "data_j.csv"
    _write_fixture(fixture)
    rows = domestic_company_rows(read_jpx_rows(fixture))
    assert len(rows) == 105
    assert all("内国株式" in row["市場・商品区分"] for row in rows)


def test_build_pilot_is_deterministic_and_limited_to_100(tmp_path):
    fixture = tmp_path / "data_j.csv"
    _write_fixture(fixture)
    kwargs = dict(
        snapshot="2026-04-30",
        source_url="https://www.jpx.co.jp/example/data_j.xls",
        retrieved_at="2026-08-21T00:00:00Z",
        limit=100,
    )
    one = build_pilot(fixture, **kwargs)
    two = build_pilot(fixture, **kwargs)
    assert one == two
    assert one["manifest"]["entity_count"] == 100
    assert len(one["manifest"]["source_sha256"]) == 64
    assert one["entities"][0]["entity_id"] == "wa:org:jp:tse:2001"
    assert one["entities"][-1]["entity_id"] == "wa:org:jp:tse:2100"


def test_build_universe_filters_and_emits_non_row_manifest(tmp_path):
    fixture = tmp_path / "listed.csv"
    _write_universe_fixture(fixture)

    payload = _build_fixture_universe(fixture)

    assert [row["security_code"] for row in payload["entities"]] == ["1001", "1002", "1003"]
    assert [row["market_segment"] for row in payload["entities"]] == [
        "Prime",
        "Standard",
        "Growth",
    ]
    source = payload["entities"][0]["identifiers"][0]["source"]
    assert source == {
        "source": "JPX",
        "source_key": "listed.csv",
        "snapshot": "2026-08-31",
        "url": "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
        "retrieved_at": "2026-09-08T00:00:00Z",
        "adapter_version": "0.4",
    }
    manifest = payload["manifest"]
    assert manifest["rights_mode"] == "local_generation_only"
    assert manifest["normalization_rule_version"] == "tse-universe-normalization-v0.1"
    assert manifest["market_counts"] == {"Prime": 1, "Standard": 1, "Growth": 1}
    assert manifest["entity_count"] == 3
    assert manifest["exclusion_counts"] == {
        "etf_etn": 1,
        "reit": 1,
        "tokyo_pro_market": 1,
        "other_market": 1,
    }
    assert len(manifest["source_sha256"]) == 64
    assert len(manifest["semantic_payload_sha256"]) == 64
    encoded_manifest = json.dumps(manifest, ensure_ascii=False)
    assert "entities" not in manifest
    assert "主要テスト" not in encoded_manifest
    assert "1001" not in encoded_manifest


def test_universe_semantic_hash_is_order_independent(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    rows = _universe_rows()
    _write_universe_fixture(first, rows)
    _write_universe_fixture(second, list(reversed(rows)))
    kwargs = dict(
        snapshot="2026-08-31",
        source_url="https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
        retrieved_at="2026-09-08T00:00:00Z",
    )

    one = jpx_snapshot.build_universe(first, **kwargs)
    two = jpx_snapshot.build_universe(second, **kwargs)

    assert _semantic_projection(one) == _semantic_projection(two)
    assert one["manifest"]["semantic_payload_sha256"] == two["manifest"]["semantic_payload_sha256"]
    assert one["manifest"]["source_sha256"] != two["manifest"]["source_sha256"]


def test_universe_semantic_hash_ignores_local_provenance_metadata(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    _write_universe_fixture(first)
    second.write_bytes(first.read_bytes())
    one = jpx_snapshot.build_universe(
        first,
        snapshot="2026-08-31",
        source_url="https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
        retrieved_at="2026-09-08T00:00:00Z",
    )
    two = jpx_snapshot.build_universe(
        second,
        snapshot="2026-08-31",
        source_url="https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
        retrieved_at="2026-09-08T01:00:00Z",
    )

    assert _semantic_projection(one) == _semantic_projection(two)
    assert one["manifest"]["source_sha256"] == two["manifest"]["source_sha256"]
    assert one["manifest"]["semantic_payload_sha256"] == two["manifest"]["semantic_payload_sha256"]


def test_build_universe_rejects_duplicate_security_codes(tmp_path):
    fixture = tmp_path / "duplicate.csv"
    rows = _universe_rows()[:3] + [
        "20260831,1001,別名テスト,プライム（内国株式）,2050,建設業,3,建設・資材,-,-"
    ]
    _write_universe_fixture(fixture, rows)

    with pytest.raises(ValueError, match="duplicate security_code: 1001"):
        _build_fixture_universe(fixture)


def test_build_universe_rejects_in_scope_row_missing_required_identity_fields(tmp_path):
    fixture = tmp_path / "missing-code.csv"
    rows = _universe_rows() + [
        "20260831,,MISSING CODE,プライム（内国株式）,2050,建設業,3,建設・資材,-,-"
    ]
    _write_universe_fixture(fixture, rows)

    with pytest.raises(ValueError, match="in-scope JPX row missing security code or name"):
        _build_fixture_universe(fixture)


def test_build_universe_rejects_source_date_mismatch(tmp_path):
    fixture = tmp_path / "wrong-date.csv"
    rows = _universe_rows()
    rows[0] = rows[0].replace("20260831", "20260901", 1)
    _write_universe_fixture(fixture, rows)

    with pytest.raises(ValueError, match="source row date 20260901 does not match snapshot 20260831"):
        _build_fixture_universe(fixture)


def test_write_universe_separates_local_rows_from_public_manifest(tmp_path):
    fixture = tmp_path / "listed.csv"
    _write_universe_fixture(fixture)
    payload = _build_fixture_universe(fixture)
    local_output = tmp_path / "universe.local.json"
    public_manifest = tmp_path / "universe.manifest.json"

    jpx_snapshot.write_universe(payload, local_output, public_manifest)

    assert json.loads(local_output.read_text(encoding="utf-8")) == payload
    assert json.loads(public_manifest.read_text(encoding="utf-8")) == payload["manifest"]
    assert "主要テスト" in local_output.read_text(encoding="utf-8")
    manifest_text = public_manifest.read_text(encoding="utf-8")
    assert "主要テスト" not in manifest_text
    assert "1001" not in manifest_text


def test_write_universe_rejects_same_local_and_public_path(tmp_path):
    fixture = tmp_path / "listed.csv"
    _write_universe_fixture(fixture)
    payload = _build_fixture_universe(fixture)
    shared_output = tmp_path / "universe.json"

    with pytest.raises(ValueError, match="local and public outputs must be distinct"):
        jpx_snapshot.write_universe(payload, shared_output, shared_output)
