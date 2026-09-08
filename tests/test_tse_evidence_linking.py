from __future__ import annotations

import pytest


def linking_api():
    try:
        from wa_commons.evidence.tse_coverage import link_mod_procurement_observations
    except ImportError as exc:
        pytest.fail(f"MOD coverage linker missing: {exc}")
    return link_mod_procurement_observations


def test_mod_observations_link_only_by_exact_corporate_number():
    link = linking_api()
    identity = {
        "manifest": {"entity_count": 3},
        "entities": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "review_state": "CONFIRMED",
                "identifiers": [
                    {"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111", "source": {}}
                ],
            },
            {
                "entity_id": "wa:org:jp:tse:1002",
                "review_state": "CONFIRMED",
                "identifiers": [
                    {"scheme": "JP_CORPORATE_NUMBER", "value": "2222222222222", "source": {}}
                ],
            },
            {
                "entity_id": "wa:org:jp:tse:1003",
                "review_state": "CONFIRMED",
                "identifiers": [],
            },
        ],
    }
    observations = [
        {
            "corporate_number": "1111111111111",
            "supplier_name": "Different Published Name",
            "identity_decision": "AUTO_LINK",
        },
        {
            "corporate_number": "1111111111111",
            "supplier_name": "Same Company Second Contract",
            "identity_decision": "AUTO_LINK",
        },
        {
            "corporate_number": "9999999999999",
            "supplier_name": "No Canonical TSE Match",
            "identity_decision": "AUTO_LINK",
        },
        {
            "corporate_number": "2222222222222",
            "supplier_name": "Should Not Link When Adapter Is Unresolved",
            "identity_decision": "UNRESOLVED",
        },
    ]

    linked = link(identity, observations)

    assert linked == [
        {"source_id": "jp-mod-procurement", "entity_id": "wa:org:jp:tse:1001"},
        {"source_id": "jp-mod-procurement", "entity_id": "wa:org:jp:tse:1001"},
    ]
