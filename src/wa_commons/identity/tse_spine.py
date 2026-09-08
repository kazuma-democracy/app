from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

from .enrich import build_nta_corporate_index, enrich_entity_batch, strong_id
from .models import EntityRecord, Identifier, SourceRef

IDENTITY_POLICY_VERSION = "wa-conservative-v0.2"
GLEIF_JP_REGISTRATION_AUTHORITY_ID = "RA001075"


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


def _semantic_entity(entity: EntityRecord) -> dict:
    identifiers = [
        {
            "scheme": identifier.scheme,
            "value": identifier.value,
            "source": {
                "source": identifier.source.source,
                "snapshot": identifier.source.snapshot,
                "url": identifier.source.url,
                "adapter_version": identifier.source.adapter_version,
            },
        }
        for identifier in entity.identifiers
    ]
    identifiers.sort(
        key=lambda item: (
            item["scheme"],
            item["value"],
            item["source"]["source"],
            item["source"]["snapshot"],
            item["source"]["url"],
            item["source"]["adapter_version"],
        )
    )
    return {
        "entity_id": entity.entity_id,
        "canonical_name": entity.canonical_name,
        "jurisdiction": entity.jurisdiction,
        "aliases": sorted(entity.aliases),
        "identifiers": identifiers,
        "addresses": sorted(entity.addresses),
        "review_state": entity.review_state,
        "review_reason": entity.review_reason,
    }


def _semantic_identity_sha256(entities: list[EntityRecord]) -> str:
    payload = [_semantic_entity(entity) for entity in entities]
    payload.sort(key=lambda item: item["entity_id"])
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _gleif_japan_registration_rows(
    rows: Iterable[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    authority_keys = (
        "Entity.RegistrationAuthority.RegistrationAuthorityID",
        "registration_authority_id",
        "registrationAuthorityId",
    )
    entity_id_keys = (
        "Entity.RegistrationAuthority.RegistrationAuthorityEntityID",
        "registration_authority_entity_id",
        "registrationAuthorityEntityId",
    )
    output: list[Mapping[str, object]] = []
    for row in rows:
        authority = next(
            (str(row.get(key, "")).strip() for key in authority_keys if str(row.get(key, "")).strip()),
            "",
        )
        registration_entity_id = next(
            (str(row.get(key, "")).strip() for key in entity_id_keys if str(row.get(key, "")).strip()),
            "",
        )
        if authority == GLEIF_JP_REGISTRATION_AUTHORITY_ID and registration_entity_id:
            output.append(row)
    return output


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
    universe_manifest = universe.get("manifest", {})
    raw_entities = list(universe.get("entities", []))
    expected_entity_count = universe_manifest.get("entity_count")
    if expected_entity_count is not None and int(expected_entity_count) != len(raw_entities):
        raise ValueError(
            f"universe manifest entity_count {expected_entity_count} does not match {len(raw_entities)} entities"
        )

    seen_jpx_codes: set[str] = set()
    for row in raw_entities:
        for identifier in row.get("identifiers", []):
            if str(identifier.get("scheme", "")) != "JPX_SECURITY_CODE":
                continue
            code = str(identifier.get("value", "")).strip()
            if code in seen_jpx_codes:
                raise ValueError(f"duplicate JPX_SECURITY_CODE: {code}")
            seen_jpx_codes.add(code)

    entities = [_entity_from_dict(row) for row in raw_entities]
    nta_rows = list(nta_rows)
    nta_by_corporate = build_nta_corporate_index(nta_rows)
    gleif_rows = _gleif_japan_registration_rows(gleif_rows)
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
    nta_validated = [
        entity
        for entity in enriched
        if entity.review_state != "DISPUTED"
        and (number := strong_id(entity, "JP_CORPORATE_NUMBER")) is not None
        and number in nta_by_corporate
    ]

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
        "edinet_count": sum(strong_id(entity, "EDINET_CODE") is not None for entity in enriched),
        "corporate_number_count": sum(
            strong_id(entity, "JP_CORPORATE_NUMBER") is not None for entity in enriched
        ),
        "nta_validated_count": len(nta_validated),
        "lei_count": sum(strong_id(entity, "LEI") is not None for entity in enriched),
        "semantic_identity_sha256": _semantic_identity_sha256(enriched),
        "sources": {key: dict(value) for key, value in sorted(source_metadata.items())},
    }
    return {
        "manifest": manifest,
        "entities": [entity.to_dict() for entity in enriched],
    }


def write_tse_identity_spine(payload: Mapping[str, object], local_path: str | Path, public_path: str | Path) -> None:
    local = Path(local_path)
    public = Path(public_path)
    if local.resolve() == public.resolve():
        raise ValueError("local and public outputs must differ")
    local.parent.mkdir(parents=True, exist_ok=True)
    public.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public.write_text(
        json.dumps(payload.get("manifest", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
