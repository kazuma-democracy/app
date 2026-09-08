from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDENTITY_SHA = "589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f"
EXPECTED_DISPLAY_IDENTITY_SHA = "50a23df77b6b1fddb8d8634974105dcec0037fede6975273ddf647674d44af35"
EXPECTED_SCREENING_SHA = "7bdfec9c733aa84940e23a8d93153b27f604ee0efc799e6cd9edf628d073971a"
EXPECTED_GRAPH_SHA = "0a4f9ed031eaa534e116dca9c441e08054be49047b4404832a14a48094cf2e15"
EXPECTED_COVERAGE_SHA = "41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403"


def runner_module():
    try:
        import scripts.run_m2_2c_report as module
    except ModuleNotFoundError as exc:
        pytest.fail(f"Issue 44 report runner missing: {exc}")
    return module


def runner_api():
    return runner_module().generate


def fixture_inputs():
    profiles = [
        ("example:strict-military-avoidance", "Strict military-specific activity avoidance", "strict-sha"),
        ("example:controversial-weapons-only", "Narrow controversial-weapons focus", "narrow-sha"),
        ("example:transparency-first", "Transparency-first informational profile", "transparent-sha"),
    ]
    identities = []
    views = []
    for index in range(100):
        code = f"{1301 + index:04d}"
        entity_id = f"wa:org:jp:tse:{code}"
        identities.append(
            {
                "entity_id": entity_id,
                "canonical_name": f"Example Company {code}",
                "identifiers": [
                    {"scheme": "JPX_SECURITY_CODE", "value": code},
                    {"scheme": "JP_CORPORATE_NUMBER", "value": f"1{index:012d}"},
                ],
            }
        )
        for profile_id, _title, policy_sha in profiles:
            views.append(
                {
                    "entity_id": entity_id,
                    "profile_id": profile_id,
                    "profile_version": "1",
                    "policy_sha256": policy_sha,
                    "decision": "NONE",
                    "reasoning": (
                        "No canonical Evidence Graph claim is linked to this entity in this snapshot; "
                        "the company-level decision is NONE. NONE is not PASS, clean, or safe."
                    ),
                    "coverage_states": {
                        "jp-mod-procurement": "no_match",
                        "jp-political-finance": "unresolved_identity",
                        "sipri-arms-industry": "not_integrated",
                        "us-uflpa-entity-list": "not_integrated",
                        "oecd-ncp-cases": "not_integrated",
                    },
                    "claim_results": [],
                }
            )
    policies = [
        {
            "profile_id": profile_id,
            "profile_version": "1",
            "title": title,
            "description": title,
        }
        for profile_id, title, _sha in profiles
    ]
    screening = {
        "screening_sha256": EXPECTED_SCREENING_SHA,
        "evidence_graph_sha256": EXPECTED_GRAPH_SHA,
        "coverage_matrix_sha256": EXPECTED_COVERAGE_SHA,
        "identity_bridge_sha256": "f12fb5bddd8b8a3f99fa47cc6f7da54b1112657d5b9b8a56260690c5ecd1e10e",
        "company_count": 100,
        "profile_count": 3,
        "view_count": 300,
        "policies": [
            {"profile_id": profile_id, "profile_version": "1", "policy_sha256": policy_sha}
            for profile_id, _title, policy_sha in profiles
        ],
        "decision_counts_by_profile": {
            profile_id: {"EXCLUDE": 0, "WATCH": 0, "NONE": 100}
            for profile_id, _title, _sha in profiles
        },
        "policy_comparison": [
            {
                "left_profile_id": profiles[left][0],
                "right_profile_id": profiles[right][0],
                "same_evidence_snapshot": True,
                "decision_difference_count": 0,
            }
            for left, right in ((0, 1), (0, 2), (1, 2))
        ],
        "views": views,
    }
    identity_report = {"semantic_payload_sha256": EXPECTED_IDENTITY_SHA}
    return screening, {"claims": []}, identities, identity_report, policies


def test_pinned_display_identity_projection_recomputes_to_recorded_hash():
    module = runner_module()
    bundle = json.loads((ROOT / "configs" / "m2-2c-display-identities-v0.1.json").read_text(encoding="utf-8"))
    identities, identity_report = module.display_identity_inputs(bundle)
    assert len(identities) == 100
    assert bundle["display_identity_sha256"] == EXPECTED_DISPLAY_IDENTITY_SHA
    assert identity_report["semantic_payload_sha256"] == EXPECTED_IDENTITY_SHA
    assert identities[0]["entity_id"] == "wa:org:jp:tse:1301"
    assert identities[0]["canonical_name"] == "極洋"


def test_runner_generates_100_company_report_and_reproducibility_manifest():
    generate = runner_api()
    screening, graph, identities, identity_report, policies = fixture_inputs()
    report, manifest = generate(
        screening=screening,
        evidence_graph=graph,
        identities=identities,
        identity_report=identity_report,
        policies=policies,
        selected_profile_id="example:strict-military-avoidance",
    )
    detail_headings = [
        line for line in report.splitlines()
        if line.startswith("## Company ") and not line.startswith("## Company index")
    ]
    assert len(detail_headings) == 100
    assert manifest["company_count"] == 100
    assert manifest["profile_count"] == 3
    assert manifest["identity_semantic_payload_sha256"] == EXPECTED_IDENTITY_SHA
    assert manifest["screening_sha256"] == EXPECTED_SCREENING_SHA
    assert manifest["report_sha256"] == hashlib.sha256(report.encode("utf-8")).hexdigest()
    assert manifest["research_only"] is True
    assert manifest["none_is_not_pass"] is True


def test_runner_rejects_changed_identity_snapshot():
    generate = runner_api()
    screening, graph, identities, identity_report, policies = fixture_inputs()
    identity_report["semantic_payload_sha256"] = "changed"
    with pytest.raises(ValueError, match="identity semantic snapshot changed"):
        generate(
            screening=screening,
            evidence_graph=graph,
            identities=identities,
            identity_report=identity_report,
            policies=policies,
            selected_profile_id="example:strict-military-avoidance",
        )


def test_runner_rejects_identity_and_screening_entity_mismatch():
    generate = runner_api()
    screening, graph, identities, identity_report, policies = fixture_inputs()
    identities[0]["entity_id"] = "wa:org:jp:tse:DIFFERENT"
    with pytest.raises(ValueError, match="identity entities and #43 screening entities differ"):
        generate(
            screening=screening,
            evidence_graph=graph,
            identities=identities,
            identity_report=identity_report,
            policies=policies,
            selected_profile_id="example:strict-military-avoidance",
        )
