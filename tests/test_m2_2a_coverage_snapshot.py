from __future__ import annotations

import json
from pathlib import Path

from wa_commons.evidence.coverage import build_coverage_matrix, canonical_coverage_sha256

EXPECTED_SHA256 = "ab41c898747c8a725ecaa240f1bb1d759c5e8233b2f9c25543647b9a7950ac68"


def test_issue42_snapshot_reproduces_100_company_matrix():
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "m2-2a-coverage-v0.1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["identity_input"]["entity_count"] == 100
    assert config["identity_input"]["semantic_payload_sha256"] == "589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f"
    assert len(config["entities"]) == 100
    assert all(entity["review_state"] == "CONFIRMED" for entity in config["entities"])

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

    assert matrix["entity_count"] == 100
    assert matrix["source_count"] == 5
    assert matrix["cell_count"] == 500
    assert matrix["state_counts"] == {
        "no_match": 200,
        "not_integrated": 300,
        "observed": 0,
        "unknown": 0,
        "unresolved_identity": 0,
    }
    assert canonical_coverage_sha256(matrix) == EXPECTED_SHA256


def test_measured_integrated_sources_have_completion_provenance():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "configs" / "m2-2a-coverage-v0.1.json").read_text(encoding="utf-8"))
    integrated = [source for source in config["source_catalog"] if source["integration_state"] == "integrated"]
    assert {source["source_id"] for source in integrated} == {"jp-mod-procurement", "jp-political-finance"}
    for source in integrated:
        assert source["run_state"] == "complete"
        assert source["provenance"]
        assert source["coverage_interpretation"] == "no_match_is_not_clean_safe_or_pass"
