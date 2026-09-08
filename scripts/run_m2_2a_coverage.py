from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.evidence.coverage import build_coverage_matrix, canonical_coverage_sha256

DEFAULT_CONFIG = Path("configs/m2-2a-coverage-v0.1.json")
DEFAULT_OUTPUT = Path("docs/results/M2_2A_COVERAGE_V01.json")


def generate(config: dict) -> dict:
    catalog = config["source_catalog"]
    sources = [source["source_id"] for source in catalog]
    integrated = {source["source_id"] for source in catalog if source["integration_state"] == "integrated"}
    unknown = {source["source_id"] for source in catalog if source["run_state"] == "unknown"}
    matrix = build_coverage_matrix(
        entities=config["entities"],
        sources=sources,
        integrated_sources=integrated,
        observations=config["linked_observations"],
        unknown_sources=unknown,
    )
    return {
        "issue": 42,
        "artifact_version": "m2-2a-coverage-artifact-v0.1",
        "identity_input": config["identity_input"],
        "source_catalog": catalog,
        "matrix_sha256": canonical_coverage_sha256(matrix),
        "matrix": matrix,
        "interpretation": {
            "coverage_only": True,
            "no_match": "The completed integrated snapshot supplied no linked observation for this entity. It is not a clean/safe/PASS judgment.",
            "unknown": "The source could not support a reliable coverage determination for this run.",
            "unresolved_identity": "Evidence could not be consequentially linked to the canonical entity under the identity policy.",
            "not_integrated": "The source is in the registry/coverage catalog but no adopted adapter is integrated in this snapshot.",
            "observed": "At least one source observation is linked to the canonical entity; this is a factual coverage state, not a policy result.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the deterministic Issue #42 evidence coverage artifact")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    artifact = generate(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "matrix_sha256": artifact["matrix_sha256"],
        "entity_count": artifact["matrix"]["entity_count"],
        "source_count": artifact["matrix"]["source_count"],
        "cell_count": artifact["matrix"]["cell_count"],
        "state_counts": artifact["matrix"]["state_counts"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
