from __future__ import annotations

import pytest


def coverage_api():
    try:
        from wa_commons.evidence.tse_coverage import build_tse_coverage
    except ModuleNotFoundError as exc:
        pytest.fail(f"TSE coverage implementation missing: {exc}")
    return build_tse_coverage


def test_tse_wide_coverage_preserves_all_entities_and_states():
    build = coverage_api()

    entities = [
        {
            "entity_id": f"wa:org:jp:tse:{index:04d}",
            "review_state": "CONFIRMED" if index <= 3699 else "UNRESOLVED",
        }
        for index in range(1, 3708)
    ]
    identity = {
        "manifest": {
            "entity_count": 3707,
            "semantic_identity_sha256": "identity-sha",
        },
        "entities": entities,
    }
    source_catalog = [
        {
            "source_id": "jp-mod-procurement",
            "category": "military_contract",
            "integration_state": "integrated",
            "run_state": "complete",
        },
        {
            "source_id": "jp-political-finance",
            "category": "political_finance",
            "integration_state": "integrated",
            "run_state": "complete",
            "identity_linkage_state": "unresolved",
        },
        {
            "source_id": "sipri-arms-industry",
            "category": "arms_industry",
            "integration_state": "not_integrated",
            "run_state": "not_run",
        },
        {
            "source_id": "us-uflpa-entity-list",
            "category": "official_listing",
            "integration_state": "not_integrated",
            "run_state": "not_run",
        },
        {
            "source_id": "oecd-ncp-cases",
            "category": "responsible_business_conduct_case",
            "integration_state": "not_integrated",
            "run_state": "not_run",
        },
    ]

    result = build(
        identity,
        source_catalog=source_catalog,
        linked_observations=[],
        code_commit="deadbeef",
    )

    matrix = result["matrix"]
    assert matrix["entity_count"] == 3707
    assert matrix["source_count"] == 5
    assert matrix["cell_count"] == 18535
    assert matrix["state_counts"] == {
        "no_match": 3699,
        "not_integrated": 11121,
        "observed": 0,
        "unknown": 0,
        "unresolved_identity": 3715,
    }

    assert result["manifest"]["identity_entity_count"] == 3707
    assert result["manifest"]["identity_semantic_sha256"] == "identity-sha"
    assert result["manifest"]["coverage_semantic_sha256"]

    assert not any(
        key in row
        for row in matrix["rows"]
        for key in ("pass", "safe", "clean", "policy_decision", "moral_score")
    )
