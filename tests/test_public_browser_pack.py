from __future__ import annotations

import copy
import json

import pytest

from wa_commons.public_client.browser_pack import (
    build_public_browser_pack,
    validate_public_browser_pack,
)
from wa_commons.public_client.source_rights import PublicSourceRights


def rights_fixture() -> dict[str, PublicSourceRights]:
    mod_fields = frozenset({
        "source_id", "source_publisher", "source_url", "source_locator",
        "claim_id", "narrow_claim", "category", "predicate",
        "adjudication_status", "confidence", "evidence_date", "retrieved_at",
        "contract_subject", "contract_subject_classification",
    })
    return {
        "jp-mod-procurement": PublicSourceRights(
            "jp-mod-procurement", "PUBLIC_FIELDS_ALLOWED", "https://example.test/mod",
            "2026-09-11", mod_fields, True, False, "test",
        ),
        "ohchr-settlements-business": PublicSourceRights(
            "ohchr-settlements-business", "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED",
            "https://example.test/un", "2026-09-11", frozenset(), False, False, "blocked",
        ),
    }


def public_identity_fixture(order: str = "forward") -> dict:
    companies = [
        {"entity_id": "jp:corporate-number:1111111111111", "corporate_number": "1111111111111",
         "canonical_name": "合成株式会社", "security_code": "1001", "edinet_code": "E00001",
         "identity_state": "CONFIRMED", "display_name_source": "jp-nta-corporate-number",
         "security_code_source": "jp-edinet"},
        {"entity_id": "jp:corporate-number:2222222222222", "corporate_number": "2222222222222",
         "canonical_name": "合成電機株式会社", "security_code": "2002", "edinet_code": "E00002",
         "identity_state": "CONFIRMED", "display_name_source": "jp-nta-corporate-number",
         "security_code_source": "jp-edinet"},
    ]
    if order == "reverse":
        companies.reverse()
    return {"manifest": {"public_projection_semantic_sha256": "a" * 64}, "companies": companies}


def bridge_fixture() -> dict:
    return {"links": [
        {"entity_id": "wa:org:jp:tse:1001", "corporate_number": "1111111111111", "review_state": "CONFIRMED"},
        {"entity_id": "wa:org:jp:tse:2002", "corporate_number": "2222222222222", "review_state": "CONFIRMED"},
    ]}


def coverage_fixture(order: str = "forward") -> dict:
    rows = [
        {"entity_id": "wa:org:jp:tse:1001", "source_id": "jp-mod-procurement", "state": "observed", "observation_count": 1},
        {"entity_id": "wa:org:jp:tse:2002", "source_id": "jp-mod-procurement", "state": "no_match", "observation_count": 0},
    ]
    if order == "reverse":
        rows.reverse()
    return {"matrix_sha256": "b" * 64, "matrix": {"entity_count": 2, "rows": rows}}


def screening_fixture(order: str = "forward") -> dict:
    views = [
        {"entity_id": "wa:org:jp:tse:1001", "profile_id": "public:strict-military-specific:v1",
         "profile_version": "1", "policy_sha256": "c" * 64, "decision": "EXCLUDE",
         "claim_results": [{"claim_id": "claim-mod-1", "decision": "EXCLUDE", "source_ids": ["jp-mod-procurement"]}],
         "coverage_states": {"jp-mod-procurement": "observed"}, "reasoning": "matched"},
        {"entity_id": "wa:org:jp:tse:2002", "profile_id": "public:strict-military-specific:v1",
         "profile_version": "1", "policy_sha256": "c" * 64, "decision": "NONE",
         "claim_results": [], "coverage_states": {"jp-mod-procurement": "no_match"},
         "reasoning": "NONE is not PASS, clean, or safe."},
    ]
    if order == "reverse":
        views.reverse()
    return {"screening_sha256": "d" * 64, "policies": [{"profile_id": "public:strict-military-specific:v1", "profile_version": "1", "policy_sha256": "c" * 64}], "views": views}


