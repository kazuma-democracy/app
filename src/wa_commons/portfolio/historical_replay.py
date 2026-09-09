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

    qualified_periods = sorted(
        qualified_by_period,
        key=_month_ordinal,
    )
    triples: list[list[str]] = []
    for index in range(len(qualified_periods) - window_length + 1):
        periods = qualified_periods[index : index + window_length]
        ordinals = [_month_ordinal(period) for period in periods]
        if ordinals == list(
            range(ordinals[0], ordinals[0] + window_length)
        ):
            triples.append(periods)

    if not triples:
        return {
            "status": "BLOCK_HISTORICAL_REPLAY_COVERAGE",
            "window": [],
            "candidate_results": candidate_results,
        }

    window = max(
        triples,
        key=lambda periods: _month_ordinal(periods[-1]),
    )
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
