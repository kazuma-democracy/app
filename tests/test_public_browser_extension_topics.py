from wa_commons.public_client.source_rights import PublicSourceRights
from wa_commons.public_client.topics import build_public_topic_states


def rights(state_mod="PUBLIC_FIELDS_ALLOWED", state_ohchr="BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"):
    def item(source_id, state):
        return PublicSourceRights(
            source_id=source_id,
            state=state,
            terms_url="https://example.invalid/terms",
            checked_at="2026-09-11",
            allowed_fields=frozenset({"narrow_claim"}) if state == "PUBLIC_FIELDS_ALLOWED" else frozenset(),
            attribution_required=True,
            raw_rows_public=False,
            note="synthetic",
        )
    return {
        "jp-mod-procurement": item("jp-mod-procurement", state_mod),
        "ohchr-settlements-business": item("ohchr-settlements-business", state_ohchr),
    }


def test_blocked_ohchr_rights_become_not_integrated_not_no_match():
    topics = build_public_topic_states(rights())
    assert topics["military_defence"]["state"] == "AVAILABLE"
    assert topics["ohchr_settlement_related"]["state"] == "NOT_INTEGRATED"
    assert topics["ohchr_settlement_related"]["reason"] == "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"
