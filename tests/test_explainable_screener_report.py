from __future__ import annotations

from copy import deepcopy

import pytest


def report_api():
    try:
        from wa_commons.policy.screener_report import render_screener_report
    except ModuleNotFoundError as exc:
        pytest.fail(f"explainable screener report implementation missing: {exc}")
    return render_screener_report


def identity(entity_id: str, name: str, code: str, corporate_number: str) -> dict:
    return {
        "entity_id": entity_id,
        "canonical_name": name,
        "identifiers": [
            {"scheme": "JPX_SECURITY_CODE", "value": code},
            {"scheme": "JP_CORPORATE_NUMBER", "value": corporate_number},
        ],
    }


def policy(profile_id: str, title: str, description: str) -> dict:
    return {
        "profile_id": profile_id,
        "profile_version": "1",
        "title": title,
        "description": description,
    }


def coverage(mod_state: str) -> dict[str, str]:
    return {
        "jp-mod-procurement": mod_state,
        "jp-political-finance": "unresolved_identity",
        "sipri-arms-industry": "not_integrated",
        "us-uflpa-entity-list": "not_integrated",
        "oecd-ncp-cases": "not_integrated",
    }


def fixture_inputs():
    identities = [
        identity("wa:org:jp:tse:1301", "極洋", "1301", "1010401033225"),
        identity("wa:org:jp:tse:1332", "ニッスイ", "1332", "1010001016866"),
    ]
    policies = [
        policy(
            "example:strict-military-avoidance",
            "Strict military-specific activity avoidance",
            "Exclude confirmed military-specific activity.",
        ),
        policy(
            "example:transparency-first",
            "Transparency-first informational profile",
            "Surface military-contract evidence for review without excluding it.",
        ),
    ]
    claim = {
        "claim_id": "wc:claim:test-1",
        "subject": {
            "entity_id": "wa:org:jp:tse:1301",
            "canonical_name": "極洋",
            "jurisdiction": "JP",
            "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": "1301"}],
            "entity_resolution": {
                "method": "exact_security_code",
                "confidence": 1.0,
                "review_status": "confirmed",
                "match_evidence": ["JPX_SECURITY_CODE=1301"],
            },
        },
        "claim": {
            "category": "military_contract",
            "predicate": "contract_subject_classification",
            "value": {"classification": "military_specific"},
            "effective_from": "2026-04-01",
            "effective_to": None,
        },
        "evidence": [
            {
                "source_id": "jp-mod-procurement",
                "publisher": "Japan Ministry of Defense",
                "source_url": "https://example.invalid/mod.xlsx",
                "locator": "sheet=A,row=2",
                "evidence_date": "2026-04-01",
                "retrieved_at": "2026-08-21T13:00:00Z",
                "support": "direct",
                "source_type": "official_procurement",
            }
        ],
        "adjudication": {
            "status": "confirmed",
            "confidence": 0.98,
            "reasoning_summary": "The contract subject is classified as military-specific.",
        },
        "correction_history": [],
        "policy_context": None,
    }
    graph = {"claims": [claim]}

    strict_id = policies[0]["profile_id"]
    transparent_id = policies[1]["profile_id"]
    strict_claim_result = {
        "claim_id": "wc:claim:test-1",
        "adjudication_status": "confirmed",
        "decision": "EXCLUDE",
        "rule_refs": ["exclude-confirmed-military-specific"],
        "uncertainty_ref": None,
        "source_ids": ["jp-mod-procurement"],
        "preference_signals": [],
        "reasoning": "Matched exclusion rule.",
    }
    transparent_claim_result = {
        **strict_claim_result,
        "decision": "WATCH",
        "rule_refs": ["watch-military-evidence"],
        "reasoning": "Matched watch rule.",
    }
    none_reason = (
        "No canonical Evidence Graph claim is linked to this entity in this snapshot; "
        "the company-level decision is NONE. NONE is not PASS, clean, or safe."
    )
    screening = {
        "artifact_version": "m2-2b-screening-artifact-v0.1",
        "screening_sha256": "screening-fixture-sha",
        "evidence_graph_sha256": "graph-fixture-sha",
        "coverage_matrix_sha256": "coverage-fixture-sha",
        "identity_bridge_sha256": "bridge-fixture-sha",
        "company_count": 2,
        "profile_count": 2,
        "view_count": 4,
        "policies": [
            {"profile_id": strict_id, "profile_version": "1", "policy_sha256": "strict-sha"},
            {"profile_id": transparent_id, "profile_version": "1", "policy_sha256": "transparent-sha"},
        ],
        "policy_comparison": [
            {
                "left_profile_id": strict_id,
                "right_profile_id": transparent_id,
                "same_evidence_snapshot": True,
                "decision_difference_count": 1,
            }
        ],
        "decision_counts_by_profile": {
            strict_id: {"EXCLUDE": 1, "WATCH": 0, "NONE": 1},
            transparent_id: {"EXCLUDE": 0, "WATCH": 1, "NONE": 1},
        },
        "views": [
            {
                "entity_id": "wa:org:jp:tse:1301",
                "profile_id": strict_id,
                "profile_version": "1",
                "policy_sha256": "strict-sha",
                "decision": "EXCLUDE",
                "reasoning": "Company decision EXCLUDE is the highest-priority linked claim result.",
                "coverage_states": coverage("observed"),
                "claim_results": [strict_claim_result],
            },
            {
                "entity_id": "wa:org:jp:tse:1301",
                "profile_id": transparent_id,
                "profile_version": "1",
                "policy_sha256": "transparent-sha",
                "decision": "WATCH",
                "reasoning": "Company decision WATCH is the highest-priority linked claim result.",
                "coverage_states": coverage("observed"),
                "claim_results": [transparent_claim_result],
            },
            {
                "entity_id": "wa:org:jp:tse:1332",
                "profile_id": strict_id,
                "profile_version": "1",
                "policy_sha256": "strict-sha",
                "decision": "NONE",
                "reasoning": none_reason,
                "coverage_states": coverage("no_match"),
                "claim_results": [],
            },
            {
                "entity_id": "wa:org:jp:tse:1332",
                "profile_id": transparent_id,
                "profile_version": "1",
                "policy_sha256": "transparent-sha",
                "decision": "NONE",
                "reasoning": none_reason,
                "coverage_states": coverage("no_match"),
                "claim_results": [],
            },
        ],
    }
    return screening, graph, identities, policies


