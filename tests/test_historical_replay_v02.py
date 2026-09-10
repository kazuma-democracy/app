from pathlib import Path

from wa_commons.portfolio.historical_replay import load_historical_replay_config


CONFIG_PATH = Path("configs/m3-3c0-historical-replay-v0.2.json")
SOURCE_REGISTRY_PATH = Path("docs/SOURCE_REGISTRY.md")


def test_v02_preregisters_clean_q1_before_returns() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    assert config["artifact_version"] == "m3.3c0-historical-replay-v0.2"
    assert config["allocation_source"]["kind"] == "ISHARES_1475_POINT_IN_TIME"
    assert config["headline_candidate_periods"] == ["2026-01", "2026-02", "2026-03"]
    assert config["engineering_validation_periods"] == [
        "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"
    ]
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
    config = load_historical_replay_config(CONFIG_PATH)
    result = qualify_candidate_month(_candidate("2026-01"), config)
    assert result["status"] == "CANDIDATE_QUALIFIED"


def test_v02_control_available_after_cutoff_blocks() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"]["available_at"] = "2025-12-30T16:00:00+09:00"
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_EVIDENCE_CUTOFF"
    assert result["blockers"] == ["CONTROL_AVAILABLE_AFTER_CUTOFF"]


def test_v02_missing_original_availability_never_uses_as_of_date_as_substitute() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"].pop("available_at")
    result = qualify_candidate_month(candidate, config)
    assert result["status"] != "CANDIDATE_QUALIFIED"
    assert result["blockers"] == ["INVALID_CONTROL_AVAILABILITY"]


def test_v02_rights_uncertainty_blocks() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
    candidate = _candidate("2026-01")
    candidate["control_source_metadata"]["rights_state"] = "REVIEW_REQUIRED"
    result = qualify_candidate_month(candidate, config)
    assert result["status"] == "BLOCK_SOURCE_RIGHTS"


def test_v02_identity_source_mismatch_blocks() -> None:
    config = load_historical_replay_config(CONFIG_PATH)
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
    config = load_historical_replay_config(CONFIG_PATH)
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
    config = load_historical_replay_config(CONFIG_PATH)
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
    config = load_historical_replay_config(CONFIG_PATH)
    candidates = [_candidate("2026-01"), _candidate("2026-02"), _candidate("2026-03")]
    first = freeze_replay_window(candidates, config)
    second = freeze_replay_window(list(reversed(candidates)), config)
    assert first["window_semantic_sha256"] == second["window_semantic_sha256"]
