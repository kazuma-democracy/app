from __future__ import annotations

from decimal import Decimal

import pytest

from wa_commons.portfolio.benchmark_snapshot import (
    build_topix_public_weight_snapshot,
    read_topix_public_weight_csv,
)


def _config() -> dict:
    return {
        "artifact_version": "m3.3b-topix-benchmark-v0.2",
        "benchmark_id": "JPX:TOPIX_TOTAL_RETURN:6000",
        "provider": "JPX Market Innovation & Research, Inc.",
        "constituent_product": "TOPIX Component Weight List",
        "effective_date": "2026-08-31",
        "available_at": "2026-09-30T16:20:00+09:00",
        "index_code": "0000",
        "return_index_code": "6000",
        "currency": "JPY",
        "weight_basis": "PROVIDER_PUBLISHED_WEIGHT",
        "semantic_weight_decimals": 12,
        "published_weight_percent_decimals": 4,
        "published_weight_sum_tolerance": "0.000100",
        "rights_mode": "official_public_web_terms_apply_no_raw_redistribution_assumed",
        "raw_publication": False,
    }


def _row(code: str, weight: str, *, name: str = "Example") -> dict[str, str]:
    return {
        "日付": "20260831",
        "銘柄名": name,
        "コード": code,
        "業種": "輸送用機器",
        "TOPIXに占める個別銘柄のウエイト": weight,
        "ニューインデックス区分": "TOPIX Core30",
    }


def test_public_weight_snapshot_rescales_published_rounding_deterministically():
    rows = [_row("7203", "60.0000%"), _row("130A", "39.9996%")]
    first = build_topix_public_weight_snapshot(rows, _config(), "a" * 64)
    second = build_topix_public_weight_snapshot(list(reversed(rows)), _config(), "a" * 64)

    assert [row["security_id"] for row in first["rows"]] == ["TSE:130A", "TSE:7203"]
    assert [row["provider_published_weight"] for row in first["rows"]] == ["0.399996", "0.600000"]
    assert sum(Decimal(row["benchmark_weight"]) for row in first["rows"]) == Decimal("1.000000000000")
    assert first["manifest"]["provider_weight_sum"] == "0.999996"
    assert first["manifest"]["provider_weight_rounding_gap"] == "0.000004"
    assert first["manifest"]["normalization_method"] == "proportional_rescale_published_weights"
    assert first["manifest"]["semantic_snapshot_sha256"] == second["manifest"]["semantic_snapshot_sha256"]


def test_public_weight_snapshot_rejects_wrong_date_duplicate_and_large_reconciliation_gap():
    with pytest.raises(ValueError, match="effective date"):
        build_topix_public_weight_snapshot(
            [{**_row("7203", "100.0000%"), "日付": "20260731"}], _config(), "b" * 64
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_topix_public_weight_snapshot(
            [_row("7203", "50.0000%"), _row("7203", "50.0000%")], _config(), "b" * 64
        )
    with pytest.raises(ValueError, match="rounding tolerance"):
        build_topix_public_weight_snapshot([_row("7203", "90.0000%")], _config(), "b" * 64)


def test_reads_cp932_public_weight_csv_and_ignores_footer_rows(tmp_path):
    path = tmp_path / "topixweight_j.csv"
    text = (
        "日付,銘柄名,コード,業種,TOPIXに占める個別銘柄のウエイト,ニューインデックス区分\n"
        "20260831,Alpha,1001,建設業,60.0000%,TOPIX Mid400\n"
        "20260831,Beta,1002,建設業,40.0000%,TOPIX Small 1\n"
        "ご注意,,,,,\n"
        "・本資料は予告なく変更される場合があります。,,,,,\n"
    )
    path.write_bytes(text.encode("cp932"))

    rows = read_topix_public_weight_csv(path)

    assert [row["コード"] for row in rows] == ["1001", "1002"]
    assert all(row["日付"] == "20260831" for row in rows)


def test_public_weight_manifest_carries_official_source_provenance():
    config = _config()
    config.update({
        "source_url": "https://www.jpx.co.jp/automation/markets/indices/topix/files/topixweight_j.csv",
        "source_page_url": "https://www.jpx.co.jp/markets/indices/topix/",
        "publication_rule": "updated after 16:20 JST on the final business day of the following month",
    })

    snapshot = build_topix_public_weight_snapshot([_row("7203", "100.0000%")], config, "c" * 64)

    manifest = snapshot["manifest"]
    assert manifest["source_url"].endswith("topixweight_j.csv")
    assert manifest["source_page_url"].endswith("/markets/indices/topix/")
    assert "following month" in manifest["publication_rule"]


def test_public_weight_reader_fails_closed_on_malformed_dated_row(tmp_path):
    path = tmp_path / "topixweight_j.csv"
    text = (
        "日付,銘柄名,コード,業種,TOPIXに占める個別銘柄のウエイト,ニューインデックス区分\n"
        "20260831,Alpha,1001,建設業,,TOPIX Mid400\n"
        "ご注意,,,,,\n"
    )
    path.write_bytes(text.encode("cp932"))

    with pytest.raises(ValueError, match="dated constituent row"):
        read_topix_public_weight_csv(path)