def mod_claim() -> dict:
    return {
        "schema_version": "0.1", "claim_id": "claim-mod-1",
        "subject": {"entity_id": "jp:corporate-number:1111111111111", "entity_type": "company",
                    "canonical_name": "合成株式会社", "jurisdiction": "JP", "identifiers": [],
                    "entity_resolution": {"method": "deterministic_identifier", "confidence": 1.0,
                                          "review_status": "confirmed", "match_evidence": ["corporate number"]}},
        "claim": {"category": "military_contract", "predicate": "contract_subject_classification",
                  "value": {"classification": "military_specific"}, "effective_from": "2026-04-01", "effective_to": None},
        "evidence": [{"source_id": "jp-mod-procurement", "source_url": "https://example.test/mod/1",
                     "publisher": "Japan Ministry of Defense", "source_type": "official_contract",
                     "evidence_date": "2026-04-01", "retrieved_at": "2026-09-01T00:00:00Z",
                     "support": "supports", "locator": "record-1"}],
        "adjudication": {"status": "confirmed", "confidence": 0.99,
                         "reasoning_summary": "Synthetic confirmed narrow claim."},
        "correction_history": [],
    }


def mod_contract_fact_claim() -> dict:
    claim = copy.deepcopy(mod_claim())
    claim["claim_id"] = "claim-mod-contract-fact"
    claim["claim"]["predicate"] = "received_contract_from_japan_ministry_of_defense"
    claim["claim"]["value"] = {
        "contracting_authority": "Japan Ministry of Defense",
        "contract_subject": "synthetic subject",
        "contract_amount_jpy": 123456789,
        "supplier_name_as_published": "synthetic supplier",
        "corporate_number": "1111111111111",
    }
    return claim


def blocked_ohchr_claim() -> dict:
    claim = copy.deepcopy(mod_claim())
    claim["claim_id"] = "claim-ohchr-blocked"
    claim["subject"]["canonical_name"] = "synthetic-blocked-company"
    claim["claim"] = {"category": "human_rights", "predicate": "ohchr_settlement_related_activity",
                      "value": {"activity": "synthetic"}, "effective_from": "2026-01-01", "effective_to": None}
    claim["evidence"] = [{"source_id": "ohchr-settlements-business", "source_url": "https://example.test/un/1",
                         "publisher": "OHCHR", "source_type": "official_database", "evidence_date": "2026-01-01",
                         "retrieved_at": "2026-09-01T00:00:00Z", "support": "supports", "locator": "row-1"}]
    return claim


def build_fixture(*, order: str = "forward", include_blocked: bool = False) -> dict:
    claims = [mod_claim()]
    if include_blocked:
        claims.append(blocked_ohchr_claim())
    screening = screening_fixture(order)
    if include_blocked:
        target = next(
            view for view in screening["views"]
            if view["entity_id"] == "wa:org:jp:tse:1001"
        )
        target["claim_results"].append({
            "claim_id": "claim-ohchr-blocked",
            "decision": "EXCLUDE",
            "source_ids": ["ohchr-settlements-business"],
        })
    if order == "reverse":
        claims.reverse()
    return build_public_browser_pack(
        public_identity=public_identity_fixture(order),
        coverage=coverage_fixture(order),
        screening=screening,
        evidence_graph={"reproduction_version": "synthetic-v1", "claims": claims},
        identity_bridge=bridge_fixture(),
        source_rights=rights_fixture(),
        profile_ids=["public:strict-military-specific:v1"],
        generated_at="2026-09-11T00:00:00Z",
        code_commit="abc123",
    )


def test_pack_is_order_independent_and_has_no_local_only_fields():
    first = build_fixture(order="forward")
    second = build_fixture(order="reverse")
    assert first["manifest"]["pack_semantic_sha256"] == second["manifest"]["pack_semantic_sha256"]
    assert first["companies"] == second["companies"]
    text = json.dumps(first, ensure_ascii=False)
    assert "raw_document_text" not in text
    assert "JPX_SECURITY_CODE" not in text
    assert "wa:org:jp:tse:" not in text
    assert first["manifest"]["release_state"] == "READY_FOR_CAPABILITY_TEST"
    validate_public_browser_pack(first)


def test_public_mod_contract_fact_minimizes_nested_value_fields():
    pack = build_public_browser_pack(
        public_identity=public_identity_fixture(),
        coverage=coverage_fixture(),
        screening=screening_fixture(),
        evidence_graph={"claims": [mod_claim(), mod_contract_fact_claim()]},
        identity_bridge=bridge_fixture(),
        source_rights=rights_fixture(),
        profile_ids=["public:strict-military-specific:v1"],
        generated_at="2026-09-11T00:00:00Z",
        code_commit="abc123",
    )
    company = next(row for row in pack["companies"] if row["corporate_number"] == "1111111111111")
    fact = next(row for row in company["evidence"] if row["claim_id"] == "claim-mod-contract-fact")
    assert fact["narrow_claim"]["value"] == {"contract_subject": "synthetic subject"}


