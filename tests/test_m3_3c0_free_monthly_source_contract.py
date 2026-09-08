import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_source_contract_is_zero_purchase_local_first_and_monthly():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = value["source_contract"]
    assert source["cost_model"] == "ZERO_PURCHASE_ZERO_SUBSCRIPTION"
    assert source["acquisition_mode"] == "MANUAL_MONTHLY_DOWNLOAD_THEN_LOCAL_HASH"
    assert source["raw_source_publication"] == "PROHIBITED_BY_PROJECT_POLICY"
    assert source["raw_storage"] == "LOCAL_ONLY"
    assert source["whole_market_daily_store"] is False
    assert source["automated_high_frequency_jpx_scraping"] is False
    roles = source["roles"]
    assert roles["start_price"]["source"] == "TSE_MONTHLY_STOCK_PRICE_TABLE"
    assert roles["start_price"]["period"] == "2026-09"
    assert roles["end_price"]["source"] == "TSE_MONTHLY_STOCK_PRICE_TABLE"
    assert roles["end_price"]["period"] == "2026-10"
    assert roles["benchmark"]["source"] == "JPX_DIVIDEND_INCLUDED_INDEX_MONTHLY_ROI"
    assert roles["benchmark"]["period"] == "2026-10"
    assert roles["action_detector"]["source"] == "TSE_MONTHLY_STATISTICS_REPORT"
    assert roles["held_security_primary_evidence"]["scope"] == "HELD_SECURITIES_ONLY"
