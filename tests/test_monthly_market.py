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
