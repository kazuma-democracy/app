from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


_FORBIDDEN_PERFORMANCE_KEYS = {
    "benchmark_decimal_return",
    "benchmark_return",
    "close_price",
    "start_price",
    "end_price",
    "total_wealth_return",
    "portfolio_return",
    "performance",
}


def load_historical_replay_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _contains_performance_fields(value: Any, *, parent_key: str | None = None) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if parent_key != "market_source_metadata" and key_text in _FORBIDDEN_PERFORMANCE_KEYS:
                return True
            if _contains_performance_fields(nested, parent_key=key_text):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_performance_fields(item, parent_key=parent_key) for item in value)
    return False


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _block(status: str, candidate: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "evaluation_period": candidate.get("evaluation_period"),
        "decision_cutoff": candidate.get("decision_cutoff"),
        "blockers": [reason],
    }


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value.strip()) is not None


def _qualify_investable_proxy_candidate(
    candidate: Mapping[str, Any],
    config: Mapping[str, Any],
    cutoff: datetime,
) -> dict[str, Any]:
    control = candidate.get("control_source_metadata")
    if not isinstance(control, Mapping):
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "MISSING_CONTROL_SOURCE_METADATA")
    if str(control.get("kind", "")) != "ISHARES_1475_POINT_IN_TIME":
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_CONTROL_KIND")
    if control.get("exists") is not True or not str(control.get("locator", "")).strip():
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "CONTROL_SOURCE_UNAVAILABLE")
    available_at = _parse_timestamp(control.get("available_at"))
    if available_at is None:
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_CONTROL_AVAILABILITY")
    if available_at > cutoff:
        return _block("BLOCK_EVIDENCE_CUTOFF", candidate, "CONTROL_AVAILABLE_AFTER_CUTOFF")
    as_of_date = str(control.get("as_of_date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of_date):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_CONTROL_AS_OF_DATE")
    if as_of_date > cutoff.date().isoformat():
        return _block("BLOCK_REPRODUCIBILITY", candidate, "CONTROL_AS_OF_AFTER_CUTOFF")
    required_rights = str(config.get("allocation_source", {}).get("rights_required_state", "LOCAL_RESEARCH_ALLOWED"))
    if str(control.get("rights_state", "")) != required_rights:
        return _block("BLOCK_SOURCE_RIGHTS", candidate, "CONTROL_SOURCE_RIGHTS_NOT_CLEARED")
    if not _valid_sha256(control.get("source_sha256")):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_CONTROL_SOURCE_HASH")

    identity = candidate.get("identity_source_metadata")
    evidence = candidate.get("evidence_source_metadata")
    if not isinstance(identity, Mapping) or identity.get("availability_complete") is not True:
        return _block("BLOCK_EVIDENCE_CUTOFF", candidate, "IDENTITY_SOURCE_AVAILABILITY_INCOMPLETE")
    if not isinstance(evidence, Mapping) or evidence.get("availability_complete") is not True:
        return _block("BLOCK_EVIDENCE_CUTOFF", candidate, "EVIDENCE_SOURCE_AVAILABILITY_INCOMPLETE")
    if not _valid_sha256(identity.get("semantic_source_sha256")) or not _valid_sha256(evidence.get("semantic_source_sha256")):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_SOURCE_SEMANTIC_HASH")
    identity_sha = str(identity.get("identity_semantic_sha256", "")).strip()
    evidence_identity_sha = str(evidence.get("identity_semantic_sha256", "")).strip()
    if identity_sha or evidence_identity_sha:
        if not _valid_sha256(identity_sha) or not _valid_sha256(evidence_identity_sha) or identity_sha != evidence_identity_sha:
            return _block("BLOCK_REPRODUCIBILITY", candidate, "IDENTITY_HASH_MISMATCH")

    market_sources = candidate.get("market_source_metadata")
    if not isinstance(market_sources, Mapping):
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "MISSING_MARKET_SOURCE_METADATA")
    for role in config.get("required_market_source_roles", []):
        source = market_sources.get(role)
        if not isinstance(source, Mapping) or source.get("exists") is not True or not str(source.get("locator", "")).strip():
            return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, f"MARKET_SOURCE_UNAVAILABLE:{role}")
    return {
        "status": "CANDIDATE_QUALIFIED",
        "evaluation_period": str(candidate["evaluation_period"]),
        "decision_cutoff": candidate["decision_cutoff"],
        "blockers": [],
    }


