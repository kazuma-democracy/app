from __future__ import annotations

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
        view
        for view in screening.get("views", [])
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

    return {
        "status": "FROZEN_POLICY_FAMILY",
        "artifact_version": config.get("artifact_version"),
        "arms": [],
        "manifest": {"paper_only": True, "real_money_authority": False},
    }
