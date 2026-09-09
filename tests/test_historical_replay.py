from __future__ import annotations

import importlib


def _config() -> dict:
    return {
        "artifact_version": "m3.3c0-historical-replay-v0.1",
        "engineering_validation_periods": ["2026-07"],
        "future_holdout_periods": ["2026-10"],
        "required_market_source_roles": [
            "start_price", "end_price", "benchmark", "action_detector"
        ],
    }


def _candidate(period: str = "2026-06") -> dict:
    return {
        "evaluation_period": period,
        "decision_cutoff": "2026-05-29T15:30:00+09:00",
        "benchmark_snapshot": {
            "effective_date": "2026-03-31",
            "available_at": "2026-04-30T16:20:00+09:00",
            "semantic_mapping_sha256": "a" * 64,
            "source_sha256": "b" * 64,
            "identity_semantic_sha256": "c" * 64,
        },
        "screening_snapshot": {
            "decision_cutoff": "2026-05-29T15:30:00+09:00",
            "availability_complete": True,
            "screening_sha256": "d" * 64,
            "identity_semantic_sha256": "c" * 64,
            "evidence_provenance_sha256": "e" * 64,
        },
        "market_source_metadata": {
            role: {"exists": True, "locator": f"https://example.test/{role}"}
            for role in _config()["required_market_source_roles"]
        },
    }


def test_candidate_with_complete_metadata_qualifies() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    result = module.qualify_candidate_month(_candidate(), _config())
    assert result["status"] == "CANDIDATE_QUALIFIED"


def test_engineering_validation_period_blocks_reproducibility() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate("2026-07")
    candidate["decision_cutoff"] = "2026-06-30T15:30:00+09:00"
    candidate["screening_snapshot"]["decision_cutoff"] = candidate["decision_cutoff"]
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_future_holdout_period_blocks_reproducibility() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate("2026-10")
    candidate["decision_cutoff"] = "2026-09-30T15:30:00+09:00"
    candidate["screening_snapshot"]["decision_cutoff"] = candidate["decision_cutoff"]
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_missing_benchmark_blocks_historical_coverage() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate()
    candidate["benchmark_snapshot"] = None
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"


def test_late_benchmark_blocks_evidence_cutoff() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate()
    candidate["benchmark_snapshot"]["available_at"] = "2026-06-01T00:00:00+09:00"
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_EVIDENCE_CUTOFF"


def test_incomplete_screening_availability_blocks_evidence_cutoff() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate()
    candidate["screening_snapshot"]["availability_complete"] = False
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_EVIDENCE_CUTOFF"


def test_identity_hash_mismatch_blocks_reproducibility() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate()
    candidate["screening_snapshot"]["identity_semantic_sha256"] = "f" * 64
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_missing_market_source_blocks_historical_coverage() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidate = _candidate()
    candidate["market_source_metadata"]["action_detector"]["exists"] = False
    result = module.qualify_candidate_month(candidate, _config())
    assert result["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"


def test_performance_bearing_candidate_keys_are_rejected() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    forbidden = {
        "benchmark_decimal_return": "0.01",
        "close_price": "100",
        "total_wealth_return": "0.02",
        "performance": {"anything": 1},
    }
    for key, value in forbidden.items():
        candidate = _candidate()
        candidate[key] = value
        result = module.qualify_candidate_month(candidate, _config())
        assert result["status"] == "BLOCK_REPRODUCIBILITY", key
