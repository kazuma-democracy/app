from __future__ import annotations

from copy import deepcopy

import pytest


def report_api():
    try:
        from wa_commons.policy.screener_report import render_screener_report
    except ModuleNotFoundError as exc:
        pytest.fail(f"explainable screener report implementation missing: {exc}")
    return render_screener_report


def fixture_inputs():
    identities = [
        {
            "entity_id": "wa:org:jp:tse:1301",
            "canonical_name": "極洋",
            "identifiers": [
                {"scheme": "JPX_SECURITY_CODE", "value": "1301"},
                {"scheme": "JP_CORPORATE_NUMBER", "value": "1010401033225"},
            ],
        },
        {
            "entity_id": "wa:org:jp:tse:1332",
            "canonical_name": "ニッスイ",
            "identifiers": [
                {"scheme": "JPX_SECURITY_CODE", "value": "1332"},
                {"scheme": "JP_CORPORATE_NUMBER", "value": "1010001016866"},
            ],
        },
    ]
    policies = [
        {
            "profile_id": "example:strict-military-avoidance",
            "profile_version": "1",
            "title": "Strict military-specific activity avoidance",
            "description": "Exclude confirmed military-specific activity.",
        },
        {
            "profile_id": "example:transparency-first",
            "profile_version": "1",
            "title": "Transparency-first informational profile",
            "description": "Surface military-contract evidence for review without excluding it.",
        },
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
    evidence_graph = {"claims": [claim]}
    coverage_states = {
        "jp-mod-procurement": "observed",
        "jp-political-finance": "unresolved_identity",
        "sipri-arms-industry": "not_integrated",
        "us-uflpa-entity-list": "not_integrated",
        "oecd-ncp-cases": "not_integrated",
    }
    none_coverage = {
        "jp-mod-procurement": "no_match",
        "jp-political-finance": "unresolved_identity",
        "sipri-arms-industry": "not_integrated",
        "us-uflpa-entity-list": "not_integrated",
        "oecd-ncp-cases": "not_integrated",
    }
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
            {"profile_id": policies[0]["profile_id"], "profile_version": "1", "policy_sha256": "strict-sha"},
            {"profile_id": policies[1]["profile_id"], "profile_version": "1", "policy_sha256": "transparent-sha"},
        ],
        "policy_comparison": [
            {
                "left_profile_id": policies[0]["profile_id"],
                "right_profile_id": policies[1]["profile_id"],
                "same_evidence_snapshot": True,
                "decision_difference_count": 1,
            }
        ],
        "decision_counts_by_profile": {
            policies[0]["profile_id"]: {"EXCLUDE": 1, "WATCH": 0, "NONE": 1},
            policies[1]["profile_id"]: {"EXCLUDE": 0, "WATCH": 1, "NONE": 1},
        },
        "views": [
            {
                "entity_id": "wa:org:jp:tse:1301",
                "profile_id": policies[0]["profile_id"],
                "profile_version": "1",
                "policy_sha256": "strict-sha",
                "decision": "EXCLUDE",
                "reasoning": "Company decision EXCLUDE is the highest-priority linked claim result.",
                "coverage_states": coverage_states,
                "claim_results": [
                    {
                        "claim_id": "wc:claim:test-1",
                        "adjudication_status": "confirmed",
                        "decision": "EXCLUDE",
                        "rule_refs": ["exclude-confirmed-military-specific"],
                        "uncertainty_ref": None,
                        "source_ids": ["jp-mod-procurement"],
                        "preference_signals": [],
                        "reasoning": "Matched exclusion rule.",
                    }
                ],
            },
            {
                "entity_id": "wa:org:jp:tse:1301",
                "profile_id": policies[1]["profile_id"],
                "profile_version": "1",
                "policy_sha256": "transparent-sha",
                "decision": "WATCH",
                "reasoning": "Company decision WATCH is the highest-priority linked claim result.",
                "coverage_states": coverage_states,
                "claim_results": [
                    {
                        "claim_id": "wc:claim:test-1",
                        "adjudication_status": "confirmed",
                        "decision": "WATCH",
                        "rule_refs": ["watch-military-evidence"],
                        "uncertainty_ref": None,
                        "source_ids": ["jp-mod-procurement"],
                        "preference_signals": [],
                        "reasoning": "Matched watch rule.",
                    }
                ],
            },
            {
                "entity_id": "wa:org:jp:tse:1332",
                "profile_id": policies[0]["profile_id"],
                "profile_version": "1",
                "policy_sha256": "strict-sha",
                "decision": "NONE",
                "reasoning": "No canonical Evidence Graph claim is linked to this entity in this snapshot; the company-level decision is NONE. NONE is not PASS, clean, or safe.",
                "coverage_states": none_coverage,
                "claim_results": [],
            },
            {
                "entity_id": "wa:org:jp:tse:1332",
                "profile_id": policies[1]["profile_id"],
                "profile_version": "1",
                "policy_sha256": "transparent-sha",
                "decision": "NONE",
                "reasoning": "No canonical Evidence Graph claim is linked to this entity in this snapshot; the company-level decision is NONE. NONE is not PASS, clean, or safe.",
                "coverage_states": none_coverage,
                "claim_results": [],
            },
        ],
    }
    return screening, evidence_graph, identities, policies


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
    assert text.count("## Company ") == 2


def test_none_is_explicitly_not_pass_and_coverage_states_remain_visible():
    text = render()
    assert "NONE is not PASS" in text
    assert "jp-mod-procurement: `no_match`" in text
    assert "jp-political-finance: `unresolved_identity`" in text
    assert "sipri-arms-industry: `not_integrated`" in text
    lowered = text.lower()
    assert "peace score" not in lowered
    assert "moral score:" not in lowered
    assert "safety score" not in lowered


def test_mapped_claim_renders_rule_evidence_card_and_challenge_path():
    text = render()
    assert "wc:claim:test-1" in text
    assert "exclude-confirmed-military-specific" in text
    assert "Japan Ministry of Defense" in text
    assert "sheet=A,row=2" in text
    assert "CONFIRMED" in text
    assert "https://github.com/kazuma-democracy/wa-commons/issues/new" in text


def test_no_claim_company_still_has_entity_scoped_challenge_path():
    text = render()
    assert "cite entity_id=`wa:org:jp:tse:1332`" in text


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
