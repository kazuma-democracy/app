from __future__ import annotations

from pathlib import Path

import pytest

from wa_commons.evidence.historical_cutoff import select_sources_available_at_cutoff


def test_mod_source_after_cutoff_is_not_selected() -> None:
    selected = select_sources_available_at_cutoff(
        [
            {"snapshot_version": "fy2025-01", "available_at": "2026-03-10T12:08:58+09:00"},
            {"snapshot_version": "fy2025-02", "available_at": "2026-04-10T10:28:20+09:00"},
        ],
        decision_cutoff="2026-03-31T15:30:00+09:00",
    )
    assert [item["snapshot_version"] for item in selected] == ["fy2025-01"]


def test_missing_or_naive_source_availability_fails_closed() -> None:
    for source in (
        {"snapshot_version": "missing"},
        {"snapshot_version": "naive", "available_at": "2026-03-10T12:08:58"},
    ):
        with pytest.raises(ValueError, match="available_at"):
            select_sources_available_at_cutoff(
                [source],
                decision_cutoff="2026-03-31T15:30:00+09:00",
            )


def _identity() -> dict:
    return {
        "manifest": {"entity_count": 2, "semantic_identity_sha256": "identity-historical"},
        "entities": [
            {"entity_id": "wa:org:jp:tse:1001", "review_state": "CONFIRMED", "identifiers": [{"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111"}]},
            {"entity_id": "wa:org:jp:tse:1002", "review_state": "CONFIRMED", "identifiers": [{"scheme": "JP_CORPORATE_NUMBER", "value": "2222222222222"}]},
        ],
    }


def _source_catalog() -> list[dict]:
    return [
        {"source_id": "jp-mod-procurement", "category": "military_contract", "integration_state": "integrated", "run_state": "complete", "coverage_interpretation": "no_match_is_not_clean_safe_or_pass", "provenance": {}},
        {"source_id": "jp-political-finance", "category": "political_finance", "integration_state": "integrated", "run_state": "complete", "identity_linkage_state": "unresolved", "coverage_interpretation": "no_match_is_not_clean_safe_or_pass", "provenance": {"snapshot_version": "soumu-20241129"}},
        {"source_id": "sipri-arms-industry", "category": "arms_industry", "integration_state": "not_integrated", "run_state": "not_run", "coverage_interpretation": "no_match_is_not_clean_safe_or_pass", "provenance": {}},
        {"source_id": "us-uflpa-entity-list", "category": "official_listing", "integration_state": "not_integrated", "run_state": "not_run", "coverage_interpretation": "no_match_is_not_clean_safe_or_pass", "provenance": {}},
        {"source_id": "oecd-ncp-cases", "category": "responsible_business_conduct_case", "integration_state": "not_integrated", "run_state": "not_run", "coverage_interpretation": "no_match_is_not_clean_safe_or_pass", "provenance": {}},
    ]


def _mod_workbook(path: Path, *, corporate_number: str, supplier: str) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "month"
    ws.append([
        "物品役務等の名称及び数量", "契約担当官等の氏名並びにその所属する部局の名称及び所在地",
        "契約を締結した日", "契約の相手方の商号又は名称及び住所", "法人番号", "予定価格", "契約金額",
    ])
    ws.append(["一般事務用品", "Japan MOD", "1月15日", supplier, corporate_number, 1200, 1000])
    wb.save(path)


def _policies() -> list[dict]:
    import json
    return json.loads(Path("schemas/examples/user-policy.examples.json").read_text(encoding="utf-8"))


def _coverage_state(screening: dict, *, entity_id: str, source_id: str) -> str:
    rows = screening["historical_coverage"]["matrix"]["rows"]
    return next(row["state"] for row in rows if row["entity_id"] == entity_id and row["source_id"] == source_id)


def test_historical_screening_only_uses_sources_available_by_cutoff(tmp_path: Path) -> None:
    from wa_commons.evidence.historical_cutoff import build_historical_screening

    first_path = tmp_path / "first.xlsx"
    second_path = tmp_path / "second.xlsx"
    _mod_workbook(first_path, corporate_number="1111111111111", supplier="First Supplier")
    _mod_workbook(second_path, corporate_number="2222222222222", supplier="Second Supplier")
    sources = [
        {
            "snapshot_version": "fy2025-01-a",
            "available_at": "2026-03-10T12:08:58+09:00",
            "local_path": str(first_path),
            "source_url": "https://example.invalid/first.xlsx",
            "source_page_url": "https://example.invalid/mod",
            "retrieved_at": "2026-03-10T12:08:58+09:00",
            "fiscal_year": 2025,
        },
        {
            "snapshot_version": "fy2025-02-b",
            "available_at": "2026-04-10T10:28:20+09:00",
            "local_path": str(second_path),
            "source_url": "https://example.invalid/second.xlsx",
            "source_page_url": "https://example.invalid/mod",
            "retrieved_at": "2026-04-10T10:28:20+09:00",
            "fiscal_year": 2025,
        },
    ]

    march = build_historical_screening(
        identity=_identity(), mod_sources=sources,
        decision_cutoff="2026-03-31T15:30:00+09:00",
        coverage_source_catalog=_source_catalog(), policies=_policies(), code_commit="march",
    )
    april = build_historical_screening(
        identity=_identity(), mod_sources=sources,
        decision_cutoff="2026-04-30T15:30:00+09:00",
        coverage_source_catalog=_source_catalog(), policies=_policies(), code_commit="april",
    )
    assert march["availability_complete"] is True
    assert march["selected_mod_snapshot_versions"] == ["fy2025-01-a"]
    assert april["selected_mod_snapshot_versions"] == ["fy2025-01-a", "fy2025-02-b"]
    assert march["mod_observation_count"] == 1
    assert april["mod_observation_count"] == 2
    assert _coverage_state(march, entity_id="wa:org:jp:tse:1002", source_id="jp-mod-procurement") == "no_match"
    assert _coverage_state(april, entity_id="wa:org:jp:tse:1002", source_id="jp-mod-procurement") == "observed"
    assert len(march["evidence_provenance_sha256"]) == 64
