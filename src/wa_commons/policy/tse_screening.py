from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from wa_commons.evidence.contract_subject import classification_claim, classify_contract_subject
from wa_commons.evidence.mod_procurement import ProcurementObservation, observation_to_claim
from wa_commons.policy.company_view import build_company_research_views, canonical_sha256

TSE_SCREENING_VERSION = "m3.2e-tse-screening-v0.1"


def _corporate_number(entity: Mapping[str, Any]) -> str | None:
    values = {
        str(identifier.get("value", "")).strip()
        for identifier in entity.get("identifiers", [])
        if str(identifier.get("scheme", "")).strip() == "JP_CORPORATE_NUMBER"
        and str(identifier.get("value", "")).strip()
    }
    if len(values) != 1:
        return None
    value = next(iter(values))
    return value if len(value) == 13 and value.isdigit() else None


def _identity_bridge(identity: Mapping[str, Any]) -> dict[str, Any]:
    links = []
    for entity in identity.get("entities", []):
        if str(entity.get("review_state", "")).upper() != "CONFIRMED":
            continue
        number = _corporate_number(entity)
        if number is None:
            continue
        links.append(
            {
                "entity_id": str(entity["entity_id"]),
                "corporate_number": number,
                "review_state": "CONFIRMED",
            }
        )
    return {
        "bridge_version": "m3.2e-derived-from-tse-identity-v0.1",
        "links": sorted(links, key=lambda item: (item["entity_id"], item["corporate_number"])),
    }


def _claims_from_mod_observations(
    observations: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for raw in observations:
        observation = ProcurementObservation(**dict(raw))
        contract_claim = observation_to_claim(observation)
        if contract_claim is not None:
            claims.append(contract_claim)
        subject_result = classify_contract_subject(observation.subject)
        subject_claim = classification_claim(observation, subject_result)
        if subject_claim is not None:
            claims.append(subject_claim)
    return sorted(claims, key=lambda claim: str(claim["claim_id"]))


def build_tse_policy_screening(
    *,
    identity: Mapping[str, Any],
    coverage_artifact: Mapping[str, Any],
    mod_observations: Sequence[Mapping[str, Any]],
    policies: Sequence[Mapping[str, Any]],
    code_commit: str,
) -> dict[str, Any]:
    coverage = deepcopy(dict(coverage_artifact))
    coverage_sha = str(coverage.get("manifest", {}).get("coverage_semantic_sha256", "")).strip()
    if coverage_sha:
        coverage["matrix_sha256"] = coverage_sha

    claims = _claims_from_mod_observations(mod_observations)
    evidence_graph = {"claims": claims}
    bridge = _identity_bridge(identity)
    screening = build_company_research_views(
        coverage_artifact=coverage,
        evidence_graph=evidence_graph,
        policies=policies,
        identity_bridge=bridge,
    )
    confirmed_ids = {str(link["entity_id"]) for link in bridge["links"]}
    screening["views"] = [
        {**view, "identity_state": "confirmed" if str(view["entity_id"]) in confirmed_ids else "unresolved"}
        for view in screening["views"]
    ]
    payload = {
        "issue": 55,
        "artifact_version": TSE_SCREENING_VERSION,
        "code_commit": code_commit,
        "identity_semantic_sha256": identity.get("manifest", {}).get("semantic_identity_sha256"),
        "coverage_semantic_sha256": coverage_sha or screening["coverage_matrix_sha256"],
        "mod_observation_count": len(mod_observations),
        "generated_claim_count": len(claims),
        "confirmed_identity_bridge_count": len(bridge["links"]),
        "unresolved_identity_entity_count": len(screening["views"]) // len(policies) - len(bridge["links"]),
        **screening,
        "interpretation": {
            "research_only": True,
            "none_is_not_pass": True,
            "row_level_output_local_only": True,
        },
    }
    semantic = {key: value for key, value in payload.items() if key != "code_commit"}
    payload["tse_screening_sha256"] = canonical_sha256(semantic)
    return payload


def write_tse_policy_screening(
    payload: Mapping[str, Any],
    local_output: str | "Path",
    public_output: str | "Path",
) -> None:
    import json
    from pathlib import Path

    local_path = Path(local_output)
    public_path = Path(public_output)
    if local_path.resolve() == public_path.resolve():
        raise ValueError("local and public outputs must differ")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    public_keys = (
        "issue", "artifact_version", "code_commit", "identity_semantic_sha256",
        "coverage_semantic_sha256", "mod_observation_count", "generated_claim_count",
        "confirmed_identity_bridge_count", "screening_version", "evidence_graph_sha256",
        "coverage_matrix_sha256", "identity_bridge_sha256", "company_count", "profile_count",
        "view_count", "graph_claim_count", "mapped_claim_count", "unmapped_claim_count",
        "policies", "decision_counts_by_profile", "policy_comparison", "screening_sha256",
        "interpretation", "unresolved_identity_entity_count", "tse_screening_sha256",
    )
    public_payload = {key: payload[key] for key in public_keys if key in payload}
    public_path.write_text(
        json.dumps(public_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summarize_weighted_coverage(
    screening: Mapping[str, Any],
    weights: Mapping[str, float],
) -> dict[str, Any]:
    total_weight = sum(float(value) for value in weights.values())
    views = list(screening.get("views", []))
    represented_ids = {str(view["entity_id"]) for view in views}
    represented_weight = sum(
        float(weight) for entity_id, weight in weights.items()
        if str(entity_id) in represented_ids
    )
    unresolved_ids = {
        str(view["entity_id"])
        for view in views
        if str(view.get("identity_state", "")) == "unresolved"
    }
    unresolved_weight = sum(
        float(weight) for entity_id, weight in weights.items()
        if str(entity_id) in unresolved_ids
    )

    decision_weight: dict[str, dict[str, float]] = {}
    for view in views:
        profile_id = str(view["profile_id"])
        decision = str(view["decision"])
        buckets = decision_weight.setdefault(
            profile_id,
            {"EXCLUDE": 0.0, "WATCH": 0.0, "NONE": 0.0},
        )
        buckets[decision] += float(weights.get(str(view["entity_id"]), 0.0))

    return {
        "interface_version": "m3.2e-weighted-coverage-v0.1",
        "total_weight": total_weight,
        "represented_weight": represented_weight,
        "unrepresented_weight": total_weight - represented_weight,
        "unresolved_identity_weight": unresolved_weight,
        "decision_weight_by_profile": {
            profile_id: decision_weight[profile_id]
            for profile_id in sorted(decision_weight)
        },
    }
