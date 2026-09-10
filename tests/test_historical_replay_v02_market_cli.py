from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    script = ROOT / "scripts" / "run_historical_replay_v02_market.py"
    spec = importlib.util.spec_from_file_location("run_historical_replay_v02_market", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v02_market_runner_rejects_unfrozen_targets_before_source_access(tmp_path: Path) -> None:
    module = _load_module()
    targets = tmp_path / "targets.json"
    targets.write_text('{"status":"BLOCK_REPRODUCIBILITY"}', encoding="utf-8")
    with pytest.raises(ValueError, match="frozen targets"):
        module.run_market_bundle(
            frozen_targets_path=targets,
            period="2026-01",
            start_price_pdf=tmp_path / "missing-start.pdf",
            end_price_pdf=tmp_path / "missing-end.pdf",
            benchmark_pdf=tmp_path / "missing-topix.pdf",
            ex_rights_pdf=tmp_path / "missing-rights.pdf",
            listed_changes_pdf=tmp_path / "missing-changes.pdf",
            evidence_resolutions_path=tmp_path / "missing-resolutions.json",
            source_manifest_path=tmp_path / "missing-source-manifest.json",
            config_path=ROOT / "configs" / "m3-3c-monthly-market-v0.1.json",
            output_path=tmp_path / "market.json",
        )


def test_v02_market_runner_derives_holdings_from_frozen_targets_only() -> None:
    module = _load_module()
    help_text = module.build_parser().format_help()
    assert "--frozen-targets" in help_text
    assert "--held-securities" not in help_text
    for option in (
        "--period", "--start-price-pdf", "--end-price-pdf", "--benchmark-pdf",
        "--ex-rights-pdf", "--listed-changes-pdf", "--evidence-resolutions",
        "--source-manifest", "--config", "--output",
    ):
        assert option in help_text


def test_v02_market_runner_unions_direct_changes_with_1475() -> None:
    module = _load_module()
    targets = {
        "status": "HISTORICAL_REPLAY_TARGETS_FROZEN",
        "window": ["2026-01", "2026-02", "2026-03"],
        "months": [{
            "period": "2026-01",
            "direct_changed_security_ids": {
                "P1": ["TSE:1001"],
                "P2": ["TSE:1002", "TSE:1001"],
            },
        }],
    }
    assert module.derive_held_security_ids(targets, "2026-01") == [
        "TSE:1001", "TSE:1002", "TSE:1475"
    ]
