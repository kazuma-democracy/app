# M3.2c minimum paper-portfolio constructor v0.1

Status: **ADOPT — benchmark L2 projection on CVXPY/OSQP**  
Issue: #47  
Decision date: 2026-09-08  
Decision basis: OSS/design review only; **no historical portfolio-performance result was inspected**.

## Decision

WA Commons adopts `benchmark-l2-projection-v0.1` as the first paper-portfolio constructor.

The #49 implementation must use:

- **CVXPY 1.9.2** as the convex-modeling layer;
- **OSQP Python 1.1.3** as the QP solver;
- benchmark weights plus existing WA Commons policy outputs only;
- no expected-return model, covariance matrix, historical-return input, market-data download, broker API, credentials, or real-money capability.

The constructor answers one bounded question: given a point-in-time benchmark and a user's explicit policy, what is the closest transparent long-only portfolio that satisfies hard exclusions, bounded soft preferences, full investment, and a simple diversification cap?

## OSS decision record

| Candidate | Evidence / fit | Decision |
|---|---|---|
| **CVXPY 1.9.2 + OSQP 1.1.3** | CVXPY is Apache-2.0, mature and active. It expresses exactly the small convex QP needed here. CVXPY 1.9.2 directly supports OSQP and declares OSQP as a normal dependency. | **ADOPT** |
| **PyPortfolioOpt** | MIT, mature and popular. It exposes ex-ante and ex-post tracking-error objectives, but those require a covariance matrix or historical asset/benchmark returns. Its broader finance abstractions are unnecessary for #49. | **WATCH** — reconsider only if a separately preregistered return/covariance-aware method is justified. |
| **skfolio** | BSD-3-Clause, active and comprehensive. Its portfolio/model-selection/risk surface is substantially larger than the one QP needed by v0.1. | **WATCH** — do not adopt prematurely. |
| **cvxportfolio** | Mature optimization/back-testing framework, but broader than #49 and GPL-3.0. It includes trading-policy/cost/forecast/backtest concerns outside this bounded task. | **REJECT for v0.1 dependency** — not a quality judgment. |
| **plain proportional renormalization** | Dependency-free and useful as a reference. Hard exclusions are easy, but max-weight caps, soft preferences and infeasibility quickly create custom redistribution logic. | **WATCH as a reference fixture**, not production constructor. |
| bespoke optimizer | Adds solver/numerical/failure-mode burden without an identified OSS gap. | **REJECT**. |

Repository evidence reviewed on 2026-09-08:

- CVXPY: https://github.com/cvxpy/cvxpy — Apache-2.0; reviewed release `v1.9.2`.
- CVXPY OSQP interface: https://github.com/cvxpy/cvxpy/blob/v1.9.2/cvxpy/reductions/solvers/qp_solvers/osqp_qpif.py.
- OSQP Python: https://github.com/osqp/osqp-python/releases/tag/v1.1.3.
- PyPortfolioOpt: https://github.com/PyPortfolio/PyPortfolioOpt — MIT; its `objective_functions.py` shows ex-ante tracking error requires covariance and ex-post tracking error requires historical returns.
- skfolio: https://github.com/skfolio/skfolio — BSD-3-Clause.
- cvxportfolio: https://github.com/cvxgrp/cvxportfolio — GPL-3.0.

## Upstream contracts preserved

#45 has already pinned TOPIX Total Return Index as the first benchmark. #47 does not change that choice.

#49 explicitly requires a deterministic paper-only component that accepts benchmark weights plus WA policy outputs, handles infeasibility without silent relaxation, preserves `EXCLUDE / WATCH / NONE`, and downloads no market data. This design stays inside that boundary.

The existing user-policy schema already defines soft preferences as `prefer` or `avoid` with a rule weight in `(0, 1]`. The existing evaluator emits `preference_signals` only for confirmed claims; unknown/disputed/expired claims are routed through uncertainty handling before preference evaluation. #49 must consume those existing outputs rather than inventing a second policy evaluator.

## Inputs

One stable row per benchmark security:

- `security_id` — stable deterministic sort key;
- `benchmark_weight` — finite non-negative point-in-time weight;
- `mapping_state` — `mapped`, `unmapped`, or `disputed`;
- for `mapped`, company policy decision `EXCLUDE`, `WATCH`, or `NONE`;
- for `mapped`, all confirmed-claim `preference_signals` already emitted by policy evaluation (`rule_id`, `direction`, `weight`).

Run-level provenance:

- benchmark ID/version/snapshot/hash references;
- policy profile ID/version/hash;
- evidence/screening snapshot references;
- constructor config/version/hash;
- when real point-in-time benchmark data is used, source effective/availability timestamps from #50.

## Validation — fail before optimization

Reject the run if:

- security IDs are duplicated;
- any benchmark weight is negative or non-finite;
- benchmark weights do not reconcile to `1.0` within the configured input tolerance;
- a mapped row lacks a valid policy decision;
- a preference signal has an invalid direction/weight;
- the same `rule_id` has conflicting direction/weight definitions for one entity;
- any row has `mapping_state = disputed`;
- the constructor config is incomplete or unknown.

