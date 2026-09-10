from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

PUBLIC_FIELDS_ALLOWED = "PUBLIC_FIELDS_ALLOWED"
BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED = "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"
BLOCK_PUBLIC_REDISTRIBUTION_REVIEW = "BLOCK_PUBLIC_REDISTRIBUTION_REVIEW"
ALLOWED_STATES = frozenset({
    PUBLIC_FIELDS_ALLOWED,
    BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED,
    BLOCK_PUBLIC_REDISTRIBUTION_REVIEW,
})


@dataclass(frozen=True)
class PublicSourceRights:
    source_id: str
    state: str
    terms_url: str
    checked_at: str
    allowed_fields: frozenset[str]
    attribution_required: bool
    raw_rows_public: bool
    note: str


def load_public_source_rights(path: Path) -> dict[str, PublicSourceRights]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = raw.get("sources") if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("public source-rights contract must contain a sources list")

    result: dict[str, PublicSourceRights] = {}
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("public source-rights entries must be objects")
        source_id = str(item.get("source_id", "")).strip()
        state = str(item.get("state", "")).strip()
        terms_url = str(item.get("terms_url", "")).strip()
        checked_at = str(item.get("checked_at", "")).strip()
        note = str(item.get("note", "")).strip()
        fields = item.get("allowed_fields", [])
        if not source_id:
            raise ValueError("source_id is required")
        if source_id in result:
            raise ValueError(f"duplicate source_id: {source_id}")
        if state not in ALLOWED_STATES:
            raise ValueError(f"unsupported public source-rights state: {state}")
        if not terms_url.startswith(("https://", "http://")):
            raise ValueError(f"terms_url is required for {source_id}")
        if not checked_at:
            raise ValueError(f"checked_at is required for {source_id}")
        if not isinstance(fields, list) or any(not str(field).strip() for field in fields):
            raise ValueError(f"allowed_fields must be a list of non-empty strings for {source_id}")
        allowed_fields = frozenset(str(field).strip() for field in fields)
        raw_rows_public = bool(item.get("raw_rows_public", False))
        if state != PUBLIC_FIELDS_ALLOWED and allowed_fields:
            raise ValueError(f"blocked source cannot allow public fields: {source_id}")
        if state != PUBLIC_FIELDS_ALLOWED and raw_rows_public:
            raise ValueError(f"blocked source cannot publish raw rows: {source_id}")
        result[source_id] = PublicSourceRights(
            source_id=source_id,
            state=state,
            terms_url=terms_url,
            checked_at=checked_at,
            allowed_fields=allowed_fields,
            attribution_required=bool(item.get("attribution_required", False)),
            raw_rows_public=raw_rows_public,
            note=note,
        )
    return result


def require_public_fields(
    source_id: str,
    fields: set[str],
    rights: Mapping[str, PublicSourceRights],
) -> None:
    entry = rights.get(source_id)
    if entry is None:
        raise ValueError(f"unknown source is not cleared for public client: {source_id}")
    if entry.state != PUBLIC_FIELDS_ALLOWED:
        raise ValueError(f"{source_id}: {entry.state}")
    requested = {str(field).strip() for field in fields}
    uncleared = sorted(requested - entry.allowed_fields)
    if uncleared:
        raise ValueError(
            f"{source_id} field(s) not cleared for public client: {', '.join(uncleared)}"
        )
