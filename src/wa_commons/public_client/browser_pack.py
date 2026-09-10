from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from wa_commons.evidence.cards import card_from_claim
from wa_commons.policy.evaluator import DECISION_PRIORITY
from wa_commons.public_client.source_rights import (
    PUBLIC_FIELDS_ALLOWED,
    PublicSourceRights,
    require_public_fields,
)
from wa_commons.public_client.topics import build_public_topic_states

PACK_VERSION = "wa-public-evidence-pack-v0.1"
RELEASE_STATES = {
    "READY_FOR_CAPABILITY_TEST",
    "BLOCK_SOURCE_RIGHTS",
    "BLOCK_PUBLIC_IDENTITY_RIGHTS",
    "BLOCK_IDENTITY_COVERAGE",
}


def _sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _canonical_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(graph))
    if "claims" in value:
        value["claims"] = sorted(value["claims"], key=lambda row: str(row.get("claim_id", "")))
    return value


def _bridge_maps(identity_bridge: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    number_to_local: dict[str, str] = {}
    local_to_number: dict[str, str] = {}
    for row in identity_bridge.get("links", []):
        if str(row.get("review_state", "")).upper() != "CONFIRMED":
            continue
        local_id = str(row.get("entity_id", "")).strip()
        number = str(row.get("corporate_number", "")).strip()
        if not local_id or not number:
            continue
        if number in number_to_local and number_to_local[number] != local_id:
            raise ValueError(f"corporate number maps to multiple bridge entities: {number}")
        if local_id in local_to_number and local_to_number[local_id] != number:
            raise ValueError(f"bridge entity maps to multiple corporate numbers: {local_id}")
        number_to_local[number] = local_id
        local_to_number[local_id] = number
    return number_to_local, local_to_number


def _coverage_by_local(coverage: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in coverage.get("matrix", {}).get("rows", []):
        local_id = str(row.get("entity_id", ""))
        source_id = str(row.get("source_id", ""))
        state = str(row.get("state", ""))
        if local_id and source_id:
            previous = result.setdefault(local_id, {}).get(source_id)
            if previous is not None and previous != state:
                raise ValueError(f"conflicting coverage state for {local_id}/{source_id}")
            result[local_id][source_id] = state
    return result


def _profile_rows(screening: Mapping[str, Any], profile_ids: Sequence[str]) -> list[dict[str, str]]:
    wanted = set(profile_ids)
    rows = [
        {"profile_id": str(row["profile_id"]), "profile_version": str(row["profile_version"]),
         "policy_sha256": str(row["policy_sha256"])}
        for row in screening.get("policies", []) if str(row.get("profile_id")) in wanted
    ]
    found = {row["profile_id"] for row in rows}
    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"configured profile(s) missing from screening: {missing}")
    return sorted(rows, key=lambda row: row["profile_id"])


def _views_by_key(screening: Mapping[str, Any]) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in screening.get("views", []):
        key = (str(row.get("entity_id", "")), str(row.get("profile_id", "")))
        if key in result:
            raise ValueError(f"duplicate screening view: {key}")
        result[key] = row
    return result


def _corporate_number_from_subject(subject_id: str, local_to_number: Mapping[str, str]) -> str | None:
    prefix = "jp:corporate-number:"
    if subject_id.startswith(prefix):
        return subject_id[len(prefix):].strip() or None
    return local_to_number.get(subject_id)


def _claims_by_number(
    graph: Mapping[str, Any], local_to_number: Mapping[str, str]
) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = {}
    for claim in graph.get("claims", []):
        subject_id = str(claim.get("subject", {}).get("entity_id", ""))
        number = _corporate_number_from_subject(subject_id, local_to_number)
        if number:
            result.setdefault(number, []).append(claim)
    for number in result:
        result[number] = sorted(result[number], key=lambda row: str(row.get("claim_id", "")))
    return result


def _public_claim_value(
    claim_payload: Mapping[str, Any],
    source_ids: Sequence[str],
    rights: Mapping[str, PublicSourceRights],
) -> dict[str, Any]:
    value = claim_payload.get("value")
    if not isinstance(value, Mapping):
        return {}

    predicate = str(claim_payload.get("predicate", ""))
    allowed_by_predicate = {
        "received_contract_from_japan_ministry_of_defense": {
            "contract_subject": "contract_subject",
        },
        "contract_subject_classification": {
            "classification": "contract_subject_classification",
            "contract_subject": "contract_subject",
        },
    }.get(predicate, {})

    if not source_ids:
        return {}
    common_allowed = set.intersection(
        *(set(rights[source_id].allowed_fields) for source_id in source_ids)
    )
    return {
        key: deepcopy(value[key])
        for key, rights_field in allowed_by_predicate.items()
        if key in value and rights_field in common_allowed
    }


def _public_claim(
    claim: Mapping[str, Any], rights: Mapping[str, PublicSourceRights]
) -> tuple[dict[str, Any] | None, list[str]]:
    raw_evidence = list(claim.get("evidence", []))
    source_ids = sorted({str(item.get("source_id", "")).strip() for item in raw_evidence if str(item.get("source_id", "")).strip()})
    blocked = [source_id for source_id in source_ids if source_id not in rights or rights[source_id].state != PUBLIC_FIELDS_ALLOWED]
    if blocked:
        return None, blocked
    if not source_ids:
        return None, ["SOURCE_RIGHTS_UNDECLARED"]

    claim_fields = {"claim_id", "narrow_claim", "category", "predicate", "adjudication_status", "confidence"}
    for source_id in source_ids:
        require_public_fields(source_id, claim_fields, rights)

    card = card_from_claim(dict(claim)).to_dict()
    public_sources: list[dict[str, Any]] = []
    for raw_source, source in zip(raw_evidence, card["sources"]):
        source_id = str(raw_source["source_id"])
        require_public_fields(
            source_id,
            {"source_id", "source_publisher", "source_url", "source_locator", "evidence_date", "retrieved_at"},
            rights,
        )
        public_sources.append({
            "source_id": source_id,
            "publisher": source.get("publisher"),
            "url": source.get("url"),
            "locator": source.get("locator"),
            "evidence_date": source.get("evidence_date"),
            "retrieved_at": source.get("retrieved_at"),
        })

    return {
        "claim_id": card["claim_id"],
        "narrow_claim": {
            "category": card["claim"]["category"],
            "predicate": card["claim"]["predicate"],
            "value": _public_claim_value(card["claim"], source_ids, rights),
        },
        "adjudication": {
            "status": card["adjudication"]["status"],
            "confidence": card["adjudication"].get("confidence"),
        },
        "entity_resolution_state": card["entity_resolution"].get("review_status"),
        "sources": sorted(public_sources, key=lambda row: (row["source_id"], str(row.get("locator") or ""))),
        "challenge_url": card["challenge_path"]["url"],
    }, []


def _public_policy_view(
    view: Mapping[str, Any], public_claim_ids: set[str]
) -> dict[str, Any]:
    claim_results = [
        {"claim_id": str(item.get("claim_id", "")), "decision": str(item.get("decision", "NONE"))}
        for item in sorted(view.get("claim_results", []), key=lambda item: str(item.get("claim_id", "")))
        if str(item.get("claim_id", "")) in public_claim_ids
    ]
    decision = "NONE"
    for item in claim_results:
        proposed = item["decision"]
        if proposed not in DECISION_PRIORITY:
            raise ValueError(f"unsupported public policy decision: {proposed}")
        if DECISION_PRIORITY[proposed] > DECISION_PRIORITY[decision]:
            decision = proposed

    if not claim_results:
        reasoning = (
            "No rights-cleared public claim contributes to this profile; "
            "NONE is not PASS, clean, or safe."
        )
    elif decision == "NONE":
        reasoning = (
            "All rights-cleared public claim results produced NONE. "
            "NONE is not PASS, clean, or safe."
        )
    else:
        decisive = ", ".join(
            item["claim_id"] for item in claim_results if item["decision"] == decision
        )
        reasoning = (
            f"Public decision {decision} is the highest-priority rights-cleared "
            f"claim result; decisive claim(s): {decisive}."
        )
    return {
        "profile_id": str(view["profile_id"]),
        "profile_version": str(view["profile_version"]),
        "policy_sha256": str(view["policy_sha256"]),
        "decision": decision,
        "claim_results": claim_results,
        "reasoning": reasoning,
    }


def _company_topics(
    coverage_states: Mapping[str, str], global_topics: Mapping[str, Mapping[str, str]]
) -> tuple[dict[str, dict[str, str]], bool]:
    topics: dict[str, dict[str, str]] = {}
    missing_coverage = False
    for topic_id, topic in global_topics.items():
        source_id = str(topic["source_id"])
        if topic["state"] != "AVAILABLE":
            topics[topic_id] = dict(topic)
            continue
        state = coverage_states.get(source_id)
        if state is None:
            topics[topic_id] = {"state": "UNKNOWN", "reason": "COVERAGE_ROW_MISSING", "source_id": source_id}
            missing_coverage = True
        else:
            topics[topic_id] = {"state": state.upper(), "reason": "COVERAGE_MATRIX", "source_id": source_id}
    return topics, missing_coverage


def _rights_hash(rights: Mapping[str, PublicSourceRights]) -> str:
    rows = []
    for source_id, item in sorted(rights.items()):
        rows.append({
            "source_id": source_id, "state": item.state, "terms_url": item.terms_url,
            "checked_at": item.checked_at, "allowed_fields": sorted(item.allowed_fields),
            "attribution_required": item.attribution_required, "raw_rows_public": item.raw_rows_public,
            "note": item.note,
        })
    return _sha256(rows)


def _semantic_payload(pack: Mapping[str, Any]) -> dict[str, Any]:
    manifest = pack["manifest"]
    keys = (
        "pack_version", "code_commit", "identity_semantic_sha256",
        "evidence_semantic_sha256", "coverage_semantic_sha256",
        "screening_semantic_sha256", "source_rights_sha256", "profile_hashes",
        "release_state", "company_count", "evidence_count",
    )
    return {
        "manifest": {key: deepcopy(manifest[key]) for key in keys},
        "topics": deepcopy(pack["topics"]),
        "companies": deepcopy(pack["companies"]),
    }


def build_public_browser_pack(
    *, public_identity: Mapping[str, Any], coverage: Mapping[str, Any],
    screening: Mapping[str, Any], evidence_graph: Mapping[str, Any],
    identity_bridge: Mapping[str, Any], source_rights: Mapping[str, PublicSourceRights],
    profile_ids: Sequence[str], generated_at: str, code_commit: str,
) -> dict[str, Any]:
    number_to_local, local_to_number = _bridge_maps(identity_bridge)
    coverage_by_local = _coverage_by_local(coverage)
    views_by_key = _views_by_key(screening)
    claims_by_number = _claims_by_number(evidence_graph, local_to_number)
    profile_rows = _profile_rows(screening, profile_ids)
    global_topics = build_public_topic_states(source_rights)

    identity_hash = str(public_identity.get("manifest", {}).get("public_projection_semantic_sha256", ""))
    identity_rights_block = not bool(identity_hash)
    coverage_block = False
    blocked_sources: set[str] = set()
    companies: list[dict[str, Any]] = []

    for source in source_rights.values():
        if source.state == PUBLIC_FIELDS_ALLOWED and source.raw_rows_public:
            raise ValueError(f"raw public source rows are forbidden in browser pack: {source.source_id}")
    for company in public_identity.get("companies", []):
        number = str(company.get("corporate_number", "")).strip()
        local_id = number_to_local.get(number)
        if local_id is None:
            raise ValueError(f"public identity has no confirmed bridge mapping: {number}")
        coverage_states = coverage_by_local.get(local_id, {})
        topics, missing = _company_topics(coverage_states, global_topics)
        coverage_block = coverage_block or missing

        evidence_rows: list[dict[str, Any]] = []
        for claim in claims_by_number.get(number, []):
            public_claim, blocked = _public_claim(claim, source_rights)
            blocked_sources.update(blocked)
            if public_claim is not None:
                evidence_rows.append(public_claim)
        public_claim_ids = {str(row["claim_id"]) for row in evidence_rows}

        policy_views = []
        for profile in profile_rows:
            key = (local_id, profile["profile_id"])
            view = views_by_key.get(key)
            if view is None:
                raise ValueError(f"screening view missing for public identity/profile: {number}/{profile['profile_id']}")
            policy_views.append(_public_policy_view(view, public_claim_ids))
        companies.append({
            "entity_id": str(company.get("entity_id", "")),
            "corporate_number": number,
            "canonical_name": str(company.get("canonical_name", "")),
            "security_code": str(company.get("security_code", "")),
            "edinet_code": str(company.get("edinet_code", "")),
            "identity_state": str(company.get("identity_state", "")),
            "aliases": sorted({str(alias) for alias in company.get("aliases", []) if str(alias).strip()}),
            "topics": topics,
            "policy_views": sorted(policy_views, key=lambda row: row["profile_id"]),
            "evidence": sorted(evidence_rows, key=lambda row: row["claim_id"]),
        })

    companies.sort(key=lambda row: (row["canonical_name"], row["corporate_number"]))
    if blocked_sources:
        release_state = "BLOCK_SOURCE_RIGHTS"
    elif identity_rights_block:
        release_state = "BLOCK_PUBLIC_IDENTITY_RIGHTS"
    elif coverage_block:
        release_state = "BLOCK_IDENTITY_COVERAGE"
    else:
        release_state = "READY_FOR_CAPABILITY_TEST"
    manifest = {
        "pack_version": PACK_VERSION,
        "generated_at": generated_at,
        "code_commit": code_commit,
        "identity_semantic_sha256": identity_hash,
        "evidence_semantic_sha256": _sha256(_canonical_graph(evidence_graph)),
        "coverage_semantic_sha256": str(coverage.get("matrix_sha256", _sha256(coverage))),
        "screening_semantic_sha256": str(screening.get("screening_sha256", _sha256(screening))),
        "source_rights_sha256": _rights_hash(source_rights),
        "profile_hashes": {row["profile_id"]: row["policy_sha256"] for row in profile_rows},
        "release_state": release_state,
        "company_count": len(companies),
        "evidence_count": sum(len(row["evidence"]) for row in companies),
    }
    pack = {"manifest": manifest, "topics": global_topics, "companies": companies}
    manifest["pack_semantic_sha256"] = _sha256(_semantic_payload(pack))
    validate_public_browser_pack(pack)
    return pack


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    elif isinstance(value, str):
        yield value


def validate_public_browser_pack(pack: Mapping[str, Any]) -> None:
    manifest = pack.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("browser pack manifest is required")
    state = str(manifest.get("release_state", ""))
    if state not in RELEASE_STATES:
        raise ValueError(f"unsupported browser pack release_state: {state}")
    companies = pack.get("companies")
    if not isinstance(companies, list):
        raise ValueError("browser pack companies must be a list")
    expected_order = sorted(companies, key=lambda row: (str(row.get("canonical_name", "")), str(row.get("corporate_number", ""))))
    if companies != expected_order:
        raise ValueError("browser pack companies are not canonical-order sorted")
    if int(manifest.get("company_count", -1)) != len(companies):
        raise ValueError("browser pack company_count mismatch")
    if int(manifest.get("evidence_count", -1)) != sum(len(row.get("evidence", [])) for row in companies):
        raise ValueError("browser pack evidence_count mismatch")
    for company in companies:
        public_claim_ids = {
            str(row.get("claim_id", ""))
            for row in company.get("evidence", [])
            if str(row.get("claim_id", ""))
        }
        for view in company.get("policy_views", []):
            for result in view.get("claim_results", []):
                claim_id = str(result.get("claim_id", ""))
                if claim_id not in public_claim_ids:
                    raise ValueError(
                        f"policy claim is not present in public evidence: {claim_id}"
                    )
    forbidden = {"raw_document_text", "JPX_SECURITY_CODE"}
    for token in _walk(pack):
        if token in forbidden:
            raise ValueError(f"forbidden public field: {token}")
        if isinstance(token, str) and "wa:org:jp:tse:" in token:
            raise ValueError("local TSE entity identifiers must not enter public pack")
    expected_hash = _sha256(_semantic_payload(pack))
    if str(manifest.get("pack_semantic_sha256", "")) != expected_hash:
        raise ValueError("browser pack semantic hash mismatch")


def write_public_browser_pack(pack: Mapping[str, Any], output: Path) -> None:
    validate_public_browser_pack(pack)
    Path(output).write_text(json.dumps(pack, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
