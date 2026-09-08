import pytest

from wa_commons.identity.models import SourceRef
from wa_commons.identity.tse_spine import build_tse_identity_spine


def src() -> SourceRef:
    return SourceRef(
        source="EDINET",
        source_key="fixture",
        snapshot="2026-08-31",
        url="https://example.test/edinet",
        retrieved_at="2026-09-08T00:00:00Z",
        adapter_version="0.4",
    )


def entity(code: str) -> dict:
    return {
        "entity_id": f"wa:org:jp:tse:{code}",
        "canonical_name": f"Company {code}",
        "jurisdiction": "JP",
        "aliases": [],
        "identifiers": [
            {
                "scheme": "JPX_SECURITY_CODE",
                "value": code,
                "source": {
                    "source": "JPX",
                    "source_key": "fixture",
                    "snapshot": "20260831",
                    "url": "https://example.test/jpx",
                    "retrieved_at": "2026-09-08T00:00:00Z",
                    "adapter_version": "0.4",
                },
            }
        ],
        "addresses": [],
        "review_state": "CONFIRMED",
        "review_reason": None,
    }


def test_spine_rejects_universe_manifest_entity_count_mismatch():
    universe = {
        "manifest": {
            "snapshot": "20260831",
            "source_sha256": "jpx-sha",
            "semantic_payload_sha256": "universe-sha",
            "entity_count": 2,
        },
        "entities": [entity("1001")],
    }

    with pytest.raises(ValueError, match="entity_count"):
        build_tse_identity_spine(
            universe,
            edinet_rows=[],
            edinet_source=src(),
            code_commit="deadbeef",
            source_metadata={},
        )


def test_spine_rejects_duplicate_jpx_security_code_in_universe():
    universe = {
        "manifest": {
            "snapshot": "20260831",
            "source_sha256": "jpx-sha",
            "semantic_payload_sha256": "universe-sha",
            "entity_count": 2,
        },
        "entities": [entity("1001"), entity("1001")],
    }

    with pytest.raises(ValueError, match="duplicate JPX_SECURITY_CODE"):
        build_tse_identity_spine(
            universe,
            edinet_rows=[],
            edinet_source=src(),
            code_commit="deadbeef",
            source_metadata={},
        )
