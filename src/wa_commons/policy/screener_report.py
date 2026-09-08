from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from wa_commons.evidence.cards import CHALLENGE_URL, card_from_claim

REPORT_VERSION = "m2-2c-explainable-screener-v0.1"


def _identifier(identity: Mapping[str, Any], scheme: str) -> str | None:
    for item in identity.get("identifiers", []):
        if str(item.get("scheme", "")) == scheme:
            value = str(item.get("value", "")).strip()
            if value:
                return value
    return None


def _code_sort_key(identity: Mapping[str, Any]) -> tuple[str, str]:
    code = _identifier(identity, "JPX_SECURITY_CODE") or str(identity.get("entity_id", ""))
    return code, str(identity.get("entity_id", ""))


def _json_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _policy_map(policies: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for policy in policies:
        profile_id = str(policy["profile_id"])
        if profile_id in result:
            raise ValueError(f"duplicate policy profile_id: {profile_id}")
        result[profile_id] = policy
    return result


def _identity_map(identities: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for identity in identities:
        entity_id = str(identity["entity_id"])
        if entity_id in result:
            raise ValueError(f"duplicate identity entity_id: {entity_id}")
        result[entity_id] = identity
    return result


def _claim_map(evidence_graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for claim in evidence_graph.get("claims", []):
        claim_id = str(claim["claim_id"])
        if claim_id in result:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        result[claim_id] = claim
    return result


def _policy_title(policy_by_id: Mapping[str, Mapping[str, Any]], profile_id: str) -> str:
    policy = policy_by_id.get(profile_id)
    return str(policy.get("title")) if policy else profile_id


def _render_claim_trace(
    *,
    claim_result: Mapping[str, Any],
    claim_by_id: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    claim_id = str(claim_result["claim_id"])
    claim = claim_by_id.get(claim_id)
    if claim is None:
        raise ValueError(f"screening references missing Evidence Graph claim: {claim_id}")
    card = card_from_claim(dict(claim)).to_dict()
    rule_refs = sorted(str(value) for value in claim_result.get("rule_refs", []))
    uncertainty_ref = claim_result.get("uncertainty_ref")
    lines = [
        f"#### Evidence Card — `{claim_id}`",
        "",
        f"- Claim decision: **{claim_result['decision']}**",
        f"- Rule refs: {', '.join(f'`{value}`' for value in rule_refs) if rule_refs else '`none`'}",
        f"- Uncertainty route: `{uncertainty_ref or 'none'}`",
        f"- Evidence status: **{card['adjudication']['status']}**",
        f"- Confidence: `{card['adjudication']['confidence']}`",
        f"- Category / predicate: `{card['claim']['category']}` / `{card['claim']['predicate']}`",
        f"- Exact value: `{_json_value(card['claim']['value'])}`",
        f"- Evidence reasoning: {card['adjudication']['reasoning_summary']}",
    ]
    if card["sources"]:
        for source in card["sources"]:
            lines.extend(
                [
                    f"- Source publisher: {source.get('publisher') or 'unknown'}",
                    f"- Source URL: {source.get('url') or 'unknown'}",
                    f"- Source locator: `{source.get('locator') or 'unknown'}`",
                ]
            )
    else:
        lines.append("- Source: no source row recorded in this claim version.")
    if card["correction_history"]:
        lines.append("- Correction history:")
        for item in card["correction_history"]:
            lines.append(
                f"  - `{item.get('changed_at')}`: `{str(item.get('previous_status')).upper()}` → "
                f"`{str(item.get('new_status')).upper()}` — {item.get('reason')}"
            )
    else:
        lines.append("- Correction history: none recorded for this claim version.")
    lines.extend(
        [
            f"- Challenge / correction: {card['challenge_path']['instruction']}",
            f"- Challenge path: {card['challenge_path']['url']}",
            "",
        ]
    )
    return lines


def render_screener_report(
    *,
    screening_artifact: Mapping[str, Any],
    evidence_graph: Mapping[str, Any],
    identities: Sequence[Mapping[str, Any]],
    policies: Sequence[Mapping[str, Any]],
    selected_profile_id: str,
) -> str:
    """Render the deterministic #43 screening artifact as a static Markdown report."""
    policy_by_id = _policy_map(policies)
    if selected_profile_id not in policy_by_id:
        raise ValueError(f"selected profile not found: {selected_profile_id}")
    identity_by_id = _identity_map(identities)
    claim_by_id = _claim_map(evidence_graph)

    company_count = int(screening_artifact["company_count"])
    if len(identity_by_id) != company_count:
        raise ValueError(f"identity count {len(identity_by_id)} does not match screening company_count {company_count}")

    screening_policy_rows = {
        str(item["profile_id"]): item for item in screening_artifact.get("policies", [])
    }
    if selected_profile_id not in screening_policy_rows:
        raise ValueError(f"selected profile missing from screening artifact: {selected_profile_id}")

    selected_views = [
        view
        for view in screening_artifact.get("views", [])
        if str(view["profile_id"]) == selected_profile_id
    ]
    view_by_entity = {str(view["entity_id"]): view for view in selected_views}
    if len(view_by_entity) != company_count:
        raise ValueError(
            f"selected profile has {len(view_by_entity)} distinct company views; expected {company_count}"
        )
    missing_identities = sorted(set(view_by_entity) - set(identity_by_id))
    if missing_identities:
        raise ValueError(f"screening entities missing from identity input: {missing_identities}")

    selected_policy = policy_by_id[selected_profile_id]
    selected_screening_policy = screening_policy_rows[selected_profile_id]
    selected_counts = screening_artifact["decision_counts_by_profile"][selected_profile_id]
    ordered_identities = sorted(identity_by_id.values(), key=_code_sort_key)

    lines = [
        "# WA Commons Explainable Company Screener",
        "",
        f"- Report version: `{REPORT_VERSION}`",
        f"- Selected policy: **{selected_policy.get('title', selected_profile_id)}**",
        f"- Profile ID / version: `{selected_profile_id}` / `{selected_screening_policy['profile_version']}`",
        f"- Policy SHA-256: `{selected_screening_policy['policy_sha256']}`",
        f"- Evidence Graph SHA-256: `{screening_artifact['evidence_graph_sha256']}`",
        f"- Coverage matrix SHA-256: `{screening_artifact['coverage_matrix_sha256']}`",
        f"- Screening SHA-256: `{screening_artifact['screening_sha256']}`",
        f"- Companies: **{company_count}**",
        "",
        "> **Interpretation guard:** `NONE` means this exact profile produced no EXCLUDE/WATCH decision from canonical claims linked to the company in this exact snapshot. **NONE is not PASS, clean, safe, peaceful, or proof of absence.** Coverage and unresolved identity states remain part of the result.",
        "",
        "No moral score, peace score, safety score, ranking, benchmark result, or portfolio recommendation is produced by this report.",
        "",
        "## Selected policy summary",
        "",
        str(selected_policy.get("description", "No description recorded.")),
        "",
        f"- EXCLUDE: **{selected_counts.get('EXCLUDE', 0)}**",
        f"- WATCH: **{selected_counts.get('WATCH', 0)}**",
        f"- NONE: **{selected_counts.get('NONE', 0)}**",
        "",
        "## Policy comparison — same evidence snapshot",
        "",
        f"All profiles below use Evidence Graph `{screening_artifact['evidence_graph_sha256']}` and screening snapshot `{screening_artifact['screening_sha256']}`.",
        "",
    ]

    comparisons = sorted(
        screening_artifact.get("policy_comparison", []),
        key=lambda item: (str(item["left_profile_id"]), str(item["right_profile_id"])),
    )
    for item in comparisons:
        left = str(item["left_profile_id"])
        right = str(item["right_profile_id"])
        if not item.get("same_evidence_snapshot"):
            raise ValueError(f"policy comparison is not on the same evidence snapshot: {left} vs {right}")
        lines.extend(
            [
                f"### {_policy_title(policy_by_id, left)} vs {_policy_title(policy_by_id, right)}",
                "",
                f"- Same evidence snapshot: `true`",
                f"- Decision differences: **{int(item['decision_difference_count'])}**",
                "",
            ]
        )

    lines.extend(
        [
            "## Company index — selected policy",
            "",
            "| TSE code | Company | Decision |",
            "| --- | --- | --- |",
        ]
    )
    for identity in ordered_identities:
        entity_id = str(identity["entity_id"])
        view = view_by_entity[entity_id]
        code = _identifier(identity, "JPX_SECURITY_CODE") or "unknown"
        name = str(identity.get("canonical_name") or entity_id)
        lines.append(f"| `{code}` | {name} | **{view['decision']}** |")

    lines.extend(["", "## How to read coverage", ""])
    lines.extend(
        [
            "- `observed`: linked evidence exists for this source/category in the snapshot.",
            "- `no_match`: the integrated source ran and produced no confirmed match for this entity; this is not proof of absence outside that source/snapshot.",
            "- `unknown`: the source/result could not establish the exact evidence state.",
            "- `unresolved_identity`: observations exist but cannot be safely linked to this entity under the identity policy.",
            "- `not_integrated`: the source/category has not yet been integrated into this coverage snapshot.",
            "",
        ]
    )

    for identity in ordered_identities:
        entity_id = str(identity["entity_id"])
        view = view_by_entity[entity_id]
        code = _identifier(identity, "JPX_SECURITY_CODE") or "unknown"
        corporate_number = _identifier(identity, "JP_CORPORATE_NUMBER") or "unknown"
        name = str(identity.get("canonical_name") or entity_id)
        lines.extend(
            [
                f"## Company {code} — {name}",
                "",
                f"- Entity ID: `{entity_id}`",
                f"- Japanese corporate number: `{corporate_number}`",
                f"- Decision under selected profile: **{view['decision']}**",
                f"- Reason: {view['reasoning']}",
                "",
                "### Coverage state",
                "",
            ]
        )
        for source_id, state in sorted(view.get("coverage_states", {}).items()):
            lines.append(f"- {source_id}: `{state}`")
        lines.extend(["", "### Policy trace and relevant Evidence Cards", ""])
        claim_results = sorted(view.get("claim_results", []), key=lambda item: str(item["claim_id"]))
        if claim_results:
            for claim_result in claim_results:
                lines.extend(_render_claim_trace(claim_result=claim_result, claim_by_id=claim_by_id))
        else:
            lines.extend(
                [
                    "No canonical Evidence Graph claim is linked to this company in this snapshot, so there is no relevant Evidence Card to display for this selected profile.",
                    "",
                    "This absence does not mean the company is clean, safe, peaceful, or free of relevant activity. Read the coverage states above.",
                    "",
                    "### Challenge / correction",
                    "",
                    f"- Open a correction/challenge issue and cite entity_id=`{entity_id}`, the screening SHA-256, and the source/coverage state being challenged.",
                    f"- Path: {CHALLENGE_URL}",
                    "",
                ]
            )

    rendered = "\n".join(lines).rstrip() + "\n"
    return rendered
