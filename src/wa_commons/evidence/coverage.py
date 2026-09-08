from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Iterable, Mapping

COVERAGE_VERSION = "m2.2a-coverage-v0.1"
COVERAGE_STATES = {
    "observed",
    "no_match",
    "unknown",
    "unresolved_identity",
    "not_integrated",
}


def _entity_id(entity: Mapping[str, object]) -> str:
    value = str(entity.get("entity_id", "")).strip()
    if not value:
        raise ValueError("coverage entity is missing entity_id")
    return value


def _identity_is_resolved(entity: Mapping[str, object]) -> bool:
    return str(entity.get("review_state", "")).upper() == "CONFIRMED"


def build_coverage_matrix(
    *,
    entities: Iterable[Mapping[str, object]],
    sources: Iterable[str],
    integrated_sources: set[str],
    observations: Iterable[Mapping[str, object]],
    unknown_sources: set[str],
) -> dict:
    """Build a deterministic entity-by-source evidence coverage matrix.

    Coverage states describe only whether an integrated source produced usable
    observations for a resolved entity. They are not moral or policy outcomes.
    In particular, ``no_match`` means only that the completed integrated source
    snapshot supplied no matching observation for that entity.
    """
    entity_rows = sorted((dict(entity) for entity in entities), key=_entity_id)
    source_ids = sorted({str(source).strip() for source in sources if str(source).strip()})
    integrated = {str(source).strip() for source in integrated_sources}
    unknown = {str(source).strip() for source in unknown_sources}

    counts: Counter[tuple[str, str]] = Counter()
    for observation in observations:
        source_id = str(observation.get("source_id", "")).strip()
        entity_id = str(observation.get("entity_id", "")).strip()
        if source_id and entity_id:
            counts[(source_id, entity_id)] += 1

    rows: list[dict[str, object]] = []
    for entity in entity_rows:
        entity_id = _entity_id(entity)
        for source_id in source_ids:
            observation_count = counts[(source_id, entity_id)]
            if source_id not in integrated:
                state = "not_integrated"
            elif not _identity_is_resolved(entity):
                state = "unresolved_identity"
            elif source_id in unknown:
                state = "unknown"
            elif observation_count:
                state = "observed"
            else:
                state = "no_match"
            rows.append(
                {
                    "entity_id": entity_id,
                    "source_id": source_id,
                    "state": state,
                    "observation_count": observation_count,
                }
            )

    state_counts = Counter(row["state"] for row in rows)
    return {
        "coverage_version": COVERAGE_VERSION,
        "entity_count": len(entity_rows),
        "source_count": len(source_ids),
        "cell_count": len(rows),
        "state_counts": {state: state_counts.get(state, 0) for state in sorted(COVERAGE_STATES)},
        "rows": rows,
    }


def canonical_coverage_sha256(matrix: Mapping[str, object]) -> str:
    payload = json.dumps(
        matrix,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
