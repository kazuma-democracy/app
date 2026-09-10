from pathlib import Path

from wa_commons.portfolio.historical_replay import load_historical_replay_config


CONFIG_PATH = Path("configs/m3-3c0-historical-replay-v0.2.json")
SOURCE_REGISTRY_PATH = Path("docs/SOURCE_REGISTRY.md")


def test_v02_records_original_q1_preregistration_and_later_contamination() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    assert config["artifact_version"] == "m3.3c0-historical-replay-v0.2"
    assert config["allocation_source"]["kind"] == "ISHARES_1475_POINT_IN_TIME"
    assert config["headline_candidate_periods"] == ["2026-01", "2026-02", "2026-03"]
    assert config["engineering_validation_periods"] == [
        "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"
    ]
    assert config["preselection_contaminated_periods"] == ["2026-01", "2026-02", "2026-03"]
    assert config["future_holdout_periods"] == ["2026-10"]
    assert config["market_values_allowed_during_selection"] is False
    assert config["performance_values_allowed_during_selection"] is False
    assert config["paper_only"] is True
    assert config["real_money_authority"] is False


from copy import deepcopy

from wa_commons.portfolio.historical_replay import freeze_replay_window, qualify_candidate_month


_PERIODS = {
    "2026-01": ("2025-12-30T15:30:00+09:00", "2025-12-30"),
    "2026-02": ("2026-01-30T15:30:00+09:00", "2026-01-30"),
    "2026-03": ("2026-02-27T15:30:00+09:00", "2026-02-27"),
    "2026-04": ("2026-03-31T15:30:00+09:00", "2026-03-31"),
    "2026-08": ("2026-07-31T15:30:00+09:00", "2026-07-31"),
    "2026-10": ("2026-09-30T15:30:00+09:00", "2026-09-30"),
}


def _uncontaminated_config() -> dict:
    config = load_historical_replay_config(CONFIG_PATH)
    config["preselection_contaminated_periods"] = []
    return config


def _candidate(period: str) -> dict:
    cutoff, as_of_date = _PERIODS[period]
    return {
        "evaluation_period": period,
        "decision_cutoff": cutoff,
        "control_source_metadata": {
            "kind": "ISHARES_1475_POINT_IN_TIME",
            "as_of_date": as_of_date,
            "available_at": cutoff.replace("15:30:00", "14:00:00"),
            "exists": True,
            "locator": f"fixture://blackrock/1475/{as_of_date}",
            "source_sha256": "a" * 64,
            "rights_state": "LOCAL_RESEARCH_ALLOWED",
        },
        "identity_source_metadata": {
            "availability_complete": True,
            "semantic_source_sha256": "b" * 64,
            "identity_semantic_sha256": "d" * 64,
        },
        "evidence_source_metadata": {
            "availability_complete": True,
            "semantic_source_sha256": "c" * 64,
            "identity_semantic_sha256": "d" * 64,
        },
        "market_source_metadata": {
            "start_price": {"exists": True, "locator": f"fixture://jpx/start/{period}"},
            "end_price": {"exists": True, "locator": f"fixture://jpx/end/{period}"},
            "benchmark": {"exists": True, "locator": f"fixture://jpx/topix/{period}"},
            "action_detector": {"exists": True, "locator": f"fixture://jpx/actions/{period}"},
        },
    }


def test_v02_candidate_qualifies_from_metadata_only() -> None:
    config = _uncontaminated_config()
    result = qualify_candidate_month(_candidate("2026-01"), config)
    assert result["status"] == "CANDIDATE_QUALIFIED"


def test_v02_control_available_after_cutoff_blocks() -> None:
    config = _uncontaminated_config()
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"]["available_at"] = "2025-12-30T16:00:00+09:00"
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_EVIDENCE_CUTOFF"
    assert result["blockers"] == ["CONTROL_AVAILABLE_AFTER_CUTOFF"]


