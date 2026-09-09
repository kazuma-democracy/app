from __future__ import annotations

import importlib
import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "m3-3b2-policy-compiler-v0.1.json"
BENCHMARK_SHA = "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409"
SCREENING_SHA = "aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c"
POLICY_SHA = "7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c"


def load_config_direct() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def minimal_inputs() -> tuple[dict, dict, dict]:
    config = load_config_direct()
    benchmark = {
        "manifest": {"semantic_mapping_sha256": BENCHMARK_SHA},
        "rows": [
            {"security_id": "1000", "benchmark_weight": "0.600000000000", "mapping_state": "mapped", "canonical_entity_id": "wa:1", "canonical_review_state": "CONFIRMED"},
            {"security_id": "2000", "benchmark_weight": "0.400000000000", "mapping_state": "mapped", "canonical_entity_id": "wa:2", "canonical_review_state": "CONFIRMED"},
        ],
    }
    screening = {
        "tse_screening_sha256": SCREENING_SHA,
        "views": [
            {
                "entity_id": "wa:1", "profile_id": "example:strict-military-avoidance", "profile_version": "1",
                "policy_sha256": POLICY_SHA, "decision": "NONE", "identity_state": "confirmed",
                "claim_results": [], "coverage_state_counts": {"observed": 1, "no_match": 0, "unknown": 0, "unresolved_identity": 0, "not_integrated": 0},
            },
            {
                "entity_id": "wa:2", "profile_id": "example:strict-military-avoidance", "profile_version": "1",
                "policy_sha256": POLICY_SHA, "decision": "WATCH", "identity_state": "confirmed",
                "claim_results": [{"claim_id": "claim:2", "decision": "WATCH", "rule_refs": [], "uncertainty_ref": "uncertainty.unknown"}],
                "coverage_state_counts": {"observed": 1, "no_match": 0, "unknown": 0, "unresolved_identity": 0, "not_integrated": 1},
            },
        ],
    }
    return benchmark, screening, config


def test_config_preregisters_three_arms_and_no_market_input() -> None:
    config = load_config_direct()
    assert config["market_data_inputs_allowed"] is False
    assert [arm["arm_id"] for arm in config["arms"]] == ["P0", "P1", "P2"]
    assert config["arms"][0]["decision_multipliers"] == {"EXCLUDE": "1.0", "WATCH": "1.0", "NONE": "1.0"}
    assert config["arms"][1]["decision_multipliers"] == {"EXCLUDE": "0.0", "WATCH": "1.0", "NONE": "1.0"}
    assert config["arms"][2]["decision_multipliers"] == {"EXCLUDE": "0.0", "WATCH": "0.5", "NONE": "1.0"}


def test_wrong_benchmark_input_hash_blocks() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    benchmark = deepcopy(benchmark)
    benchmark["manifest"]["semantic_mapping_sha256"] = "0" * 64
    result = module.compile_policy_family(benchmark, screening, config)
    assert result["status"] == "BLOCK_INPUT_VERSION"


def test_duplicate_security_id_blocks_identity() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    benchmark["rows"].append(deepcopy(benchmark["rows"][0]))
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_IDENTITY"


def test_nonconfirmed_benchmark_identity_blocks() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    benchmark["rows"][0]["canonical_review_state"] = "UNRESOLVED"
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_IDENTITY"


def test_missing_strict_profile_view_blocks_identity() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    screening["views"] = screening["views"][:1]
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_IDENTITY"


def test_unsupported_decision_blocks_policy_instruction() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    screening["views"][0]["decision"] = "PASS"
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_POLICY_INSTRUCTION"


def test_multiplier_above_one_blocks_policy_instruction() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    config = deepcopy(config)
    config["arms"][2]["decision_multipliers"]["WATCH"] = "1.1"
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_POLICY_INSTRUCTION"


def test_profile_policy_hash_mismatch_blocks_input_version() -> None:
    module = importlib.import_module("wa_commons.portfolio.policy_compiler")
    benchmark, screening, config = minimal_inputs()
    screening["views"][0]["policy_sha256"] = "f" * 64
    assert module.compile_policy_family(benchmark, screening, config)["status"] == "BLOCK_INPUT_VERSION"
