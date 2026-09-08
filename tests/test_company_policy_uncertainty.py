from __future__ import annotations

import pytest

from wa_commons.policy.company_view import build_company_research_views


def strict_policy() -> dict:
    return {
        "schema_version": "0.1",
        "profile_id": "test:strict",
        "profile_version": "1",
        "title": "strict",
        "description": "strict fixture",
        "origin": {"kind": "example", "author": "test", "official_status": "not_official", "forked_from": None},
        "default_decision": "NONE",
        "uncertainty": {"unknown": "WATCH", "disputed": "WATCH", "expired": "WATCH"},
        "exclusions": [
            {
                "rule_id": "exclude-confirmed-military",
                "description": "fixture",
                "match": {
                    "categories": ["military_contract"],
                    "predicates": ["contract_subject_classification"],
                },
                "condition": {"field": "claim.value.classification", "operator": "eq", "value": "military_specific"},
                "min_confidence": 0.8,
                "decision": "EXCLUDE",
            }
        ],
        "preferences": [],
    }


def claim(claim_id: str, status: str) -> dict:
    return {
        "claim_id": claim_id,
        "subject": {"entity_id": "jp:corporate-number:1111111111111", "jurisdiction": "JP"},
        "claim": {
            "category": "military_contract",
            "predicate": "contract_subject_classification",
            "value": {"classification": "military_specific"},
        },
        "evidence": [{"source_id": "jp-mod-procurement"}],
        "adjudication": {"status": status, "confidence": 0.98 if status == "confirmed" else 0.0},
    }


def inputs(claims: list[dict]):
    coverage = {
        "matrix_sha256": "coverage",
        "matrix": {
            "entity_count": 1,
            "rows": [
                {
                    "entity_id": "wa:org:jp:tse:1001",
                    "source_id": "jp-mod-procurement",
                    "state": "observed",
                    "observation_count": 1,
                }
            ],
        },
    }
    graph = {"reproduction_version": "fixture", "claims": claims}
    bridge = {
        "bridge_version": "fixture",
        "links": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "corporate_number": "1111111111111",
                "review_state": "CONFIRMED",
            }
        ],
    }
    return coverage, graph, bridge


@pytest.mark.parametrize("status", ["unknown", "disputed", "expired"])
def test_uncertain_claim_cannot_become_exclude_at_company_level(status: str) -> None:
    coverage, graph, bridge = inputs([claim(f"claim-{status}", status)])
    result = build_company_research_views(
        coverage_artifact=coverage,
        evidence_graph=graph,
        policies=[strict_policy()],
        identity_bridge=bridge,
    )
    view = result["views"][0]
    assert view["decision"] == "WATCH"
    assert view["claim_results"][0]["decision"] == "WATCH"
    assert view["claim_results"][0]["rule_refs"] == []
    assert view["claim_results"][0]["uncertainty_ref"] == f"uncertainty.{status}"


def test_confirmed_exclude_dominates_watch_but_both_claim_traces_remain_visible() -> None:
    coverage, graph, bridge = inputs([
        claim("claim-confirmed", "confirmed"),
        claim("claim-disputed", "disputed"),
    ])
    result = build_company_research_views(
        coverage_artifact=coverage,
        evidence_graph=graph,
        policies=[strict_policy()],
        identity_bridge=bridge,
    )
    view = result["views"][0]
    assert view["decision"] == "EXCLUDE"
    assert [(item["claim_id"], item["decision"]) for item in view["claim_results"]] == [
        ("claim-confirmed", "EXCLUDE"),
        ("claim-disputed", "WATCH"),
    ]
    confirmed = view["claim_results"][0]
    disputed = view["claim_results"][1]
    assert confirmed["rule_refs"] == ["exclude-confirmed-military"]
    assert disputed["uncertainty_ref"] == "uncertainty.disputed"
