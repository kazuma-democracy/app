from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_cli_module():
    script = ROOT / "scripts" / "run_historical_replay_qualification.py"
    spec = importlib.util.spec_from_file_location(
        "run_historical_replay_qualification", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_qualification_cli_exposes_metadata_only_arguments() -> None:
    module = _load_cli_module()
    help_text = module.build_parser().format_help()
    required = {
        "--config", "--candidate-metadata", "--output", "--code-commit"
    }
    assert all(option in help_text for option in required)
    forbidden = {
        "--price", "--return", "--benchmark-roi", "--market-payload"
    }
    assert not any(option in help_text for option in forbidden)


def test_qualification_cli_blocks_performance_fields_before_selection(
    tmp_path: Path,
) -> None:
    module = _load_cli_module()
    config = tmp_path / "config.json"
    candidates = tmp_path / "candidates.json"
    output = tmp_path / "output.json"
    config.write_text(
        json.dumps({
            "artifact_version": "test",
            "engineering_validation_periods": [],
            "future_holdout_periods": [],
            "required_market_source_roles": [],
        }),
        encoding="utf-8",
    )
    candidates.write_text(
        json.dumps({
            "candidates": [{
                "evaluation_period": "2026-06",
                "close_price": "100",
            }]
        }),
        encoding="utf-8",
    )
    result = module.run_qualification(
        config_path=config,
        candidate_metadata_path=candidates,
        output_path=output,
        code_commit="abc123",
    )
    assert result["status"] == "BLOCK_HISTORICAL_REPLAY_COVERAGE"
    assert result["candidate_results"][0]["status"] == "BLOCK_REPRODUCIBILITY"
    assert "PERFORMANCE_FIELD_PRESENT" in result["candidate_results"][0]["blockers"]
