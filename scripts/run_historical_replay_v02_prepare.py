from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from wa_commons.evidence.historical_cutoff import build_historical_screening
from wa_commons.identity.historical_edinet import build_historical_proxy_identity
from wa_commons.identity.models import SourceRef
from wa_commons.portfolio.historical_replay import verify_frozen_target_manifest
from wa_commons.portfolio.investable_proxy import (
    bind_policy_compiler_inputs,
    directly_changed_security_ids,
    map_investable_control_snapshot,
    parse_ishares_1475_holdings_csv,
)
from wa_commons.portfolio.policy_compiler import compile_policy_family


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze v0.2 proxy policy targets after window selection and before market data."
    )
    parser.add_argument("--frozen-window", required=True, type=Path)
    parser.add_argument("--pre-return-input-manifest", required=True, type=Path)
    parser.add_argument("--policy-config", required=True, type=Path)
    parser.add_argument("--policies", required=True, type=Path)
    parser.add_argument("--local-output-dir", required=True, type=Path)
    parser.add_argument("--targets-manifest", required=True, type=Path)
    parser.add_argument("--code-commit", required=True)
    return parser


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _window_months(window: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    months = window.get("months")
    if not isinstance(months, list):
        raise ValueError("frozen window months are required")
    result: dict[str, Mapping[str, Any]] = {}
    for month in months:
        if not isinstance(month, Mapping):
            raise ValueError("invalid frozen window month")
        period = str(month.get("evaluation_period", ""))
        if not period or period in result:
            raise ValueError("invalid or duplicate frozen window period")
        result[period] = month
    if set(result) != set(window.get("window", [])):
        raise ValueError("frozen window months do not match window")
    return result


def _policy_semantics(payload: Mapping[str, Any]) -> dict[str, Any]:
    manifest = payload.get("manifest")
    arms = payload.get("arms")
    if not isinstance(manifest, Mapping) or not isinstance(arms, list):
        raise ValueError("invalid frozen policy family")
    return {
        "profile_id": str(manifest.get("profile_id", "")),
        "profile_version": str(manifest.get("profile_version", "")),
        "policy_sha256": str(manifest.get("policy_sha256", "")),
        "arms": [
            {
                "arm_id": str(arm.get("arm_id", "")),
                "allocation_policy_id": str(arm.get("allocation_policy_id", "")),
                "allocation_policy_version": str(arm.get("allocation_policy_version", "")),
            }
            for arm in sorted(arms, key=lambda item: str(item.get("arm_id", "")))
        ],
    }


def _edinet_source(meta: Mapping[str, Any]) -> SourceRef:
    return SourceRef(
        source="jp-edinet",
        source_key=str(meta.get("source_key", "")),
        snapshot=str(meta.get("snapshot", "")),
        url=str(meta.get("url", "")),
        retrieved_at=str(meta.get("retrieved_at", "")),
        adapter_version=str(meta.get("adapter_version", "0.1")),
    )


def _validate_holdings_binding(
    window_month: Mapping[str, Any],
    holdings_meta: Mapping[str, Any],
) -> Path:
    local_path = Path(str(holdings_meta.get("local_path", "")))
    if not local_path.is_file():
        raise ValueError(f"holdings local_path unavailable: {local_path}")
    actual_sha = hashlib.sha256(local_path.read_bytes()).hexdigest()
    declared_sha = str(holdings_meta.get("source_sha256", "")).lower()
    if actual_sha != declared_sha or declared_sha != str(window_month.get("control_source_sha256", "")).lower():
        raise ValueError("holdings source hash does not match frozen window")
    if str(holdings_meta.get("as_of_date", "")) != str(window_month.get("control_as_of_date", "")):
        raise ValueError("holdings as-of date does not match frozen window")
    if str(holdings_meta.get("source_locator", "")) != str(window_month.get("control_source_locator", "")):
        raise ValueError("holdings locator does not match frozen window")
    return local_path


def run_prepare(
    *,
    frozen_window_path: str | Path,
    pre_return_input_manifest_path: str | Path,
    policy_config_path: str | Path,
    policies_path: str | Path,
    local_output_dir: str | Path,
    targets_manifest_path: str | Path,
    code_commit: str,
) -> dict[str, Any]:
    window = _read_json(frozen_window_path)
    if not isinstance(window, dict) or window.get("status") != "HISTORICAL_REPLAY_WINDOW_FROZEN":
        raise ValueError("frozen window is required before pre-return source access")
    window_periods = [str(period) for period in window.get("window", [])]
    if len(window_periods) != 3:
        raise ValueError("exact three-month frozen window is required")
    window_months = _window_months(window)

    manifest = _read_json(pre_return_input_manifest_path)
    base_config = _read_json(policy_config_path)
    policies = _read_json(policies_path)
    if not isinstance(manifest, Mapping) or not isinstance(base_config, Mapping):
        raise ValueError("pre-return manifest and policy config must be JSON objects")
    if not isinstance(policies, list):
        raise ValueError("policies must be a JSON array")
    period_inputs = manifest.get("periods")
    source_catalog = manifest.get("coverage_source_catalog")
    if not isinstance(period_inputs, Mapping) or set(period_inputs) != set(window_periods):
        raise ValueError("pre-return periods must exactly match frozen window")
    if not isinstance(source_catalog, list):
        raise ValueError("coverage_source_catalog must be a list")

    output_dir = Path(local_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly_policy_payloads: dict[str, Any] = {}
    target_months: list[dict[str, Any]] = []
    expected_semantics: dict[str, Any] | None = None
    expected_semantics_sha: str | None = None

    for period in window_periods:
        entry = period_inputs[period]
        if not isinstance(entry, Mapping):
            raise ValueError(f"invalid pre-return entry for {period}")
        window_month = window_months[period]
        cutoff = str(entry.get("decision_cutoff", ""))
        if cutoff != str(window_month.get("decision_cutoff", "")):
            raise ValueError(f"decision cutoff mismatch for {period}")
        holdings_meta = entry.get("holdings")
        edinet_meta = entry.get("edinet")
        mod_sources = entry.get("mod_sources", [])
        if not isinstance(holdings_meta, Mapping) or not isinstance(edinet_meta, Mapping):
            raise ValueError(f"missing holdings or EDINET metadata for {period}")
        if not isinstance(mod_sources, list):
            raise ValueError(f"mod_sources must be a list for {period}")

        holdings_path = _validate_holdings_binding(window_month, holdings_meta)
        control = parse_ishares_1475_holdings_csv(
            holdings_path.read_text(encoding="utf-8"),
            as_of_date=str(holdings_meta["as_of_date"]),
            source_sha256=str(holdings_meta["source_sha256"]),
            retrieved_at=str(holdings_meta["retrieved_at"]),
            source_locator=str(holdings_meta["source_locator"]),
        )

        edinet_path = Path(str(edinet_meta.get("local_path", "")))
        if not edinet_path.is_file():
            raise ValueError(f"EDINET local_path unavailable for {period}")
        edinet_records = _read_json(edinet_path)
        if not isinstance(edinet_records, list):
            raise ValueError(f"EDINET records must be a list for {period}")
        identity = build_historical_proxy_identity(
            control,
            edinet_records,
            decision_cutoff=cutoff,
            edinet_source=_edinet_source(edinet_meta),
            code_commit=code_commit,
        )
        mapped_control = map_investable_control_snapshot(control, identity)
        screening = build_historical_screening(
            identity=identity,
            mod_sources=mod_sources,
            decision_cutoff=cutoff,
            coverage_source_catalog=source_catalog,
            policies=policies,
            code_commit=code_commit,
        )

        bound_config = bind_policy_compiler_inputs(base_config, mapped_control, screening)
        policy_payload = compile_policy_family(mapped_control, screening, bound_config)
        if policy_payload.get("status") != "FROZEN_POLICY_FAMILY":
            raise ValueError(f"policy compiler blocked for {period}: {policy_payload.get('status')}")

        semantics = _policy_semantics(policy_payload)
        semantics_sha = _canonical_sha256(semantics)
        if expected_semantics is None:
            expected_semantics = semantics
            expected_semantics_sha = semantics_sha
        elif semantics != expected_semantics or semantics_sha != expected_semantics_sha:
            raise ValueError(f"policy semantics drift for {period}")

        period_dir = output_dir / period
        _write_json(period_dir / "control.json", control)
        _write_json(period_dir / "identity.json", identity)
        _write_json(period_dir / "mapped-control.json", mapped_control)
        _write_json(period_dir / "screening.json", screening)
        _write_json(period_dir / "policy.json", policy_payload)
        monthly_policy_payloads[period] = policy_payload

        arm_transmission = [
            {
                "arm_id": str(arm.get("arm_id", "")),
                "semantic_target_sha256": str(arm.get("semantic_target_sha256", "")),
                "metrics": dict(arm.get("metrics", {})),
            }
            for arm in sorted(policy_payload.get("arms", []), key=lambda item: str(item.get("arm_id", "")))
        ]
        target_months.append({
            "period": period,
            "control_snapshot_sha256": str(control["manifest"]["semantic_snapshot_sha256"]),
            "control_mapping_sha256": str(mapped_control["manifest"]["semantic_mapping_sha256"]),
            "identity_semantic_sha256": str(identity["manifest"]["semantic_identity_sha256"]),
            "screening_sha256": str(screening["tse_screening_sha256"]),
            "evidence_provenance_sha256": str(screening["evidence_provenance_sha256"]),
            "policy_family_sha256": str(policy_payload["manifest"]["policy_family_sha256"]),
            "policy_payload_sha256": _canonical_sha256(policy_payload),
            "policy_semantics_sha256": semantics_sha,
            "direct_changed_security_ids": {
                "P1": directly_changed_security_ids(policy_payload, "P1"),
                "P2": directly_changed_security_ids(policy_payload, "P2"),
            },
            "policy_transmission": arm_transmission,
        })

    if expected_semantics is None or expected_semantics_sha is None:
        raise ValueError("no frozen target months were produced")
    target_manifest = {
        "artifact_version": "m3.3c0-historical-replay-targets-v0.2",
        "status": "HISTORICAL_REPLAY_TARGETS_FROZEN",
        "window": window_periods,
        "window_semantic_sha256": str(window.get("window_semantic_sha256", "")),
        "policy_semantics": expected_semantics,
        "policy_semantics_sha256": expected_semantics_sha,
        "months": target_months,
        "code_commit": code_commit,
    }
    blocker = verify_frozen_target_manifest(window, target_manifest)
    if blocker is not None:
        raise ValueError(f"frozen target manifest verification failed: {blocker}")

    _write_json(output_dir / "monthly_policy_payload_map.json", monthly_policy_payloads)
    _write_json(targets_manifest_path, target_manifest)
    return target_manifest


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_prepare(
        frozen_window_path=args.frozen_window,
        pre_return_input_manifest_path=args.pre_return_input_manifest,
        policy_config_path=args.policy_config,
        policies_path=args.policies,
        local_output_dir=args.local_output_dir,
        targets_manifest_path=args.targets_manifest,
        code_commit=args.code_commit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
