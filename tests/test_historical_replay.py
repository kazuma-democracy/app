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


_PERIOD_META = {
    "2026-02": ("2026-01-30T15:30:00+09:00", "2025-12-30", "2026-01-30T16:20:00+09:00"),
    "2026-03": ("2026-02-27T15:30:00+09:00", "2025-12-30", "2026-01-30T16:20:00+09:00"),
    "2026-04": ("2026-03-31T15:30:00+09:00", "2026-01-30", "2026-02-27T16:20:00+09:00"),
    "2026-05": ("2026-04-30T15:30:00+09:00", "2026-02-27", "2026-03-31T16:20:00+09:00"),
    "2026-06": ("2026-05-29T15:30:00+09:00", "2026-03-31", "2026-04-30T16:20:00+09:00"),
    "2026-07": ("2026-06-30T15:30:00+09:00", "2026-04-30", "2026-05-29T16:20:00+09:00"),
    "2026-08": ("2026-07-31T15:30:00+09:00", "2026-05-29", "2026-06-30T16:20:00+09:00"),
}


def _candidate_for_period(period: str) -> dict:
    cutoff, effective_date, available_at = _PERIOD_META[period]
    candidate = _candidate(period)
    candidate["decision_cutoff"] = cutoff
    candidate["benchmark_snapshot"]["effective_date"] = effective_date
    candidate["benchmark_snapshot"]["available_at"] = available_at
    candidate["benchmark_snapshot"]["semantic_mapping_sha256"] = period.replace("-", "") + "a" * 58
    candidate["screening_snapshot"]["decision_cutoff"] = cutoff
    candidate["screening_snapshot"]["screening_sha256"] = period.replace("-", "") + "d" * 58
    return candidate


def test_freeze_selects_most_recent_qualified_consecutive_triple() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidates = [_candidate_for_period(p) for p in ("2026-04", "2026-05", "2026-06", "2026-07", "2026-08")]
    result = module.freeze_replay_window(candidates, _config())
    assert result["status"] == "HISTORICAL_REPLAY_WINDOW_FROZEN"
    assert result["window"] == ["2026-04", "2026-05", "2026-06"]
    assert len(result["window_semantic_sha256"]) == 64


def test_freeze_is_input_order_independent() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidates = [_candidate_for_period(p) for p in ("2026-04", "2026-05", "2026-06", "2026-07", "2026-08")]
    left = module.freeze_replay_window(candidates, _config())
    right = module.freeze_replay_window(list(reversed(candidates)), _config())
    assert left["window"] == right["window"]
    assert left["window_semantic_sha256"] == right["window_semantic_sha256"]


