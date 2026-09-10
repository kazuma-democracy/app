from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from wa_commons.identity.enrich import normalize_edinet_security_code
from wa_commons.public_client.source_rights import PublicSourceRights, require_public_fields

IDENTITY_POLICY_VERSION = "wa-conservative-v0.2"


def _sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _first(row: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _corporate_numbers(entity: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("value", "")).strip()
        for item in entity.get("identifiers", [])
        if str(item.get("scheme", "")) == "JP_CORPORATE_NUMBER"
        and str(item.get("value", "")).strip()
    }

def _group_by_corporate_number(
    rows: Sequence[Mapping[str, Any]], *keys: str
) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        number = _first(row, *keys)
        if number:
            grouped.setdefault(number, []).append(row)
    return grouped


def _rights_payload(rights: Mapping[str, PublicSourceRights]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": item.source_id,
            "state": item.state,
            "terms_url": item.terms_url,
            "checked_at": item.checked_at,
            "allowed_fields": sorted(item.allowed_fields),
            "attribution_required": item.attribution_required,
            "raw_rows_public": item.raw_rows_public,
            "note": item.note,
        }
        for _, item in sorted(rights.items())
    ]


def _opaque_ref(entity: Mapping[str, Any]) -> str:
    return _sha256({
        "entity_id": str(entity.get("entity_id", "")),
        "review_state": str(entity.get("review_state", "")),
    })


def build_public_company_identity(
    *,
    canonical_identity: Mapping[str, Any],
    edinet_rows: Sequence[Mapping[str, Any]],
    nta_rows: Sequence[Mapping[str, Any]],
    rights: Mapping[str, PublicSourceRights],
    code_commit: str,
) -> dict[str, Any]:
    require_public_fields(
        "jp-nta-corporate-number", {"corporate_number", "legal_name"}, rights
    )
    require_public_fields(
        "jp-edinet",
        {"corporate_number", "edinet_code", "security_code"},
        rights,
    )
    nta_by_number = _group_by_corporate_number(
        nta_rows, "法人番号", "corporateNumber", "corporate_number"
    )
    edinet_by_number = _group_by_corporate_number(
        edinet_rows, "提出者法人番号", "法人番号", "Corporate Number", "corporate_number"
    )

    companies: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for entity in canonical_identity.get("entities", []):
        review_state = str(entity.get("review_state", "")).upper()
        numbers = _corporate_numbers(entity)
        if review_state != "CONFIRMED" or len(numbers) != 1:
            unresolved.append({
                "opaque_ref": _opaque_ref(entity),
                "reason": "missing_strong_corporate_number" if not numbers else "ambiguous_canonical_identity",
            })
            continue

        number = next(iter(numbers))
        nta_matches = nta_by_number.get(number, [])
        edinet_matches = edinet_by_number.get(number, [])
        if len(nta_matches) != 1:
            unresolved.append({"opaque_ref": _opaque_ref(entity), "reason": "missing_or_ambiguous_nta_identity"})
            continue
        if len(edinet_matches) != 1:
            unresolved.append({"opaque_ref": _opaque_ref(entity), "reason": "ambiguous_edinet_identity" if edinet_matches else "missing_edinet_identity"})
            continue
        nta = nta_matches[0]
        edinet = edinet_matches[0]
        legal_name = _first(nta, "商号又は名称", "name", "corporate_name")
        edinet_code = _first(edinet, "ＥＤＩＮＥＴコード", "EDINETコード", "EDINET Code", "edinet_code")
        raw_security = _first(edinet, "証券コード", "Security Code", "security_code")
        if not legal_name or not edinet_code or not raw_security:
            unresolved.append({"opaque_ref": _opaque_ref(entity), "reason": "incomplete_public_identity_fields"})
            continue

        companies.append({
            "entity_id": f"jp:corporate-number:{number}",
            "corporate_number": number,
            "canonical_name": legal_name,
            "security_code": normalize_edinet_security_code(raw_security),
            "edinet_code": edinet_code,
            "identity_state": "CONFIRMED",
            "display_name_source": "jp-nta-corporate-number",
            "security_code_source": "jp-edinet",
        })

    companies.sort(key=lambda row: (row["canonical_name"], row["corporate_number"]))
    unresolved.sort(key=lambda row: (row["reason"], row["opaque_ref"]))
    semantic_payload = {"companies": companies, "unresolved": unresolved}
    manifest = {
        "identity_policy_version": IDENTITY_POLICY_VERSION,
        "code_commit": code_commit,
        "canonical_identity_semantic_sha256": str(
            canonical_identity.get("manifest", {}).get("semantic_identity_sha256", "")
        ),
        "edinet_rows_sha256": _sha256(list(edinet_rows)),
        "nta_rows_sha256": _sha256(list(nta_rows)),
        "rights_contract_sha256": _sha256(_rights_payload(rights)),
        "resolved_public_company_count": len(companies),
        "unresolved_count": len(unresolved),
        "public_projection_semantic_sha256": _sha256(semantic_payload),
    }
    return {
        "manifest": manifest,
        "companies": companies,
        "unresolved": unresolved,
    }
