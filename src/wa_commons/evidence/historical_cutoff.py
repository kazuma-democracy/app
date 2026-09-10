from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Sequence


def _aware_datetime(value: object, *, field: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return parsed


def select_sources_available_at_cutoff(
    sources: Sequence[Mapping[str, Any]],
    *,
    decision_cutoff: str,
) -> list[dict[str, Any]]:
    cutoff = _aware_datetime(decision_cutoff, field="decision_cutoff")
    selected: list[dict[str, Any]] = []
    for raw in sources:
        source = dict(raw)
        available_at = _aware_datetime(source.get("available_at"), field="available_at")
        if available_at <= cutoff:
            selected.append(source)
    return sorted(selected, key=lambda item: (str(item.get("available_at", "")), str(item.get("snapshot_version", ""))))


import hashlib
import json
from copy import deepcopy
from pathlib import Path

from wa_commons.evidence.mod_procurement import parse_workbook
from wa_commons.evidence.tse_coverage import build_tse_coverage, link_mod_procurement_observations
from wa_commons.policy.tse_screening import build_tse_policy_screening


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _historical_source_catalog(
    source_catalog: Sequence[Mapping[str, Any]],
    *,
    selected_sources: Sequence[Mapping[str, Any]],
    observations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    catalog = deepcopy([dict(item) for item in source_catalog])
    source_hashes = sorted({str(item.get("source_sha256", "")) for item in observations if item.get("source_sha256")})
    selected_summary = [
        {
            "snapshot_version": str(item.get("snapshot_version", "")),
            "available_at": str(item.get("available_at", "")),
            "source_url": str(item.get("source_url", "")),
        }
        for item in selected_sources
    ]
    for source in catalog:
        if source.get("source_id") == "jp-mod-procurement":
            provenance = dict(source.get("provenance", {}))
            provenance.update({
                "historical_cutoff_mode": True,
                "selected_sources": selected_summary,
                "source_sha256s": source_hashes,
            })
            source["provenance"] = provenance
    return catalog


def build_historical_screening(
    *,
    identity: Mapping[str, Any],
    mod_sources: Sequence[Mapping[str, Any]],
    decision_cutoff: str,
    coverage_source_catalog: Sequence[Mapping[str, Any]],
    policies: Sequence[Mapping[str, Any]],
    code_commit: str,
) -> dict[str, Any]:
    selected = select_sources_available_at_cutoff(mod_sources, decision_cutoff=decision_cutoff)
    observations: list[dict[str, Any]] = []
    for source in selected:
        local_path = Path(str(source.get("local_path", "")))
        if not local_path.is_file():
            raise ValueError(f"historical MOD local_path unavailable: {local_path}")
        parsed = parse_workbook(
            local_path,
            retrieved_at=str(source.get("retrieved_at", source["available_at"])),
            source_url=str(source.get("source_url", "")),
            source_page_url=str(source.get("source_page_url", "")),
            snapshot_version=str(source.get("snapshot_version", "")),
            fiscal_year=int(source.get("fiscal_year", 2026)),
        )
        observations.extend(item.to_dict() for item in parsed)

    observations.sort(key=lambda item: str(item["observation_id"]))
    catalog = _historical_source_catalog(
        coverage_source_catalog,
        selected_sources=selected,
        observations=observations,
    )
    linked = link_mod_procurement_observations(identity, observations)
    coverage = build_tse_coverage(
        identity,
        source_catalog=catalog,
        linked_observations=linked,
        code_commit=code_commit,
    )
    screening = build_tse_policy_screening(
        identity=identity,
        coverage_artifact=coverage,
        mod_observations=observations,
        policies=policies,
        code_commit=code_commit,
    )
    provenance = {
        "decision_cutoff": decision_cutoff,
        "selected_mod_sources": [
            {
                "snapshot_version": str(item.get("snapshot_version", "")),
                "available_at": str(item.get("available_at", "")),
                "source_url": str(item.get("source_url", "")),
            }
            for item in selected
        ],
        "observation_source_sha256s": sorted({str(item["source_sha256"]) for item in observations}),
        "identity_semantic_sha256": identity.get("manifest", {}).get("semantic_identity_sha256"),
        "coverage_semantic_sha256": coverage.get("manifest", {}).get("coverage_semantic_sha256"),
        "tse_screening_sha256": screening.get("tse_screening_sha256"),
    }
    result = dict(screening)
    result.update({
        "decision_cutoff": decision_cutoff,
        "availability_complete": True,
        "selected_mod_snapshot_versions": [str(item.get("snapshot_version", "")) for item in selected],
        "evidence_provenance_sha256": _canonical_sha256(provenance),
        "historical_coverage": coverage,
        "historical_provenance": provenance,
    })
    return result
