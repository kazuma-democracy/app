from __future__ import annotations

from typing import Iterable, Mapping

from .enrich import enrich_entity_batch, strong_id
from .models import EntityRecord, Identifier, SourceRef

IDENTITY_POLICY_VERSION = "wa-conservative-v0.2"


def _source_from_dict(value: Mapping[str, object]) -> SourceRef:
    return SourceRef(
        source=str(value.get("source", "")),
        source_key=str(value.get("source_key", "")),
        snapshot=str(value.get("snapshot", "")),
        url=str(value.get("url", "")),
        retrieved_at=str(value.get("retrieved_at", "")),
        adapter_version=str(value.get("adapter_version", "0.1")),
    )


def _entity_from_dict(value: Mapping[str, object]) -> EntityRecord:
    identifiers = [
        Identifier(
            scheme=str(item.get("scheme", "")),
            value=str(item.get("value", "")),
            source=_source_from_dict(item.get("source", {})),
        )
        for item in value.get("identifiers", [])
    ]
    return EntityRecord(
        entity_id=str(value.get("entity_id", "")),
        canonical_name=str(value.get("canonical_name", "")),
        jurisdiction=str(value.get("jurisdiction", "JP")),
        aliases=[str(item) for item in value.get("aliases", [])],
        identifiers=identifiers,
        addresses=[str(item) for item in value.get("addresses", [])],
        review_state=str(value.get("review_state", "CONFIRMED")),
        review_reason=value.get("review_reason"),
    )


def build_tse_identity_spine(
    universe: Mapping[str, object],
    *,
    edinet_rows: Iterable[Mapping[str, object]],
    edinet_source: SourceRef,
    nta_rows: Iterable[Mapping[str, object]] = (),
    nta_source: SourceRef | None = None,
    gleif_rows: Iterable[Mapping[str, object]] = (),
    gleif_source: SourceRef | None = None,
    code_commit: str,
    source_metadata: Mapping[str, Mapping[str, object]],
) -> dict:
    entities = [_entity_from_dict(row) for row in universe.get("entities", [])]
    enriched = enrich_entity_batch(
        entities,
        edinet_rows=edinet_rows,
        edinet_source=edinet_source,
        nta_rows=nta_rows,
        nta_source=nta_source,
        gleif_rows=gleif_rows,
        gleif_source=gleif_source,
    )
    enriched.sort(key=lambda entity: entity.entity_id)

    disputed = [entity for entity in enriched if entity.review_state == "DISPUTED"]
    mapped = [
        entity
        for entity in enriched
        if entity.review_state != "DISPUTED" and strong_id(entity, "JP_CORPORATE_NUMBER") is not None
    ]
    unresolved = [
        entity
        for entity in enriched
        if entity.review_state != "DISPUTED" and strong_id(entity, "JP_CORPORATE_NUMBER") is None
    ]

    universe_manifest = universe.get("manifest", {})
    manifest = {
        "identity_policy_version": IDENTITY_POLICY_VERSION,
        "code_commit": code_commit,
        "universe_snapshot": universe_manifest.get("snapshot"),
        "universe_source_sha256": universe_manifest.get("source_sha256"),
        "universe_semantic_payload_sha256": universe_manifest.get("semantic_payload_sha256"),
        "entity_count": len(enriched),
        "mapped_count": len(mapped),
        "unresolved_count": len(unresolved),
        "disputed_count": len(disputed),
        "sources": {key: dict(value) for key, value in sorted(source_metadata.items())},
    }
    return {
        "manifest": manifest,
        "entities": [entity.to_dict() for entity in enriched],
    }
