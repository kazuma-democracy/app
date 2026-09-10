from __future__ import annotations

import json
from pathlib import Path

from wa_commons.public_client.policy_screening import (
    build_public_policy_screening,
)

ROOT = Path(__file__).resolve().parents[1]


def policies():
    return json.loads(
        (ROOT / "configs/public-browser-extension-policies-v0.1.json").read_text(
            encoding="utf-8"
        )
    )


def coverage():
    return {
        "matrix_sha256": "a" * 64,
        "matrix": {
            "entity_count": 1,
            "rows": [
                {
                    "entity_id": "wa:org:jp:tse:1001",
                    "source_id": "jp-mod-procurement",
                    "state": "observed",
                    "observation_count": 1,
                }
            ],
        },
    }


def bridge():
    return {
        "links": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "corporate_number": "1111111111111",
                "review_state": "CONFIRMED",
            }
        ]
    }


def claim(claim_id, category, predicate, status="unknown", value=None, source_id="jp-mod-procurement"):
    return {
        "claim_id": claim_id,
        "subject": {
            "entity_id": "jp:corporate-number:1111111111111",
            "jurisdiction": "JP",
        },
        "claim": {
            "category": category,
            "predicate": predicate,
            "value": value if value is not None else {},
        },
        "evidence": [{"source_id": source_id}],
        "adjudication": {
            "status": status,
            "confidence": 0.0 if status != "confirmed" else 1.0,
        },
    }


def decisions(result):
    return {
        row["profile_id"]: row["decision"]
        for row in result["views"]
    }


def test_unknown_military_claim_affects_only_military_scoped_profiles():
    graph = {
        "claims": [
            claim(
                "military-unknown",
                "military_contract",
                "contract_subject_classification",
                value={"classification": "unknown"},
            )
        ]
    }
    result = build_public_policy_screening(
        coverage_artifact=coverage(),
        evidence_graph=graph,
        policies=policies(),
        identity_bridge=bridge(),
    )
    assert decisions(result) == {
        "public:information-only:v1": "NONE",
        "public:strict-military-specific:v1": "WATCH",
        "public:ohchr-settlement-avoidance:v1": "NONE",
        "public:military-and-settlement:v1": "WATCH",
    }


def test_unknown_ohchr_claim_affects_only_settlement_scoped_profiles():
    graph = {
        "claims": [
            claim(
                "ohchr-unknown",
                "human_rights",
                "ohchr_settlement_related_activity",
                source_id="ohchr-settlements-business",
            )
        ]
    }
    result = build_public_policy_screening(
        coverage_artifact=coverage(),
        evidence_graph=graph,
        policies=policies(),
        identity_bridge=bridge(),
    )
    assert decisions(result) == {
        "public:information-only:v1": "NONE",
        "public:strict-military-specific:v1": "NONE",
        "public:ohchr-settlement-avoidance:v1": "WATCH",
        "public:military-and-settlement:v1": "WATCH",
    }


def test_generic_israel_presence_is_not_in_settlement_scope():
    graph = {
        "claims": [
            claim(
                "israel-presence",
                "human_rights",
                "business_presence_in_israel",
                status="confirmed",
                source_id="company-primary-disclosures",
            )
        ]
    }
    result = build_public_policy_screening(
        coverage_artifact=coverage(),
        evidence_graph=graph,
        policies=policies(),
        identity_bridge=bridge(),
    )
    assert set(decisions(result).values()) == {"NONE"}


def test_public_screening_hash_is_order_independent():
    items = [
        claim(
            "military-unknown",
            "military_contract",
            "contract_subject_classification",
            value={"classification": "unknown"},
        ),
        claim(
            "ohchr-confirmed",
            "human_rights",
            "ohchr_settlement_related_activity",
            status="confirmed",
            source_id="ohchr-settlements-business",
        ),
    ]
    first = build_public_policy_screening(
        coverage_artifact=coverage(),
        evidence_graph={"claims": items},
        policies=policies(),
        identity_bridge=bridge(),
    )
    second = build_public_policy_screening(
        coverage_artifact=coverage(),
        evidence_graph={"claims": list(reversed(items))},
        policies=list(reversed(policies())),
        identity_bridge=bridge(),
    )
    assert first["screening_sha256"] == second["screening_sha256"]