Do not silently normalize a benchmark that failed input reconciliation. Do not coerce a disputed identity into either mapped or unmapped.

## Policy semantics

### EXCLUDE

Hard constraint: `w_i = 0`.

EXCLUDE overrides soft preferences. The manifest records excluded benchmark weight.

### WATCH

WATCH is **not** exclusion and creates no automatic weight penalty. The security stays eligible. A separately emitted confirmed-claim preference signal may still tilt it.

### NONE

NONE is **not PASS** and creates no automatic favorable treatment. The security stays eligible unless an explicit preference applies.

### Unmapped

An unmapped benchmark security stays eligible with no hard exclusion and no soft tilt. It is flagged `unscreened = true`; its benchmark weight must be reported separately in evaluation.

### Disputed

**v0.1 always fails closed if any benchmark-security identity is disputed.** There is no alternate disputed-as-unmapped path in this constructor version. A later rule change requires a new version.

## Soft preference aggregation

Soft preferences never become hidden exclusions.

For each mapped, non-EXCLUDE security:

1. collect all existing `preference_signals`;
2. de-duplicate by `rule_id` so repeated claim matches do not amplify one policy rule;
3. map `prefer` to `+weight` and `avoid` to `-weight`;
4. sum the signed unique-rule weights;
5. clamp the result to `[-1, +1]` as `preference_score_i`.

Fixed v0.1 tilt strength, chosen before performance inspection:

`preference_tilt_strength = 0.50`

Reference multiplier:

`m_i = 1 + 0.50 * preference_score_i`

Thus `m_i` is bounded in `[0.50, 1.50]`: even the strongest soft avoid cannot become zero, and the strongest prefer cannot exceed 1.5× before normalization.

Set:

- eligible: `r_i = benchmark_weight_i * m_i`;
- EXCLUDE: `r_i = 0`.

Normalize once:

`t_i = r_i / sum(r)`.

If `sum(r) == 0`, return `INFEASIBLE_ALL_EXCLUDED`. Do not create cash or weaken exclusions.

The 0.50 tilt is a versioned constructor parameter, not a moral score or factual confidence value. The primary v0.1 run must not tune it after seeing performance.

## Optimization problem

Let `w` be target weights and `t` the normalized policy-adjusted benchmark reference.

```text
minimize    Σ_i (w_i - t_i)^2

subject to
            Σ_i w_i = 1
            0 <= w_i <= 0.10
            w_i = 0             for EXCLUDE
```

The fixed v0.1 single-name cap is **10%**.

The squared L2 objective is strictly convex on a non-empty feasible affine set, avoiding the multiple-optimum tie problem of a pure L1 active-share objective.

No expected return, covariance, volatility, factor, sector, alpha, turnover, transaction-cost or tax term is in v0.1. Tracking difference/error is measured later under the preregistered M3 evaluation; it is not optimized here using market data that has not yet been adopted.

## Diversification / risk boundary

The constructor enforces only controls supported by current inputs:

- long-only;
- fully invested;
- 10% single-name cap;
- EXCLUDE = zero;
- bounded soft tilt.

Do not invent sector/factor constraints before canonical sector/factor inputs exist. Concentration, effective holdings, tracking difference/error, turnover and sector/factor drift where available remain evaluation outputs.

## Feasibility and solver failure

Pre-solver checks:

- at least one eligible security;
- `eligible_count * 0.10 >= 1 - feasibility_tolerance`;
- all validation rules passed.

After solve, accept **only `OPTIMAL`**.

`OPTIMAL_INACCURATE`, infeasible/inaccurate, unbounded/inaccurate, user-limit and solver-error statuses all produce no target portfolio. Never relax the cap, exclusions, identity rule, or preference semantics automatically.

## Solver/reproducibility contract

#49 should encode and hash this v0.1 configuration:

```json
{
  "schema_version": "0.1",
  "constructor_id": "benchmark-l2-projection",
  "constructor_version": "0.1",
  "objective": "l2_distance_to_policy_adjusted_benchmark",
  "preference": {
    "aggregation": "unique_rule_signed_sum_clamp",
    "tilt_strength": 0.5,
    "score_min": -1.0,
    "score_max": 1.0
  },
  "constraints": {
    "long_only": true,
    "fully_invested": true,
    "max_single_name_weight": 0.1,
    "exclude_weight": 0.0
  },
  "identity": {
    "unmapped_behavior": "retain_unscreened_no_tilt",
    "disputed_behavior": "fail_closed"
  },
  "decision_semantics": {
    "watch_behavior": "eligible_no_automatic_tilt",
    "none_behavior": "eligible_no_automatic_tilt",
    "none_is_pass": false
  },
  "solver": {
    "library": "cvxpy",
    "library_version": "1.9.2",
    "name": "OSQP",
    "python_package_version": "1.1.3",
    "warm_start": false,
    "eps_abs": 1e-8,
    "eps_rel": 1e-8,
    "max_iter": 100000,
    "polishing": true,
    "adaptive_rho": false
  },
  "numerical": {
    "input_weight_tolerance": 1e-8,
    "feasibility_tolerance": 1e-10,
    "output_invariant_tolerance": 1e-8,
    "semantic_weight_decimals": 12,
    "rounding_mode": "ROUND_HALF_EVEN"
  },
  "paper_only": true
}
```

