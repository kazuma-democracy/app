import json

from wa_commons.public_client.identity_projection import build_public_company_identity
from wa_commons.public_client.source_rights import PublicSourceRights


def allowed_rights_fixture():
    return {
        "jp-nta-corporate-number": PublicSourceRights(
            source_id="jp-nta-corporate-number",
            state="PUBLIC_FIELDS_ALLOWED",
            terms_url="https://example.invalid/nta",
            checked_at="2026-09-11",
            allowed_fields=frozenset({"corporate_number", "legal_name", "source_url", "source_snapshot"}),
            attribution_required=True,
            raw_rows_public=False,
            note="synthetic",
        ),
        "jp-edinet": PublicSourceRights(
            source_id="jp-edinet",
            state="PUBLIC_FIELDS_ALLOWED",
            terms_url="https://example.invalid/edinet",
            checked_at="2026-09-11",
            allowed_fields=frozenset({"edinet_code", "security_code", "filer_name", "corporate_number", "source_url", "source_snapshot"}),
            attribution_required=True,
            raw_rows_public=False,
            note="synthetic",
        ),
    }

def test_projection_uses_only_cleared_display_sources():
    canonical = {
        "manifest": {"semantic_identity_sha256": "a" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1001",
            "review_state": "CONFIRMED",
            "identifiers": [
                {"scheme": "JP_CORPORATE_NUMBER", "value": "1234567890123"}
            ],
        }],
    }
    edinet = [{
        "EDINETコード": "E00001",
        "証券コード": "10010",
        "提出者法人番号": "1234567890123",
        "提出者名": "合成株式会社",
    }]
    nta = [{"法人番号": "1234567890123", "商号又は名称": "合成株式会社"}]
    payload = build_public_company_identity(
        canonical_identity=canonical,
        edinet_rows=edinet,
        nta_rows=nta,
        rights=allowed_rights_fixture(),
        code_commit="abc123",
    )
    row = payload["companies"][0]
    assert row["entity_id"] == "jp:corporate-number:1234567890123"
    assert row["canonical_name"] == "合成株式会社"
    assert row["security_code"] == "1001"
    assert row["edinet_code"] == "E00001"
    assert row["display_name_source"] == "jp-nta-corporate-number"
    assert row["security_code_source"] == "jp-edinet"
    assert "filer_name" not in row
    assert "JPX_SECURITY_CODE" not in json.dumps(payload)
    assert payload["manifest"]["resolved_public_company_count"] == 1
    assert payload["manifest"]["unresolved_count"] == 0


def test_projection_does_not_resolve_name_only_entity():
    canonical = {
        "manifest": {"semantic_identity_sha256": "b" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1002",
            "canonical_name": "同名株式会社",
            "review_state": "CONFIRMED",
            "identifiers": [],
        }],
    }
    edinet = [{
        "EDINETコード": "E00002",
        "証券コード": "10020",
        "提出者法人番号": "9999999999999",
        "提出者名": "同名株式会社",
    }]
    nta = [{"法人番号": "9999999999999", "商号又は名称": "同名株式会社"}]
    payload = build_public_company_identity(
        canonical_identity=canonical,
        edinet_rows=edinet,
        nta_rows=nta,
        rights=allowed_rights_fixture(),
        code_commit="abc123",
    )
    assert payload["manifest"]["resolved_public_company_count"] == 0
    assert payload["manifest"]["unresolved_count"] == 1
    assert payload["companies"] == []
    assert payload["unresolved"][0]["reason"] == "missing_strong_corporate_number"


def test_projection_disambiguates_duplicate_corporate_number_by_strong_edinet_code():
    canonical = {
        "manifest": {"semantic_identity_sha256": "c" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1003",
            "review_state": "CONFIRMED",
            "identifiers": [
                {"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111"},
                {"scheme": "EDINET_CODE", "value": "E00004"},
            ],
        }],
    }
    edinet = [
        {"EDINETコード": "E00003", "証券コード": "", "提出者法人番号": "1111111111111", "提出者名": "旧提出者"},
        {"EDINETコード": "E00004", "証券コード": "10040", "提出者法人番号": "1111111111111", "提出者名": "上場提出者"},
    ]
    nta = [{"法人番号": "1111111111111", "商号又は名称": "A社"}]
    payload = build_public_company_identity(
        canonical_identity=canonical,
        edinet_rows=edinet,
        nta_rows=nta,
        rights=allowed_rights_fixture(),
        code_commit="abc123",
    )
    assert payload["manifest"]["resolved_public_company_count"] == 1
    assert payload["companies"][0]["edinet_code"] == "E00004"
    assert payload["companies"][0]["security_code"] == "1004"


def test_projection_rejects_conflicting_edinet_rows_for_one_corporate_number():
    canonical = {
        "manifest": {"semantic_identity_sha256": "c" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1003",
            "review_state": "CONFIRMED",
            "identifiers": [
                {"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111"}
            ],
        }],
    }
    edinet = [
        {"EDINETコード": "E00003", "証券コード": "10030", "提出者法人番号": "1111111111111", "提出者名": "A社"},
        {"EDINETコード": "E00004", "証券コード": "10040", "提出者法人番号": "1111111111111", "提出者名": "A社"},
    ]
    nta = [{"法人番号": "1111111111111", "商号又は名称": "A社"}]
    payload = build_public_company_identity(
        canonical_identity=canonical,
        edinet_rows=edinet,
        nta_rows=nta,
        rights=allowed_rights_fixture(),
        code_commit="abc123",
    )
    assert payload["companies"] == []
    assert payload["unresolved"][0]["reason"] == "ambiguous_edinet_identity"
