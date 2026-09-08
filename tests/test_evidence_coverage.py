from __future__ import annotations

import pytest


def coverage_api():
    try:
        from wa_commons.evidence.coverage import (
            COVERAGE_STATES,
            build_coverage_matrix,
            canonical_coverage_sha256,
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"coverage implementation missing: {exc}")
    return COVERAGE_STATES, build_coverage_matrix, canonical_coverage_sha256


def entity(entity_id: str, *, review_state: str = "CONFIRMED") -> dict:
    return {
        "entity_id": entity_id,
        "canonical_name": entity_id,
        "review_state": review_state,
    }


def test_matrix_emits_one_explicit_state_per_entity_source():
    states, build, _ = coverage_api()
    assert states == {
        "observed",
        "no_match",
        "unknown",
        "unresolved_identity",
        "not_integrated",
    }
    result = build(
        entities=[entity("e2"), entity("e1")],
        sources=["integrated-a", "future-b"],
        integrated_sources={"integrated-a"},
        observations=[{"source_id": "integrated-a", "entity_id": "e1"}],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    assert [(row["entity_id"], row["source_id"], row["state"]) for row in result["rows"]] == [
        ("e1", "future-b", "not_integrated"),
        ("e1", "integrated-a", "observed"),
        ("e2", "future-b", "not_integrated"),
        ("e2", "integrated-a", "no_match"),
    ]


def test_unresolved_identity_takes_precedence_over_no_match():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1", review_state="UNRESOLVED")],
        sources=["integrated-a"],
        integrated_sources={"integrated-a"},
        observations=[],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    assert result["rows"][0]["state"] == "unresolved_identity"


def test_missing_identity_review_state_is_not_assumed_confirmed():
    _, build, _ = coverage_api()
    result = build(
        entities=[{"entity_id": "e1", "canonical_name": "e1"}],
        sources=["integrated-a"],
        integrated_sources={"integrated-a"},
        observations=[{"source_id": "integrated-a", "entity_id": "e1"}],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    assert result["rows"][0]["state"] == "unresolved_identity"


def test_source_level_unresolved_identity_takes_precedence_over_no_match():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1")],
        sources=["integrated-a"],
        integrated_sources={"integrated-a"},
        observations=[],
        unknown_sources=set(),
        unresolved_sources={"integrated-a"},
    )
    assert result["rows"][0]["state"] == "unresolved_identity"


def test_linked_observation_remains_observed_for_source_with_other_unresolved_identity_rows():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1")],
        sources=["integrated-a"],
        integrated_sources={"integrated-a"},
        observations=[{"source_id": "integrated-a", "entity_id": "e1"}],
        unknown_sources=set(),
        unresolved_sources={"integrated-a"},
    )
    assert result["rows"][0]["state"] == "observed"


def test_source_unknown_takes_precedence_over_no_match():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1")],
        sources=["integrated-a"],
        integrated_sources={"integrated-a"},
        observations=[],
        unknown_sources={"integrated-a"},
        unresolved_sources=set(),
    )
    assert result["rows"][0]["state"] == "unknown"


def test_missing_or_unintegrated_states_never_emit_moral_or_policy_result():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1")],
        sources=["integrated-a", "future-b"],
        integrated_sources={"integrated-a"},
        observations=[],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    for row in result["rows"]:
        assert set(row) == {"entity_id", "source_id", "state", "observation_count"}
        assert row["state"] in {"no_match", "not_integrated"}
        assert not any(key in row for key in ("pass", "safe", "clean", "policy_decision", "moral_score"))


def test_summary_counts_all_matrix_cells_without_interpreting_them():
    _, build, _ = coverage_api()
    result = build(
        entities=[entity("e1"), entity("e2")],
        sources=["a", "b"],
        integrated_sources={"a"},
        observations=[
            {"source_id": "a", "entity_id": "e1"},
            {"source_id": "a", "entity_id": "e1"},
        ],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    assert result["entity_count"] == 2
    assert result["source_count"] == 2
    assert result["cell_count"] == 4
    assert result["state_counts"] == {
        "no_match": 1,
        "not_integrated": 2,
        "observed": 1,
        "unknown": 0,
        "unresolved_identity": 0,
    }
    observed = next(row for row in result["rows"] if row["state"] == "observed")
    assert observed["observation_count"] == 2


def test_semantic_hash_is_input_order_independent():
    _, build, digest = coverage_api()
    kwargs = dict(
        sources=["a", "b"],
        integrated_sources={"a"},
        observations=[{"source_id": "a", "entity_id": "e1"}],
        unknown_sources=set(),
        unresolved_sources=set(),
    )
    first = build(entities=[entity("e1"), entity("e2")], **kwargs)
    second = build(
        entities=[entity("e2"), entity("e1")],
        observations=list(reversed(kwargs["observations"])),
        sources=list(reversed(kwargs["sources"])),
        integrated_sources=kwargs["integrated_sources"],
        unknown_sources=kwargs["unknown_sources"],
        unresolved_sources=kwargs["unresolved_sources"],
    )
    assert digest(first) == digest(second)
