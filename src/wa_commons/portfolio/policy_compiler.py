from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping


EXPECTED_DECISIONS = {"EXCLUDE", "WATCH", "NONE"}
EXPECTED_ARMS = ("P0", "P1", "P2")


def load_policy_compiler_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _failure(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "artifact_version": None,
        "arms": [],
        "manifest": {"paper_only": True, "real_money_authority": False},
    }


def _config_status(config: Mapping[str, Any]) -> str | None:
    if config.get("market_data_inputs_allowed") is not False:
        return "BLOCK_POLICY_INSTRUCTION"
    arms = list(config.get("arms", []))
    if tuple(arm.get("arm_id") for arm in arms) != EXPECTED_ARMS:
        return "BLOCK_POLICY_INSTRUCTION"
    for arm in arms:
        multipliers = arm.get("decision_multipliers", {})
        if set(multipliers) != EXPECTED_DECISIONS:
            return "BLOCK_POLICY_INSTRUCTION"
        for value in multipliers.values():
            try:
                number = Decimal(str(value))
            except InvalidOperation:
                return "BLOCK_POLICY_INSTRUCTION"
            if number < 0 or number > 1:
                return "BLOCK_POLICY_INSTRUCTION"
    return None


def _benchmark_identity_status(rows: list[Mapping[str, Any]]) -> str | None:
    security_ids: set[str] = set()
    entity_ids: set[str] = set()
    for row in rows:
        security_id = str(row.get("security_id", "")).strip()
        entity_id = str(row.get("canonical_entity_id", "")).strip()
        if not security_id or not entity_id or security_id in security_ids or entity_id in entity_ids:
            return "BLOCK_IDENTITY"
        if row.get("mapping_state") != "mapped":
            return "BLOCK_IDENTITY"
        if str(row.get("canonical_review_state", "")).upper() != "CONFIRMED":
            return "BLOCK_IDENTITY"
        security_ids.add(security_id)
        entity_ids.add(entity_id)
    return None


