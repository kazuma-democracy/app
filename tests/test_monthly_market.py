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


TOPIX_TEXT = """ROI of Dividend-Included Stock Price Indices (As of the End of Jul. 2026)
Index 1-Month 3-Month 6-Month 1-Year
TOPIX 0.22 5.18 8.41 12.34
"""

EX_RIGHTS_TEXT = """Ex-Rights Information July 2026
2026/07/30 2163 ARTNER CO.,LTD. 2026/07/31 Stock Split 1:2
"""

LISTED_CHANGES_TEXT = """Listed Company Changes July 2026
Delisting
2026/07/31 3681 V-CUBE, INC.
Margin Trading
2026/07/15 1301 KYOKUYO CO.,LTD.
Name Change
2026/07/01 2163 ARTNER CO.,LTD.
"""


def test_topix_monthly_roi_parser_extracts_official_one_month_return() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_topix_monthly_roi_text(TOPIX_TEXT, period="2026-07")
    assert result["status"] == "BENCHMARK_ROI_OK"
    assert result["one_month_percent"] == "0.220000000000"
    assert result["decimal_return"] == "0.002200000000"


def test_topix_monthly_roi_parser_blocks_missing_or_conflicting_rows() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    missing = module.parse_topix_monthly_roi_text("As of the End of Jul. 2026\nNikkei 225 1.00", "2026-07")
    conflicting = module.parse_topix_monthly_roi_text(TOPIX_TEXT + "TOPIX 0.23 5.18 8.41 12.34\n", "2026-07")
    wrong_period = module.parse_topix_monthly_roi_text(TOPIX_TEXT, "2026-06")
    assert missing["status"] == "BLOCK_BENCHMARK_MONTHLY_RETURN"
    assert conflicting["status"] == "BLOCK_BENCHMARK_MONTHLY_RETURN"
    assert wrong_period["status"] == "BLOCK_BENCHMARK_MONTHLY_RETURN"


def test_ex_rights_parser_normalizes_split_event_for_exact_code() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_ex_rights_text(EX_RIGHTS_TEXT, "2026-07", ["TSE:2163", "TSE:1301"])
    assert result["status"] == "EVENTS_OK"
    assert result["events"] == [{
        "security_id": "TSE:2163",
        "security_code": "2163",
        "event_type": "STOCK_SPLIT",
        "ex_rights_date": "2026-07-30",
        "record_date": "2026-07-31",
        "split_ratio": "1:2",
    }]


def test_ex_rights_parser_does_not_invent_event_for_absent_code() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_ex_rights_text(EX_RIGHTS_TEXT, "2026-07", ["TSE:1301"])
    assert result == {"status": "EVENTS_OK", "period": "2026-07", "events": []}


def test_listed_changes_parser_detects_only_delisting_rows() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.parse_listed_company_changes_text(
        LISTED_CHANGES_TEXT, "2026-07", ["TSE:3681", "TSE:1301", "TSE:2163"]
    )
    assert result["status"] == "EVENTS_OK"
    assert result["events"] == [{
        "security_id": "TSE:3681",
        "security_code": "3681",
        "event_type": "DELISTING",
        "effective_date": "2026-07-31",
    }]


def test_event_parsers_reject_noncanonical_identity() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    assert module.parse_ex_rights_text(EX_RIGHTS_TEXT, "2026-07", ["ARTNER"])["status"] == "BLOCK_IDENTITY"
    assert module.parse_listed_company_changes_text(LISTED_CHANGES_TEXT, "2026-07", ["V-CUBE"])["status"] == "BLOCK_IDENTITY"



def _price_snapshot(values: dict[str, str]) -> dict[str, object]:
    return {
        "status": "PRICE_SNAPSHOT_OK",
        "rows": [
            {"security_id": security_id, "close_price": price}
            for security_id, price in values.items()
        ],
    }


def _resolution(
    *,
    dividend_status: str = "CONFIRMED_NONE",
    dividend_cash: str = "0",
    action_resolution: dict[str, object] | None = None,
    identity_state: str = "RESOLVED",
) -> dict[str, object]:
    value: dict[str, object] = {
        "identity_state": identity_state,
        "dividend_status": dividend_status,
        "dividend_cash_per_start_unit": dividend_cash,
        "evidence_refs": ["issuer:example"],
    }
    if action_resolution is not None:
        value["action_resolution"] = action_resolution
    return value


