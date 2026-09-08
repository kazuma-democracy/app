from __future__ import annotations

import json
from pathlib import Path

from scripts.run_m2_2a_coverage import generate as generate_coverage
from wa_commons.policy.company_view import build_company_research_views, canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRIDGE_SHA256 = "f12fb5bddd8b8a3f99fa47cc6f7da54b1112657d5b9b8a56260690c5ecd1e10e"
EXPECTED_COVERAGE_SHA256 = "41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_bridge_is_exactly_the_confirmed_fixed_100_company_cohort() -> None:
    coverage_config = load_json(ROOT / "configs" / "m2-2a-coverage-v0.1.json")
    bridge = load_json(ROOT / "configs" / "m2-2b-identity-bridge-v0.1.json")

    expected_entities = {row["entity_id"] for row in coverage_config["entities"]}
    links = bridge["links"]
    assert len(links) == 100
    assert {row["entity_id"] for row in links} == expected_entities
    assert len({row["corporate_number"] for row in links}) == 100
    assert all(len(row["corporate_number"]) == 13 and row["corporate_number"].isdigit() for row in links)
    assert all(row["review_state"] == "CONFIRMED" for row in links)
    assert bridge["source_identity_input"]["semantic_payload_sha256"] == (
        "589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f"
    )
    assert canonical_sha256(bridge) == EXPECTED_BRIDGE_SHA256


def test_completed_42_coverage_and_three_profiles_yield_explicit_zero_claim_views() -> None:
    coverage_config = load_json(ROOT / "configs" / "m2-2a-coverage-v0.1.json")
    coverage = generate_coverage(coverage_config)
    policies = load_json(ROOT / "schemas" / "examples" / "user-policy.examples.json")
    bridge = load_json(ROOT / "configs" / "m2-2b-identity-bridge-v0.1.json")

    assert coverage["matrix_sha256"] == EXPECTED_COVERAGE_SHA256
    assert len(policies) == 3

    result = build_company_research_views(
        coverage_artifact=coverage,
        evidence_graph={"reproduction_version": "empty-contract-fixture", "claims": []},
        policies=policies,
        identity_bridge=bridge,
    )
    assert result["company_count"] == 100
    assert result["profile_count"] == 3
    assert result["view_count"] == 300
    assert result["mapped_claim_count"] == 0
    assert all(view["decision"] == "NONE" for view in result["views"])
    assert all(view["claim_results"] == [] for view in result["views"])
    assert all(
        view["coverage_state_counts"] == {
            "observed": 0,
            "no_match": 1,
            "unknown": 0,
            "unresolved_identity": 1,
            "not_integrated": 3,
        }
        for view in result["views"]
    )
    assert all("NONE is not PASS" in view["reasoning"] for view in result["views"])
    assert len(result["policy_comparison"]) == 3
    assert all(item["same_evidence_snapshot"] is True for item in result["policy_comparison"])
