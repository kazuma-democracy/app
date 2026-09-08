# Issue #49 Paper Portfolio Constructor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the preregistered `benchmark-l2-projection-v0.1` constructor from Issue #47 as a deterministic, paper-only WA Commons component.

**Architecture:** Add a small `wa_commons.portfolio` package with one pure constructor module. It validates normalized benchmark/policy rows, builds the bounded policy-adjusted reference, solves the fixed strictly-convex L2 projection through CVXPY/OSQP, canonicalizes weights deterministically, and emits a provenance-rich manifest. Configuration lives in a versioned JSON artifact validated by a JSON Schema; no market-data, return, broker, order, credential, or real-money surface is added.

**Tech Stack:** Python 3.11, CVXPY 1.9.2, OSQP Python 1.1.3, NumPy/SciPy transitively via CVXPY, pytest, jsonschema for config-schema tests.

**Spec:** `docs/results/M3_2C_CONSTRUCTOR_DESIGN_V01.md`

## Global Constraints

- Constructor ID/version: `benchmark-l2-projection` / `0.1`.
- CVXPY exactly `1.9.2`; OSQP Python exactly `1.1.3`.
- Inputs are benchmark weights plus existing WA policy outputs only.
- No expected returns, covariance, historical returns, market-data download, broker API, credentials, orders, or real-money authority.
- `EXCLUDE = 0`; `WATCH` and `NONE` remain eligible and receive no automatic penalty.
- `NONE` is not PASS/clean/safe.
- Unmapped securities remain eligible with no tilt and are reported as unscreened.
- Any disputed mapping fails closed.
- Soft preferences are de-duplicated by `rule_id`, mapped to signed weights, summed, clamped to `[-1, 1]`, and applied with fixed `tilt_strength = 0.5`.
- Optimization: minimize `sum_squares(w - t)` subject to full investment, long-only, hard 10% single-name cap, and EXCLUDE zero.
- Accept only solver status `OPTIMAL`; never relax constraints automatically.
- Canonical weights: 12 decimals, Decimal `ROUND_HALF_EVEN`, residual assigned deterministically to a non-EXCLUDE security with sufficient headroom.
- Semantic hash must be independent of input row order.
- Focused #49 tests first; full CI only at final PR gate.

---

### Task 1: Basic deterministic benchmark projection

**Files:**
- Create: `tests/test_paper_portfolio_constructor.py`
- Create: `src/wa_commons/portfolio/__init__.py`
- Create: `src/wa_commons/portfolio/constructor.py`
- Create: `configs/portfolio/benchmark-l2-projection-v0.1.json`
- Create: `schemas/paper-portfolio-constructor.v0.1.schema.json`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: `rows: list[dict]`, `provenance: dict`, `config: dict`.
- Produces: `construct_paper_portfolio(rows, provenance, config) -> dict` with `status`, `target_weights`, and `manifest`.
- Produces: `load_constructor_config(path) -> dict` and `semantic_hash(payload) -> str`.

- [ ] **Step 1: Write the failing no-policy test**

```python
from decimal import Decimal

from wa_commons.portfolio.constructor import construct_paper_portfolio


def _rows(n=20):
    return [
        {
            "security_id": f"TSE:{1000+i}",
            "benchmark_weight": 1 / n,
            "mapping_state": "mapped",
            "decision": "NONE",
            "preference_signals": [],
        }
        for i in range(n)
    ]


def _provenance():
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


def test_no_policy_fixture_reproduces_benchmark(default_config):
    result = construct_paper_portfolio(_rows(), _provenance(), default_config)
    assert result["status"] == "OPTIMAL"
    assert [Decimal(row["target_weight"]) for row in result["target_weights"]] == [
        Decimal("0.050000000000")
    ] * 20
    assert result["manifest"]["paper_only"] is True
    assert result["manifest"]["real_money_authority"] is False
```

- [ ] **Step 2: Open a draft PR and verify RED**

Expected focused failure: import error because `wa_commons.portfolio.constructor` does not yet exist.

- [ ] **Step 3: Add pinned dependencies, config/schema, and minimal constructor**

`pyproject.toml` project dependencies gain:

```toml
"cvxpy==1.9.2",
"osqp==1.1.3"
```

The constructor must:

```python
def construct_paper_portfolio(rows, provenance, config):
    ordered = sorted(rows, key=lambda row: row["security_id"])
    benchmark = np.array([float(row["benchmark_weight"]) for row in ordered])
    # validate sum/nonnegative/duplicates and v0.1 config identity
    # build t from benchmark when no exclusions/preferences apply
    w = cp.Variable(len(ordered))
    constraints = [cp.sum(w) == 1, w >= 0, w <= config["constraints"]["max_single_name_weight"]]
    problem = cp.Problem(cp.Minimize(cp.sum_squares(w - t)), constraints)
    problem.solve(solver="OSQP", warm_start=False, **solver_options)
    # accept only cp.OPTIMAL, canonicalize, hash, emit manifest
```