def test_monthly_return_payload_no_action_total_wealth_arithmetic() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.build_monthly_return_payload(
        period="2026-07",
        held_security_ids=["TSE:1301"],
        start_prices=_price_snapshot({"TSE:1301": "100"}),
        end_prices=_price_snapshot({"TSE:1301": "110"}),
        benchmark_roi={"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"},
        events=[],
        evidence_resolutions={"TSE:1301": _resolution()},
        provenance={"sources": ["sha256:abc"]},
        config={"semantic_decimals": 12},
    )
    assert result["status"] == "MONTHLY_RETURN_OK"
    row = result["rows"][0]
    assert row["state"] == "RETURN_OK_NO_ACTION"
    assert row["ending_wealth_per_start_unit"] == "110.000000000000"
    assert row["total_wealth_return"] == "0.100000000000"


def test_monthly_return_payload_adds_cash_dividend_without_reinvestment() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.build_monthly_return_payload(
        "2026-07", ["TSE:1301"],
        _price_snapshot({"TSE:1301": "100"}),
        _price_snapshot({"TSE:1301": "105"}),
        {"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"},
        [],
        {"TSE:1301": _resolution(dividend_status="CONFIRMED_CASH", dividend_cash="2")},
        {}, {"semantic_decimals": 12},
    )
    row = result["rows"][0]
    assert row["ending_wealth_per_start_unit"] == "107.000000000000"
    assert row["total_wealth_return"] == "0.070000000000"


def test_monthly_return_payload_resolves_split_units_explicitly() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    split_event = {
        "security_id": "TSE:2163", "event_type": "STOCK_SPLIT", "split_ratio": "1:2"
    }
    action = {
        "status": "RESOLVED",
        "end_units_per_start_unit": "2",
        "cash_consideration_per_start_unit": "0",
        "terminal_security_id": "TSE:2163",
        "evidence_refs": ["jpx:split"],
    }
    result = module.build_monthly_return_payload(
        "2026-07", ["TSE:2163"],
        _price_snapshot({"TSE:2163": "200"}),
        _price_snapshot({"TSE:2163": "105"}),
        {"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"},
        [split_event],
        {"TSE:2163": _resolution(action_resolution=action)},
        {}, {"semantic_decimals": 12},
    )
    row = result["rows"][0]
    assert row["state"] == "RETURN_OK_ACTION_EXPLAINED"
    assert row["ending_wealth_per_start_unit"] == "210.000000000000"
    assert row["total_wealth_return"] == "0.050000000000"


def test_monthly_return_payload_blocks_missing_start_and_end_prices() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    kwargs = dict(
        period="2026-07", held_security_ids=["TSE:1301"],
        benchmark_roi={"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"},
        events=[], evidence_resolutions={"TSE:1301": _resolution()}, provenance={}, config={"semantic_decimals": 12},
    )
    missing_start = module.build_monthly_return_payload(start_prices=_price_snapshot({}), end_prices=_price_snapshot({"TSE:1301": "110"}), **kwargs)
    missing_end = module.build_monthly_return_payload(start_prices=_price_snapshot({"TSE:1301": "100"}), end_prices=_price_snapshot({}), **kwargs)
    assert missing_start["rows"][0]["state"] == "BLOCK_START_PRICE"
    assert missing_end["rows"][0]["state"] == "BLOCK_END_PRICE"


def test_monthly_return_payload_blocks_identity_dividend_and_action_gaps() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    base = dict(
        period="2026-07", held_security_ids=["TSE:1301"],
        start_prices=_price_snapshot({"TSE:1301": "100"}), end_prices=_price_snapshot({"TSE:1301": "110"}),
        benchmark_roi={"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"}, provenance={}, config={"semantic_decimals": 12},
    )
    identity = module.build_monthly_return_payload(events=[], evidence_resolutions={"TSE:1301": _resolution(identity_state="UNRESOLVED")}, **base)
    dividend = module.build_monthly_return_payload(events=[], evidence_resolutions={"TSE:1301": _resolution(dividend_status="UNKNOWN")}, **base)
    action = module.build_monthly_return_payload(events=[{"security_id": "TSE:1301", "event_type": "STOCK_SPLIT", "split_ratio": "1:2"}], evidence_resolutions={"TSE:1301": _resolution()}, **base)
    assert identity["rows"][0]["state"] == "BLOCK_IDENTITY"
    assert dividend["rows"][0]["state"] == "BLOCK_DIVIDEND_EVIDENCE"
    assert action["rows"][0]["state"] == "BLOCK_CORPORATE_ACTION"


