from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Mapping, Sequence

from wa_commons.policy.company_view import (
    build_company_research_views,
    canonical_sha256,
)

PUBLIC_SCREENING_VERSION = "m2.5-public-policy-screening-v0.1"


def _claim_source_ids(claim: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("source_id", "")).strip()
        for item in claim.get("evidence", [])
        if str(item.get("source_id", "")).strip()
    }


def _rule_scope_matches(
    rule: Mapping[str, Any],
    claim: Mapping[str, Any],
) -> bool:
    match = rule.get("match", {})
    factual = claim.get("claim", {})
    subject = claim.get("subject", {})

    categories = list(match.get("categories", []))
    if categories and factual.get("category") not in categories:
        return False
    predicates = list(match.get("predicates", []))
    if predicates and factual.get("predicate") not in predicates:
        return False
    jurisdictions = list(match.get("jurisdictions", []))
    if jurisdictions and subject.get("jurisdiction") not in jurisdictions:
        return False
    source_ids = set(match.get("source_ids", []))
    if source_ids and not source_ids.intersection(_claim_source_ids(claim)):
        return False
    return True


def claim_relevant_to_policy(
    policy: Mapping[str, Any],
    claim: Mapping[str, Any],
) -> bool:
    rules = [
        *policy.get("exclusions", []),
        *policy.get("preferences", []),
    ]
    return any(_rule_scope_matches(rule, claim) for rule in rules)


def _canonical_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(graph))
    result["claims"] = sorted(
        [deepcopy(dict(item)) for item in graph.get("claims", [])],
        key=lambda item: str(item.get("claim_id", "")),
    )
    return result


def build_public_policy_screening(
    *,
    coverage_artifact: Mapping[str, Any],
    evidence_graph: Mapping[str, Any],
    policies: Sequence[Mapping[str, Any]],
    identity_bridge: Mapping[str, Any],
) -> dict[str, Any]:
    ordered_policies = sorted(
        [deepcopy(dict(policy)) for policy in policies],
        key=lambda policy: (
            str(policy.get("profile_id", "")),
            str(policy.get("profile_version", "")),
        ),
    )
    source_graph = _canonical_graph(evidence_graph)

    views: list[dict[str, Any]] = []
    policy_rows: list[dict[str, str]] = []
    decision_counts: dict[str, dict[str, int]] = {}
    relevant_counts: dict[str, int] = {}
    company_count: int | None = None

    for policy in ordered_policies:
        profile_id = str(policy["profile_id"])
        filtered_claims = [
            claim
            for claim in source_graph["claims"]
            if claim_relevant_to_policy(policy, claim)
        ]
        result = build_company_research_views(
            coverage_artifact=coverage_artifact,
            evidence_graph={"claims": filtered_claims},
            policies=[policy],
            identity_bridge=identity_bridge,
        )
        if company_count is None:
            company_count = int(result["company_count"])
        elif company_count != int(result["company_count"]):
            raise ValueError("public policy screening company counts disagree")

        views.extend(deepcopy(result["views"]))
        policy_rows.extend(deepcopy(result["policies"]))
        decision_counts[profile_id] = deepcopy(
            result["decision_counts_by_profile"][profile_id]
        )
        relevant_counts[profile_id] = len(filtered_claims)


    views.sort(
        key=lambda view: (
            str(view["entity_id"]),
            str(view["profile_id"]),
            str(view["profile_version"]),
        )
    )
    policy_rows.sort(
        key=lambda row: (
            str(row["profile_id"]),
            str(row["profile_version"]),
            str(row["policy_sha256"]),
        )
    )

    decisions = {
        (str(view["entity_id"]), str(view["profile_id"])): str(view["decision"])
        for view in views
    }
    entity_ids = sorted({str(view["entity_id"]) for view in views})
    comparisons: list[dict[str, Any]] = []
    for left, right in combinations(
        [str(row["profile_id"]) for row in policy_rows], 2
    ):
        differences = sum(
            decisions[(entity_id, left)] != decisions[(entity_id, right)]
            for entity_id in entity_ids
        )
        comparisons.append({
            "left_profile_id": left,
            "right_profile_id": right,
            "same_evidence_snapshot": True,
            "decision_difference_count": differences,
        })

    semantic = {
        "screening_version": PUBLIC_SCREENING_VERSION,
        "source_evidence_graph_sha256": canonical_sha256(source_graph),
        "company_count": company_count or 0,
        "profile_count": len(policy_rows),
        "view_count": len(views),
        "policies": policy_rows,
        "relevant_claim_count_by_profile": {
            key: relevant_counts[key] for key in sorted(relevant_counts)
        },
        "decision_counts_by_profile": {
            key: decision_counts[key] for key in sorted(decision_counts)
        },
        "policy_comparison": sorted(
            comparisons,
            key=lambda row: (
                row["left_profile_id"],
                row["right_profile_id"],
            ),
        ),
        "views": views,
    }
    return {
        **semantic,
        "screening_sha256": canonical_sha256(semantic),
    }
