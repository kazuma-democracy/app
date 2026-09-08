import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_monthly_return_contract_is_total_wealth_and_fail_closed():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = value["return_contract"]
    assert contract["basis"] == "MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY"
    assert contract["start_price_date"] == "2026-09-30"
    assert contract["end_price_date"] == "2026-10-30"
    assert contract["cash_distribution_treatment"] == "RETAIN_AS_CASH_TO_ENDPOINT"
    assert contract["synthetic_reinvestment"] is False
    assert contract["infer_action_from_price_jump"] is False
    assert contract["missing_value_treatment"] == "BLOCK"
    assert contract["name_only_relink"] == "PROHIBITED"
    held = set(value["terminal_states"]["held_security"])
    assert held == {
        "RETURN_OK_NO_ACTION",
        "RETURN_OK_ACTION_EXPLAINED",
        "BLOCK_START_PRICE",
        "BLOCK_END_PRICE",
        "BLOCK_DIVIDEND_EVIDENCE",
        "BLOCK_CORPORATE_ACTION",
        "BLOCK_IDENTITY",
    }
    snapshot = set(value["terminal_states"]["snapshot"])
    assert snapshot == {
        "BLOCK_SOURCE_UNAVAILABLE",
        "BLOCK_BENCHMARK_MONTHLY_RETURN",
        "BLOCK_RIGHTS_PUBLICATION",
    }
