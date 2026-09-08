# M3.2c minimum paper-portfolio constructor v0.1

Status: **ADOPT — benchmark L2 projection on CVXPY/OSQP**  
Issue: #47  
Decision date: 2026-09-08  
Decision basis: OSS/design review only; **no portfolio performance or historical return result was inspected**.

## Decision

WA Commons adopts a deliberately small constructor named:

`benchmark-l2-projection-v0.1`

The constructor takes a point-in-time benchmark weight vector plus WA Commons policy outputs and returns a long-only, fully invested paper target that stays as close as possible to the policy-adjusted benchmark reference under explicit diversification constraints.

The implementation in #49 should use:

- **CVXPY 1.9.2** as the modeling layer;
- **OSQP Python 1.1.3** as the QP solver;
- no expected-return model;
- no covariance matrix;
- no historical-return input;
- no market-data download;
- no broker/trading capability.

This keeps #49 independent of #50/#56 market-data work and makes the constructor selection impossible to tune using observed portfolio performance.

## Why this is the minimum sufficient method

The first Peace Capital constructor does not need to predict returns. It needs to answer a narrower question:

> Given the benchmark weights and this user's explicit policy, what is the smallest transparent weight change that satisfies hard exclusions, bounded soft preferences and ordinary diversification constraints?

A strictly convex squared-distance objective has three useful properties for this task:

1. it is benchmark-aware without requiring return/covariance data;
2. it has a unique optimum whenever the feasible set is non-empty;
3. every deviation from the benchmark is caused by an explicit policy tilt or an explicit constraint rather than a hidden alpha model.

CVXPY is a mature general convex-optimization modeling library rather than a portfolio-opinion layer. The repository is Apache-2.0, active, and its current 1.9.2 release includes OSQP as a normal dependency. OSQP is purpose-built for quadratic programs. This is a smaller dependency and assumption surface than importing an entire portfolio/backtesting framework.

## OSS decision record

| Candidate | Evidence / fit | Decision |
|---|---|---|
| **CVXPY 1.9.2 + OSQP 1.1.3** | CVXPY is Apache-2.0, mature and active; it expresses exactly the small convex QP needed here. OSQP is already a CVXPY dependency and directly solves the resulting QP. No market-return assumptions are imposed by the library. | **ADOPT** |
| **PyPortfolioOpt** | MIT, mature and popular. It includes ex-ante/ex-post tracking-error objectives, but those objectives require a covariance matrix or historical returns. Its main abstraction surface also includes expected returns, efficient frontier, Black-Litterman and related finance methods that are unnecessary for #49. | **WATCH** — useful later if a separately preregistered covariance/return-aware constructor is justified; do not add now. |
| **skfolio** | BSD-3-Clause, active and comprehensive portfolio-optimization library built on scikit-learn/CVXPY concepts. Strong candidate for richer research, but its model-selection/risk/portfolio abstraction surface is larger than the one QP needed by v0.1. | **WATCH** — avoid premature framework adoption. |
| **cvxportfolio** | Mature portfolio optimization/back-testing framework, but materially broader than #49 and GPL-3.0. It is designed around trading policies, costs, forecasts and backtests that are out of scope for the bounded constructor. | **REJECT for v0.1 dependency** — not a judgment on project quality. |
| **plain proportional renormalization** | No dependency and easy to explain. Works for only hard exclusions, but max-weight caps, soft preferences and infeasibility handling quickly require custom redistribution logic. | **WATCH as a reference fixture**, not the production constructor. |
| bespoke optimizer | No reuse benefit; creates solver/numerical/failure-mode burden without an identified gap. | **REJECT**. |

Repository evidence reviewed on 2026-09-08:

- CVXPY repository: https://github.com/cvxpy/cvxpy — Apache-2.0; current release reviewed: `v1.9.2`.
- CVXPY OSQP interface: https://github.com/cvxpy/cvxpy/blob/v1.9.2/cvxpy/reductions/solvers/qp_solvers/osqp_qpif.py.
- OSQP Python current release reviewed: https://github.com/osqp/osqp-python/releases/tag/v1.1.3.
- PyPortfolioOpt repository: https://github.com/PyPortfolio/PyPortfolioOpt — MIT.
- PyPortfolioOpt tracking-error objectives: `pypfopt/objective_functions.py`; ex-ante requires covariance and ex-post requires historical asset/benchmark returns.
- skfolio repository: https://github.com/skfolio/skfolio — BSD-3-Clause.
- cvxportfolio repository: https://github.com/cvxgrp/cvxportfolio — GPL-3.0.