def qualify_candidate_month(
    candidate: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    period = str(candidate.get("evaluation_period", ""))
    if _contains_performance_fields(candidate):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "PERFORMANCE_FIELD_PRESENT")
    if not re.fullmatch(r"\d{4}-\d{2}", period):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_EVALUATION_PERIOD")
    if period in set(config.get("engineering_validation_periods", [])):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "ENGINEERING_VALIDATION_PERIOD")
    if period in set(config.get("future_holdout_periods", [])):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "FUTURE_HOLDOUT_PERIOD")
    cutoff = _parse_timestamp(candidate.get("decision_cutoff"))
    if cutoff is None:
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_DECISION_CUTOFF")

    if str(config.get("allocation_source", {}).get("kind", "")) == "ISHARES_1475_POINT_IN_TIME":
        return _qualify_investable_proxy_candidate(candidate, config, cutoff)

    benchmark = candidate.get("benchmark_snapshot")
    if not isinstance(benchmark, Mapping):
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "MISSING_BENCHMARK_SNAPSHOT")
    benchmark_available = _parse_timestamp(benchmark.get("available_at"))
    if benchmark_available is None:
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_BENCHMARK_AVAILABILITY")
    if benchmark_available > cutoff:
        return _block("BLOCK_EVIDENCE_CUTOFF", candidate, "BENCHMARK_AVAILABLE_AFTER_CUTOFF")
    effective_date = str(benchmark.get("effective_date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", effective_date):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "INVALID_BENCHMARK_EFFECTIVE_DATE")
    if effective_date > cutoff.date().isoformat():
        return _block("BLOCK_REPRODUCIBILITY", candidate, "BENCHMARK_EFFECTIVE_AFTER_CUTOFF")

    screening = candidate.get("screening_snapshot")
    if not isinstance(screening, Mapping):
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "MISSING_SCREENING_SNAPSHOT")
    if screening.get("availability_complete") is not True:
        return _block("BLOCK_EVIDENCE_CUTOFF", candidate, "SCREENING_AVAILABILITY_INCOMPLETE")
    if str(screening.get("decision_cutoff", "")) != str(candidate.get("decision_cutoff", "")):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "SCREENING_CUTOFF_MISMATCH")
    if str(benchmark.get("identity_semantic_sha256", "")) != str(screening.get("identity_semantic_sha256", "")):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "IDENTITY_HASH_MISMATCH")

    market_sources = candidate.get("market_source_metadata")
    if not isinstance(market_sources, Mapping):
        return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, "MISSING_MARKET_SOURCE_METADATA")
    for role in config.get("required_market_source_roles", []):
        source = market_sources.get(role)
        if not isinstance(source, Mapping):
            return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, f"MISSING_MARKET_SOURCE:{role}")
        if source.get("exists") is not True or not str(source.get("locator", "")).strip():
            return _block("BLOCK_HISTORICAL_REPLAY_COVERAGE", candidate, f"MARKET_SOURCE_UNAVAILABLE:{role}")

    required_hashes = (
        benchmark.get("semantic_mapping_sha256"),
        benchmark.get("source_sha256"),
        benchmark.get("identity_semantic_sha256"),
        screening.get("screening_sha256"),
        screening.get("evidence_provenance_sha256"),
    )
    if any(not isinstance(value, str) or not value.strip() for value in required_hashes):
        return _block("BLOCK_REPRODUCIBILITY", candidate, "MISSING_REQUIRED_HASH")

    return {
        "status": "CANDIDATE_QUALIFIED",
        "evaluation_period": period,
        "decision_cutoff": candidate["decision_cutoff"],
        "blockers": [],
    }


from collections.abc import Sequence
import hashlib


