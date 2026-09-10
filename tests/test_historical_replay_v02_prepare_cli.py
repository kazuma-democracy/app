from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

from wa_commons.portfolio.historical_replay import verify_frozen_target_manifest


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    script = ROOT / "scripts" / "run_historical_replay_v02_prepare.py"
    spec = importlib.util.spec_from_file_location("run_historical_replay_v02_prepare", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_rejects_unfrozen_window_before_source_access(tmp_path: Path) -> None:
    module = _load_module()
    window = tmp_path / "window.json"
    window.write_text('{"status":"BLOCK_HISTORICAL_REPLAY_COVERAGE"}', encoding="utf-8")
    with pytest.raises(ValueError, match="frozen window"):
        module.run_prepare(
            frozen_window_path=window,
            pre_return_input_manifest_path=tmp_path / "does-not-exist.json",
            policy_config_path=ROOT / "configs" / "m3-3b2-policy-compiler-v0.1.json",
            policies_path=ROOT / "schemas" / "examples" / "user-policy.examples.json",
            local_output_dir=tmp_path / "out",
            targets_manifest_path=tmp_path / "targets.json",
            code_commit="a" * 40,
        )


def test_prepare_cli_has_no_return_bearing_inputs() -> None:
    module = _load_module()
    help_text = module.build_parser().format_help().lower()
    for required in (
        "--frozen-window", "--pre-return-input-manifest", "--policy-config",
        "--policies", "--local-output-dir", "--targets-manifest", "--code-commit",
    ):
        assert required in help_text
    for forbidden in (
        "--price", "--return", "--dividend", "--distribution",
        "--benchmark-value", "--performance", "--nav",
    ):
        assert forbidden not in help_text


def _window() -> dict:
    return {
        "status": "HISTORICAL_REPLAY_WINDOW_FROZEN",
        "window": ["2026-01", "2026-02", "2026-03"],
        "window_semantic_sha256": "0" * 64,
        "months": [
            {"evaluation_period": "2026-01", "decision_cutoff": "2025-12-30T15:30:00+09:00"},
            {"evaluation_period": "2026-02", "decision_cutoff": "2026-01-30T15:30:00+09:00"},
            {"evaluation_period": "2026-03", "decision_cutoff": "2026-02-27T15:30:00+09:00"},
        ],
    }


def _targets() -> dict:
    months = []
    for period in ("2026-01", "2026-02", "2026-03"):
        months.append({
            "period": period,
            "control_snapshot_sha256": "a" * 64,
            "control_mapping_sha256": "b" * 64,
            "identity_semantic_sha256": "c" * 64,
            "screening_sha256": "d" * 64,
            "evidence_provenance_sha256": "e" * 64,
            "policy_family_sha256": "f" * 64,
            "policy_payload_sha256": "1" * 64,
            "policy_semantics_sha256": hashlib.sha256(json.dumps({"profile_id": "example:strict-military-avoidance", "profile_version": "1", "policy_sha256": "2" * 64, "arms": ["P0", "P1", "P2"]}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "direct_changed_security_ids": {"P1": [], "P2": ["TSE:1001"]},
        })
    return {
        "status": "HISTORICAL_REPLAY_TARGETS_FROZEN",
        "window": ["2026-01", "2026-02", "2026-03"],
        "window_semantic_sha256": "0" * 64,
        "policy_semantics": {
            "profile_id": "example:strict-military-avoidance",
            "profile_version": "1",
            "policy_sha256": "2" * 64,
            "arms": ["P0", "P1", "P2"],
        },
        "policy_semantics_sha256": hashlib.sha256(json.dumps({"profile_id": "example:strict-military-avoidance", "profile_version": "1", "policy_sha256": "2" * 64, "arms": ["P0", "P1", "P2"]}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "months": months,
    }


def test_frozen_target_manifest_accepts_exact_three_month_binding() -> None:
    assert verify_frozen_target_manifest(_window(), _targets()) is None


def test_frozen_target_manifest_rejects_performance_or_window_mismatch() -> None:
    bad = _targets()
    bad["months"][0]["portfolio_return"] = "0.01"
    assert verify_frozen_target_manifest(_window(), bad) == "BLOCK_REPRODUCIBILITY"

    bad = _targets()
    bad["window_semantic_sha256"] = "9" * 64
    assert verify_frozen_target_manifest(_window(), bad) == "BLOCK_REPRODUCIBILITY"


def _holdings_csv(as_of_label: str) -> str:
    return (
        f'Fund Holdings as of,"{as_of_label}"\n'
        'Ticker,Name,Asset Class,Market Value,Quantity,Price\n'
        '7203,TOYOTA MOTOR CORP,Equity,"100,000",100,1000\n'
        'JPY,CASH,Cash,"1,000",1000,1\n'
    )


def test_prepare_freezes_three_month_policy_targets_without_market_inputs(tmp_path: Path) -> None:
    module = _load_module()
    period_specs = [
        ("2026-01", "2025-12-30T15:30:00+09:00", "2025-12-30", "Dec 30, 2025"),
        ("2026-02", "2026-01-30T15:30:00+09:00", "2026-01-30", "Jan 30, 2026"),
        ("2026-03", "2026-02-27T15:30:00+09:00", "2026-02-27", "Feb 27, 2026"),
    ]
    periods: dict[str, dict] = {}
    window_months = []
    for index, (period, cutoff, as_of, label) in enumerate(period_specs, start=1):
        holdings = tmp_path / f"holdings-{period}.csv"
        holdings.write_text(_holdings_csv(label), encoding="utf-8")
        holdings_sha = hashlib.sha256(holdings.read_bytes()).hexdigest()
        edinet = tmp_path / f"edinet-{period}.json"
        edinet.write_text(json.dumps([{
            "submitDateTime": cutoff[:10] + " 09:00",
            "secCode": "72030",
            "JCN": "1111111111111",
            "edinetCode": "E00001",
        }]), encoding="utf-8")
        mod_path = tmp_path / f"mod-{period}.xlsx"
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "month"
        ws.append([
            "物品役務等の名称及び数量",
            "契約担当官等の氏名並びにその所属する部局の名称及び所在地",
            "契約を締結した日", "契約の相手方の商号又は名称及び住所",
            "法人番号", "予定価格", "契約金額",
        ])
        ws.append(["一般事務用品", "Japan MOD", "11月15日", "TOYOTA MOTOR CORP",
                   "1111111111111", 1200, 1000])
        wb.save(mod_path)
        locator = f"fixture://blackrock/1475/{as_of}"
        window_months.append({
            "evaluation_period": period,
            "decision_cutoff": cutoff,
            "control_kind": "ISHARES_1475_POINT_IN_TIME",
            "control_as_of_date": as_of,
            "control_available_at": cutoff,
            "control_source_locator": locator,
            "control_source_sha256": holdings_sha,
            "control_rights_state": "LOCAL_RESEARCH_ALLOWED",
        })
        periods[period] = {
            "decision_cutoff": cutoff,
            "holdings": {
                "local_path": str(holdings), "as_of_date": as_of,
                "source_sha256": holdings_sha,
                "retrieved_at": "2026-09-10T10:00:00+09:00",
                "source_locator": locator,
            },
            "edinet": {
                "local_path": str(edinet),
                "source_key": f"documents-{as_of}", "snapshot": f"cutoff-{as_of}",
                "url": f"fixture://edinet/{as_of}",
                "retrieved_at": "2026-09-10T10:00:00+09:00",
            },
            "mod_sources": [{
                "snapshot_version": f"fy2025-11-{index}",
                "available_at": "2025-12-01T12:00:00+09:00",
                "local_path": str(mod_path),
                "source_url": f"fixture://mod/{period}.xlsx",
                "source_page_url": "fixture://mod/index",
                "retrieved_at": "2026-09-10T10:00:00+09:00",
                "fiscal_year": 2025,
            }],
        }

    coverage_config = json.loads(
        (ROOT / "configs" / "m2-2a-coverage-v0.1.json").read_text(encoding="utf-8")
    )
    window = {
        "status": "HISTORICAL_REPLAY_WINDOW_FROZEN",
        "window": ["2026-01", "2026-02", "2026-03"],
        "window_semantic_sha256": "0" * 64,
        "months": window_months,
    }
    window_path = tmp_path / "window.json"
    window_path.write_text(json.dumps(window), encoding="utf-8")
    manifest_path = tmp_path / "pre-return.json"
    manifest_path.write_text(json.dumps({
        "artifact_version": "fixture-pre-return-v0.1",
        "coverage_source_catalog": coverage_config["source_catalog"],
        "periods": periods,
    }), encoding="utf-8")
    targets_path = tmp_path / "targets.json"
    output_dir = tmp_path / "out"
    result = module.run_prepare(
        frozen_window_path=window_path,
        pre_return_input_manifest_path=manifest_path,
        policy_config_path=ROOT / "configs" / "m3-3b2-policy-compiler-v0.1.json",
        policies_path=ROOT / "schemas" / "examples" / "user-policy.examples.json",
        local_output_dir=output_dir,
        targets_manifest_path=targets_path,
        code_commit="a" * 40,
    )
    assert result["status"] == "HISTORICAL_REPLAY_TARGETS_FROZEN"
    assert verify_frozen_target_manifest(window, result) is None
    assert targets_path.is_file()
    policy_map = json.loads((output_dir / "monthly_policy_payload_map.json").read_text(encoding="utf-8"))
    assert sorted(policy_map) == ["2026-01", "2026-02", "2026-03"]
    serialized = json.dumps(result, sort_keys=True).lower()
    assert not any(token in serialized for token in (
        "start_price", "end_price", "portfolio_return", "benchmark_return",
        "total_wealth_return", "nav", "equity_market_value",
    ))
