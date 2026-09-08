import copy
import json

from wa_commons.identity import tse_spine
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


def metadata() -> dict:
    return {
        "edinet": {"snapshot": "2026-08-31", "sha256": "edinet-sha"},
        "nta": {"snapshot": "2026-08-31", "sha256": "nta-sha"},
        "gleif": {"snapshot": "2026-08-31", "sha256": "gleif-sha"},
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
        source_metadata=metadata(),
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


def test_semantic_identity_hash_ignores_input_order_and_retrieval_time():
    first = {
        "manifest": {"snapshot": "20260831", "source_sha256": "jpx-sha", "semantic_payload_sha256": "universe-sha"},
        "entities": [universe_entity("1002", "Two Co"), universe_entity("1001", "One Co")],
    }
    second = copy.deepcopy(first)
    second["entities"].reverse()
    for entity in second["entities"]:
        for identifier in entity["identifiers"]:
            identifier["source"]["retrieved_at"] = "2026-09-09T12:34:56Z"

    kwargs = {
        "edinet_rows": [
            {"証券コード": "10010", "ＥＤＩＮＥＴコード": "E10001", "提出者法人番号": "1111111111111"}
        ],
        "edinet_source": src("EDINET"),
        "code_commit": "deadbeef",
        "source_metadata": metadata(),
    }
    first_result = build_tse_identity_spine(first, **kwargs)
    second_result = build_tse_identity_spine(second, **kwargs)

    assert first_result["manifest"]["semantic_identity_sha256"] == second_result["manifest"]["semantic_identity_sha256"]


def test_manifest_reports_identifier_and_validation_coverage():
    universe = {
        "manifest": {"snapshot": "20260831", "source_sha256": "jpx-sha", "semantic_payload_sha256": "universe-sha"},
        "entities": [universe_entity("1001", "Mapped Co"), universe_entity("1002", "Unresolved Co")],
    }
    result = build_tse_identity_spine(
        universe,
        edinet_rows=[
            {"証券コード": "10010", "ＥＤＩＮＥＴコード": "E10001", "提出者法人番号": "1111111111111"}
        ],
        edinet_source=src("EDINET"),
        nta_rows=[
            {"法人番号": "1111111111111", "商号又は名称": "Mapped Co株式会社", "国内所在地（都道府県市区町村）": "東京都"}
        ],
        nta_source=src("NTA"),
        gleif_rows=[
            {"LEI": "549300EXAMPLE0000001", "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111"}
        ],
        gleif_source=src("GLEIF"),
        code_commit="deadbeef",
        source_metadata=metadata(),
    )

    manifest = result["manifest"]
    assert manifest["edinet_count"] == 1
    assert manifest["corporate_number_count"] == 1
    assert manifest["nta_validated_count"] == 1
    assert manifest["lei_count"] == 1
    assert manifest["sources"] == metadata()


def test_writer_keeps_row_level_identity_local_and_public_output_manifest_only(tmp_path):
    payload = build_tse_identity_spine(
        {
            "manifest": {"snapshot": "20260831", "source_sha256": "jpx-sha", "semantic_payload_sha256": "universe-sha"},
            "entities": [universe_entity("1001", "Private Row Co")],
        },
        edinet_rows=[],
        edinet_source=src("EDINET"),
        code_commit="deadbeef",
        source_metadata=metadata(),
    )
    local_path = tmp_path / "identity-local.json"
    public_path = tmp_path / "identity-manifest.json"

    tse_spine.write_tse_identity_spine(payload, local_path, public_path)

    local = json.loads(local_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    assert local["entities"][0]["canonical_name"] == "Private Row Co"
    assert public == payload["manifest"]
    assert "entities" not in public
    assert "Private Row Co" not in public_path.read_text(encoding="utf-8")
    assert "1001" not in public_path.read_text(encoding="utf-8")