## Inputs

#49 should consume one normalized record per benchmark security in a stable security-ID order.

Required per-security inputs:

- `security_id`: stable canonical security identifier used for deterministic sorting;
- `benchmark_weight`: non-negative point-in-time benchmark weight;
- `mapping_state`: `mapped`, `unmapped`, or `disputed`;
- when mapped, WA company-level policy decision: `EXCLUDE`, `WATCH`, or `NONE`;
- when mapped, all confirmed-claim `preference_signals` already emitted by the existing policy evaluator, each with `rule_id`, `direction` (`prefer`/`avoid`) and `weight` in `(0, 1]`.

Required run-level inputs:

- benchmark ID/version/snapshot identifiers from #45/#50;
- user-policy profile ID/version/hash;
- constructor config/version/hash;
- stable evidence/screening snapshot identifiers;
- source availability / decision timestamp boundary from #50 when real point-in-time data is eventually used.

The current policy evaluator already emits preference signals only for confirmed claims and routes unknown/disputed/expired factual claims through uncertainty handling before preference evaluation. #49 must consume those existing signals; it must not reinterpret uncertain evidence as a soft preference.

## Input validation — fail before optimization

Reject the run if any of the following is true:

- benchmark security IDs are duplicated;
- any benchmark weight is negative or non-finite;
- benchmark weights do not reconcile to `1.0` within configured input tolerance;
- mapped rows lack a valid policy decision;
- a preference signal has an unknown direction, invalid weight, or conflicting definitions for the same `rule_id`;
- the same `rule_id` appears with different direction/weight values for one entity;
- a disputed identity is silently treated as mapped;
- constructor config is unknown or incomplete.

Do not repair bad benchmark weights by silent normalization when the input reconciliation check fails. The data issue belongs upstream.

## Policy semantics

### EXCLUDE

`EXCLUDE` is a hard constraint:

`w_i = 0`

It overrides any soft preference signal on the same entity. The manifest records the excluded benchmark weight so the cost of the policy constraint remains visible.

### WATCH

`WATCH` is **not** an exclusion and does not automatically change weight.

The security remains eligible. Any separately emitted confirmed-claim soft preference signal may still tilt its reference weight. WATCH itself only remains visible in the manifest/report.

### NONE

`NONE` is **not PASS** and is not an exclusion. The security remains eligible at its benchmark reference unless an explicit soft preference signal applies.

### Unmapped benchmark security

An `unmapped` security remains eligible at benchmark reference with:

- no hard exclusion;
- no soft preference tilt;
- `unscreened = true` in the manifest.

This is deliberately conservative about semantics: lack of a WA identity/policy result does not become favorable or unfavorable treatment. The later evaluation must report unscreened benchmark weight separately.

### Disputed identity

A `disputed` benchmark-security mapping is not allowed to inherit a company policy result. v0.1 should fail the constructor input if upstream presents it as mapped. If represented explicitly as disputed/unscreened, the run may retain it at benchmark reference only when the downstream acceptance contract explicitly permits that state and reports its weight separately; #49 tests must choose and lock one representation rather than silently coercing it.

For the minimum #49 implementation, the recommended representation is **fail closed on disputed benchmark identity** so there is no ambiguity about which legal entity's policy result would apply.

## Soft preference aggregation

Soft preferences must never become hidden exclusions.

For each mapped, non-EXCLUDE security:

1. collect all `preference_signals` from confirmed claims;
2. de-duplicate by `rule_id` so one policy rule matching several claims does not gain extra strength merely because more records exist;
3. map `prefer` to `+weight` and `avoid` to `-weight`;
4. sum the signed unique-rule weights;
5. clamp the result to `[-1, +1]`.

Call the result `preference_score_i`.

The v0.1 tilt strength is fixed before performance inspection:

`preference_tilt_strength = 0.50`

Reference multiplier:

`m_i = 1 + 0.50 * preference_score_i`

Therefore the multiplier is bounded in `[0.50, 1.50]`.

Consequences:

- even the strongest soft `avoid` signal cannot drive a security to zero;
- soft `prefer` cannot increase the pre-constraint reference above 1.5× benchmark weight;
- equal and opposite signals can cancel transparently;
- the rule is symmetric and directly inspectable.

For EXCLUDE rows set the pre-normalization reference to zero regardless of multiplier.

Then form:

`r_i = benchmark_weight_i * m_i`

for eligible rows and `r_i = 0` for EXCLUDE rows.

Normalize the eligible reference vector once:

`t_i = r_i / sum(r)`

If `sum(r) == 0`, return `INFEASIBLE_ALL_EXCLUDED`; do not substitute cash or relax exclusions in v0.1.

The `0.50` strength is a constructor-method parameter, not a moral truth and not a policy confidence score. It must be versioned and may be varied only in a preregistered sensitivity analysis; the primary v0.1 result must not tune it to improve performance.

## Optimization problem

Let `w` be the target portfolio weights and `t` the policy-adjusted normalized reference vector above.

Objective:

```text
minimize    Σ_i (w_i - t_i)^2
```

Constraints:

```text
Σ_i w_i = 1
0 <= w_i <= max_single_name_weight
w_i = 0                     for EXCLUDE
```

v0.1 fixed diversification setting:

`max_single_name_weight = 0.10`

No expected-return, covariance, volatility, factor, sector, alpha, turnover or transaction-cost term is part of the v0.1 optimization objective.

Why L2 rather than L1: the squared-distance objective is strictly convex on the feasible affine set and therefore avoids the multiple-optimum/tie-breaking problem that a pure minimum-active-share L1 objective can create.

Why no covariance tracking error yet: that would require return/covariance inputs before #56 and would turn #49 into an implicit market-data methodology issue. Tracking difference/error is still measured later by the preregistered M3 evaluation; it is not optimized here using data that has not yet been adopted.

## Diversification and risk controls

The constructor itself enforces only controls supported by current inputs:

- long-only;
- fully invested;
- hard 10% single-name cap;
- explicit EXCLUDE zero weight;
- bounded soft preference tilt.

Do not invent sector/factor constraints before canonical sector/factor inputs exist. The evaluation stage still reports concentration, effective number of holdings, sector/factor drift where available, tracking difference/error, turnover and other M3.1 metrics.

A later issue may add a risk model only after its data, timing and methodology are independently preregistered. Poor results do not authorize silently adding one to v0.1.

## Feasibility gates

Before invoking CVXPY, perform cheap deterministic checks:

- at least one eligible security exists;
- `eligible_count * max_single_name_weight >= 1 - feasibility_tolerance`;
- every EXCLUDE row has allowable upper bound zero;
- all inputs passed validation.

If these fail, emit an explicit infeasible result and no target portfolio.

After solving, accept only solver status `OPTIMAL`.

Treat `OPTIMAL_INACCURATE`, `INFEASIBLE`, `INFEASIBLE_INACCURATE`, `UNBOUNDED`, user-limit and solver-error statuses as failure. **Never** auto-relax the 10% cap, exclusions, or preference semantics to obtain a solution.

## Solver/reproducibility contract

#49 should pin at least:

```json
{
  "modeling_library": "cvxpy",
  "modeling_library_version": "1.9.2",
  "solver": "OSQP",
  "solver_python_version": "1.1.3",
  "warm_start": false,
  "solver_options": {
    "eps_abs": 1e-8,
    "eps_rel": 1e-8,
    "max_iter": 100000,
    "polishing": true,
    "adaptive_rho": false,
    "verbose": false
  }
}
```

CVXPY 1.9.2's OSQP interface itself supplies explicit defaults when options are omitted; WA Commons should nevertheless pass and record its own settings so a dependency default change cannot silently change accepted outputs.

The implementation must also record Python, NumPy and SciPy versions in the constructor manifest because they participate in the numerical environment.

## Canonical ordering and output determinism

Before vectorization, sort rows by `security_id` using bytewise/Unicode code-point order and reject duplicates.

Solver floating-point output is accepted only if all invariants hold within configured tolerance. For the semantic output/hash:

1. quantize target weights to 12 decimal places using one documented rounding mode;
2. compute the residual to exactly `1.000000000000` at that precision;
3. assign that tiny residual to the largest non-EXCLUDE target weight, breaking ties by stable `security_id` order;
4. re-check non-negativity, EXCLUDE=0 and the 10% cap after residual assignment;
5. fail rather than repair if post-quantization invariants cannot be satisfied.

