from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

import wa_commons.portfolio.constructor as constructor
from wa_commons.portfolio.constructor import construct_paper_portfolio


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def default_config() -> dict:
    return json.loads(
        (ROOT / "configs/portfolio/benchmark-l2-projection-v0.1.json").read_text(
            encoding="utf-8"
        )
    )


def _rows(n: int = 20) -> list[dict]:
    return [
        {
            "security_id": f"TSE:{1000 + i}",
            "benchmark_weight": 1 / n,
            "mapping_state": "mapped",
            "decision": "NONE",
            "preference_signals": [],
        }
        for i in range(n)
    ]


def _provenance() -> dict:
    return {
        "benchmark_id": "fixture:benchmark",
        "benchmark_snapshot": "fixture:v1",
        "benchmark_hash": "b" * 64,
        "policy_profile_id": "fixture-policy",
        "policy_profile_version": "0.1",
        "policy_hash": "p" * 64,
        "evidence_snapshot": "fixture:evidence",
        "screening_snapshot": "fixture:screening",
    }


def test_no_policy_fixture_reproduces_benchmark(default_config: dict) -> None:
    result = construct_paper_portfolio(_rows(), _provenance(), default_config)

    assert result["status"] == "OPTIMAL"
    assert [Decimal(row["target_weight"]) for row in result["target_weights"]] == [
        Decimal("0.050000000000")
    ] * 20
    assert result["manifest"]["paper_only"] is True
    assert result["manifest"]["real_money_authority"] is False


def test_exclude_is_zero_and_weight_is_redistributed(default_config: dict) -> None:
    rows = _rows()
    rows[0]["decision"] = "EXCLUDE"

    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weights = {row["security_id"]: row["target_weight"] for row in result["target_weights"]}

    assert weights["TSE:1000"] == "0.000000000000"
    assert result["manifest"]["excluded_benchmark_weight"] == "0.050000000000"
    assert sum(Decimal(value) for value in weights.values()) == Decimal("1.000000000000")


def test_watch_and_none_are_not_automatic_penalties(default_config: dict) -> None:
    rows = _rows()
    rows[0]["decision"] = "WATCH"

    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weights = {row["security_id"]: row["target_weight"] for row in result["target_weights"]}

    assert weights["TSE:1000"] == "0.050000000000"
    assert weights["TSE:1001"] == "0.050000000000"


def test_unmapped_stays_eligible_and_unscreened(default_config: dict) -> None:
    rows = _rows()
    rows[0] = {
        "security_id": "TSE:1000",
        "benchmark_weight": 0.05,
        "mapping_state": "unmapped",
        "preference_signals": [],
    }

    result = construct_paper_portfolio(rows, _provenance(), default_config)

    assert result["status"] == "OPTIMAL"
    assert result["manifest"]["unmapped_count"] == 1
    assert result["manifest"]["unscreened_benchmark_weight"] == "0.050000000000"


def test_disputed_identity_fails_closed(default_config: dict) -> None:
    rows = _rows()
    rows[0]["mapping_state"] = "disputed"

    result = construct_paper_portfolio(rows, _provenance(), default_config)

    assert result["status"] == "INVALID_INPUT_DISPUTED_IDENTITY"
    assert result["target_weights"] == []


def test_preference_signals_deduplicate_by_rule_id(default_config: dict) -> None:
    rows = _rows()
    rows[0]["preference_signals"] = [
        {"rule_id": "r1", "direction": "prefer", "weight": 0.4},
        {"rule_id": "r1", "direction": "prefer", "weight": 0.4},
        {"rule_id": "r2", "direction": "avoid", "weight": 0.1},
    ]

    result = construct_paper_portfolio(rows, _provenance(), default_config)
    entry = next(
        item
        for item in result["manifest"]["preference_scores"]
        if item["security_id"] == "TSE:1000"
    )

    assert entry["score"] == 0.3


def test_strongest_soft_avoid_remains_nonzero(default_config: dict) -> None:
    rows = _rows()
    rows[0]["preference_signals"] = [
        {"rule_id": "r1", "direction": "avoid", "weight": 1.0}
    ]

    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weight = next(
        Decimal(item["target_weight"])
        for item in result["target_weights"]
        if item["security_id"] == "TSE:1000"
    )

    assert weight > 0


def test_all_excluded_fails_closed(default_config: dict) -> None:
    rows = _rows()
    for row in rows:
        row["decision"] = "EXCLUDE"

    result = construct_paper_portfolio(rows, _provenance(), default_config)

    assert result["status"] == "INFEASIBLE_ALL_EXCLUDED"
    assert result["target_weights"] == []


def test_too_few_eligible_for_cap_fails_closed(default_config: dict) -> None:
    rows = _rows()
    for row in rows[9:]:
        row["decision"] = "EXCLUDE"

    result = construct_paper_portfolio(rows, _provenance(), default_config)

    assert result["status"] == "INFEASIBLE_DIVERSIFICATION_CAP"
    assert result["target_weights"] == []


def test_non_optimal_solver_status_emits_no_portfolio(
    default_config: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        constructor,
        "_solve_weights",
        lambda *args, **kwargs: ("optimal_inaccurate", None, {}),
    )

    result = constructor.construct_paper_portfolio(_rows(), _provenance(), default_config)

    assert result["status"] == "SOLVER_FAILURE"
    assert result["target_weights"] == []