def test_nonconsecutive_qualified_months_do_not_freeze() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidates = [_candidate_for_period(p) for p in ("2026-02", "2026-04", "2026-06")]
    result = module.freeze_replay_window(candidates, _config())
    assert result["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"
    assert result["window"] == []
    assert len(result["candidate_results"]) == 3


def test_newer_metadata_block_does_not_hide_older_valid_triple() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    candidates = [_candidate_for_period(p) for p in ("2026-03", "2026-04", "2026-05", "2026-06", "2026-08")]
    candidates[-1]["benchmark_snapshot"] = None
    result = module.freeze_replay_window(candidates, _config())
    assert result["status"] == "HISTORICAL_REPLAY_WINDOW_FROZEN"
    assert result["window"] == ["2026-04", "2026-05", "2026-06"]
    august = next(item for item in result["candidate_results"] if item["evaluation_period"] == "2026-08")
    assert august["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"


class _ExplodingMarketMap(dict):
    def get(self, *args, **kwargs):  # pragma: no cover - should never run
        raise AssertionError("market payload was read before window freeze")

    def __getitem__(self, key):  # pragma: no cover - should never run
        raise AssertionError("market payload was read before window freeze")


def _frozen_window() -> dict:
    return {
        "status": "HISTORICAL_REPLAY_WINDOW_FROZEN",
        "window": ["2026-04", "2026-05", "2026-06"],
        "window_semantic_sha256": "f" * 64,
    }


def _arm(
    arm_id: str,
    period: str,
    weights: tuple[str, str],
) -> dict:
    policy_ids = {
        "P0": "control:topix",
        "P1": "example:strict-military-avoidance:minimal-intervention",
        "P2": "example:strict-military-avoidance:active-avoidance",
    }
    return {
        "arm_id": arm_id,
        "allocation_policy_id": policy_ids[arm_id],
        "allocation_policy_version": "1",
        "semantic_target_sha256": (period + arm_id).encode().hex().ljust(64, "0")[:64],
        "target_weights": [
            {"security_id": "TSE:1000", "target_weight": weights[0]},
            {"security_id": "TSE:2000", "target_weight": weights[1]},
        ],
        "metrics": {
            "active_share": "0.000000000000" if arm_id != "P2" else "0.300000000000",
            "reallocation_mass": "0.000000000000" if arm_id != "P2" else "0.300000000000",
        },
    }


def _policy_payload(period: str) -> dict:
    return {
        "status": "FROZEN_POLICY_FAMILY",
        "manifest": {
            "profile_id": "example:strict-military-avoidance",
            "profile_version": "1",
            "policy_sha256": "p" * 64,
        },
        "arms": [
            _arm("P0", period, ("0.6", "0.4")),
            _arm("P1", period, ("0.6", "0.4")),
            _arm("P2", period, ("0.3", "0.7")),
        ],
    }


def _market_payload(period: str, a_return: str, b_return: str, benchmark: str) -> dict:
    return {
        "status": "MONTHLY_RETURN_OK",
        "period": period,
        "benchmark_decimal_return": benchmark,
        "rows": [
            {
                "security_id": "TSE:1000",
                "state": "RETURN_OK_NO_ACTION",
                "total_wealth_return": a_return,
            },
            {
                "security_id": "TSE:2000",
                "state": "RETURN_OK_NO_ACTION",
                "total_wealth_return": b_return,
            },
        ],
    }


def _three_month_policy_map() -> dict:
    return {
        period: _policy_payload(period)
        for period in ("2026-04", "2026-05", "2026-06")
    }


def _three_month_market_map() -> dict:
    return {
        "2026-04": _market_payload("2026-04", "0.02", "0.00", "0.005"),
        "2026-05": _market_payload("2026-05", "-0.01", "0.03", "0.010"),
        "2026-06": _market_payload("2026-06", "0.01", "0.01", "-0.002"),
    }


def test_frozen_replay_rejects_unfrozen_window_before_market_access() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    result = module.run_frozen_replay(
        {"status": "BLOCK_HISTORICAL_REPLAY_COVERAGE", "window": []},
        {},
        _ExplodingMarketMap(),
        _config(),
    )
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_frozen_replay_computes_three_month_returns_deterministically() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    result = module.run_frozen_replay(
        _frozen_window(),
        _three_month_policy_map(),
        _three_month_market_map(),
        _config(),
    )
    assert result["status"] == "HISTORICAL_REPLAY_OK"
    by_arm = {item["arm_id"]: item for item in result["arms"]}
    assert by_arm["P0"]["cumulative_wealth"] == "1.028252720000"
    assert by_arm["P1"]["cumulative_wealth"] == "1.028252720000"
    assert by_arm["P2"]["cumulative_wealth"] == "1.034349080000"
    assert result["benchmark"]["cumulative_wealth"] == "1.013019900000"


def test_frozen_replay_blocks_missing_policy_month() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    policies = _three_month_policy_map()
    del policies["2026-05"]
    result = module.run_frozen_replay(
        _frozen_window(), policies, _three_month_market_map(), _config()
    )
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_frozen_replay_blocks_market_and_corporate_action_failures() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    market = _three_month_market_map()
    market["2026-05"] = {
        "status": "MONTHLY_RETURN_BLOCKED",
        "period": "2026-05",
        "rows": [],
    }
    blocked = module.run_frozen_replay(
        _frozen_window(), _three_month_policy_map(), market, _config()
    )
    assert blocked["status"] == "BLOCK_MARKET_DATA"

    market = _three_month_market_map()
    market["2026-05"]["status"] = "MONTHLY_RETURN_BLOCKED"
    market["2026-05"]["rows"][0]["state"] = "BLOCK_CORPORATE_ACTION"
    action = module.run_frozen_replay(
        _frozen_window(), _three_month_policy_map(), market, _config()
    )
    assert action["status"] == "BLOCK_CORPORATE_ACTION"


def test_frozen_replay_blocks_policy_semantics_drift() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    policies = _three_month_policy_map()
    policies["2026-05"]["arms"][2]["allocation_policy_version"] = "2"
    result = module.run_frozen_replay(
        _frozen_window(), policies, _three_month_market_map(), _config()
    )
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_frozen_replay_is_mapping_order_independent() -> None:
    module = importlib.import_module("wa_commons.portfolio.historical_replay")
    policies = _three_month_policy_map()
    market = _three_month_market_map()
    left = module.run_frozen_replay(
        _frozen_window(), policies, market, _config()
    )
    right = module.run_frozen_replay(
        _frozen_window(),
        dict(reversed(list(policies.items()))),
        dict(reversed(list(market.items()))),
        _config(),
    )
    assert left["semantic_payload_sha256"] == right["semantic_payload_sha256"]
    assert left["arms"] == right["arms"]
    assert left["benchmark"] == right["benchmark"]
