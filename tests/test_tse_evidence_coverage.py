from __future__ import annotations

import pytest


def coverage_api():
    try:
        from wa_commons.evidence.tse_coverage import build_tse_coverage
    except ModuleNotFoundError as exc:
        pytest.fail(f"TSE coverage implementation missing: {exc}")
    return build_tse_coverage


def _entity(index: int) -> dict:
    identifiers = []
    if index <= 3699:
        identifiers.append(
            {
                "scheme": "JP_CORPORATE_NUMBER",
                "value": f"{index:013d}",
                "source": {},
            }
        )
    return {
        "entity_id": f"wa:org:jp:tse:{index:04d}",
        "review_state": "CONFIRMED",
        "identifiers": identifiers,
    }


def test_tse_wide_coverage_preserves_all_entities_and_states():
    build = coverage_api()

    identity = {
        "manifest": {
            "entity_count": 3707,
            "mapped_count": 3699,
            "unresolved_count": 8,
            "disputed_count": 0,
            "semantic_identity_sha256": "identity-sha",
        },
        "entities": [_entity(index) for index in range(1, 3708)],
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

    unresolved_mod_rows = [
        row
        for row in matrix["rows"]
        if row["source_id"] == "jp-mod-procurement" and row["state"] == "unresolved_identity"
    ]
    assert len(unresolved_mod_rows) == 8

    assert result["manifest"]["identity_entity_count"] == 3707
    assert result["manifest"]["identity_semantic_sha256"] == "identity-sha"
    assert result["manifest"]["coverage_semantic_sha256"]

    assert not any(
        key in row
        for row in matrix["rows"]
        for key in ("pass", "safe", "clean", "policy_decision", "moral_score")
    )


def test_integrated_source_outage_stays_unknown_not_no_match():
    build = coverage_api()
    identity = {
        "manifest": {"entity_count": 1, "semantic_identity_sha256": "identity-sha"},
        "entities": [_entity(1)],
    }
    result = build(
        identity,
        source_catalog=[
            {
                "source_id": "jp-mod-procurement",
                "category": "military_contract",
                "integration_state": "integrated",
                "run_state": "unknown",
            }
        ],
        linked_observations=[],
        code_commit="deadbeef",
    )
    assert result["matrix"]["rows"] == [
        {
            "entity_id": "wa:org:jp:tse:0001",
            "source_id": "jp-mod-procurement",
            "state": "unknown",
            "observation_count": 0,
        }
    ]


def test_semantic_coverage_hash_is_stable_across_input_order_and_source_metadata():
    build = coverage_api()
    entity_a = _entity(1)
    entity_b = _entity(2)
    source_a = {
        "source_id": "jp-mod-procurement",
        "category": "military_contract",
        "integration_state": "integrated",
        "run_state": "complete",
        "provenance": {"retrieved_at": "2026-09-08T00:00:00Z"},
    }
    source_b = {
        "source_id": "sipri-arms-industry",
        "category": "arms_industry",
        "integration_state": "not_integrated",
        "run_state": "not_run",
    }
    identity = {
        "manifest": {"entity_count": 2, "semantic_identity_sha256": "identity-sha"},
        "entities": [entity_a, entity_b],
    }
    first = build(
        identity,
        source_catalog=[source_a, source_b],
        linked_observations=[
            {"source_id": "jp-mod-procurement", "entity_id": entity_b["entity_id"]},
            {"source_id": "jp-mod-procurement", "entity_id": entity_a["entity_id"]},
        ],
        code_commit="first-commit",
    )

    source_a_later = dict(source_a)
    source_a_later["provenance"] = {"retrieved_at": "2026-09-08T12:34:56Z"}
    second = build(
        {**identity, "entities": [entity_b, entity_a]},
        source_catalog=[source_b, source_a_later],
        linked_observations=[
            {"source_id": "jp-mod-procurement", "entity_id": entity_a["entity_id"]},
            {"source_id": "jp-mod-procurement", "entity_id": entity_b["entity_id"]},
        ],
        code_commit="second-commit",
    )

    assert first["matrix"] == second["matrix"]
    assert first["manifest"]["coverage_semantic_sha256"] == second["manifest"]["coverage_semantic_sha256"]