def _month_ordinal(period: str) -> int:
    year, month = period.split("-")
    return int(year) * 12 + int(month)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _freeze_candidate_record(
    candidate: Mapping[str, Any],
    qualified: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(candidate.get("control_source_metadata"), Mapping):
        control = candidate["control_source_metadata"]
        identity = candidate["identity_source_metadata"]
        evidence = candidate["evidence_source_metadata"]
        return {
            "evaluation_period": qualified["evaluation_period"],
            "decision_cutoff": qualified["decision_cutoff"],
            "control_kind": control["kind"],
            "control_as_of_date": control["as_of_date"],
            "control_available_at": control["available_at"],
            "control_source_locator": control["locator"],
            "control_source_sha256": control["source_sha256"],
            "control_rights_state": control["rights_state"],
            "identity_source_semantic_sha256": identity["semantic_source_sha256"],
            "evidence_source_semantic_sha256": evidence["semantic_source_sha256"],
            "qualification_status": qualified["status"],
        }
    benchmark = candidate["benchmark_snapshot"]
    screening = candidate["screening_snapshot"]
    return {
        "evaluation_period": qualified["evaluation_period"],
        "decision_cutoff": qualified["decision_cutoff"],
        "benchmark_effective_date": benchmark["effective_date"],
        "benchmark_semantic_mapping_sha256": benchmark["semantic_mapping_sha256"],
        "benchmark_source_sha256": benchmark["source_sha256"],
        "identity_semantic_sha256": benchmark["identity_semantic_sha256"],
        "screening_sha256": screening["screening_sha256"],
        "evidence_provenance_sha256": screening["evidence_provenance_sha256"],
        "qualification_status": qualified["status"],
    }


def freeze_replay_window(
    candidates: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    ordered_candidates = sorted(
        candidates,
        key=lambda item: str(item.get("evaluation_period", "")),
    )
    qualified_by_period: dict[
        str, tuple[Mapping[str, Any], dict[str, Any]]
    ] = {}
    candidate_results: list[dict[str, Any]] = []

    for candidate in ordered_candidates:
        result = qualify_candidate_month(candidate, config)
        candidate_results.append(result)
        if result["status"] == "CANDIDATE_QUALIFIED":
            period = str(result["evaluation_period"])
            qualified_by_period[period] = (candidate, result)

    window_length = int(config.get("window_length_months", 3))
    if window_length != 3:
        window_length = 3

    selection_rule = str(config.get(
        "selection_rule",
        "MOST_RECENT_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS",
    ))
    if selection_rule == "EXACT_PREREGISTERED_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS":
        window = [str(period) for period in config.get("headline_candidate_periods", [])]
        if len(window) != window_length or any(period not in qualified_by_period for period in window):
            return {
                "status": "BLOCK_HISTORICAL_REPLAY_COVERAGE",
                "window": [],
                "candidate_results": candidate_results,
            }
        ordinals = [_month_ordinal(period) for period in window]
        if ordinals != list(range(ordinals[0], ordinals[0] + window_length)):
            return {
                "status": "BLOCK_HISTORICAL_REPLAY_COVERAGE",
                "window": [],
                "candidate_results": candidate_results,
            }
    else:
        qualified_periods = sorted(
            qualified_by_period,
            key=_month_ordinal,
        )
        triples: list[list[str]] = []
        for index in range(len(qualified_periods) - window_length + 1):
            periods = qualified_periods[index : index + window_length]
            ordinals = [_month_ordinal(period) for period in periods]
            if ordinals == list(range(ordinals[0], ordinals[0] + window_length)):
                triples.append(periods)
        if not triples:
            return {
                "status": "BLOCK_HISTORICAL_REPLAY_COVERAGE",
                "window": [],
                "candidate_results": candidate_results,
            }
        window = max(triples, key=lambda periods: _month_ordinal(periods[-1]))
    frozen_candidates = [
        _freeze_candidate_record(*qualified_by_period[period])
        for period in window
    ]
    policy_contract = dict(config.get("policy_contract", {}))
    semantic_manifest = {
        "artifact_version": config.get("artifact_version"),
        "selection_rule": config.get(
            "selection_rule",
            "MOST_RECENT_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS",
        ),
        "window": window,
        "months": frozen_candidates,
        "policy_contract": {
            "artifact_version": policy_contract.get("artifact_version"),
            "profile_id": policy_contract.get("profile_id"),
            "profile_version": str(policy_contract.get("profile_version", "")),
            "policy_sha256": policy_contract.get("policy_sha256"),
            "policy_config_semantic_sha256": policy_contract.get(
                "policy_config_semantic_sha256"
            ),
            "arms": list(policy_contract.get("arms", [])),
        },
    }
    return {
        "status": "HISTORICAL_REPLAY_WINDOW_FROZEN",
        **semantic_manifest,
        "candidate_results": candidate_results,
        "window_semantic_sha256": _canonical_sha256(semantic_manifest),
    }


from decimal import Decimal, InvalidOperation


def _decimal_text(value: Decimal, decimals: int = 12) -> str:
    quantum = Decimal(1).scaleb(-decimals)
    return format(value.quantize(quantum), "f")


def _replay_block(status: str, window: Sequence[str], reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "window": list(window),
        "blockers": [reason],
    }


def _policy_semantics_signature(payload: Mapping[str, Any]) -> tuple[Any, ...] | None:
    if payload.get("status") != "FROZEN_POLICY_FAMILY":
        return None
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        return None
    arms = payload.get("arms")
    if not isinstance(arms, list):
        return None
    arm_signature = tuple(
        (
            str(arm.get("arm_id", "")),
            str(arm.get("allocation_policy_id", "")),
            str(arm.get("allocation_policy_version", "")),
        )
        for arm in sorted(arms, key=lambda item: str(item.get("arm_id", "")))
    )
    return (
        str(manifest.get("profile_id", "")),
        str(manifest.get("profile_version", "")),
        str(manifest.get("policy_sha256", "")),
        arm_signature,
    )


def _market_return_index(payload: Mapping[str, Any]) -> dict[str, Decimal] | None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return None
    index: dict[str, Decimal] = {}
    for row in rows:
        security_id = str(row.get("security_id", ""))
        state = str(row.get("state", ""))
        if not security_id or not state.startswith("RETURN_OK_"):
            return None
        if security_id in index:
            return None
        try:
            index[security_id] = Decimal(str(row["total_wealth_return"]))
        except (KeyError, InvalidOperation):
            return None
    return index


def _arm_month_return(
    arm: Mapping[str, Any],
    market_returns: Mapping[str, Decimal],
) -> Decimal | None:
    rows = arm.get("target_weights")
    if not isinstance(rows, list):
        return None
    total_weight = Decimal("0")
    result = Decimal("0")
    seen: set[str] = set()
    for row in sorted(rows, key=lambda item: str(item.get("security_id", ""))):
        security_id = str(row.get("security_id", ""))
        if not security_id or security_id in seen or security_id not in market_returns:
            return None
        try:
            weight = Decimal(str(row["target_weight"]))
        except (KeyError, InvalidOperation):
            return None
        if weight < 0:
            return None
        seen.add(security_id)
        total_weight += weight
        result += weight * market_returns[security_id]
    if total_weight != Decimal("1"):
        return None
    return result


def run_frozen_replay(
    window_manifest: Mapping[str, Any],
    monthly_policy_payloads: Mapping[str, Mapping[str, Any]],
    monthly_market_payloads: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if window_manifest.get("status") != "HISTORICAL_REPLAY_WINDOW_FROZEN":
        return _replay_block("BLOCK_REPRODUCIBILITY", [], "WINDOW_NOT_FROZEN")

    window = list(window_manifest.get("window", []))
    if len(window) != 3:
        return _replay_block("BLOCK_REPRODUCIBILITY", window, "INVALID_WINDOW_LENGTH")

    expected_signature: tuple[Any, ...] | None = None
    cumulative_by_arm: dict[str, Decimal] = {}
    benchmark_wealth = Decimal("1")
    month_results: list[dict[str, Any]] = []

    for period in window:
        policy_payload = monthly_policy_payloads.get(period)
        if not isinstance(policy_payload, Mapping):
            return _replay_block(
                "BLOCK_REPRODUCIBILITY", window, f"MISSING_POLICY_MONTH:{period}"
            )
        signature = _policy_semantics_signature(policy_payload)
        if signature is None:
            return _replay_block(
                "BLOCK_REPRODUCIBILITY", window, f"INVALID_POLICY_MONTH:{period}"
            )
        if expected_signature is None:
            expected_signature = signature
        elif signature != expected_signature:
            return _replay_block(
                "BLOCK_REPRODUCIBILITY", window, f"POLICY_SEMANTICS_DRIFT:{period}"
            )

        market_payload = monthly_market_payloads.get(period)
        if not isinstance(market_payload, Mapping):
            return _replay_block(
                "BLOCK_MARKET_DATA", window, f"MISSING_MARKET_MONTH:{period}"
            )
        rows = market_payload.get("rows", [])
        if any(
            str(row.get("state", "")) == "BLOCK_CORPORATE_ACTION"
            for row in rows
            if isinstance(row, Mapping)
        ):
            return _replay_block(
                "BLOCK_CORPORATE_ACTION", window, f"CORPORATE_ACTION_BLOCK:{period}"
            )
        if market_payload.get("status") != "MONTHLY_RETURN_OK":
            return _replay_block(
                "BLOCK_MARKET_DATA", window, f"MONTHLY_RETURN_BLOCKED:{period}"
            )
        market_returns = _market_return_index(market_payload)
        if market_returns is None:
            return _replay_block(
                "BLOCK_MARKET_DATA", window, f"INVALID_MARKET_ROWS:{period}"
            )
        try:
            benchmark_return = Decimal(str(market_payload["benchmark_decimal_return"]))
        except (KeyError, InvalidOperation):
            return _replay_block(
                "BLOCK_MARKET_DATA", window, f"INVALID_BENCHMARK_RETURN:{period}"
            )
        benchmark_wealth *= Decimal("1") + benchmark_return

        transmission: list[dict[str, Any]] = []
        financial_arms: list[dict[str, Any]] = []
        for arm in sorted(
            policy_payload["arms"],
            key=lambda item: str(item.get("arm_id", "")),
        ):
            arm_id = str(arm.get("arm_id", ""))
            month_return = _arm_month_return(arm, market_returns)
            if month_return is None:
                return _replay_block(
                    "BLOCK_MARKET_DATA", window, f"TARGET_MARKET_MISMATCH:{period}:{arm_id}"
                )
            cumulative_by_arm.setdefault(arm_id, Decimal("1"))
            cumulative_by_arm[arm_id] *= Decimal("1") + month_return
            transmission.append({
                "arm_id": arm_id,
                "semantic_target_sha256": arm.get("semantic_target_sha256"),
                "metrics": dict(arm.get("metrics", {})),
            })
            financial_arms.append({
                "arm_id": arm_id,
                "portfolio_return": _decimal_text(month_return),
            })

        month_results.append({
            "period": period,
            "policy_transmission": transmission,
            "financial": {
                "benchmark_return": _decimal_text(benchmark_return),
                "arms": financial_arms,
            },
        })

    arm_summaries = [
        {
            "arm_id": arm_id,
            "cumulative_wealth": _decimal_text(cumulative_by_arm[arm_id]),
            "cumulative_return": _decimal_text(cumulative_by_arm[arm_id] - Decimal("1")),
        }
        for arm_id in sorted(cumulative_by_arm)
    ]
    benchmark_summary = {
        "cumulative_wealth": _decimal_text(benchmark_wealth),
        "cumulative_return": _decimal_text(benchmark_wealth - Decimal("1")),
    }
    semantic_payload = {
        "status": "HISTORICAL_REPLAY_OK",
        "window": window,
        "window_semantic_sha256": window_manifest.get("window_semantic_sha256"),
        "months": month_results,
        "arms": arm_summaries,
        "benchmark": benchmark_summary,
    }
    return {
        **semantic_payload,
        "semantic_payload_sha256": _canonical_sha256(semantic_payload),
    }


def _valid_sha256_text(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def verify_frozen_target_manifest(
    window_manifest: Mapping[str, Any],
    target_manifest: Mapping[str, Any],
) -> str | None:
    if window_manifest.get("status") != "HISTORICAL_REPLAY_WINDOW_FROZEN":
        return "BLOCK_REPRODUCIBILITY"
    if target_manifest.get("status") != "HISTORICAL_REPLAY_TARGETS_FROZEN":
        return "BLOCK_REPRODUCIBILITY"
    if _contains_performance_fields(target_manifest):
        return "BLOCK_REPRODUCIBILITY"

    window = list(window_manifest.get("window", []))
    if len(window) != 3 or list(target_manifest.get("window", [])) != window:
        return "BLOCK_REPRODUCIBILITY"
    window_sha = window_manifest.get("window_semantic_sha256")
    if not _valid_sha256_text(window_sha):
        return "BLOCK_REPRODUCIBILITY"
    if target_manifest.get("window_semantic_sha256") != window_sha:
        return "BLOCK_REPRODUCIBILITY"

    policy_semantics = target_manifest.get("policy_semantics")
    policy_semantics_sha = target_manifest.get("policy_semantics_sha256")
    if not isinstance(policy_semantics, Mapping):
        return "BLOCK_REPRODUCIBILITY"
    if not _valid_sha256_text(policy_semantics_sha):
        return "BLOCK_REPRODUCIBILITY"
    if policy_semantics_sha != _canonical_sha256(policy_semantics):
        return "BLOCK_REPRODUCIBILITY"

    months = target_manifest.get("months")
    if not isinstance(months, list) or len(months) != 3:
        return "BLOCK_REPRODUCIBILITY"
    by_period: dict[str, Mapping[str, Any]] = {}
    required_hashes = (
        "control_snapshot_sha256",
        "control_mapping_sha256",
        "identity_semantic_sha256",
        "screening_sha256",
        "evidence_provenance_sha256",
        "policy_family_sha256",
        "policy_payload_sha256",
        "policy_semantics_sha256",
    )
    for month in months:
        if not isinstance(month, Mapping):
            return "BLOCK_REPRODUCIBILITY"
        period = str(month.get("period", ""))
        if period in by_period or period not in window:
            return "BLOCK_REPRODUCIBILITY"
        by_period[period] = month
        if any(not _valid_sha256_text(month.get(key)) for key in required_hashes):
            return "BLOCK_REPRODUCIBILITY"
        if month.get("policy_semantics_sha256") != policy_semantics_sha:
            return "BLOCK_REPRODUCIBILITY"
        changed = month.get("direct_changed_security_ids")
        if not isinstance(changed, Mapping):
            return "BLOCK_REPRODUCIBILITY"
        for arm_id in ("P1", "P2"):
            values = changed.get(arm_id)
            if not isinstance(values, list):
                return "BLOCK_REPRODUCIBILITY"
            normalized = [str(value) for value in values]
            if normalized != sorted(set(normalized)):
                return "BLOCK_REPRODUCIBILITY"

    if set(by_period) != set(window):
        return "BLOCK_REPRODUCIBILITY"
    return None


def _proxy_policy_semantics(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    manifest = payload.get("manifest")
    arms = payload.get("arms")
    if payload.get("status") != "FROZEN_POLICY_FAMILY":
        return None
    if not isinstance(manifest, Mapping) or not isinstance(arms, list):
        return None
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


def _proxy_target_months(targets: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    months = targets.get("months")
    if not isinstance(months, list):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for month in months:
        if not isinstance(month, Mapping):
            return {}
        period = str(month.get("period", ""))
        if not period or period in result:
            return {}
        result[period] = month
    return result


def _proxy_security_returns(payload: Mapping[str, Any]) -> tuple[str | None, dict[str, Decimal]]:
    security_payload = payload.get("security_returns")
    if not isinstance(security_payload, Mapping):
        return "BLOCK_MARKET_DATA", {}
    if security_payload.get("status") != "SECURITY_RETURNS_OK":
        return "BLOCK_MARKET_DATA", {}
    rows = security_payload.get("rows")
    if not isinstance(rows, list):
        return "BLOCK_MARKET_DATA", {}
    values: dict[str, Decimal] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            return "BLOCK_MARKET_DATA", {}
        state = str(row.get("state", ""))
        if state == "BLOCK_CORPORATE_ACTION":
            return "BLOCK_CORPORATE_ACTION", {}
        if not state.startswith("RETURN_OK_"):
            return "BLOCK_MARKET_DATA", {}
        security_id = str(row.get("security_id", ""))
        if not security_id or security_id in values:
            return "BLOCK_MARKET_DATA", {}
        try:
            values[security_id] = Decimal(str(row["total_wealth_return"]))
        except (KeyError, InvalidOperation):
            return "BLOCK_MARKET_DATA", {}
    return None, values


def _proxy_arm(payload: Mapping[str, Any], arm_id: str) -> Mapping[str, Any] | None:
    arms = [
        arm for arm in payload.get("arms", [])
        if isinstance(arm, Mapping) and str(arm.get("arm_id", "")) == arm_id
    ]
    return arms[0] if len(arms) == 1 else None


def run_investable_proxy_replay(
    window_manifest: Mapping[str, Any],
    frozen_targets: Mapping[str, Any],
    monthly_policy_payloads: Mapping[str, Mapping[str, Any]],
    monthly_market_payloads: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    from wa_commons.portfolio.investable_proxy import (
        compute_residual_sleeve_financial,
        directly_changed_security_ids,
    )

    window = list(window_manifest.get("window", []))
    if verify_frozen_target_manifest(window_manifest, frozen_targets) is not None:
        return _replay_block("BLOCK_REPRODUCIBILITY", window, "TARGETS_NOT_FROZEN")
    if str(config.get("allocation_source", {}).get("kind", "")) != "ISHARES_1475_POINT_IN_TIME":
        return _replay_block("BLOCK_REPRODUCIBILITY", window, "INVALID_PROXY_CONFIG")
    target_months = _proxy_target_months(frozen_targets)
    if set(target_months) != set(window):
        return _replay_block("BLOCK_REPRODUCIBILITY", window, "TARGET_MONTH_MISMATCH")

    validated_policies: dict[str, Mapping[str, Any]] = {}
    expected_semantics_sha = str(frozen_targets.get("policy_semantics_sha256", ""))
    for period in window:
        policy = monthly_policy_payloads.get(period)
        if not isinstance(policy, Mapping):
            return _replay_block("BLOCK_REPRODUCIBILITY", window, f"MISSING_POLICY_MONTH:{period}")
        target_month = target_months[period]
        semantics = _proxy_policy_semantics(policy)
        if semantics is None or _canonical_sha256(semantics) != expected_semantics_sha:
            return _replay_block("BLOCK_REPRODUCIBILITY", window, f"POLICY_SEMANTICS_DRIFT:{period}")
        if _canonical_sha256(policy) != str(target_month.get("policy_payload_sha256", "")):
            return _replay_block("BLOCK_REPRODUCIBILITY", window, f"POLICY_PAYLOAD_HASH_MISMATCH:{period}")
        family_sha = str(policy.get("manifest", {}).get("policy_family_sha256", ""))
        if family_sha != str(target_month.get("policy_family_sha256", "")):
            return _replay_block("BLOCK_REPRODUCIBILITY", window, f"POLICY_FAMILY_HASH_MISMATCH:{period}")
        for arm_id in ("P1", "P2"):
            expected_ids = list(target_month.get("direct_changed_security_ids", {}).get(arm_id, []))
            try:
                actual_ids = directly_changed_security_ids(policy, arm_id)
            except ValueError:
                return _replay_block("BLOCK_REPRODUCIBILITY", window, f"INVALID_POLICY_ARM:{period}:{arm_id}")
            if actual_ids != expected_ids:
                return _replay_block("BLOCK_REPRODUCIBILITY", window, f"DIRECT_CHANGE_HASH_MISMATCH:{period}:{arm_id}")
        validated_policies[period] = policy

    cumulative_by_arm = {arm_id: Decimal("1") for arm_id in ("P0", "P1", "P2")}
    topix_wealth = Decimal("1")
    month_results: list[dict[str, Any]] = []

    for period in window:
        market = monthly_market_payloads.get(period)
        if not isinstance(market, Mapping) or market.get("status") != "PROXY_MARKET_BUNDLE_OK":
            return _replay_block("BLOCK_MARKET_DATA", window, f"INVALID_PROXY_MARKET_MONTH:{period}")
        market_block, security_returns = _proxy_security_returns(market)
        if market_block is not None:
            return _replay_block(market_block, window, f"SECURITY_RETURN_BLOCK:{period}")
        if "TSE:1475" not in security_returns:
            return _replay_block("BLOCK_MARKET_DATA", window, f"MISSING_P0_RETURN:{period}")
        p0_return = security_returns["TSE:1475"]

        topix = market.get("topix_roi")
        if not isinstance(topix, Mapping) or topix.get("status") != "BENCHMARK_ROI_OK":
            return _replay_block("BLOCK_MARKET_DATA", window, f"INVALID_TOPIX_RETURN:{period}")
        try:
            topix_return = Decimal(str(topix["decimal_return"]))
        except (KeyError, InvalidOperation):
            return _replay_block("BLOCK_MARKET_DATA", window, f"INVALID_TOPIX_RETURN:{period}")

        policy = validated_policies[period]
        p0_arm = _proxy_arm(policy, "P0")
        if p0_arm is None:
            return _replay_block("BLOCK_REPRODUCIBILITY", window, f"MISSING_P0_ARM:{period}")
        control_rows = list(p0_arm.get("target_weights", []))
        transmission: list[dict[str, Any]] = []
        financial_arms: list[dict[str, Any]] = []
        for arm_id in ("P0", "P1", "P2"):
            arm = _proxy_arm(policy, arm_id)
            if arm is None:
                return _replay_block("BLOCK_REPRODUCIBILITY", window, f"MISSING_POLICY_ARM:{period}:{arm_id}")
            transmission.append({
                "arm_id": arm_id,
                "semantic_target_sha256": arm.get("semantic_target_sha256"),
                "metrics": dict(arm.get("metrics", {})),
            })
            if arm_id == "P0":
                arm_return = p0_return
            else:
                try:
                    residual = compute_residual_sleeve_financial(
                        p0_total_return=p0_return,
                        control_rows=control_rows,
                        policy_rows=list(arm.get("target_weights", [])),
                        changed_returns=security_returns,
                    )
                    arm_return = Decimal(str(residual["policy_return"]))
                except ValueError:
                    return _replay_block("BLOCK_MARKET_DATA", window, f"CHANGED_SECURITY_RETURN_MISSING:{period}:{arm_id}")
            cumulative_by_arm[arm_id] *= Decimal("1") + arm_return
            financial_arms.append({
                "arm_id": arm_id,
                "portfolio_return": _decimal_text(arm_return),
                "policy_effect_vs_p0": _decimal_text(arm_return - p0_return),
            })
        topix_wealth *= Decimal("1") + topix_return
        month_results.append({
            "period": period,
            "policy_transmission": transmission,
            "financial": {
                "p0_return": _decimal_text(p0_return),
                "arms": financial_arms,
                "topix_total_return": _decimal_text(topix_return),
                "p0_tracking_difference_vs_topix": _decimal_text(p0_return - topix_return),
            },
        })

    arm_summaries = [
        {
            "arm_id": arm_id,
            "cumulative_wealth": _decimal_text(cumulative_by_arm[arm_id]),
            "cumulative_return": _decimal_text(cumulative_by_arm[arm_id] - Decimal("1")),
        }
        for arm_id in ("P0", "P1", "P2")
    ]
    topix_summary = {
        "cumulative_wealth": _decimal_text(topix_wealth),
        "cumulative_return": _decimal_text(topix_wealth - Decimal("1")),
    }
    semantic_payload = {
        "status": "HISTORICAL_REPLAY_OK",
        "window": window,
        "window_semantic_sha256": window_manifest.get("window_semantic_sha256"),
        "targets_semantic_sha256": _canonical_sha256(frozen_targets),
        "months": month_results,
        "arms": arm_summaries,
        "topix": topix_summary,
    }
    return {
        **semantic_payload,
        "semantic_payload_sha256": _canonical_sha256(semantic_payload),
    }
