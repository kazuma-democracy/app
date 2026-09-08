from wa_commons.identity.models import SourceRef
from wa_commons.identity.tse_spine import build_tse_identity_spine


def src(name: str) -> SourceRef:
    return SourceRef(
        source=name,
        source_key="fixture",
        snapshot="2026-08-31",
        url=f"https://example.test/{name}",
        retrieved_at="2026-09-08T00:00:00Z",
        adapter_version="0.4",
    )


def entity() -> dict:
    return {
        "entity_id": "wa:org:jp:tse:1001",
        "canonical_name": "Example Co",
        "jurisdiction": "JP",
        "aliases": [],
        "identifiers": [
            {
                "scheme": "JPX_SECURITY_CODE",
                "value": "1001",
                "source": src("JPX").__dict__,
            },
            {
                "scheme": "JP_CORPORATE_NUMBER",
                "value": "1111111111111",
                "source": src("EDINET").__dict__,
            },
        ],
        "addresses": [],
        "review_state": "CONFIRMED",
        "review_reason": None,
        "security_code": "1001",
        "market_segment": "Prime",
    }


def test_gleif_row_from_non_japanese_registration_authority_cannot_attach_lei():
    result = build_tse_identity_spine(
        {
            "manifest": {
                "snapshot": "20260831",
                "source_sha256": "jpx-sha",
                "semantic_payload_sha256": "universe-sha",
            },
            "entities": [entity()],
        },
        edinet_rows=[],
        edinet_source=src("EDINET"),
        gleif_rows=[
            {
                "LEI": "549300WRONGAUTHORITY001",
                "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA999999",
                "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111",
            }
        ],
        gleif_source=src("GLEIF"),
        code_commit="deadbeef",
        source_metadata={"gleif": {"snapshot": "2026-08-31", "sha256": "gleif-sha"}},
    )

    assert result["manifest"]["lei_count"] == 0
    assert all(identifier["scheme"] != "LEI" for identifier in result["entities"][0]["identifiers"])