def test_v02_missing_original_availability_never_uses_as_of_date_as_substitute() -> None:
    config = _uncontaminated_config()
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"].pop("available_at")
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_EVIDENCE_CUTOFF"
    assert result["blockers"] == ["CONTROL_AVAILABILITY_UNVERIFIED"]


def test_v02_rights_uncertainty_blocks() -> None:
    config = _uncontaminated_config()
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"]["rights_state"] = "REVIEW_REQUIRED"
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_SOURCE_RIGHTS"


def test_v02_identity_source_mismatch_blocks() -> None:
    config = _uncontaminated_config()
    candidate = _candidate("2026-01")
    candidate["evidence_source_metadata"]["identity_semantic_sha256"] = "e" * 64
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"
    assert result["blockers"] == ["IDENTITY_HASH_MISMATCH"]


def test_v02_performance_field_blocks_before_selection() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    candidate = _candidate("2026-01")
    candidate["leak"] = {"portfolio_return": "0.10"}
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"
    assert result["blockers"] == ["PERFORMANCE_FIELD_PRESENT"]


def test_v02_freezes_exact_q1_only_when_all_three_qualify() -> None:
    config = _uncontaminated_config()
    result = freeze_replay_window(
        [_candidate("2026-03"), _candidate("2026-01"), _candidate("2026-02")],
        config,
    )
    assert result["status"] == "HISTORICAL_REPLAY_WINDOW_FROZEN"
    assert result["window"] == ["2026-01", "2026-02", "2026-03"]
    assert len(result["window_semantic_sha256"]) == 64
    serialized = str(result)
    assert "benchmark_return" not in serialized
    assert "portfolio_return" not in serialized


