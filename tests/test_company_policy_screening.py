from __future__ import annotations

import pytest


def screening_api():
    try:
        from wa_commons.policy.company_view import build_company_research_views
    except ModuleNotFoundError as exc:
        pytest.fail(f"company screening implementation missing: {exc}")
    return build_company_research_views


def policy(profile_id: str, *, uncertainty: str = "WATCH", military_decision: str = "NONE") -> dict:
    exclusions = []
    if military_decision != "NONE":
        exclusions.append(
            {
                "rule_id": f"{profile_id}:military",
                "description": "test military rule",
                "match": {
                    "categories": ["military_contract"],
                    "predicates": ["contract_subject_classification"],
                },
                "condition": {
                    "field": "claim.value.classification",
                    "operator": "eq",
                    "value": "military_specific",
                },
                "min_confidence": 0.8,
                "decision": military_decision,
            }
        )
    return {
        "schema_version": "0.1",
        "profile_id": profile_id,
        "profile_version": "1",
        "title": profile_id,
        "description": "test",
        "origin": {
            "kind": "example",
            "author": "test",
            "official_status": "not_official",
            "forked_from": None,
        },
        "default_decision": "NONE",
        "uncertainty": {"unknown": uncertainty, "disputed": uncertainty, "expired": uncertainty},
        "exclusions": exclusions,
        "preferences": [],
    }


def claim(claim_id: str, corporate_number: str, *, status: str = "confirmed", classification: str = "military_specific") -> dict:
    return {
        "claim_id": claim_id,
        "subject": {"entity_id": f"jp:corporate-number:{corporate_number}", "jurisdiction": "JP"},
        "claim": {
            "category": "military_contract",
            "predicate": "contract_subject_classification",
            "value": {"classification": classification},
        },
        "evidence": [{"source_id": "jp-mod-procurement", "source_record_id": claim_id}],
        "adjudication": {"status": status, "confidence": 0.98 if status == "confirmed" else 0.0},
    }


def fixture_inputs():
    coverage = {
        "matrix_sha256": "coverage-hash",
        "matrix": {
            "entity_count": 2,
            "source_count": 2,
            "cell_count": 4,
            "rows": [
                {"entity_id": "wa:org:jp:tse:1001", "source_id": "jp-mod-procurement", "state": "observed", "observation_count": 2},
                {"entity_id": "wa:org:jp:tse:1001", "source_id": "jp-political-finance", "state": "unresolved_identity", "observation_count": 0},
                {"entity_id": "wa:org:jp:tse:1002", "source_id": "jp-mod-procurement", "state": "no_match", "observation_count": 0},
                {"entity_id": "wa:org:jp:tse:1002", "source_id": "jp-political-finance", "state": "not_integrated", "observation_count": 0},
            ],
        },
    }
    graph = {
        "reproduction_version": "test-graph-v1",
        "claims": [
            claim("claim-confirmed", "1111111111111"),
            claim("claim-disputed", "1111111111111", status="disputed"),
        ],
    }
    bridge = {
        "bridge_version": "test-bridge-v1",
        "links": [
            {"entity_id": "wa:org:jp:tse:1001", "corporate_number": "1111111111111", "review_state": "CONFIRMED"},
            {"entity_id": "wa:org:jp:tse:1002", "corporate_number": "2222222222222", "review_state": "CONFIRMED"},
        ],
    }
    policies = [
        policy("strict", military_decision="EXCLUDE"),
        policy("watch", military_decision="WATCH"),
        policy("narrow", uncertainty="NONE", military_decision="NONE"),
    ]
    return coverage, graph, bridge, policies


def test_emits_one_view_for_every_company_and_profile():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    assert result["company_count"] == 2
    assert result["profile_count"] == 3
    assert result["view_count"] == 6
    assert len(result["views"]) == 6
    assert {(v["entity_id"], v["profile_id"]) for v in result["views"]} == {
        (entity_id, profile_id)
        for entity_id in ("wa:org:jp:tse:1001", "wa:org:jp:tse:1002")
        for profile_id in ("strict", "watch", "narrow")
    }


def test_company_aggregation_uses_exclude_watch_none_priority():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    by_key = {(v["entity_id"], v["profile_id"]): v for v in result["views"]}
    assert by_key[("wa:org:jp:tse:1001", "strict")]["decision"] == "EXCLUDE"
    assert by_key[("wa:org:jp:tse:1001", "watch")]["decision"] == "WATCH"
    assert by_key[("wa:org:jp:tse:1001", "narrow")]["decision"] == "NONE"
    assert by_key[("wa:org:jp:tse:1002", "strict")]["decision"] == "NONE"


def test_every_non_none_result_has_claim_rule_or_uncertainty_basis_and_source_refs():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    for view in result["views"]:
        for item in view["claim_results"]:
            if item["decision"] == "NONE":
                continue
            assert item["claim_id"]
            assert item["source_ids"] == ["jp-mod-procurement"]
            assert item["rule_refs"] or item["uncertainty_ref"] in {
                "uncertainty.unknown",
                "uncertainty.disputed",
                "uncertainty.expired",
            }


def test_coverage_uncertainty_is_preserved_even_when_company_decision_is_none():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    view = next(v for v in result["views"] if v["entity_id"] == "wa:org:jp:tse:1002" and v["profile_id"] == "strict")
    assert view["decision"] == "NONE"
    assert view["coverage_states"] == {
        "jp-mod-procurement": "no_match",
        "jp-political-finance": "not_integrated",
    }
    assert view["coverage_state_counts"]["no_match"] == 1
    assert view["coverage_state_counts"]["not_integrated"] == 1
    assert "NONE is not PASS" in view["reasoning"]


def test_zero_claim_company_never_gets_pass_clean_or_safe_fields():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    view = next(v for v in result["views"] if v["entity_id"] == "wa:org:jp:tse:1002" and v["profile_id"] == "narrow")
    assert view["decision"] == "NONE"
    assert view["claim_results"] == []
    assert not any(key in view for key in ("pass", "safe", "clean", "moral_score"))


def test_same_snapshot_records_distinct_policy_hashes_and_pairwise_comparison():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    result = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    hashes = {p["policy_sha256"] for p in result["policies"]}
    assert len(hashes) == 3
    assert len(result["policy_comparison"]) == 3
    assert all(item["same_evidence_snapshot"] is True for item in result["policy_comparison"])


def test_semantic_screening_hash_is_input_order_independent():
    build = screening_api()
    coverage, graph, bridge, policies = fixture_inputs()
    first = build(coverage_artifact=coverage, evidence_graph=graph, policies=policies, identity_bridge=bridge)
    shuffled_coverage = {**coverage, "matrix": {**coverage["matrix"], "rows": list(reversed(coverage["matrix"]["rows"]))}}
    shuffled_graph = {**graph, "claims": list(reversed(graph["claims"]))}
    shuffled_bridge = {**bridge, "links": list(reversed(bridge["links"]))}
    second = build(
        coverage_artifact=shuffled_coverage,
        evidence_graph=shuffled_graph,
        policies=list(reversed(policies)),
        identity_bridge=shuffled_bridge,
    )
    assert first["screening_sha256"] == second["screening_sha256"]
