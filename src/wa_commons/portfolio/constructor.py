from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

import cvxpy as cp
import numpy as np


EXPECTED_CONSTRUCTOR_ID = "benchmark-l2-projection"
EXPECTED_CONSTRUCTOR_VERSION = "0.1"
ALLOWED_MAPPING_STATES = {"mapped", "unmapped", "disputed"}
ALLOWED_DECISIONS = {"EXCLUDE", "WATCH", "NONE"}
ALLOWED_PREFERENCE_DIRECTIONS = {"prefer", "avoid"}


def load_constructor_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def semantic_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_config(config: dict[str, Any]) -> None:
    if config.get("constructor_id") != EXPECTED_CONSTRUCTOR_ID:
        raise ValueError("unsupported constructor_id")
    if config.get("constructor_version") != EXPECTED_CONSTRUCTOR_VERSION:
        raise ValueError("unsupported constructor_version")
    if config.get("paper_only") is not True:
        raise ValueError("constructor must be paper-only")


def _ordered_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["security_id"])
    ids = [row["security_id"] for row in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate security_id")
    return ordered


def _validate_benchmark(ordered: list[dict[str, Any]], config: dict[str, Any]) -> np.ndarray:
    weights = np.array([float(row["benchmark_weight"]) for row in ordered], dtype=float)
    if not np.all(np.isfinite(weights)):
        raise ValueError("benchmark weights must be finite")
    if np.any(weights < 0):
        raise ValueError("benchmark weights must be non-negative")
    tolerance = float(config["numerical"]["input_weight_tolerance"])
    if not math.isclose(float(weights.sum()), 1.0, abs_tol=tolerance, rel_tol=0.0):
        raise ValueError("benchmark weights do not reconcile to 1.0")
    return weights


def _classify_rows(
    ordered: list[dict[str, Any]],
) -> tuple[set[int], list[int], bool]:
    excluded: set[int] = set()
    unmapped: list[int] = []
    disputed = False

    for index, row in enumerate(ordered):
        mapping_state = row.get("mapping_state")
        if mapping_state not in ALLOWED_MAPPING_STATES:
            raise ValueError(f"unsupported mapping_state: {mapping_state}")
        if mapping_state == "disputed":
            disputed = True
            continue
        if mapping_state == "unmapped":
            unmapped.append(index)
            continue

        decision = row.get("decision")
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(f"mapped row lacks valid decision: {row['security_id']}")
        if decision == "EXCLUDE":
            excluded.add(index)

    return excluded, unmapped, disputed


def _aggregate_preference(signals: list[dict[str, Any]]) -> tuple[float, list[dict[str, Any]]]:
    unique: dict[str, tuple[str, float]] = {}
    for signal in signals:
        rule_id = signal.get("rule_id")
        direction = signal.get("direction")
        weight = float(signal.get("weight"))
        if not isinstance(rule_id, str) or not rule_id:
            raise ValueError("preference signal requires non-empty rule_id")
        if direction not in ALLOWED_PREFERENCE_DIRECTIONS:
            raise ValueError(f"unsupported preference direction: {direction}")
        if not math.isfinite(weight) or not (0 < weight <= 1):
            raise ValueError("preference weight must be finite and in (0, 1]")
        definition = (direction, weight)
        previous = unique.get(rule_id)
        if previous is not None and previous != definition:
            raise ValueError(f"conflicting preference definition for rule_id: {rule_id}")
        unique[rule_id] = definition

    signed = 0.0
    normalized: list[dict[str, Any]] = []
    for rule_id in sorted(unique):
        direction, weight = unique[rule_id]
        signed += weight if direction == "prefer" else -weight
        normalized.append({"rule_id": rule_id, "direction": direction, "weight": weight})
    score = max(-1.0, min(1.0, signed))
    return round(score, 12), normalized


def _build_reference(
    ordered: list[dict[str, Any]],
    benchmark: np.ndarray,
    excluded: set[int],
    unmapped: list[int],
    config: dict[str, Any],
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    reference = benchmark.copy()
    preference_scores: list[dict[str, Any]] = []
    tilt_strength = float(config["preference"]["tilt_strength"])
    unmapped_set = set(unmapped)

    for index, row in enumerate(ordered):
        if index in excluded:
            reference[index] = 0.0
            continue
        if index in unmapped_set:
            continue
        score, unique_signals = _aggregate_preference(row.get("preference_signals", []))
        if unique_signals:
            reference[index] *= 1.0 + tilt_strength * score
            preference_scores.append(
                {
                    "security_id": row["security_id"],
                    "score": score,
                    "signals": unique_signals,
                }
            )

    total = float(reference.sum())
    if total <= 0:
        return reference, preference_scores
    return reference / total, preference_scores


def _solver_options(config: dict[str, Any]) -> dict[str, Any]:
    solver = config["solver"]
    return {
        "eps_abs": float(solver["eps_abs"]),
        "eps_rel": float(solver["eps_rel"]),
        "max_iter": int(solver["max_iter"]),
        "polishing": bool(solver["polishing"]),
        "adaptive_rho": bool(solver["adaptive_rho"]),
    }


def _solve_weights(
    reference: np.ndarray,
    config: dict[str, Any],
    excluded: set[int] | None = None,
) -> tuple[str, np.ndarray | None, dict[str, Any]]:
    excluded = excluded or set()
    weights = cp.Variable(len(reference))
    max_weight = float(config["constraints"]["max_single_name_weight"])
    constraints = [
        cp.sum(weights) == 1,
        weights >= 0,
        weights <= max_weight,
    ]
    constraints.extend(weights[index] == 0 for index in sorted(excluded))
    problem = cp.Problem(cp.Minimize(cp.sum_squares(weights - reference)), constraints)
    problem.solve(
        solver=config["solver"]["name"],
        warm_start=bool(config["solver"]["warm_start"]),
        verbose=False,
        **_solver_options(config),
    )
    diagnostics = {
        "objective_value": None if problem.value is None else float(problem.value),
        "iterations": problem.solver_stats.num_iters,
    }
    if weights.value is None:
        return problem.status, None, diagnostics
    return problem.status, np.asarray(weights.value, dtype=float), diagnostics


def _validate_raw_solution(
    weights: np.ndarray,
    config: dict[str, Any],
    excluded: set[int],
) -> None:
    tolerance = float(config["numerical"]["output_invariant_tolerance"])
    cap = float(config["constraints"]["max_single_name_weight"])
    if not math.isclose(float(weights.sum()), 1.0, abs_tol=tolerance, rel_tol=0.0):
        raise ValueError("solver weights do not sum to 1")
    if float(weights.min()) < -tolerance:
        raise ValueError("solver emitted a negative weight")
    if float(weights.max()) > cap + tolerance:
        raise ValueError("solver exceeded max_single_name_weight")
    if any(abs(float(weights[index])) > tolerance for index in excluded):
        raise ValueError("solver emitted non-zero EXCLUDE weight")


def _canonicalize_weights(
    security_ids: list[str],
    weights: np.ndarray,
    config: dict[str, Any],
    excluded: set[int],
) -> list[str]:
    decimals = int(config["numerical"]["semantic_weight_decimals"])
    quantum = Decimal(1).scaleb(-decimals)
    cap = Decimal(str(config["constraints"]["max_single_name_weight"])).quantize(
        quantum,
        rounding=ROUND_HALF_EVEN,
    )
    canonical = [
        Decimal(str(float(weight))).quantize(quantum, rounding=ROUND_HALF_EVEN)
        for weight in weights
    ]
    for index in excluded:
        canonical[index] = Decimal("0").quantize(quantum)

    residual = Decimal("1").quantize(quantum) - sum(canonical)
    if residual:
        candidates = sorted(
            (index for index in range(len(canonical)) if index not in excluded),
            key=lambda index: (-canonical[index], security_ids[index]),
        )
        for index in candidates:
            adjusted = canonical[index] + residual
            if Decimal("0") <= adjusted <= cap:
                canonical[index] = adjusted
                break
        else:
            raise ValueError("no canonical residual recipient satisfies weight bounds")
    if sum(canonical) != Decimal("1").quantize(quantum):
        raise ValueError("canonical weights do not sum to 1")
    if min(canonical) < 0 or max(canonical) > cap:
        raise ValueError("canonical weights violate bounds")
    if any(canonical[index] != 0 for index in excluded):
        raise ValueError("canonical EXCLUDE weight is non-zero")
    return [f"{value:.{decimals}f}" for value in canonical]


def _format_weight(value: float, config: dict[str, Any]) -> str:
    decimals = int(config["numerical"]["semantic_weight_decimals"])
    quantum = Decimal(1).scaleb(-decimals)
    return f"{Decimal(str(float(value))).quantize(quantum, rounding=ROUND_HALF_EVEN):.{decimals}f}"


def _failure(status: str, *, solver_status: str | None = None) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "paper_only": True,
        "real_money_authority": False,
    }
    if solver_status is not None:
        manifest["solver_status"] = solver_status
    return {"status": status, "target_weights": [], "manifest": manifest}


def construct_paper_portfolio(
    rows: list[dict[str, Any]],
    provenance: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Construct the bounded v0.1 paper portfolio from benchmark/policy rows."""

    _validate_config(config)
    ordered = _ordered_rows(rows)
    benchmark = _validate_benchmark(ordered, config)
    excluded, unmapped, disputed = _classify_rows(ordered)
    if disputed:
        return _failure("INVALID_INPUT_DISPUTED_IDENTITY")

    eligible_count = len(ordered) - len(excluded)
    if eligible_count == 0:
        return _failure("INFEASIBLE_ALL_EXCLUDED")
    max_weight = float(config["constraints"]["max_single_name_weight"])
    feasibility_tolerance = float(config["numerical"]["feasibility_tolerance"])
    if eligible_count * max_weight < 1.0 - feasibility_tolerance:
        return _failure("INFEASIBLE_DIVERSIFICATION_CAP")

    reference, preference_scores = _build_reference(
        ordered,
        benchmark,
        excluded,
        unmapped,
        config,
    )
    if float(reference.sum()) <= 0:
        return _failure("INFEASIBLE_ALL_EXCLUDED")

    status, raw_weights, diagnostics = _solve_weights(reference, config, excluded)
    if status != cp.OPTIMAL or raw_weights is None:
        return _failure("SOLVER_FAILURE", solver_status=status)

    _validate_raw_solution(raw_weights, config, excluded)
    security_ids = [row["security_id"] for row in ordered]
    canonical = _canonicalize_weights(security_ids, raw_weights, config, excluded)
    target_weights = [
        {"security_id": security_id, "target_weight": weight}
        for security_id, weight in zip(security_ids, canonical, strict=True)
    ]

    excluded_weight = float(sum(benchmark[index] for index in excluded))
    unscreened_weight = float(sum(benchmark[index] for index in unmapped))
    return {
        "status": "OPTIMAL",
        "target_weights": target_weights,
        "manifest": {
            "constructor_id": config["constructor_id"],
            "constructor_version": config["constructor_version"],
            "paper_only": True,
            "real_money_authority": False,
            "solver_status": status,
            "solver_objective": diagnostics["objective_value"],
            "solver_iterations": diagnostics["iterations"],
            "excluded_benchmark_weight": _format_weight(excluded_weight, config),
            "unmapped_count": len(unmapped),
            "unscreened_benchmark_weight": _format_weight(unscreened_weight, config),
            "preference_scores": preference_scores,
            "provenance": dict(provenance),
        },
    }
