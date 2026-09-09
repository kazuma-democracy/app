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
