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
