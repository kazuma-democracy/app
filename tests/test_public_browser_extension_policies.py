import json
from pathlib import Path

import jsonschema

from wa_commons.policy.evaluator import evaluate_claim

ROOT = Path(__file__).resolve().parents[1]


def profiles():
    return json.loads((ROOT / "configs/public-browser-extension-policies-v0.1.json").read_text(encoding="utf-8"))


def profile(profile_id):
    return next(item for item in profiles() if item["profile_id"] == profile_id)


def claim(category, predicate, status="confirmed", value=True):
    return {
        "claim_id": f"synthetic:{predicate}",
        "subject": {"entity_id": "jp:corporate-number:1", "jurisdiction": "JP"},
        "claim": {"category": category, "predicate": predicate, "value": value},
        "evidence": [],
        "adjudication": {"status": status, "confidence": 1.0},
    }

def test_public_profiles_validate_and_have_exact_ids():
    schema = json.loads((ROOT / "schemas/user-policy.v0.1.schema.json").read_text(encoding="utf-8"))
    items = profiles()
    assert [item["profile_id"] for item in items] == [
        "public:information-only:v1",
        "public:strict-military-specific:v1",
        "public:ohchr-settlement-avoidance:v1",
        "public:military-and-settlement:v1",
    ]
    for item in items:
        jsonschema.validate(item, schema)


def test_strict_military_profile_preserves_existing_semantics():
    strict = profile("public:strict-military-specific:v1")
    rule = strict["exclusions"][0]
    assert rule["match"] == {
        "categories": ["military_contract"],
        "predicates": ["contract_subject_classification"],
    }
    assert rule["condition"]["value"] == "military_specific"


def test_settlement_profile_matches_only_exact_narrow_predicate():
    p = profile("public:ohchr-settlement-avoidance:v1")
    exact = claim("human_rights", "ohchr_settlement_related_activity")
    ordinary = claim("human_rights", "business_presence_in_israel")
    assert evaluate_claim(p, exact).decision == "EXCLUDE"
    assert evaluate_claim(p, ordinary).decision == "NONE"