- [ ] **Step 4: Verify focused GREEN**

Expected: no-policy fixture reproduces all 20 benchmark weights exactly at semantic precision.

---

### Task 2: Policy and identity semantics

**Files:**
- Modify: `tests/test_paper_portfolio_constructor.py`
- Modify: `src/wa_commons/portfolio/constructor.py`

**Interfaces:**
- `EXCLUDE`: exact canonical zero.
- `WATCH`/`NONE`: eligibility unchanged unless an explicit preference signal applies.
- `unmapped`: eligible, no tilt, manifest unscreened weight/count.
- `disputed`: input error with no target portfolio.

- [ ] **Step 1: Add failing policy tests**

```python
def test_exclude_is_zero_and_weight_is_redistributed(default_config):
    rows = _rows()
    rows[0]["decision"] = "EXCLUDE"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weights = {row["security_id"]: row["target_weight"] for row in result["target_weights"]}
    assert weights["TSE:1000"] == "0.000000000000"
    assert result["manifest"]["excluded_benchmark_weight"] == "0.050000000000"
    assert sum(Decimal(v) for v in weights.values()) == Decimal("1.000000000000")


def test_watch_and_none_are_not_automatic_penalties(default_config):
    rows = _rows()
    rows[0]["decision"] = "WATCH"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weights = {row["security_id"]: row["target_weight"] for row in result["target_weights"]}
    assert weights["TSE:1000"] == "0.050000000000"
    assert weights["TSE:1001"] == "0.050000000000"


def test_unmapped_stays_eligible_and_unscreened(default_config):
    rows = _rows()
    rows[0] = {
        "security_id": "TSE:1000",
        "benchmark_weight": 0.05,
        "mapping_state": "unmapped",
        "preference_signals": [],
    }
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    assert result["manifest"]["unmapped_count"] == 1
    assert result["manifest"]["unscreened_benchmark_weight"] == "0.050000000000"


def test_disputed_identity_fails_closed(default_config):
    rows = _rows()
    rows[0]["mapping_state"] = "disputed"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    assert result["status"] == "INVALID_INPUT_DISPUTED_IDENTITY"
    assert result["target_weights"] == []
```

- [ ] **Step 2: Verify RED**

Expected failures: current minimal constructor lacks EXCLUDE/policy/mapping behavior.

- [ ] **Step 3: Implement policy/identity behavior**

Use explicit helpers:

```python
def _aggregate_preference(signals): ...
def _build_reference(ordered_rows, config): ...
def _validate_rows(ordered_rows, config): ...
```

EXCLUDE overrides preferences; WATCH/NONE do not create automatic multipliers; unmapped multiplier is exactly 1.0; disputed returns an explicit fail-closed status.

- [ ] **Step 4: Verify focused GREEN**

---

### Task 3: Preference aggregation and infeasibility/failure modes

**Files:**
- Modify: `tests/test_paper_portfolio_constructor.py`
- Modify: `src/wa_commons/portfolio/constructor.py`

**Interfaces:**
- Preference aggregation is unique-rule signed sum clamp.
- Strongest soft avoid retains positive reference/target absent other binding constraints.
- All excluded and too-few-eligible cases fail before solve.
- Non-OPTIMAL solver result produces no target.

- [ ] **Step 1: Add failing preference and infeasibility tests**

```python
def test_preference_signals_deduplicate_by_rule_id(default_config):
    rows = _rows()
    rows[0]["preference_signals"] = [
        {"rule_id": "r1", "direction": "prefer", "weight": 0.4},
        {"rule_id": "r1", "direction": "prefer", "weight": 0.4},
        {"rule_id": "r2", "direction": "avoid", "weight": 0.1},
    ]
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    entry = next(x for x in result["manifest"]["preference_scores"] if x["security_id"] == "TSE:1000")
    assert entry["score"] == 0.3


def test_strongest_soft_avoid_remains_nonzero(default_config):
    rows = _rows()
    rows[0]["preference_signals"] = [{"rule_id": "r1", "direction": "avoid", "weight": 1.0}]
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weight = next(Decimal(x["target_weight"]) for x in result["target_weights"] if x["security_id"] == "TSE:1000")
    assert weight > 0


def test_all_excluded_fails_closed(default_config):
    rows = _rows()
    for row in rows:
        row["decision"] = "EXCLUDE"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    assert result["status"] == "INFEASIBLE_ALL_EXCLUDED"
    assert result["target_weights"] == []


def test_too_few_eligible_for_cap_fails_closed(default_config):
    rows = _rows()
    for row in rows[9:]:
        row["decision"] = "EXCLUDE"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    assert result["status"] == "INFEASIBLE_DIVERSIFICATION_CAP"
    assert result["target_weights"] == []
```