def test_public_mod_nested_value_fails_closed_without_explicit_field_right():
    rights = rights_fixture()
    current = rights["jp-mod-procurement"]
    rights["jp-mod-procurement"] = PublicSourceRights(
        current.source_id,
        current.state,
        current.terms_url,
        current.checked_at,
        frozenset(field for field in current.allowed_fields if field != "contract_subject"),
        current.attribution_required,
        current.raw_rows_public,
        current.note,
    )
    pack = build_public_browser_pack(
        public_identity=public_identity_fixture(),
        coverage=coverage_fixture(),
        screening=screening_fixture(),
        evidence_graph={"claims": [mod_contract_fact_claim()]},
        identity_bridge=bridge_fixture(),
        source_rights=rights,
        profile_ids=["public:strict-military-specific:v1"],
        generated_at="2026-09-11T00:00:00Z",
        code_commit="abc123",
    )
    company = next(row for row in pack["companies"] if row["corporate_number"] == "1111111111111")
    fact = next(row for row in company["evidence"] if row["claim_id"] == "claim-mod-contract-fact")
    assert fact["narrow_claim"]["value"] == {}


def test_blocked_ohchr_source_is_not_serialized():
    pack = build_fixture(include_blocked=True)
    assert pack["manifest"]["release_state"] == "BLOCK_SOURCE_RIGHTS"
    assert pack["topics"]["ohchr_settlement_related"]["state"] == "NOT_INTEGRATED"
    assert "synthetic-blocked-company" not in json.dumps(pack, ensure_ascii=False)
    assert "claim-ohchr-blocked" not in json.dumps(pack, ensure_ascii=False)


def test_blocked_claim_cannot_leave_a_public_policy_decision():
    screening = screening_fixture()
    target = next(
        view for view in screening["views"]
        if view["entity_id"] == "wa:org:jp:tse:1001"
    )
    target["claim_results"][0]["decision"] = "NONE"
    target["decision"] = "EXCLUDE"
    target["claim_results"].append({
        "claim_id": "claim-ohchr-blocked",
        "decision": "EXCLUDE",
        "source_ids": ["ohchr-settlements-business"],
    })
    pack = build_public_browser_pack(
        public_identity=public_identity_fixture(),
        coverage=coverage_fixture(),
        screening=screening,
        evidence_graph={"claims": [mod_claim(), blocked_ohchr_claim()]},
        identity_bridge=bridge_fixture(),
        source_rights=rights_fixture(),
        profile_ids=["public:strict-military-specific:v1"],
        generated_at="2026-09-11T00:00:00Z",
        code_commit="abc123",
    )
    company = next(row for row in pack["companies"] if row["corporate_number"] == "1111111111111")
    view = company["policy_views"][0]
    assert view["claim_results"] == [{"claim_id": "claim-mod-1", "decision": "NONE"}]
    assert view["decision"] == "NONE"
    assert "claim-ohchr-blocked" not in view["reasoning"]


def test_bridge_is_build_time_only_and_zero_claim_company_is_preserved():
    pack = build_fixture()
    by_number = {row["corporate_number"]: row for row in pack["companies"]}
    assert set(by_number) == {"1111111111111", "2222222222222"}
    assert by_number["2222222222222"]["policy_views"][0]["decision"] == "NONE"
    assert by_number["2222222222222"]["topics"]["military_defence"]["state"] == "NO_MATCH"
    text = json.dumps(pack, ensure_ascii=False)
    assert "identity_bridge" not in text
    assert "wa:org:jp:tse:" not in text


def test_validator_rejects_policy_reference_to_nonpublic_claim():
    pack = build_fixture()
    company = next(row for row in pack["companies"] if row["corporate_number"] == "1111111111111")
    company["policy_views"][0]["claim_results"].append(
        {"claim_id": "not-in-public-evidence", "decision": "EXCLUDE"}
    )
    with pytest.raises(ValueError, match="policy claim is not present in public evidence"):
        validate_public_browser_pack(pack)


def test_missing_confirmed_bridge_for_public_company_fails_closed():
    bridge = bridge_fixture()
    bridge["links"] = bridge["links"][:1]
    with pytest.raises(ValueError, match="public identity.*bridge"):
        build_public_browser_pack(
            public_identity=public_identity_fixture(), coverage=coverage_fixture(),
            screening=screening_fixture(), evidence_graph={"claims": [mod_claim()]},
            identity_bridge=bridge, source_rights=rights_fixture(),
            profile_ids=["public:strict-military-specific:v1"],
            generated_at="2026-09-11T00:00:00Z", code_commit="abc123",
        )
