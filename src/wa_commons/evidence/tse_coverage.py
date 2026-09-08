from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Iterable, Mapping

from .coverage import build_coverage_matrix, canonical_coverage_sha256

TSE_COVERAGE_ARTIFACT_VERSION = "m3-2d-tse-coverage-v0.1"
MOD_SOURCE_ID = "jp-mod-procurement"
_PUBLIC_PILOT_MEASUREMENT_KEYS = {
    "pilot_matched_entity_count",
    "unresolved_observation_count",
    "canonical_claim_count",
    "measurement_note",
}


def _corporate_number_values(entity: Mapping[str, object]) -> set[str]:
    values: set[str] = set()
    for identifier in entity.get("identifiers", []):
        if str(identifier.get("scheme", "")).strip() != "JP_CORPORATE_NUMBER":
            continue
        value = str(identifier.get("value", "")).strip()
        if value:
            values.add(value)
    return values


def _coverage_entities(identity: Mapping[str, object]) -> list[dict[str, object]]:
    manifest = identity.get("manifest", {})
    raw_entities = list(identity.get("entities", []))
    expected_count = manifest.get("entity_count")
    if expected_count is not None and int(expected_count) != len(raw_entities):
        raise ValueError(
            f"identity manifest entity_count {expected_count} does not match {len(raw_entities)} entities"
        )

    entities: list[dict[str, object]] = []
    for raw in raw_entities:
        entity = dict(raw)
        review_state = str(entity.get("review_state", "")).strip().upper()
        corporate_numbers = _corporate_number_values(entity)
        if review_state == "DISPUTED":
            entity["review_state"] = "DISPUTED"
        elif review_state == "CONFIRMED" and len(corporate_numbers) == 1:
            entity["review_state"] = "CONFIRMED"
        else:
            entity["review_state"] = "UNRESOLVED"
        entities.append(entity)
    return entities


def link_mod_procurement_observations(
    identity: Mapping[str, object],
    observations: Iterable[Mapping[str, object]],
) -> list[dict[str, str]]:
    """Link existing MOD observations to canonical TSE entities by exact corporate number only."""
    by_corporate_number: dict[str, str] = {}
    duplicates: set[str] = set()
    for entity in identity.get("entities", []):
        entity_id = str(entity.get("entity_id", "")).strip()
        numbers = _corporate_number_values(entity)
        if not entity_id or len(numbers) != 1:
            continue
        number = next(iter(numbers))
        if number in by_corporate_number:
            duplicates.add(number)
        else:
            by_corporate_number[number] = entity_id
    for number in duplicates:
        by_corporate_number.pop(number, None)

    linked: list[dict[str, str]] = []
    for observation in observations:
        if str(observation.get("identity_decision", "")).strip() != "AUTO_LINK":
            continue
        number = str(observation.get("corporate_number", "")).strip()
        if len(number) != 13 or not number.isdigit():
            continue
        entity_id = by_corporate_number.get(number)
        if entity_id:
            linked.append({"source_id": MOD_SOURCE_ID, "entity_id": entity_id})
    return linked


def _state_counts_by_source(matrix: Mapping[str, object]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in matrix.get("rows", []):
        counts[str(row["source_id"])][str(row["state"])] += 1
    return {
        source_id: dict(sorted(state_counts.items()))
        for source_id, state_counts in sorted(counts.items())
    }


def _state_counts_by_category(
    matrix: Mapping[str, object], source_catalog: Iterable[Mapping[str, object]]
) -> dict[str, dict[str, int]]:
    category_by_source = {
        str(source.get("source_id", "")).strip(): str(source.get("category", "")).strip()
        for source in source_catalog
    }
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in matrix.get("rows", []):
        category = category_by_source.get(str(row["source_id"]), "")
        if category:
            counts[category][str(row["state"])] += 1
    return {
        category: dict(sorted(state_counts.items()))
        for category, state_counts in sorted(counts.items())
    }


def _public_source_catalog(source_catalog: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    public_catalog: list[dict[str, object]] = []
    for raw_source in source_catalog:
        source = dict(raw_source)
        provenance = source.get("provenance")
        if isinstance(provenance, Mapping):
            source["provenance"] = {
                key: value
                for key, value in provenance.items()
                if key not in _PUBLIC_PILOT_MEASUREMENT_KEYS
            }
        public_catalog.append(source)
    return public_catalog


def build_tse_coverage(
    identity: Mapping[str, object],
    *,
    source_catalog: Iterable[Mapping[str, object]],
    linked_observations: Iterable[Mapping[str, object]],
    code_commit: str,
) -> dict:
    catalog = sorted(
        (dict(source) for source in source_catalog),
        key=lambda source: str(source.get("source_id", "")),
    )
    sources = [str(source.get("source_id", "")).strip() for source in catalog]
    integrated = {
        str(source.get("source_id", "")).strip()
        for source in catalog
        if source.get("integration_state") == "integrated"
    }
    unknown = {
        str(source.get("source_id", "")).strip()
        for source in catalog
        if source.get("run_state") == "unknown"
    }
    unresolved = {
        str(source.get("source_id", "")).strip()
        for source in catalog
        if source.get("identity_linkage_state") == "unresolved"
    }

    entities = _coverage_entities(identity)
    matrix = build_coverage_matrix(
        entities=entities,
        sources=sources,
        integrated_sources=integrated,
        observations=linked_observations,
        unknown_sources=unknown,
        unresolved_sources=unresolved,
    )
    identity_manifest = identity.get("manifest", {})
    coverage_sha = canonical_coverage_sha256(matrix)

    return {
        "manifest": {
            "artifact_version": TSE_COVERAGE_ARTIFACT_VERSION,
            "code_commit": code_commit,
            "identity_entity_count": len(entities),
            "identity_semantic_sha256": identity_manifest.get("semantic_identity_sha256"),
            "coverage_semantic_sha256": coverage_sha,
            "source_count": matrix["source_count"],
            "category_count": len({source.get("category") for source in catalog if source.get("category")}),
            "state_counts": dict(matrix["state_counts"]),
            "source_state_counts": _state_counts_by_source(matrix),
            "category_state_counts": _state_counts_by_category(matrix, catalog),
        },
        "source_catalog": catalog,
        "matrix": matrix,
    }


def write_tse_coverage(
    payload: Mapping[str, object],
    local_output: str | Path,
    public_output: str | Path,
) -> None:
    """Write the full row-level matrix locally and only aggregate metadata publicly."""
    local_path = Path(local_output)
    public_path = Path(public_output)
    if local_path.resolve() == public_path.resolve():
        raise ValueError("local and public outputs must differ")

    local_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    local_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    public_payload = {
        "manifest": payload["manifest"],
        "source_catalog": _public_source_catalog(payload["source_catalog"]),
    }
    public_path.write_text(
        json.dumps(public_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_tse_coverage_local(
    *,
    identity_path: str | Path,
    coverage_config_path: str | Path,
    mod_observations_path: str | Path,
    local_output: str | Path,
    public_output: str | Path,
    code_commit: str,
) -> dict:
    """Build #54 coverage only from operator-supplied local artifacts."""
    identity = json.loads(Path(identity_path).read_text(encoding="utf-8"))
    config = json.loads(Path(coverage_config_path).read_text(encoding="utf-8"))
    mod_observations = json.loads(Path(mod_observations_path).read_text(encoding="utf-8"))

    linked = link_mod_procurement_observations(identity, mod_observations)
    result = build_tse_coverage(
        identity,
        source_catalog=config["source_catalog"],
        linked_observations=linked,
        code_commit=code_commit,
    )
    write_tse_coverage(result, local_output, public_output)
    return result