def test_v02_does_not_substitute_another_window_when_q1_month_blocks() -> None:
    config = _uncontaminated_config()
    blocked = _candidate("2026-02")
    blocked["control_source_metadata"]["rights_state"] = "REVIEW_REQUIRED"
    result = freeze_replay_window(
        [_candidate("2026-01"), blocked, _candidate("2026-03")],
        config,
    )
    assert result["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"
    assert result["window"] == []
    feb = next(item for item in result["candidate_results"] if item["evaluation_period"] == "2026-02")
    assert feb["status"] == "BLOCK_SOURCE_RIGHTS"


def test_v02_engineering_and_holdout_periods_never_qualify() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    for period, reason in (("2026-04", "ENGINEERING_VALIDATION_PERIOD"), ("2026-08", "ENGINEERING_VALIDATION_PERIOD"), ("2026-10", "FUTURE_HOLDOUT_PERIOD")):
        result = qualify_candidate_month(_candidate(period), config)
        assert result["status"] == "BLOCK_REPRODUCIBILITY"
        assert result["blockers"] == [reason]


def test_v02_window_hash_is_input_order_independent() -> None:
    config = _uncontaminated_config()
    candidates = [_candidate("2026-01"), _candidate("2026-02"), _candidate("2026-03")]
    first = freeze_replay_window(candidates, config)
    second = freeze_replay_window(list(reversed(candidates)), config)
    assert first["window_semantic_sha256"] == second["window_semantic_sha256"]


import hashlib
import json


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _execution_policy() -> dict:
    base_rows = [
        {"security_id": "TSE:1001", "benchmark_weight": "0.200000000000",
         "target_weight": "0.200000000000", "instruction": "NEUTRAL", "multiplier": "1.000000000000"},
        {"security_id": "TSE:1002", "benchmark_weight": "0.800000000000",
         "target_weight": "0.800000000000", "instruction": "NEUTRAL", "multiplier": "1.000000000000"},
    ]
    p2_rows = [
        {"security_id": "TSE:1001", "benchmark_weight": "0.200000000000",
         "target_weight": "0.100000000000", "instruction": "UNDERWEIGHT", "multiplier": "0.500000000000"},
        {"security_id": "TSE:1002", "benchmark_weight": "0.800000000000",
         "target_weight": "0.900000000000", "instruction": "NEUTRAL", "multiplier": "1.000000000000"},
    ]
    arms = [
        {"arm_id": "P0", "allocation_policy_id": "control:topix", "allocation_policy_version": "1",
         "semantic_target_sha256": "0" * 64, "metrics": {"active_share": "0.000000000000"},
         "target_weights": base_rows},
        {"arm_id": "P1", "allocation_policy_id": "minimal", "allocation_policy_version": "1",
         "semantic_target_sha256": "1" * 64, "metrics": {"active_share": "0.000000000000"},
         "target_weights": base_rows},
        {"arm_id": "P2", "allocation_policy_id": "active", "allocation_policy_version": "1",
         "semantic_target_sha256": "2" * 64, "metrics": {"active_share": "0.100000000000"},
         "target_weights": p2_rows},
    ]
    return {
        "status": "FROZEN_POLICY_FAMILY",
        "manifest": {
            "profile_id": "example:strict-military-avoidance",
            "profile_version": "1", "policy_sha256": "a" * 64,
            "policy_family_sha256": "b" * 64,
        },
        "arms": arms,
    }


def _execution_inputs() -> tuple[dict, dict, dict, dict]:
    periods = ["2026-01", "2026-02", "2026-03"]
    window = {"status": "HISTORICAL_REPLAY_WINDOW_FROZEN", "window": periods,
              "window_semantic_sha256": "c" * 64}
    policy = _execution_policy()
    semantics = {
        "profile_id": policy["manifest"]["profile_id"],
        "profile_version": policy["manifest"]["profile_version"],
        "policy_sha256": policy["manifest"]["policy_sha256"],
        "arms": [
            {"arm_id": arm["arm_id"], "allocation_policy_id": arm["allocation_policy_id"],
             "allocation_policy_version": arm["allocation_policy_version"]}
            for arm in policy["arms"]
        ],
    }
    semantics_sha = _sha(semantics)
    target_months = []
    for period in periods:
        target_months.append({
            "period": period, "control_snapshot_sha256": "d" * 64,
            "control_mapping_sha256": "e" * 64, "identity_semantic_sha256": "f" * 64,
            "screening_sha256": "1" * 64, "evidence_provenance_sha256": "2" * 64,
            "policy_family_sha256": policy["manifest"]["policy_family_sha256"],
            "policy_payload_sha256": _sha(policy), "policy_semantics_sha256": semantics_sha,
            "direct_changed_security_ids": {"P1": [], "P2": ["TSE:1001"]},
        })
    targets = {
        "status": "HISTORICAL_REPLAY_TARGETS_FROZEN", "window": periods,
        "window_semantic_sha256": window["window_semantic_sha256"],
        "policy_semantics": semantics, "policy_semantics_sha256": semantics_sha,
        "months": target_months,
    }
    policies = {period: deepcopy(policy) for period in periods}
    markets = {
        period: {
            "status": "PROXY_MARKET_BUNDLE_OK",
            "security_returns": {
                "status": "SECURITY_RETURNS_OK",
                "rows": [
                    {"security_id": "TSE:1475", "state": "RETURN_OK_NO_ACTION",
                     "total_wealth_return": "0.010000000000"},
                    {"security_id": "TSE:1001", "state": "RETURN_OK_NO_ACTION",
                     "total_wealth_return": "0.020000000000"},
                ],
            },
            "topix_roi": {"status": "BENCHMARK_ROI_OK", "decimal_return": "0.009000000000"},
        }
        for period in periods
    }
    return window, targets, policies, markets


def test_v02_execution_separates_policy_effect_from_topix_tracking() -> None:
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay
    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, markets = _execution_inputs()
    result = run_investable_proxy_replay(window, targets, policies, markets, config)
    assert result["status"] == "HISTORICAL_REPLAY_OK"
    financial = result["months"][0]["financial"]
    assert financial["p0_return"] == "0.010000000000"
    assert financial["p0_tracking_difference_vs_topix"] == "0.001000000000"
    p2 = next(item for item in financial["arms"] if item["arm_id"] == "P2")
    assert p2["portfolio_return"] == "0.008750000000"
    assert p2["policy_effect_vs_p0"] == "-0.001250000000"


def test_v02_execution_rejects_unfrozen_targets_before_market_access() -> None:
    from collections.abc import Mapping
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay

    class ExplodingMapping(Mapping):
        def __getitem__(self, key):
            raise AssertionError("market payload must not be read")
        def __iter__(self):
            raise AssertionError("market payload must not be iterated")
        def __len__(self):
            raise AssertionError("market payload must not be sized")

    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, _ = _execution_inputs()
    targets["status"] = "BLOCK_REPRODUCIBILITY"
    result = run_investable_proxy_replay(window, targets, policies, ExplodingMapping(), config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_v02_execution_fails_closed_on_missing_or_blocked_changed_return() -> None:
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay
    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, markets = _execution_inputs()
    markets["2026-01"]["security_returns"]["rows"] = [
        markets["2026-01"]["security_returns"]["rows"][0]
    ]
    result = run_investable_proxy_replay(window, targets, policies, markets, config)
    assert result["status"] == "BLOCK_MARKET_DATA"

    window, targets, policies, markets = _execution_inputs()
    changed = markets["2026-01"]["security_returns"]["rows"][1]
    changed["state"] = "BLOCK_CORPORATE_ACTION"
    changed.pop("total_wealth_return")
    result = run_investable_proxy_replay(window, targets, policies, markets, config)
    assert result["status"] == "BLOCK_CORPORATE_ACTION"


def test_v02_execution_blocks_missing_p0_or_invalid_topix() -> None:
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay
    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, markets = _execution_inputs()
    markets["2026-01"]["security_returns"]["rows"] = [
        markets["2026-01"]["security_returns"]["rows"][1]
    ]
    assert run_investable_proxy_replay(window, targets, policies, markets, config)["status"] == "BLOCK_MARKET_DATA"

    window, targets, policies, markets = _execution_inputs()
    markets["2026-01"]["topix_roi"] = {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN"}
    assert run_investable_proxy_replay(window, targets, policies, markets, config)["status"] == "BLOCK_MARKET_DATA"


def test_v02_execution_blocks_policy_semantics_drift() -> None:
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay
    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, markets = _execution_inputs()
    policies["2026-02"]["manifest"]["policy_sha256"] = "9" * 64
    result = run_investable_proxy_replay(window, targets, policies, markets, config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"


def test_v02_execution_hash_is_input_order_independent() -> None:
    from wa_commons.portfolio.historical_replay import run_investable_proxy_replay
    config = load_historical_replay_config(CONFIG_PATH)
    window, targets, policies, markets = _execution_inputs()
    first = run_investable_proxy_replay(window, targets, policies, markets, config)
    policies = dict(reversed(list(policies.items())))
    markets = dict(reversed(list(markets.items())))
    for payload in markets.values():
        payload["security_returns"]["rows"].reverse()
    second = run_investable_proxy_replay(window, targets, policies, markets, config)
    assert first["semantic_payload_sha256"] == second["semantic_payload_sha256"]


def test_v02_preregistered_q1_is_durably_disqualified_after_preselection_inspection() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    assert config["preselection_contaminated_periods"] == ["2026-01", "2026-02", "2026-03"]
    result = qualify_candidate_month(_candidate("2026-01"), config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"
    assert result["blockers"] == ["PRESELECTION_MARKET_VALUE_INSPECTION"]


def test_v02_preselection_market_value_inspection_blocks_headline_candidate() -> None:
    config = _uncontaminated_config()
    candidate = _candidate("2026-01")
    candidate["selection_integrity"] = {
        "market_value_inspected_before_freeze": True,
        "note": "metadata-only boundary was breached during engineering inspection",
    }
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_REPRODUCIBILITY"
    assert result["blockers"] == ["PRESELECTION_MARKET_VALUE_INSPECTION"]
