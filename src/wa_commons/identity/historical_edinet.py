from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from wa_commons.identity.enrich import normalize_edinet_security_code
from wa_commons.identity.jpx import entity_id_from_tse_code
from wa_commons.identity.models import EntityRecord, Identifier, SourceRef
from wa_commons.identity.tse_spine import build_tse_identity_spine


def _submitted_at(value: object) -> datetime:
    text = str(value or "").strip().replace(" ", "T")
    if not text:
        raise ValueError("EDINET submitDateTime is required")
    try:
        submitted = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("invalid EDINET submitDateTime") from exc
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone(timedelta(hours=9)))
    return submitted


def normalize_edinet_document_rows(
    records: Sequence[Mapping[str, Any]],
    *,
    decision_cutoff: str,
) -> list[dict[str, str]]:
    cutoff = datetime.fromisoformat(decision_cutoff)
    if cutoff.tzinfo is None:
        raise ValueError("decision_cutoff must be timezone-aware")
    candidates: dict[str, list[dict[str, str]]] = {}
    for record in records:
        if _submitted_at(record.get("submitDateTime")) > cutoff:
            continue
        raw_code = str(record.get("secCode", "")).strip()
        normalized_code = normalize_edinet_security_code(raw_code)
        if not normalized_code:
            continue
        candidates.setdefault(normalized_code, []).append(
            {
                "security_code": raw_code,
                "edinet_code": str(record.get("edinetCode", "")).strip(),
                "corporate_number": str(record.get("JCN", "")).strip(),
            }
        )
    output: list[dict[str, str]] = []
    for normalized_code in sorted(candidates):
        rows = candidates[normalized_code]
        corporate_numbers = sorted(
            {row["corporate_number"] for row in rows if row["corporate_number"]}
        )
        edinet_codes = sorted({row["edinet_code"] for row in rows if row["edinet_code"]})
        if len(corporate_numbers) > 1:
            raise ValueError("conflicting historical corporate number")
        if len(edinet_codes) > 1:
            raise ValueError("conflicting historical EDINET code")
        output.append(
            {
                "security_code": sorted(row["security_code"] for row in rows)[0],
                "edinet_code": edinet_codes[0] if edinet_codes else "",
                "corporate_number": corporate_numbers[0] if corporate_numbers else "",
            }
        )
    return output


def _holdings_source(control_snapshot: Mapping[str, Any], code: str) -> SourceRef:
    manifest = control_snapshot.get("manifest", {})
    return SourceRef(
        source="blackrock-ishares-1475-holdings",
        source_key=code,
        snapshot=str(manifest.get("as_of_date", "")),
        url=str(manifest.get("source_locator", "")),
        retrieved_at=str(manifest.get("retrieved_at", "")),
        adapter_version="0.1",
    )


def _proxy_universe(control_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    if control_snapshot.get("status") != "INVESTABLE_CONTROL_SNAPSHOT_OK":
        raise ValueError("investable control snapshot must be valid")
    manifest = control_snapshot.get("manifest", {})
    entities: list[dict[str, Any]] = []
    for row in control_snapshot.get("rows", []):
        code = str(row.get("security_code", "")).strip().upper()
        source = _holdings_source(control_snapshot, code)
        entity = EntityRecord(
            entity_id=entity_id_from_tse_code(code),
            canonical_name=str(row.get("name", "")).strip(),
            identifiers=[Identifier("JPX_SECURITY_CODE", code, source)],
            review_state="CONFIRMED",
        )
        entities.append(entity.to_dict())
    entities.sort(key=lambda item: str(item["entity_id"]))
    return {
        "manifest": {
            "snapshot": manifest.get("as_of_date"),
            "source_sha256": manifest.get("source_sha256"),
            "semantic_payload_sha256": manifest.get("semantic_snapshot_sha256"),
            "entity_count": len(entities),
        },
        "entities": entities,
    }


def _source_metadata(source: SourceRef) -> dict[str, str]:
    return {
        "source": source.source,
        "source_key": source.source_key,
        "snapshot": source.snapshot,
        "url": source.url,
        "retrieved_at": source.retrieved_at,
        "adapter_version": source.adapter_version,
    }


def build_historical_proxy_identity(
    control_snapshot: Mapping[str, Any],
    edinet_records: Sequence[Mapping[str, Any]],
    *,
    decision_cutoff: str,
    edinet_source: SourceRef,
    code_commit: str,
) -> dict[str, Any]:
    universe = _proxy_universe(control_snapshot)
    rows = normalize_edinet_document_rows(
        edinet_records,
        decision_cutoff=decision_cutoff,
    )
    holdings_meta = control_snapshot.get("manifest", {})
    result = build_tse_identity_spine(
        universe,
        edinet_rows=rows,
        edinet_source=edinet_source,
        code_commit=code_commit,
        source_metadata={
            "edinet": _source_metadata(edinet_source),
            "holdings": {
                "source": "blackrock-ishares-1475-holdings",
                "snapshot": str(holdings_meta.get("as_of_date", "")),
                "url": str(holdings_meta.get("source_locator", "")),
                "retrieved_at": str(holdings_meta.get("retrieved_at", "")),
                "source_sha256": str(holdings_meta.get("source_sha256", "")),
            },
        },
    )
    result["manifest"]["decision_cutoff"] = decision_cutoff
    result["manifest"]["availability_complete"] = True
    return result