def test_monthly_return_payload_blocks_missing_benchmark_snapshot() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    result = module.build_monthly_return_payload(
        "2026-07", ["TSE:1301"], _price_snapshot({"TSE:1301": "100"}), _price_snapshot({"TSE:1301": "110"}),
        {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN"}, [], {"TSE:1301": _resolution()}, {}, {"semantic_decimals": 12},
    )
    assert result["status"] == "BLOCK_BENCHMARK_MONTHLY_RETURN"
    assert result["rows"] == []


def test_monthly_return_payload_hash_and_rows_are_order_independent() -> None:
    module = importlib.import_module("wa_commons.portfolio.monthly_market")
    common = dict(
        period="2026-07",
        start_prices=_price_snapshot({"TSE:1301": "100", "TSE:2163": "200"}),
        end_prices=_price_snapshot({"TSE:1301": "110", "TSE:2163": "210"}),
        benchmark_roi={"status": "BENCHMARK_ROI_OK", "decimal_return": "0.0022"}, events=[],
        evidence_resolutions={"TSE:1301": _resolution(), "TSE:2163": _resolution()}, provenance={}, config={"semantic_decimals": 12},
    )
    left = module.build_monthly_return_payload(held_security_ids=["TSE:1301", "TSE:2163"], **common)
    right = module.build_monthly_return_payload(held_security_ids=["TSE:2163", "TSE:1301"], **common)
    assert left["semantic_payload_sha256"] == right["semantic_payload_sha256"]
    assert left["rows"] == right["rows"]



def _load_monthly_cli_module():
    import importlib.util
    script = ROOT / "scripts" / "run_monthly_market.py"
    spec = importlib.util.spec_from_file_location("run_monthly_market", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_monthly_cli_exposes_only_explicit_local_input_options() -> None:
    module = _load_monthly_cli_module()
    parser = module.build_parser()
    help_text = parser.format_help()
    required = {
        "--period", "--start-price-pdf", "--end-price-pdf", "--benchmark-pdf",
        "--ex-rights-pdf", "--listed-changes-pdf", "--held-securities",
        "--evidence-resolutions", "--source-manifest", "--config",
        "--local-output", "--public-output", "--code-commit",
    }
    assert all(option in help_text for option in required)
    assert not any(token in help_text.lower() for token in {"--url", "--download", "--network"})


def test_monthly_cli_rejects_identical_local_and_public_output_paths(tmp_path: Path) -> None:
    module = _load_monthly_cli_module()
    path = tmp_path / "same.json"
    try:
        module.validate_output_paths(path, path)
    except ValueError as exc:
        assert "distinct" in str(exc).lower()
    else:
        raise AssertionError("identical output paths must be rejected")


def test_public_monthly_artifact_redacts_security_and_performance_rows_without_rights() -> None:
    module = _load_monthly_cli_module()
    local_payload = {
        "status": "MONTHLY_RETURN_OK",
        "period": "2026-07",
        "benchmark_decimal_return": "0.002200000000",
        "rows": [{
            "security_id": "TSE:1301",
            "start_price": "100.000000000000",
            "end_price": "110.000000000000",
            "total_wealth_return": "0.100000000000",
            "state": "RETURN_OK_NO_ACTION",
            "evidence_refs": ["issuer:secret-row"],
        }],
        "semantic_payload_sha256": "abc123",
        "provenance": {"source_hashes": ["sha256:one"]},
    }
    public = module.build_public_artifact(
        local_payload,
        performance_publication_rights="NOT_CLEARED",
        artifact_version="m3.3c-monthly-market-v0.1",
        code_commit="deadbeef",
        source_hashes=["sha256:one"],
    )
    serialized = json.dumps(public, sort_keys=True)
    assert public["paper_only"] is True
    assert public["performance_publication_rights"] == "NOT_CLEARED"
    assert public["semantic_payload_sha256"] == "abc123"
    assert public["status_counts"] == {"RETURN_OK_NO_ACTION": 1}
    assert "TSE:1301" not in serialized
    assert "100.000000000000" not in serialized
    assert "110.000000000000" not in serialized
    assert "0.100000000000" not in serialized
    assert "0.002200000000" not in serialized
    assert "issuer:secret-row" not in serialized


def test_source_manifest_period_mismatch_fails_closed() -> None:
    module = _load_monthly_cli_module()
    manifest = {"period": "2026-06", "sources": {}}
    try:
        module.validate_source_manifest_period(manifest, "2026-07")
    except ValueError as exc:
        assert "period" in str(exc).lower()
    else:
        raise AssertionError("source manifest period mismatch must fail")