Add an injectable private solver boundary for one regression test only:

```python
def test_non_optimal_solver_status_emits_no_portfolio(default_config, monkeypatch):
    monkeypatch.setattr(constructor, "_solve_weights", lambda *args, **kwargs: ("optimal_inaccurate", None, {}))
    result = constructor.construct_paper_portfolio(_rows(), _provenance(), default_config)
    assert result["status"] == "SOLVER_FAILURE"
    assert result["target_weights"] == []
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement deterministic preference aggregation and fail-closed gates**

- [ ] **Step 4: Verify focused GREEN**

---

### Task 4: Canonicalization, manifest, schema, and capability boundary

**Files:**
- Modify: `tests/test_paper_portfolio_constructor.py`
- Modify: `src/wa_commons/portfolio/constructor.py`
- Modify: `src/wa_commons/portfolio/__init__.py`
- Verify: `configs/portfolio/benchmark-l2-projection-v0.1.json`
- Verify: `schemas/paper-portfolio-constructor.v0.1.schema.json`

**Interfaces:**
- Stable semantic hash over canonical target/config/provenance.
- Row-order permutations yield identical target/hash.
- Manifest records exact runtime/solver/config/provenance and policy/mapping summaries.
- Package exposes constructor/config loader only; no execution/trading interface.

- [ ] **Step 1: Add failing determinism/schema/capability tests**

```python
def test_input_order_does_not_change_target_or_hash(default_config):
    rows = _rows()
    forward = construct_paper_portfolio(rows, _provenance(), default_config)
    reverse = construct_paper_portfolio(list(reversed(rows)), _provenance(), default_config)
    assert forward["target_weights"] == reverse["target_weights"]
    assert forward["manifest"]["semantic_target_hash"] == reverse["manifest"]["semantic_target_hash"]


def test_canonical_weights_obey_all_invariants(default_config):
    rows = _rows()
    rows[0]["decision"] = "EXCLUDE"
    result = construct_paper_portfolio(rows, _provenance(), default_config)
    weights = [Decimal(x["target_weight"]) for x in result["target_weights"]]
    assert sum(weights) == Decimal("1.000000000000")
    assert min(weights) >= 0
    assert max(weights) <= Decimal("0.100000000000")


def test_fixed_fixture_semantic_hash_repeats(default_config):
    first = construct_paper_portfolio(_rows(), _provenance(), default_config)
    second = construct_paper_portfolio(_rows(), _provenance(), default_config)
    assert first["manifest"]["semantic_target_hash"] == second["manifest"]["semantic_target_hash"]


def test_config_matches_schema(default_config, constructor_schema):
    jsonschema.validate(default_config, constructor_schema)


def test_portfolio_package_has_no_real_money_interfaces():
    import wa_commons.portfolio as portfolio
    forbidden = {"buy", "sell", "order", "broker", "execute_trade", "place_order", "credentials"}
    assert forbidden.isdisjoint(set(dir(portfolio)))
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Complete canonicalization and manifest**

Semantic hash payload must contain only deterministic semantic data:

```python
{
    "constructor_id": config["constructor_id"],
    "constructor_version": config["constructor_version"],
    "config_hash": config_hash,
    "provenance": provenance,
    "target_weights": canonical_target_weights,
}
```

Hash with UTF-8 JSON using `sort_keys=True`, compact separators and `ensure_ascii=False`, SHA-256 hex digest.

Manifest includes required counts/weights, config hash, solver status/objective/iterations, Python/CVXPY/OSQP/NumPy/SciPy versions, target min/max/sum, semantic hash, `paper_only=true`, `real_money_authority=false`.

- [ ] **Step 4: Verify focused GREEN**

Run only:

```text
python -m pytest -q tests/test_paper_portfolio_constructor.py
```

- [ ] **Step 5: Inspect bounded diff and run final CI gate**

Expected changed paths only:

```text
docs/superpowers/plans/2026-09-08-issue-49-paper-constructor.md
pyproject.toml
configs/portfolio/benchmark-l2-projection-v0.1.json
schemas/paper-portfolio-constructor.v0.1.schema.json
src/wa_commons/portfolio/__init__.py
src/wa_commons/portfolio/constructor.py
tests/test_paper_portfolio_constructor.py
```

Final PR gate runs repository CI once. No benchmark ingestion, historical performance, CLI trading, broker, order, or credential code is permitted.