def _screening_index(
    screening: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[str | None, dict[str, Mapping[str, Any]]]:
    profile_id = contract.get("profile_id")
    profile_version = contract.get("profile_version")
    policy_sha = contract.get("policy_sha256")
    selected = [
        view for view in screening.get("views", [])
        if view.get("profile_id") == profile_id
        and str(view.get("profile_version")) == str(profile_version)
    ]
    index: dict[str, Mapping[str, Any]] = {}
    for view in selected:
        if view.get("policy_sha256") != policy_sha:
            return "BLOCK_INPUT_VERSION", {}
        entity_id = str(view.get("entity_id", "")).strip()
        if not entity_id or entity_id in index:
            return "BLOCK_IDENTITY", {}
        if str(view.get("identity_state", "")).lower() != "confirmed":
            return "BLOCK_IDENTITY", {}
        if view.get("decision") not in EXPECTED_DECISIONS:
            return "BLOCK_POLICY_INSTRUCTION", {}
        index[entity_id] = view
    return None, index


def _quantizer(config: Mapping[str, Any]) -> Decimal:
    decimals = int(config.get("numerical", {}).get("semantic_weight_decimals", 12))
    return Decimal(1).scaleb(-decimals)


def _format_decimal(value: Decimal, quantum: Decimal) -> str:
    return format(value.quantize(quantum), "f")


def _semantic_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _coverage_metrics(
    benchmark_rows: list[Mapping[str, Any]],
    screening_by_entity: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
    quantum: Decimal,
) -> tuple[dict[str, str], str]:
    states = ("observed", "no_match", "unknown", "unresolved_identity", "not_integrated")
    totals = {state: Decimal("0") for state in states}
    insufficient_states = set(config.get("unknown_handling", {}).get("insufficient_states", []))
    insufficient = Decimal("0")
    for row in benchmark_rows:
        weight = Decimal(str(row["benchmark_weight"]))
        view = screening_by_entity[str(row["canonical_entity_id"])]
        counts = dict(view.get("coverage_state_counts", {}))
        present = {state for state in states if int(counts.get(state, 0)) > 0}
        for state in present:
            totals[state] += weight
        if present & insufficient_states:
            insufficient += weight
    return (
        {state: _format_decimal(totals[state], quantum) for state in states},
        _format_decimal(insufficient, quantum),
    )


def _claim_refs(view: Mapping[str, Any], decision: str) -> tuple[list[str], list[str]]:
    claim_ids: set[str] = set()
    rule_refs: set[str] = set()
    for result in view.get("claim_results", []):
        if str(result.get("decision", "")) != decision:
            continue
        claim_id = str(result.get("claim_id", "")).strip()
        if claim_id:
            claim_ids.add(claim_id)
        for rule_ref in result.get("rule_refs", []):
            rule = str(rule_ref).strip()
            if rule:
                rule_refs.add(rule)
    return sorted(claim_ids), sorted(rule_refs)


def _instruction_id(record: Mapping[str, Any]) -> str:
    return "instruction:" + _semantic_sha256(record)[:24]


def _compile_arm(
    benchmark_rows: list[Mapping[str, Any]],
    screening_by_entity: Mapping[str, Mapping[str, Any]],
    arm: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any] | None:
    quantum = _quantizer(config)
    ordered = sorted(benchmark_rows, key=lambda row: str(row["security_id"]))
    multipliers = {
        key: Decimal(str(value)) for key, value in arm["decision_multipliers"].items()
    }
    staged: list[dict[str, Any]] = []
    instructions: list[dict[str, Any]] = []
    raw_total = Decimal("0")
    excluded_weight = Decimal("0")
    underweighted_weight = Decimal("0")
    neutral_weight = Decimal("0")

    for row in ordered:
        entity_id = str(row["canonical_entity_id"])
        view = screening_by_entity[entity_id]
        decision = str(view["decision"])
        benchmark_weight = Decimal(str(row["benchmark_weight"]))
        multiplier = multipliers[decision]
        raw_weight = benchmark_weight * multiplier
        instruction = (
            "EXCLUDE" if multiplier == 0
            else "UNDERWEIGHT" if multiplier < 1
            else "NEUTRAL"
        )
        claim_refs, rule_refs = _claim_refs(view, decision)
        instruction_base = {
            "arm_id": str(arm["arm_id"]),
            "security_id": str(row["security_id"]),
            "entity_id": entity_id,
            "source_decision": decision,
            "instruction": instruction,
            "multiplier": _format_decimal(multiplier, quantum),
            "source_evidence_refs": claim_refs,
            "source_rule_refs": rule_refs,
        }
        instruction_record = {
            **instruction_base,
            "instruction_id": _instruction_id(instruction_base),
        }
        instructions.append(instruction_record)
        if instruction == "EXCLUDE":
            excluded_weight += benchmark_weight
        elif instruction == "UNDERWEIGHT":
            underweighted_weight += benchmark_weight
        else:
            neutral_weight += benchmark_weight
        staged.append({
            "security_id": str(row["security_id"]),
            "entity_id": entity_id,
            "benchmark_weight": benchmark_weight,
            "decision": decision,
            "instruction": instruction,
            "multiplier": multiplier,
            "raw_weight": raw_weight,
            "instruction_id": instruction_record["instruction_id"],
        })
        raw_total += raw_weight

    if raw_total == 0:
        return None

    rounded_targets: dict[str, Decimal] = {}
    unrounded_targets: dict[str, Decimal] = {}
    for item in staged:
        target = item["raw_weight"] / raw_total
        unrounded_targets[item["security_id"]] = target
        rounded_targets[item["security_id"]] = target.quantize(quantum)

    residual = Decimal("1").quantize(quantum) - sum(rounded_targets.values())
    if residual:
        recipient = sorted(
            staged,
            key=lambda item: (-unrounded_targets[item["security_id"]], item["security_id"]),
        )[0]
        rounded_targets[recipient["security_id"]] += residual

    active_instruction_ids = sorted(
        row["instruction_id"] for row in instructions if row["instruction"] != "NEUTRAL"
    )
    target_rows: list[dict[str, Any]] = []
    active_share = Decimal("0")
    max_change = Decimal("0")
    changed_count = 0
    hhi = Decimal("0")
    holding_count = 0
    for item in staged:
        target = rounded_targets[item["security_id"]]
        benchmark_weight = item["benchmark_weight"].quantize(quantum)
        delta = target - benchmark_weight
        absolute_delta = abs(delta)
        active_share += absolute_delta / 2
        max_change = max(max_change, absolute_delta)
        if target > 0:
            holding_count += 1
        hhi += target * target
        if absolute_delta != 0:
            changed_count += 1
        if item["instruction"] != "NEUTRAL" and absolute_delta != 0:
            attribution_kind = "DIRECT_POLICY_INSTRUCTION"
            source_instruction_ids = [item["instruction_id"]]
        elif absolute_delta != 0:
            attribution_kind = "NORMALIZATION_REDISTRIBUTION"
            source_instruction_ids = active_instruction_ids
        else:
            attribution_kind = "NO_CHANGE"
            source_instruction_ids = []
        target_rows.append({
            "security_id": item["security_id"],
            "entity_id": item["entity_id"],
            "benchmark_weight": _format_decimal(benchmark_weight, quantum),
            "target_weight": _format_decimal(target, quantum),
            "allocation_delta": _format_decimal(delta, quantum),
            "decision": item["decision"],
            "instruction": item["instruction"],
            "multiplier": _format_decimal(item["multiplier"], quantum),
            "attribution": {
                "kind": attribution_kind,
                "source_instruction_ids": source_instruction_ids,
            },
        })

    coverage_weights, insufficient_weight = _coverage_metrics(
        ordered, screening_by_entity, config, quantum
    )
    semantic_target_sha = _semantic_sha256(target_rows)
    status = (
        "POLICY_TRANSMISSION_ZERO"
        if changed_count == 0
        else "POLICY_TRANSMISSION_OK"
    )
    return {
        "arm_id": arm["arm_id"],
        "allocation_policy_id": arm["allocation_policy_id"],
        "allocation_policy_version": arm["allocation_policy_version"],
        "status": status,
        "semantic_target_sha256": semantic_target_sha,
        "instructions": instructions,
        "target_weights": target_rows,
        "metrics": {
            "active_share": _format_decimal(active_share, quantum),
            "reallocation_mass": _format_decimal(active_share, quantum),
            "excluded_benchmark_weight": _format_decimal(excluded_weight, quantum),
            "underweighted_benchmark_weight": _format_decimal(underweighted_weight, quantum),
            "neutral_benchmark_weight": _format_decimal(neutral_weight, quantum),
            "changed_security_count": changed_count,
            "max_absolute_weight_change": _format_decimal(max_change, quantum),
            "holding_count": holding_count,
            "hhi": _format_decimal(hhi, quantum),
            "coverage_state_benchmark_weight": coverage_weights,
            "insufficient_coverage_benchmark_weight": insufficient_weight,
        },
    }


def compile_policy_family(
    benchmark_mapping: Mapping[str, Any],
    screening: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    config_status = _config_status(config)
    if config_status:
        return _failure(config_status)

    contract = dict(config.get("input_contract", {}))
    benchmark_sha = str(
        benchmark_mapping.get("manifest", {}).get("semantic_mapping_sha256", "")
    )
    screening_sha = str(screening.get("tse_screening_sha256", ""))
    if benchmark_sha != contract.get("benchmark_semantic_mapping_sha256"):
        return _failure("BLOCK_INPUT_VERSION")
    if screening_sha != contract.get("screening_sha256"):
        return _failure("BLOCK_INPUT_VERSION")

    benchmark_rows = list(benchmark_mapping.get("rows", []))
    identity_status = _benchmark_identity_status(benchmark_rows)
    if identity_status:
        return _failure(identity_status)

    screening_status, screening_by_entity = _screening_index(screening, contract)
    if screening_status:
        return _failure(screening_status)
    if any(
        str(row["canonical_entity_id"]) not in screening_by_entity
        for row in benchmark_rows
    ):
        return _failure("BLOCK_IDENTITY")

    arms: list[dict[str, Any]] = []
    for arm in config["arms"]:
        compiled = _compile_arm(benchmark_rows, screening_by_entity, arm, config)
        if compiled is None:
            return _failure("BLOCK_POLICY_INFEASIBLE")
        arms.append(compiled)

    return {
        "status": "FROZEN_POLICY_FAMILY",
        "artifact_version": config.get("artifact_version"),
        "arms": arms,
        "manifest": {
            "paper_only": True,
            "real_money_authority": False,
            "market_data_inputs_allowed": False,
            "policy_family_sha256": _semantic_sha256([
                {
                    "arm_id": arm["arm_id"],
                    "semantic_target_sha256": arm["semantic_target_sha256"],
                }
                for arm in arms
            ]),
        },
    }
