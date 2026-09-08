from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from itertools import combinations
import json
from typing import Any, Mapping, Sequence

from wa_commons.policy.evaluator import DECISION_PRIORITY, evaluate_claim

SCREENING_VERSION = "m2.2b-screening-v0.1"
COVERAGE_STATES = (
    "observed",
    "no_match",
    "unknown",
    "unresolved_identity",
    "not_integrated",
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _corporate_number_from_subject(subject_id: str) -> str | None:
    prefix = "jp:corporate-number:"
    if subject_id.startswith(prefix):
        value = subject_id[len(prefix) :].strip()
        return value or None
    return None


def _source_ids(claim: Mapping[str, Any]) -> list[str]:
    return sorted(
        {
            str(item.get("source_id", "")).strip()
            for item in claim.get("evidence", [])
            if str(item.get("source_id", "")).strip()
        }
    )


def _coverage_by_entity(coverage_artifact: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    rows = coverage_artifact["matrix"]["rows"]
    result: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        entity_id = str(row["entity_id"])
        source_id = str(row["source_id"])
        state = str(row["state"])
        if state not in COVERAGE_STATES:
            raise ValueError(f"unsupported coverage state: {state}")
        previous = result[entity_id].get(source_id)
        if previous is not None and previous != state:
            raise ValueError(f"conflicting coverage state for {entity_id}/{source_id}")
        result[entity_id][source_id] = state
    return {entity_id: dict(sorted(states.items())) for entity_id, states in result.items()}


def _confirmed_bridge(identity_bridge: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    company_to_number: dict[str, str] = {}
    number_to_company: dict[str, str] = {}
    for link in identity_bridge["links"]:
        entity_id = str(link["entity_id"])
        corporate_number = str(link["corporate_number"])
        if str(link.get("review_state", "")).upper() != "CONFIRMED":
            continue
        if entity_id in company_to_number and company_to_number[entity_id] != corporate_number:
            raise ValueError(f"conflicting corporate number for {entity_id}")
        if corporate_number in number_to_company and number_to_company[corporate_number] != entity_id:
            raise ValueError(f"corporate number maps to multiple companies: {corporate_number}")
        company_to_number[entity_id] = corporate_number
        number_to_company[corporate_number] = entity_id
    return company_to_number, number_to_company


def _map_claims_to_companies(
    evidence_graph: Mapping[str, Any],
    *,
    company_ids: set[str],
    number_to_company: Mapping[str, str],
) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    mapped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unmapped: list[str] = []
    for raw_claim in sorted(evidence_graph.get("claims", []), key=lambda item: str(item["claim_id"])):
        claim = deepcopy(raw_claim)
        subject_id = str(claim["subject"]["entity_id"])
        company_id: str | None = subject_id if subject_id in company_ids else None
        if company_id is None:
            corporate_number = _corporate_number_from_subject(subject_id)
            if corporate_number is not None:
                company_id = number_to_company.get(corporate_number)
        if company_id is None:
            unmapped.append(str(claim["claim_id"]))
            continue
        mapped[company_id].append(claim)
    return {entity_id: claims for entity_id, claims in sorted(mapped.items())}, sorted(unmapped)


def _claim_result(policy: Mapping[str, Any], claim: Mapping[str, Any]) -> dict[str, Any]:
    result = evaluate_claim(dict(policy), dict(claim))
    status = str(claim["adjudication"]["status"]).lower()
    uncertainty_ref = None if status == "confirmed" else f"uncertainty.{status}"
    return {
        "claim_id": str(claim["claim_id"]),
        "adjudication_status": status,
        "decision": result.decision,
        "rule_refs": sorted(result.matched_rule_ids),
        "uncertainty_ref": uncertainty_ref,
        "source_ids": _source_ids(claim),
        "preference_signals": sorted(
            (deepcopy(item) for item in result.preference_signals),
            key=lambda item: (str(item.get("rule_id", "")), str(item.get("direction", ""))),
        ),
        "reasoning": result.reasoning,
    }


def _view_reasoning(*, decision: str, claim_results: Sequence[Mapping[str, Any]]) -> str:
    if not claim_results:
        return (
            "No canonical Evidence Graph claim is linked to this entity in this snapshot; "
            "the company-level decision is NONE. NONE is not PASS, clean, or safe. "
            "Coverage states remain explicit."
        )
    if decision == "NONE":
        return (
            "All linked claims produced NONE under this profile. NONE is not PASS, clean, or safe; "
            "it only means this profile produced no EXCLUDE/WATCH decision from the linked claims."
        )
    decisive_claims = sorted(
        item["claim_id"]
        for item in claim_results
        if DECISION_PRIORITY[item["decision"]] == DECISION_PRIORITY[decision]
    )
    return f"Company decision {decision} is the highest-priority linked claim result; decisive claim(s): {', '.join(decisive_claims)}."


def build_company_research_views(
    *,
    coverage_artifact: Mapping[str, Any],
    evidence_graph: Mapping[str, Any],
    policies: Sequence[Mapping[str, Any]],
    identity_bridge: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic company-level research views without inventing PASS.

    The existing claim-level evaluator remains authoritative for policy decisions.
    This layer only maps canonical claims to the fixed company cohort, aggregates
    EXCLUDE/WATCH/NONE by documented priority, and preserves coverage uncertainty.
    """
    coverage = _coverage_by_entity(coverage_artifact)
    company_ids = sorted(coverage)
    if int(coverage_artifact["matrix"].get("entity_count", len(company_ids))) != len(company_ids):
        raise ValueError("coverage entity_count does not match distinct matrix entities")

    company_to_number, number_to_company = _confirmed_bridge(identity_bridge)
    missing_bridge = sorted(set(company_ids) - set(company_to_number))
    if missing_bridge:
        raise ValueError(f"confirmed identity bridge missing coverage entities: {missing_bridge}")

    claims_by_company, unmapped_claim_ids = _map_claims_to_companies(
        evidence_graph,
        company_ids=set(company_ids),
        number_to_company=number_to_company,
    )

    policy_rows = sorted(
        (
            {
                "profile_id": str(policy["profile_id"]),
                "profile_version": str(policy["profile_version"]),
                "policy_sha256": canonical_sha256(policy),
                "policy": deepcopy(dict(policy)),
            }
            for policy in policies
        ),
        key=lambda row: (row["profile_id"], row["profile_version"], row["policy_sha256"]),
    )

    views: list[dict[str, Any]] = []
    decision_counts_by_profile: dict[str, Counter[str]] = defaultdict(Counter)
    mapped_claim_ids: set[str] = set()
    for entity_id in company_ids:
        coverage_states = coverage[entity_id]
        coverage_counts = Counter(coverage_states.values())
        coverage_state_counts = {state: coverage_counts.get(state, 0) for state in COVERAGE_STATES}
        company_claims = claims_by_company.get(entity_id, [])
        mapped_claim_ids.update(str(claim["claim_id"]) for claim in company_claims)
        for policy_row in policy_rows:
            claim_results = sorted(
                (_claim_result(policy_row["policy"], claim) for claim in company_claims),
                key=lambda item: item["claim_id"],
            )
            decision = "NONE"
            for item in claim_results:
                if DECISION_PRIORITY[item["decision"]] > DECISION_PRIORITY[decision]:
                    decision = item["decision"]
            decision_counts_by_profile[policy_row["profile_id"]][decision] += 1
            views.append(
                {
                    "entity_id": entity_id,
                    "profile_id": policy_row["profile_id"],
                    "profile_version": policy_row["profile_version"],
                    "policy_sha256": policy_row["policy_sha256"],
                    "decision": decision,
                    "claim_results": claim_results,
                    "coverage_states": coverage_states,
                    "coverage_state_counts": coverage_state_counts,
                    "reasoning": _view_reasoning(decision=decision, claim_results=claim_results),
                }
            )

    comparable_policies = [
        {
            "profile_id": row["profile_id"],
            "profile_version": row["profile_version"],
            "policy_sha256": row["policy_sha256"],
        }
        for row in policy_rows
    ]
    decisions = {(view["entity_id"], view["profile_id"]): view["decision"] for view in views}
    policy_comparison: list[dict[str, Any]] = []
    for left, right in combinations(comparable_policies, 2):
        differences = sum(
            decisions[(entity_id, left["profile_id"])] != decisions[(entity_id, right["profile_id"])]
            for entity_id in company_ids
        )
        policy_comparison.append(
            {
                "left_profile_id": left["profile_id"],
                "right_profile_id": right["profile_id"],
                "same_evidence_snapshot": True,
                "decision_difference_count": differences,
            }
        )

    semantic = {
        "screening_version": SCREENING_VERSION,
        "evidence_graph_sha256": canonical_sha256(evidence_graph),
        "coverage_matrix_sha256": str(coverage_artifact.get("matrix_sha256", canonical_sha256(coverage_artifact["matrix"]))),
        "identity_bridge_sha256": canonical_sha256(identity_bridge),
        "company_count": len(company_ids),
        "profile_count": len(policy_rows),
        "view_count": len(views),
        "graph_claim_count": len(evidence_graph.get("claims", [])),
        "mapped_claim_count": len(mapped_claim_ids),
        "unmapped_claim_count": len(unmapped_claim_ids),
        "unmapped_claim_ids": unmapped_claim_ids,
        "policies": comparable_policies,
        "decision_counts_by_profile": {
            profile_id: {
                decision: decision_counts_by_profile[profile_id].get(decision, 0)
                for decision in ("EXCLUDE", "WATCH", "NONE")
            }
            for profile_id in sorted(decision_counts_by_profile)
        },
        "views": sorted(views, key=lambda view: (view["entity_id"], view["profile_id"], view["profile_version"])),
        "policy_comparison": sorted(
            policy_comparison,
            key=lambda item: (item["left_profile_id"], item["right_profile_id"]),
        ),
    }
    return {**semantic, "screening_sha256": canonical_sha256(semantic)}
