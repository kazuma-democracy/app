import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_free_monthly_window_is_pinned_before_performance():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["artifact_version"] == "m3.3c0-free-monthly-prereg-v0.1"
    assert value["issue"] == 78
    assert value["benchmark_id"] == "JPX:TOPIX_TOTAL_RETURN:6000"
    assert value["benchmark_effective_date"] == "2026-07-31"
    assert value["benchmark_semantic_mapping_sha256"] == "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409"
    assert value["portfolio_definition_cutoff"] == "2026-09-29_CLOSE"
    assert value["execution_start_valuation"] == "2026-09-30_CLOSE"
    assert value["evaluation_start"] == "2026-10-01"
    assert value["evaluation_end"] == "2026-10-30"
    assert value["benchmark_period"] == "2026-10"
    assert value["return_basis"] == "MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY"
    assert value["rebalance_policy"] == "NONE_AFTER_INITIAL_ALLOCATION"
    assert value["purchase_authorized"] is False
    assert value["subscription_authorized"] is False
    assert value["selected_period_rows_ingested"] is False
    assert value["implementation_gate"] == "READY_FOR_ISSUE_56_AFTER_PREREG_VERIFICATION"
    forbidden = {
        "candidate_return",
        "benchmark_return",
        "excess_return",
        "tracking_error",
        "cumulative_return",
        "selected_period_performance",
    }
    assert forbidden.isdisjoint(value)
