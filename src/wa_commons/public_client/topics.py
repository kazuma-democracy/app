from __future__ import annotations

from typing import Mapping

from wa_commons.public_client.source_rights import PublicSourceRights, PUBLIC_FIELDS_ALLOWED

PUBLIC_TOPICS = {
    "military_defence": {
        "source_id": "jp-mod-procurement",
        "label": "military / defence-related evidence",
    },
    "ohchr_settlement_related": {
        "source_id": "ohchr-settlements-business",
        "label": "OHCHR settlement-related activity evidence",
    },
}


def build_public_topic_states(
    rights: Mapping[str, PublicSourceRights],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for topic_id, metadata in PUBLIC_TOPICS.items():
        source_id = metadata["source_id"]
        source = rights.get(source_id)
        if source is None:
            result[topic_id] = {
                "state": "NOT_INTEGRATED",
                "reason": "SOURCE_RIGHTS_UNDECLARED",
                "source_id": source_id,
            }
            continue
        if source.state == PUBLIC_FIELDS_ALLOWED:
            result[topic_id] = {
                "state": "AVAILABLE",
                "reason": "PUBLIC_FIELDS_ALLOWED",
                "source_id": source_id,
            }
        else:
            result[topic_id] = {
                "state": "NOT_INTEGRATED",
                "reason": source.state,
                "source_id": source_id,
            }
    return result
