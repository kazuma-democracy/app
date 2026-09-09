from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from openpyxl import Workbook

from wa_commons.evidence.mod_procurement import observation_to_claim, parse_workbook, resolve_supplier


def _fixture(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "4月"
    ws.append([
        "物品役務等の名称及び数量",
        "契約担当官等の氏名並びにその所属する部局の名称及び所在地",
        "契約を締結した日",
        "契約の相手方の商号又は名称及び住所",
        "法人番号",
        "予定価格",
        "契約金額",
    ])
    ws.append([
        "鉛筆 ＨＢ外２８５件（単価契約）一式",
        "支出負担行為担当官 大臣官房会計課",
        "4月1日",
        "株式会社第一文眞堂\n東京都港区芝大門1-3-16",
        "5010401017488",
        49503041,
        47711079,
    ])
    ws.append([
        "名称だけの曖昧な役務",
        "支出負担行為担当官 大臣官房会計課",
        "4月2日",
        "同名株式会社\n東京都千代田区",
        "",
        1000000,
        900000,
    ])
    wb.save(path)


def test_civilian_contract_is_not_weapons_activity(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    _fixture(path)
    observations = parse_workbook(path, retrieved_at="2026-08-21T12:00:00Z")
    civilian = observations[0]
    claim = observation_to_claim(civilian)
    assert civilian.subject.startswith("鉛筆")
    assert civilian.identity_decision == "AUTO_LINK"
    assert claim is not None
    assert claim["claim"]["category"] == "military_contract"
    assert claim["claim"]["predicate"] == "received_contract_from_japan_ministry_of_defense"
    assert claim["claim"]["value"]["contract_subject"].startswith("鉛筆")
    assert "weapons_activity" not in json.dumps(claim, ensure_ascii=False)
    assert claim["policy_context"] is None


def test_name_only_supplier_stays_unresolved(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    _fixture(path)
    observations = parse_workbook(path, retrieved_at="2026-08-21T12:00:00Z")
    unresolved = observations[1]
    assert unresolved.identity_decision == "UNRESOLVED"
    assert unresolved.entity_id is None
    assert observation_to_claim(unresolved) is None


def test_resolution_uses_m1_strong_identifier_policy() -> None:
    decision, entity_id = resolve_supplier("株式会社第一文眞堂", "5010401017488")
    assert decision == "AUTO_LINK"
    assert entity_id == "jp:corporate-number:5010401017488"
    decision, entity_id = resolve_supplier("株式会社第一文眞堂", "")
    assert decision == "UNRESOLVED"
    assert entity_id is None


def test_claim_validates_against_canonical_schema(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    _fixture(path)
    claim = observation_to_claim(parse_workbook(path, retrieved_at="2026-08-21T12:00:00Z")[0])
    assert claim is not None
    schema = json.loads(Path("schemas/evidence-claim.v0.1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(claim)


def test_parse_workbook_accepts_historical_source_metadata(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    _fixture(path)
    observations = parse_workbook(
        path,
        retrieved_at="2026-03-10T12:08:58+09:00",
        source_url="https://example.invalid/fy2025-01.xlsx",
        source_page_url="https://example.invalid/mod-index",
        snapshot_version="fy2025-01-buppin-competitive",
        fiscal_year=2025,
    )
    observation = observations[0]
    assert observation.contract_date == "2025-04-01"
    assert observation.source_url == "https://example.invalid/fy2025-01.xlsx"
    assert observation.source_page_url == "https://example.invalid/mod-index"
    assert observation.snapshot_version == "fy2025-01-buppin-competitive"
    assert observation.observation_id.startswith("wc:obs:mod:fy2025-01-buppin-competitive:")
    claim = observation_to_claim(observation)
    assert claim is not None
    assert claim["claim_id"].startswith("wc:claim:mod:fy2025-01-buppin-competitive:")
    assert claim["evidence"][0]["evidence_id"].startswith("wc:evidence:mod:fy2025-01-buppin-competitive:")


def test_parse_workbook_defaults_remain_current_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "fixture.xlsx"
    _fixture(path)
    observation = parse_workbook(path, retrieved_at="2026-08-21T12:00:00Z")[0]
    assert observation.contract_date == "2026-04-01"
    assert observation.snapshot_version == "fy2026-04-buppin-competitive"
    assert observation.observation_id.startswith("wc:obs:mod:fy2026-04-buppin-competitive:")
