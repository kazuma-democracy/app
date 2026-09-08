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
) -> tuple[str, np.ndarray | None, dict[str, Any]]:
    weights = cp.Variable(len(reference))
    max_weight = float(config["constraints"]["max_single_name_weight"])
    problem = cp.Problem(
        cp.Minimize(cp.sum_squares(weights - reference)),
        [
            cp.sum(weights) == 1,
            weights >= 0,
            weights <= max_weight,
        ],
    )
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


def _validate_raw_solution(weights: np.ndarray, config: dict[str, Any]) -> None:
    tolerance = float(config["numerical"]["output_invariant_tolerance"])
    cap = float(config["constraints"]["max_single_name_weight"])
    if not math.isclose(float(weights.sum()), 1.0, abs_tol=tolerance, rel_tol=0.0):
        raise ValueError("solver weights do not sum to 1")
    if float(weights.min()) < -tolerance:
        raise ValueError("solver emitted a negative weight")
    if float(weights.max()) > cap + tolerance:
        raise ValueError("solver exceeded max_single_name_weight")


def _canonicalize_weights(
    security_ids: list[str],
    weights: np.ndarray,
    config: dict[str, Any],
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
    residual = Decimal("1").quantize(quantum) - sum(canonical)
    if residual:
        candidates = sorted(
            range(len(canonical)),
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
    return [f"{value:.{decimals}f}" for value in canonical]


def construct_paper_portfolio(
    rows: list[dict[str, Any]],
    provenance: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Construct the bounded v0.1 paper portfolio from benchmark weights.

    The first TDD increment intentionally covers the no-policy case only. Policy,
    identity and preference semantics are added by subsequent focused increments.
    """

    _validate_config(config)
    ordered = _ordered_rows(rows)
    benchmark = _validate_benchmark(ordered, config)
    status, raw_weights, diagnostics = _solve_weights(benchmark, config)
    if status != cp.OPTIMAL or raw_weights is None:
        return {
            "status": "SOLVER_FAILURE",
            "target_weights": [],
            "manifest": {
                "paper_only": True,
                "real_money_authority": False,
                "solver_status": status,
            },
        }
    _validate_raw_solution(raw_weights, config)
    security_ids = [row["security_id"] for row in ordered]
    canonical = _canonicalize_weights(security_ids, raw_weights, config)
    target_weights = [
        {"security_id": security_id, "target_weight": weight}
        for security_id, weight in zip(security_ids, canonical, strict=True)
    ]
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
            "provenance": dict(provenance),
        },
    }