The manifest should retain both solver diagnostics and the canonical quantized weights used for semantic hashing.

#49 should prove with fixtures that row-order permutations produce the same canonical target/hash.

## Proposed constructor config schema

This is the exact v0.1 proposal for #49 to encode as a machine-readable schema/config; #49 may correct only a demonstrated implementation incompatibility, not redesign the method.

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
    "unmapped_behavior": "retain_unscreened_at_benchmark_reference",
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
    "semantic_weight_decimals": 12
  },
  "paper_only": true
}
```

## Required #49 output manifest

At minimum:

- constructor/config ID/version/hash;
- exact solver/runtime versions and options;
- benchmark ID/snapshot/hash references;
- policy profile/version/hash;
- evidence/screening snapshot references;
- input security count and benchmark-weight reconciliation;
- mapped/unmapped/disputed counts and weights;
- EXCLUDE/WATCH/NONE counts and benchmark weights;
- preference-rule signals and per-security aggregate preference score for affected rows;
- excluded benchmark weight;
- unscreened benchmark weight;
- solver status/objective/iterations;
- target weight sum/max/min;
- semantic target hash;
- explicit `paper_only = true` and `real_money_authority = false`.

Licensed benchmark constituent rows from #50 remain subject to the #45 storage/redistribution boundary; a constructor manifest must not leak licensed raw rows merely because weights were processed.

## Required #49 focused tests

1. no-policy fixture reproduces benchmark weights when all weights are under the cap;
2. EXCLUDE fixture gives exact canonical zero to excluded rows and redistributes only as required;
3. WATCH and NONE do not become exclusions or automatic penalties;
4. strongest soft avoid remains nonzero absent another binding constraint;
5. prefer/avoid signals deduplicate by `rule_id` and aggregate deterministically;
6. unmapped remains eligible/unscreened with no tilt;
7. disputed mapping fails closed;
8. all-excluded fails closed;
9. too-few-eligible-for-10%-cap fails closed;
10. solver non-OPTIMAL status fails closed with no portfolio;
11. input-order permutations produce identical canonical weights/hash;
12. output respects sum=1, long-only, cap and EXCLUDE invariants after quantization;
13. repeated fixed-fixture runs reproduce the semantic target hash;
14. no broker, order, credential or real-money interface exists.

No historical return or performance assertion belongs in #49 tests.

## Alternatives intentionally deferred

- covariance-weighted tracking-error minimization;
- expected-return/utility optimization;
- Black-Litterman;
- risk parity / hierarchical risk parity;
- CVaR;
- sector/factor neutralization;
- turnover-aware multi-period optimization;
- transaction-cost optimization;
- cardinality/minimum-lot constraints;
- tax-aware optimization;
- real-money execution.

Each can be reconsidered only after an explicit need, adopted input data and separate methodology gate. They are not implied by this design.

## No-performance / anti-gaming declaration

No historical benchmark return, candidate portfolio return, Sharpe ratio, drawdown, tracking error result or other outcome statistic was used to select CVXPY, OSQP, L2 projection, the 10% cap or the 0.50 preference-tilt strength.

The selection was based on dependency boundaries, transparency, deterministic feasibility, OSS maturity/license, and the existing #45/#49/M3.1 contracts.

If the later paper evaluation performs poorly, v0.1 remains the preregistered primary constructor. Method changes require a new explicit hypothesis and rule version; they cannot overwrite this result post hoc.

## Final disposition

`M3_2C_CONSTRUCTOR_SELECTION = ADOPT`

Constructor: **`benchmark-l2-projection-v0.1`**  
Modeling OSS: **CVXPY 1.9.2 / Apache-2.0**  
Solver: **OSQP Python 1.1.3**  
Objective: **L2 distance to bounded policy-adjusted benchmark reference**  
Hard decisions: **EXCLUDE = 0; WATCH/NONE remain eligible**  
Soft preference: **deduplicated signed score, bounded ±50% reference tilt**  
Identity uncertainty: **unmapped retained as unscreened; disputed fails closed**  
Diversification: **long-only, fully invested, 10% single-name cap**  
Market-return/covariance input: **NONE**  
Performance inspected before selection: **NO**  
Real-money authority: **NONE**
