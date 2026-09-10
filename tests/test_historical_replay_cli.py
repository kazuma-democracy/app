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


def _load_execution_cli_module():
    script = ROOT / "scripts" / "run_historical_replay.py"
    spec = importlib.util.spec_from_file_location("run_historical_replay", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_execution_cli_has_only_frozen_execution_inputs() -> None:
    module = _load_execution_cli_module()
    help_text = module.build_parser().format_help()
    required = {
        "--frozen-window", "--policy-payload-map", "--market-payload-map",
        "--config", "--local-output", "--public-output",
    }
    assert all(option in help_text for option in required)
    assert "--candidate-metadata" not in help_text


def test_execution_cli_rejects_identical_output_paths(tmp_path: Path) -> None:
    module = _load_execution_cli_module()
    same = tmp_path / "same.json"
    try:
        module.validate_output_paths(same, same)
    except ValueError as exc:
        assert "distinct" in str(exc).lower()
    else:
        raise AssertionError("identical local/public paths must be rejected")


def test_execution_cli_rejects_unfrozen_window_before_other_inputs(
    tmp_path: Path,
) -> None:
    module = _load_execution_cli_module()
    frozen_window = tmp_path / "window.json"
    frozen_window.write_text(
        json.dumps({
            "status": "BLOCK_HISTORICAL_REPLAY_COVERAGE",
            "window": [],
        }),
        encoding="utf-8",
    )
    try:
        module.run_replay(
            frozen_window_path=frozen_window,
            policy_payload_map_path=tmp_path / "missing-policy.json",
            market_payload_map_path=tmp_path / "missing-market.json",
            config_path=tmp_path / "missing-config.json",
            local_output_path=tmp_path / "local.json",
            public_output_path=tmp_path / "public.json",
        )
    except ValueError as exc:
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("unfrozen window must be rejected before other inputs")


def test_public_replay_payload_hides_financial_values_when_rights_uncleared() -> None:
    module = _load_execution_cli_module()
    local_payload = {
        "status": "HISTORICAL_REPLAY_OK",
        "window": ["2026-04", "2026-05", "2026-06"],
        "window_semantic_sha256": "w" * 64,
        "semantic_payload_sha256": "s" * 64,
        "months": [{
            "period": "2026-04",
            "policy_transmission": [{
                "arm_id": "P2",
                "semantic_target_sha256": "t" * 64,
                "metrics": {"active_share": "0.1"},
            }],
            "financial": {
                "benchmark_return": "0.02",
                "arms": [{"arm_id": "P2", "portfolio_return": "0.03"}],
            },
        }],
        "arms": [{
            "arm_id": "P2",
            "cumulative_wealth": "1.03",
            "cumulative_return": "0.03",
        }],
        "benchmark": {"cumulative_wealth": "1.02", "cumulative_return": "0.02"},
    }
    public = module.build_public_payload(
        local_payload,
        {"publication": {"performance_rights_cleared": False}},
    )
    assert public["status"] == "HISTORICAL_REPLAY_OK"
    assert public["window"] == ["2026-04", "2026-05", "2026-06"]
    assert public["months"][0]["policy_transmission"][0]["metrics"]["active_share"] == "0.1"
    assert public["publication"]["performance_rights_cleared"] is False
    assert public["publication"]["financial_values_published"] is False

    serialized = json.dumps(public, sort_keys=True)
    forbidden = (
        "benchmark_return", "portfolio_return", "cumulative_wealth",
        "cumulative_return", "security_id", "start_price", "end_price",
    )
    assert not any(token in serialized for token in forbidden)
    assert "0.02" not in serialized
    assert "0.03" not in serialized


def _v02_cli_candidate(period: str, cutoff: str, as_of: str, suffix: str) -> dict:
    return {
        "evaluation_period": period,
        "decision_cutoff": cutoff,
        "control_source_metadata": {
            "kind": "ISHARES_1475_POINT_IN_TIME",
            "as_of_date": as_of,
            "available_at": cutoff,
            "exists": True,
            "locator": f"fixture://1475/{as_of}",
            "source_sha256": suffix * 64,
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
            role: {"exists": True, "locator": f"fixture://{role}/{period}"}
            for role in ("start_price", "end_price", "benchmark", "action_detector")
        },
    }


def test_qualification_cli_freezes_v02_q1_without_performance_inputs(tmp_path: Path) -> None:
    module = _load_cli_module()
    inventory = tmp_path / "v02-candidates.json"
    output = tmp_path / "v02-window.json"
    inventory.write_text(
        json.dumps({
            "artifact_version": "fixture-v0.2",
            "candidates": [
                _v02_cli_candidate("2026-01", "2025-12-30T15:30:00+09:00", "2025-12-30", "1"),
                _v02_cli_candidate("2026-02", "2026-01-30T15:30:00+09:00", "2026-01-30", "2"),
                _v02_cli_candidate("2026-03", "2026-02-27T15:30:00+09:00", "2026-02-27", "3"),
            ],
        }),
        encoding="utf-8",
    )
    result = module.run_qualification(
        config_path=ROOT / "configs" / "m3-3c0-historical-replay-v0.2.json",
        candidate_metadata_path=inventory,
        output_path=output,
        code_commit="test-v02",
    )
    assert result["status"] == "HISTORICAL_REPLAY_WINDOW_FROZEN"
    assert result["window"] == ["2026-01", "2026-02", "2026-03"]
    assert result["selection_input_semantics"] == "METADATA_ONLY_NO_RETURNS"
    serialized = output.read_text(encoding="utf-8").lower()
    for forbidden in ("benchmark_return", "portfolio_return", "total_wealth_return", "nav"):
        assert forbidden not in serialized


def test_execution_cli_exposes_optional_v02_frozen_targets_without_selection_inputs() -> None:
    module = _load_execution_cli_module()
    help_text = module.build_parser().format_help()
    assert "--frozen-targets" in help_text
    assert "--candidate-metadata" not in help_text


def test_v02_execution_cli_requires_frozen_targets_before_policy_or_market_access(tmp_path: Path) -> None:
    module = _load_execution_cli_module()
    window = tmp_path / "window.json"
    window.write_text(json.dumps({
        "status": "HISTORICAL_REPLAY_WINDOW_FROZEN",
        "window": ["2026-01", "2026-02", "2026-03"],
        "window_semantic_sha256": "a" * 64,
    }), encoding="utf-8")
    try:
        module.run_replay(
            frozen_window_path=window,
            frozen_targets_path=None,
            policy_payload_map_path=tmp_path / "missing-policy.json",
            market_payload_map_path=tmp_path / "missing-market.json",
            config_path=ROOT / "configs" / "m3-3c0-historical-replay-v0.2.json",
            local_output_path=tmp_path / "local.json",
            public_output_path=tmp_path / "public.json",
        )
    except ValueError as exc:
        assert "frozen targets" in str(exc).lower()
    else:
        raise AssertionError("v0.2 must require frozen targets before market access")


def test_v02_public_payload_hides_topix_and_tracking_values_without_rights() -> None:
    module = _load_execution_cli_module()
    local = {
        "status": "HISTORICAL_REPLAY_OK", "window": ["2026-01", "2026-02", "2026-03"],
        "window_semantic_sha256": "w" * 64, "targets_semantic_sha256": "t" * 64,
        "semantic_payload_sha256": "s" * 64,
        "months": [{
            "period": "2026-01", "policy_transmission": [{"arm_id": "P2", "metrics": {"active_share": "0.1"}}],
            "financial": {"p0_return": "0.01", "topix_total_return": "0.009",
                          "p0_tracking_difference_vs_topix": "0.001"},
        }],
        "arms": [{"arm_id": "P0", "cumulative_return": "0.03"}],
        "topix": {"cumulative_return": "0.027"},
    }
    public = module.build_public_payload(local, {"publication": {"performance_rights_cleared": False}})
    assert public["targets_semantic_sha256"] == "t" * 64
    serialized = json.dumps(public, sort_keys=True)
    assert "p0_tracking_difference_vs_topix" not in serialized
    assert "topix_total_return" not in serialized
    assert '"topix"' not in serialized
    assert "0.009" not in serialized