CVXPY 1.9.2's OSQP interface defines explicit fallback tolerances/iteration limits when omitted; WA Commons must nevertheless pass its own options and record them so dependency defaults cannot silently change accepted outputs.

The manifest also records Python, NumPy and SciPy versions.

## Canonical ordering and semantic output

1. Sort input rows by `security_id` using one documented bytewise/Unicode-code-point ordering and reject duplicates.
2. Solve with warm start disabled.
3. Verify raw solver weights against sum/nonnegative/cap/EXCLUDE invariants within tolerance.
4. Quantize weights to 12 decimal places with Decimal `ROUND_HALF_EVEN`.
5. Compute the residual to exactly `1.000000000000`.
6. Assign the signed residual to the highest-weight non-EXCLUDE security that has sufficient cap/nonnegative headroom; ties break by stable `security_id` order.
7. Re-check all invariants after residual assignment; fail if no eligible residual recipient exists.
8. Hash the canonical quantized weight vector plus config/provenance, while retaining raw solver diagnostics separately.

Input row permutations must produce the same canonical target and semantic hash.

## Required #49 output manifest

At minimum:

- constructor/config ID/version/hash;
- exact solver/runtime versions/options;
- benchmark ID/snapshot/hash references;
- policy profile/version/hash;
- evidence/screening snapshot references;
- input count and benchmark-weight reconciliation;
- mapped/unmapped/disputed counts/weights;
- EXCLUDE/WATCH/NONE counts and benchmark weights;
- affected preference rules and per-security aggregate preference score;
- excluded benchmark weight and unscreened benchmark weight;
- solver status/objective/iterations;
- target sum/max/min;
- semantic target hash;
- `paper_only = true`;
- `real_money_authority = false`.

Licensed benchmark rows remain subject to #45's storage/redistribution boundary; the constructor manifest must not leak raw licensed constituent data.

## Required #49 focused tests

1. no-policy fixture reproduces the benchmark when all benchmark weights are below the cap;
2. EXCLUDE yields exact canonical zero and required redistribution;
3. WATCH/NONE do not become exclusions or automatic penalties;
4. strongest soft avoid remains nonzero absent another binding constraint;
5. prefer/avoid signals deduplicate by rule ID and aggregate deterministically;
6. unmapped stays eligible/unscreened with no tilt;
7. any disputed identity fails closed;
8. all-excluded fails closed;
9. too few eligible names for the 10% cap fails closed;
10. any non-OPTIMAL solver status yields no portfolio;
11. input-order permutations reproduce canonical weights/hash;
12. post-quantization output satisfies sum=1, long-only, cap and EXCLUDE invariants;
13. repeated fixed-fixture runs reproduce the semantic target hash;
14. no broker/order/credential/real-money interface exists.

No historical return or performance assertion belongs in #49 tests.

## Deferred, not silently included

- covariance-weighted tracking-error minimization;
- expected-return/utility optimization;
- Black-Litterman;
- risk parity / HRP / CVaR;
- sector/factor neutralization;
- turnover/multi-period/transaction-cost optimization;
- cardinality, minimum-lot or tax optimization;
- real-money execution.

Each requires a separate need, adopted inputs and methodology gate.

## Anti-gaming declaration

No historical benchmark return, candidate portfolio return, Sharpe ratio, drawdown or tracking-error result was used to select the OSS, objective, 10% cap, or 0.50 soft-tilt strength.

If the later paper evaluation performs poorly, this v0.1 remains the preregistered primary constructor. Any change requires a new explicit hypothesis and version; poor observed performance is not authority to rewrite this result.

## Final disposition

`M3_2C_CONSTRUCTOR_SELECTION = ADOPT`

Constructor: **`benchmark-l2-projection-v0.1`**  
OSS: **CVXPY 1.9.2 / Apache-2.0**  
Solver: **OSQP Python 1.1.3**  
Objective: **L2 distance to bounded policy-adjusted benchmark reference**  
Hard semantics: **EXCLUDE = 0; WATCH/NONE remain eligible**  
Soft preference: **unique-rule signed score, bounded ±50% reference tilt**  
Identity: **unmapped retained unscreened/no tilt; disputed fails closed**  
Diversification: **long-only, fully invested, 10% single-name cap**  
Market-return/covariance input: **NONE**  
Performance inspected before selection: **NO**  
Real-money authority: **NONE**
