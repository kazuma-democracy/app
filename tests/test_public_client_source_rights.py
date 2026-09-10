from pathlib import Path

import pytest

from wa_commons.public_client.source_rights import (
    load_public_source_rights,
    require_public_fields,
)

ROOT = Path(__file__).resolve().parents[1]


def test_current_rights_states_are_explicit():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    assert rights["jp-mod-procurement"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-nta-corporate-number"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-edinet"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-jpx-listed"].state == "BLOCK_PUBLIC_REDISTRIBUTION_REVIEW"
    assert rights["ohchr-settlements-business"].state == "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"


def test_blocked_and_undeclared_fields_fail_closed():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    require_public_fields("jp-mod-procurement", {"source_url", "narrow_claim"}, rights)
    with pytest.raises(ValueError, match="not cleared for public client"):
        require_public_fields("jp-mod-procurement", {"raw_document_text"}, rights)
    with pytest.raises(ValueError, match="BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"):
        require_public_fields("ohchr-settlements-business", {"entity_name"}, rights)


def test_invalid_rights_contract_is_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(
        '[{"source_id":"x","state":"BLOCK_PUBLIC_REDISTRIBUTION_REVIEW",'
        '"terms_url":"https://example.invalid/terms","checked_at":"2026-09-11",'
        '"allowed_fields":["field"],"attribution_required":true,"raw_rows_public":false,"note":"x"}]',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="blocked source cannot allow public fields"):
        load_public_source_rights(bad)

def test_rights_contract_rejects_non_boolean_flags(tmp_path):
    bad = tmp_path / "bad-flags.json"
    bad.write_text(
        '[{"source_id":"x","state":"PUBLIC_FIELDS_ALLOWED",'
        '"terms_url":"https://example.invalid/terms","checked_at":"2026-09-11",'
        '"allowed_fields":["field"],"attribution_required":"false",'
        '"raw_rows_public":"false","note":"x"}]',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be boolean"):
        load_public_source_rights(bad)

