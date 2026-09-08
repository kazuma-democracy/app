from wa_commons.identity.models import SourceRef
from wa_commons.identity.tse_spine import build_tse_identity_spine


def src(name: str) -> SourceRef:
    return SourceRef(
        source=name,
        source_key=f"{name}-fixture",
        snapshot="2026-08-31",
        url=f"https://example.test/{name}",
        retrieved_at="2026-09-08T00:00:00Z",
        adapter_version="0.4",
    )


def universe_entity(code: str, name: str, *, corporate_number: str | None = None) -> dict:
    identifiers = [
        {
            "scheme": "JPX_SECURITY_CODE",
            "value": code,
            "source": src("JPX").__dict__,
        }
    ]
    if corporate_number:
        identifiers.append(
            {
                "scheme": "JP_CORPORATE_NUMBER",
                "value": corporate_number,
                "source": src("seed").__dict__,
            }
        )
    return {
        "entity_id": f"wa:org:jp:tse:{code}",
        "canonical_name": name,
        "jurisdiction": "JP",
        "aliases": [],
        "identifiers": identifiers,
        "addresses": [],
        "review_state": "CONFIRMED",
        "review_reason": None,
        "security_code": code,
        "market_segment": "Prime",
    }


def test_every_universe_entity_is_preserved_and_identity_states_partition_output():
    universe = {
        "manifest": {
            "snapshot": "20260831",
            "source_sha256": "jpx-sha",
            "semantic_payload_sha256": "universe-sha",
        },
        "entities": [
            universe_entity("1001", "Mapped Co"),
            universe_entity("1002", "Unresolved Co"),
            universe_entity("1003", "Conflict Co", corporate_number="3333333333333"),
        ],
    }
    edinet_rows = [
        {"証券コード": "10010", "ＥＤＩＮＥＴコード": "E10001", "提出者法人番号": "1111111111111"},
        {"証券コード": "10030", "ＥＤＩＮＥＴコード": "E10003", "提出者法人番号": "9999999999999"},
    ]

    result = build_tse_identity_spine(
        universe,
        edinet_rows=edinet_rows,
        edinet_source=src("EDINET"),
        code_commit="deadbeef",
        source_metadata={
            "edinet": {"snapshot": "2026-08-31", "sha256": "edinet-sha"},
            "nta": {"snapshot": "2026-08-31", "sha256": "nta-sha"},
            "gleif": {"snapshot": "2026-08-31", "sha256": "gleif-sha"},
        },
    )

    assert [row["entity_id"] for row in result["entities"]] == [
        "wa:org:jp:tse:1001",
        "wa:org:jp:tse:1002",
        "wa:org:jp:tse:1003",
    ]
    assert result["manifest"]["entity_count"] == 3
    assert result["manifest"]["mapped_count"] == 1
    assert result["manifest"]["unresolved_count"] == 1
    assert result["manifest"]["disputed_count"] == 1
    assert result["manifest"]["mapped_count"] + result["manifest"]["unresolved_count"] + result["manifest"]["disputed_count"] == 3
    assert result["manifest"]["identity_policy_version"] == "wa-conservative-v0.2"
