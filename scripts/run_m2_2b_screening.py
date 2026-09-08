from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.policy.company_view import build_company_research_views, canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COVERAGE = ROOT / "artifacts" / "m2-coverage" / "coverage.json"
DEFAULT_GRAPH = ROOT / "artifacts" / "m1-reproduction" / "canonical-graph.json"
DEFAULT_BRIDGE = ROOT / "configs" / "m2-2b-identity-bridge-v0.1.json"
DEFAULT_POLICIES = ROOT / "schemas" / "examples" / "user-policy.examples.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "m2-screening" / "screening.json"

EXPECTED_M1_GRAPH_SHA256 = "0a4f9ed031eaa534e116dca9c441e08054be49047b4404832a14a48094cf2e15"
EXPECTED_COVERAGE_SHA256 = "41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403"
EXPECTED_BRIDGE_SHA256 = "f12fb5bddd8b8a3f99fa47cc6f7da54b1112657d5b9b8a56260690c5ecd1e10e"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def generate(*, coverage: dict, evidence_graph: dict, policies: list[dict], identity_bridge: dict) -> dict:
    if coverage.get("matrix_sha256") != EXPECTED_COVERAGE_SHA256:
        raise ValueError(
            f"#42 coverage snapshot changed: expected {EXPECTED_COVERAGE_SHA256}, got {coverage.get('matrix_sha256')}"
        )
    graph_sha = canonical_sha256(evidence_graph)
    if graph_sha != EXPECTED_M1_GRAPH_SHA256:
        raise ValueError(f"M1 Evidence Graph changed: expected {EXPECTED_M1_GRAPH_SHA256}, got {graph_sha}")
    bridge_sha = canonical_sha256(identity_bridge)
    if bridge_sha != EXPECTED_BRIDGE_SHA256:
        raise ValueError(f"M1.1 identity bridge changed: expected {EXPECTED_BRIDGE_SHA256}, got {bridge_sha}")

    screening = build_company_research_views(
        coverage_artifact=coverage,
        evidence_graph=evidence_graph,
        policies=policies,
        identity_bridge=identity_bridge,
    )
    if screening["evidence_graph_sha256"] != graph_sha:
        raise ValueError("screening graph hash diverged from the pinned input graph")
    if screening["coverage_matrix_sha256"] != EXPECTED_COVERAGE_SHA256:
        raise ValueError("screening coverage hash diverged from the pinned #42 artifact")
    if screening["identity_bridge_sha256"] != EXPECTED_BRIDGE_SHA256:
        raise ValueError("screening identity bridge hash diverged from the pinned bridge")

    return {
        "issue": 43,
        "artifact_version": "m2-2b-screening-artifact-v0.1",
        **screening,
        "interpretation": {
            "research_only": True,
            "none_is_not_pass": True,
            "none": "NONE means the selected profile produced no EXCLUDE/WATCH decision from canonical claims linked to this entity in this exact snapshot. It is not evidence that the company is clean, safe, peaceful, or free of relevant activity.",
            "coverage": "The #42 coverage states remain visible in every company/profile view and must be read alongside the policy decision.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic Issue #43 company-level policy research views")
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--bridge", type=Path, default=DEFAULT_BRIDGE)
    parser.add_argument("--policies", type=Path, default=DEFAULT_POLICIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    artifact = generate(
        coverage=load_json(args.coverage),
        evidence_graph=load_json(args.graph),
        policies=load_json(args.policies),
        identity_bridge=load_json(args.bridge),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "screening_sha256": artifact["screening_sha256"],
                "evidence_graph_sha256": artifact["evidence_graph_sha256"],
                "coverage_matrix_sha256": artifact["coverage_matrix_sha256"],
                "identity_bridge_sha256": artifact["identity_bridge_sha256"],
                "company_count": artifact["company_count"],
                "profile_count": artifact["profile_count"],
                "view_count": artifact["view_count"],
                "graph_claim_count": artifact["graph_claim_count"],
                "mapped_claim_count": artifact["mapped_claim_count"],
                "unmapped_claim_count": artifact["unmapped_claim_count"],
                "decision_counts_by_profile": artifact["decision_counts_by_profile"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
