from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DECISION_PRIORITY = {"NONE": 0, "WATCH": 1, "EXCLUDE": 2}
ALLOWED_FACTUAL_STATUSES = {"confirmed", "unknown", "disputed", "expired"}


@dataclass(frozen=True)
class PolicyResult:
    profile_id: str
    profile_version: str
    claim_id: str
    decision: str
    matched_rule_ids: tuple[str, ...]
    preference_signals: tuple[dict[str, Any], ...]
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "claim_id": self.claim_id,
            "decision": self.decision,
            "matched_rule_ids": list(self.matched_rule_ids),
            "preference_signals": list(self.preference_signals),
            "reasoning": self.reasoning,
        }


def _get_field(claim: dict[str, Any], path: str) -> Any:
    value: Any = claim
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _compare(actual: Any, operator: str, expected: Any) -> bool:
    if operator == "exists":
        return (actual is not None) is bool(expected)
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return isinstance(expected, list) and actual in expected
    if actual is None:
        return False
    try:
        if operator == "gt":
            return actual > expected
        if operator == "gte":
            return actual >= expected
        if operator == "lt":
            return actual < expected
        if operator == "lte":
            return actual <= expected
    except TypeError:
        return False
    raise ValueError(f"unsupported operator: {operator}")


def _matches_scope(rule: dict[str, Any], claim: dict[str, Any]) -> bool:
    match = rule["match"]
    c = claim["claim"]
    subject = claim["subject"]
    evidence = claim.get("evidence", [])
    if c.get("category") not in match["categories"]:
        return False
    if match.get("predicates") and c.get("predicate") not in match["predicates"]:
        return False
    if match.get("jurisdictions") and subject.get("jurisdiction") not in match["jurisdictions"]:
        return False
    if match.get("source_ids"):
        source_ids = {e.get("source_id") for e in evidence}
        if not source_ids.intersection(match["source_ids"]):
            return False
    min_confidence = rule.get("min_confidence")
    if min_confidence is not None and claim["adjudication"].get("confidence", 0) < min_confidence:
        return False
    condition = rule.get("condition")
    if condition and not _compare(_get_field(claim, condition["field"]), condition["operator"], condition["value"]):
        return False
    return True


def evaluate_claim(policy: dict[str, Any], claim: dict[str, Any]) -> PolicyResult:
    """Evaluate one factual claim without mutating evidence or granting action authority."""
    raw_status = claim["adjudication"]["status"]
    if not isinstance(raw_status, str):
        raise ValueError(f"unsupported factual status: {raw_status}")
    status = raw_status.lower()
    if status not in ALLOWED_FACTUAL_STATUSES:
        raise ValueError(f"unsupported factual status: {status}")

    # Uncertainty is resolved before exclusion rules. A disputed/unknown/expired
    # factual claim cannot become EXCLUDE merely because its category matches.
    if status != "confirmed":
        decision = policy["uncertainty"][status]
        return PolicyResult(
            profile_id=policy["profile_id"],
            profile_version=policy["profile_version"],
            claim_id=claim["claim_id"],
            decision=decision,
            matched_rule_ids=(),
            preference_signals=(),
            reasoning=f"Factual status {status.upper()} is routed by the profile uncertainty rule; exclusion rules were not evaluated.",
        )

    matched: list[str] = []
    decision = policy["default_decision"]
    for rule in policy["exclusions"]:
        if _matches_scope(rule, claim):
            matched.append(rule["rule_id"])
            proposed = rule["decision"]
            if DECISION_PRIORITY[proposed] > DECISION_PRIORITY[decision]:
                decision = proposed

    preferences: list[dict[str, Any]] = []
    for rule in policy["preferences"]:
        if _matches_scope(rule, claim):
            preferences.append({
                "rule_id": rule["rule_id"],
                "direction": rule["direction"],
                "weight": rule["weight"],
            })

    reason = "No policy rule matched; NONE does not assert that the entity is safe or clean."
    if matched:
        reason = f"Matched user policy rule(s): {', '.join(matched)}."
    return PolicyResult(
        profile_id=policy["profile_id"],
        profile_version=policy["profile_version"],
        claim_id=claim["claim_id"],
        decision=decision,
        matched_rule_ids=tuple(matched),
        preference_signals=tuple(preferences),
        reasoning=reason,
    )
