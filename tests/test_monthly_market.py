from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "m3-3c-monthly-market-v0.1.json"
PYPROJECT = ROOT / "pyproject.toml"


def test_pyproject_pins_pypdf_runtime_dependency() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert '"pypdf==6.18.0"' in text


def test_monthly_config_pins_local_only_zero_cost_contract() -> None:
    assert CONFIG.exists()
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["artifact_version"] == "m3.3c-monthly-market-v0.1"
    assert value["issue"] == 56
    assert value["cost_model"] == "ZERO_PURCHASE_ZERO_SUBSCRIPTION"
    assert value["acquisition_mode"] == "EXPLICIT_LOCAL_FILES_ONLY"
    assert value["raw_storage"] == "LOCAL_ONLY"
    assert value["whole_market_daily_store"] is False
    assert value["automated_high_frequency_jpx_scraping"] is False

def test_monthly_config_preserves_exact_identity_and_fail_closed_states() -> None:
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["identity_mapping"] == "EXACT_JPX_SECURITY_CODE_ONLY"
    assert value["name_only_relink"] == "PROHIBITED"
    assert value["performance_publication_rights_default"] == "NOT_CLEARED"
    assert set(value["held_security_terminal_states"]) == {
        "RETURN_OK_NO_ACTION",
        "RETURN_OK_ACTION_EXPLAINED",
        "BLOCK_START_PRICE",
        "BLOCK_END_PRICE",
        "BLOCK_DIVIDEND_EVIDENCE",
        "BLOCK_CORPORATE_ACTION",
        "BLOCK_IDENTITY",
    }
    assert "BLOCK_BENCHMARK_MONTHLY_RETURN" in value["snapshot_terminal_states"]
    assert "BLOCK_SOURCE_UNAVAILABLE" in value["snapshot_terminal_states"]


def test_source_provenance_hashes_explicit_local_file(tmp_path: Path) -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"monthly-jpx-source")
    result = module.source_provenance(
        source,
        locator="https://www.jpx.co.jp/example/sample.pdf",
        retrieved_at="2026-09-09T16:30:00+09:00",
    )
    assert result["status"] == "SOURCE_OK"
    assert result["source_sha256"] == hashlib.sha256(b"monthly-jpx-source").hexdigest()
    assert result["source_locator"].startswith("https://www.jpx.co.jp/")
    assert result["retrieved_at"] == "2026-09-09T16:30:00+09:00"

def test_missing_local_source_fails_closed(tmp_path: Path) -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.source_provenance(
        tmp_path / "missing.pdf",
        locator="https://www.jpx.co.jp/example/missing.pdf",
        retrieved_at="2026-09-09T16:30:00+09:00",
    )
    assert result["status"] == "BLOCK_SOURCE_UNAVAILABLE"
    assert "source_sha256" not in result


def test_pdf_extractor_accepts_only_local_path_argument() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    params = set(inspect.signature(module.extract_pdf_text).parameters)
    assert params == {"path"}
    assert not any(token in params for token in {"url", "download", "session", "client"})


PRICE_TEXT = """Year/Month Code ...
2026/07 1301 KYOKUYO CO.,LTD. Fishery P loan 100 4,360.00 1 4,715.00 29 4,295.00 1 4,540.00 31 4,512.95 1,002,200 914,700 87,500 4,521,223,022 4,125,439,000 395,784,022 22
2026/07 2163 ARTNER CO.,LTD. Services ex-subscription right P loan 100 1,962.00 1 2,044.00 7 1,961.00 1 2,016.00 29 2,009.20 404,700 384,800 19,900 812,838,970 772,861,800 39,977,170 20
2026/07 2163 ARTNER CO.,LTD. Services ex-subscription right P loan 100 951.00 30 963.00 30 939.00 30 951.00 31 952.00 217,200 210,200 7,000 207,211,150 200,530,300 6,680,850 2
"""


def test_price_parser_extracts_normal_month_end_close() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_stock_price_table_text(
        PRICE_TEXT,
        period="2026-07",
        valuation_date="2026-07-31",
        security_ids=["TSE:1301"],
        price_role="end",
    )
    assert result["status"] == "PRICE_SNAPSHOT_OK"
    row = result["rows"][0]
    assert row["security_id"] == "TSE:1301"
    assert row["close_price"] == "4540.000000000000"
    assert row["close_date"] == "2026-07-31"
    assert row["source_row_count"] == 1


def test_price_parser_selects_unique_post_action_row_by_close_date() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_stock_price_table_text(
        PRICE_TEXT,
        period="2026-07",
        valuation_date="2026-07-31",
        security_ids=["TSE:2163"],
        price_role="end",
    )
    assert result["status"] == "PRICE_SNAPSHOT_OK"
    row = result["rows"][0]
    assert row["close_price"] == "951.000000000000"
    assert row["close_date"] == "2026-07-31"
    assert row["source_row_count"] == 2
    assert row["selection_reason"] == "UNIQUE_CLOSE_DATE_MATCH"


def test_price_parser_missing_requested_code_uses_role_specific_blocker() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    start = module.parse_stock_price_table_text(
        PRICE_TEXT, "2026-07", "2026-07-31", ["TSE:9999"], "start"
    )
    end = module.parse_stock_price_table_text(
        PRICE_TEXT, "2026-07", "2026-07-31", ["TSE:9999"], "end"
    )
    assert start["status"] == "BLOCK_START_PRICE"
    assert end["status"] == "BLOCK_END_PRICE"


def test_price_parser_ambiguous_duplicate_rows_block_corporate_action() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    ambiguous = PRICE_TEXT + (
        "2026/07 2163 ARTNER CO.,LTD. Services P loan 100 950.00 31 960.00 31 "
        "940.00 31 950.00 31 950.00 1 1 0 950 950 0 1\n"
    )
    result = module.parse_stock_price_table_text(
        ambiguous, "2026-07", "2026-07-31", ["TSE:2163"], "end"
    )
    assert result["status"] == "BLOCK_CORPORATE_ACTION"


def test_price_parser_rejects_noncanonical_security_identifier() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_stock_price_table_text(
        PRICE_TEXT, "2026-07", "2026-07-31", ["ARTNER"], "end"
    )
    assert result["status"] == "BLOCK_IDENTITY"


def test_price_parser_hash_is_independent_of_requested_order() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    left = module.parse_stock_price_table_text(
        PRICE_TEXT, "2026-07", "2026-07-31", ["TSE:1301", "TSE:2163"], "end"
    )
    right = module.parse_stock_price_table_text(
        PRICE_TEXT, "2026-07", "2026-07-31", ["TSE:2163", "TSE:1301"], "end"
    )
    assert left["semantic_rows_sha256"] == right["semantic_rows_sha256"]
    assert left["rows"] == right["rows"]