def render():
    screening, graph, identities, policies = fixture_inputs()
    return report_api()(
        screening_artifact=screening,
        evidence_graph=graph,
        identities=identities,
        policies=policies,
        selected_profile_id="example:strict-military-avoidance",
    )


def test_report_is_non_developer_readable_and_lists_every_company():
    text = render()
    assert "# WA Commons Explainable Company Screener" in text
    assert "Strict military-specific activity avoidance" in text
    assert "極洋" in text and "1301" in text
    assert "ニッスイ" in text and "1332" in text
    detail_headings = [
        line for line in text.splitlines()
        if line.startswith("## Company ") and not line.startswith("## Company index")
    ]
    assert len(detail_headings) == 2


def test_none_is_explicitly_not_pass_and_coverage_states_remain_visible():
    text = render()
    assert "NONE is not PASS" in text
    assert "jp-mod-procurement: `no_match`" in text
    assert "jp-political-finance: `unresolved_identity`" in text
    assert "sipri-arms-industry: `not_integrated`" in text
    lowered = text.lower()
    assert "no moral score, peace score, safety score" in lowered
    assert "peace score:" not in lowered
    assert "moral score:" not in lowered
    assert "safety score:" not in lowered
    assert "score =" not in lowered


def test_mapped_claim_renders_rule_evidence_card_and_challenge_path():
    text = render()
    assert "wc:claim:test-1" in text
    assert "exclude-confirmed-military-specific" in text
    assert "Japan Ministry of Defense" in text
    assert "sheet=A,row=2" in text
    assert "CONFIRMED" in text
    assert "https://github.com/kazuma-democracy/wa-commons/issues/new" in text


def test_no_claim_company_still_has_entity_scoped_challenge_path():
    assert "cite entity_id=`wa:org:jp:tse:1332`" in render()


def test_profile_comparison_uses_the_same_snapshot():
    text = render()
    assert "## Policy comparison — same evidence snapshot" in text
    assert "Strict military-specific activity avoidance" in text
    assert "Transparency-first informational profile" in text
    assert "graph-fixture-sha" in text
    assert "screening-fixture-sha" in text
    assert "Decision differences: **1**" in text


def test_report_is_input_order_independent():
    build = report_api()
    screening, graph, identities, policies = fixture_inputs()
    first = build(
        screening_artifact=screening,
        evidence_graph=graph,
        identities=identities,
        policies=policies,
        selected_profile_id="example:strict-military-avoidance",
    )
    shuffled = deepcopy(screening)
    shuffled["views"] = list(reversed(shuffled["views"]))
    shuffled["policy_comparison"] = list(reversed(shuffled["policy_comparison"]))
    second = build(
        screening_artifact=shuffled,
        evidence_graph={"claims": list(reversed(graph["claims"]))},
        identities=list(reversed(identities)),
        policies=list(reversed(policies)),
        selected_profile_id="example:strict-military-avoidance",
    )
    assert first == second
