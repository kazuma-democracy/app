# Peace Capital Policy Transmission + Historical Replay Design

Status: **PROPOSED SUPERSEDING ARCHITECTURE — pending written-spec review**

Date: 2026-09-09

## 1. Why this design changes now

The current M3 architecture is strong at measurement integrity but weak at transmitting user policy into capital allocation.

The new fact is not an observed return result. No selected-period October 2026 portfolio or benchmark return has been ingested or inspected for methodology selection.

The design premise that broke is:

> `EXCLUDE / WATCH / NONE` plus the current benchmark-L2 constructor is sufficient to create a meaningfully policy-affected first portfolio.

Current accepted screening has no `EXCLUDE` names under the frozen strict profile, while `WATCH` has no portfolio-weight effect. Therefore the current base arm can structurally collapse toward the benchmark even when the evidence/policy pipeline is functioning correctly.

This is a treatment-strength problem, separate from measurement validity.

The response is to preserve the audit/reproducibility foundation and add the smallest missing layer between Policy and Portfolio: a deterministic Policy Instruction / Policy Compiler layer. Historical replay is then used to validate that layer quickly without waiting for future market data.

## 2. Goals

This design must prove, in order:

1. the same evidence can produce different capital allocations under different explicit user policies;
2. every active weight change is traceable to a policy instruction and upstream evidence state;
3. the amount of capital reallocated by policy is measurable before returns are observed;
4. historical months can be replayed without look-ahead, survivorship, or evidence-timestamp leakage;
5. the October 2026 forward run remains a true future holdout.

The first success criterion is **policy transmission**, not outperformance.

## 3. What remains unchanged

The following remain adopted foundations:

- Evidence First;
- Evidence and user-value judgment remain separate;
- no universal company peace/moral score;
- `UNKNOWN`, `DISPUTED`, `EXPIRED`, unresolved and no-match states remain visible;
- `NONE` never means safe, clean, peaceful or verified-good;
- exact entity resolution / JPX security identity; no name-only relinking;
- point-in-time benchmark membership/weights;
- as-known-at-cutoff information integrity;
- deterministic version/hash manifests;
- pre-return freeze / preregistration;
- negative/unfavorable outcomes are publishable with equal prominence;
- paper research only; no broker or real-money authority;
- TOPIX Total Return remains the financial benchmark family unless separately changed through an explicit design process;
- the free monthly JPX/primary-source strategy remains the default market-data direction.

## 4. Core architectural change

Old flow:

```text
Evidence
  -> Policy
  -> EXCLUDE / WATCH / NONE
  -> benchmark-L2 constructor
  -> one frozen portfolio
```

New flow:

```text
Evidence / evidence state
  -> User Policy
  -> Policy Compiler
  -> Portfolio Instructions
  -> deterministic reweighting
  -> Policy Transmission Metrics
  -> freeze
  -> market returns
  -> financial consequences
```

`EXCLUDE / WATCH / NONE` may remain as human-readable/audit labels. They are no longer the only possible portfolio control surface.

## 5. Policy Compiler v0 — intentionally minimal

The fastest v0 does not introduce a universal company score, probabilistic peace vector, positive-theme ontology, factor model, or tracking-error optimizer.

It supports only a small instruction vocabulary:

- `EXCLUDE`
- `UNDERWEIGHT`
- `NEUTRAL`
- explicit `UNKNOWN` handling

Positive `OVERWEIGHT`, `CAP`, richer thematic evidence and risk-budget optimization are deferred until the negative/neutral compiler path is proven.

Every instruction is generated from a versioned user policy. WA Commons does not assign a moral value directly to the company.

Minimum instruction record:

```text
entity_id
security_id
policy_id
policy_version
instruction
multiplier
source_decision_or_rule
source_evidence_refs
coverage_state
reason
```

No instruction may be generated from price behavior or future return data.

## 6. Preregistered policy family for the first transmission test

The first v0 transmission test uses three arms over the same benchmark/evidence snapshot.

### P0 — Benchmark Control

- every eligible benchmark row multiplier = `1.0`;
- used only as the financial/control allocation.

### P1 — Strict Minimal Intervention

Preserve the existing `example:strict-military-avoidance` profile semantics.

- `EXCLUDE` -> multiplier `0.0`;
- otherwise -> multiplier `1.0`;
- `WATCH` remains an audit label and does not itself alter weight;
- explicit unknown/unresolved states remain reported, never relabeled safe.

This arm preserves the existing design as a valid **minimal-intervention control policy** even if it generates zero active allocation.

### P2 — Active Avoidance

A separate preregistered user-policy arm, not a revision of P1.

- `EXCLUDE` -> multiplier `0.0`;
- `WATCH` -> multiplier `0.5`;
- `NONE` -> multiplier `1.0`;
- explicit unresolved/unknown coverage is never converted into evidence of absence;
- v0 default for unknown without a stronger explicit policy instruction is weight-neutral but reported separately as `UNKNOWN_MASS`.

The `0.5` WATCH multiplier is a policy choice belonging to this arm. It is not a WA Commons company score.

No multiplier is selected using observed financial performance.

## 7. Portfolio construction v0

For v0, use deterministic simple reweighting before considering a more complex optimizer.

For benchmark weight `b_i` and policy multiplier `m_i`:

```text
raw_i = b_i * m_i
w_i = raw_i / sum(raw_j)
```

Rules:

- exact benchmark identity spine only;
- no top-N pruning;
- no minimum-weight pruning;
- no sparsity penalty;
- no expected-return forecast;
- no post-hoc manual editing;
- no positive multiplier above 1.0 in v0;
- if all raw weights become zero, `BLOCK_POLICY_INFEASIBLE`;
- exact deterministic normalization and semantic hash are required.

Because v0 only reduces or removes selected names, concentration/sector drift is measured and reported rather than hidden. A new risk constraint is added only if real evidence shows this simple v0 becomes infeasible or unsafe as a research representation.

The existing benchmark-L2 constructor is not deleted. It remains a reusable financial-fidelity implementation for later designs, but is not required for the fastest first Policy Transmission proof.

## 8. Primary Policy Transmission metrics

These metrics are computed and frozen **before any corresponding market return is loaded**.

Required:

1. `active_share` / `reallocation_mass`

```text
0.5 * sum_i(abs(w_policy_i - w_benchmark_i))
```

2. benchmark weight affected by each instruction:
   - excluded weight;
   - underweighted weight;
   - neutral weight;
   - unknown/unresolved weight where measurable;
3. number of securities with changed weight;
4. maximum absolute single-name weight change;
5. sector allocation difference when the pinned taxonomy is available;
6. holding count and concentration diagnostics already defined by M3.1;
7. rule-level capital attribution: every active weight difference must map back to a policy rule/instruction;
8. evidence/coverage mass: benchmark weight for which the relevant policy topic is unresolved or insufficiently researched, where the evidence model can support that statement without inference.

Financial return is secondary to these first-stage treatment metrics.

A zero or near-zero P1 treatment is a valid finding and must be described as "this policy generated little/no capital-allocation intervention under this evidence snapshot," not as proof that peace investing equals TOPIX.

## 9. Two-stage validation for speed

### Stage A — Current-snapshot transmission test

Use the already accepted benchmark/evidence/policy inputs.

No new market-return data is required.

Run P0/P1/P2 and verify:

- deterministic output;
- policy family produces the expected differences or honest zero-treatment result;
- all active weights are attributable;
- unknown/unresolved mass is visible where supported;
- no future/market input exists in the compiler interface.

This is the fastest proof that Peace Capital can route capital at all.

### Stage B — Historical Replay

After Stage A passes, add a bounded walk-forward replay using historical point-in-time inputs.

Do **not** begin with 12–24 months. First validate exactly three consecutive months.

## 10. Historical Replay information-integrity contract

A historical month is a small simulated live run.

For decision cutoff `t`:

```text
only evidence/data with availability_at <= t
  -> compile policy
  -> freeze target weights
  -> then load the following evaluation month's returns
```

Mandatory safeguards:

- future evidence never leaks backward;
- current evidence state may not be projected backward merely because the underlying real-world event happened earlier;
- original publication/availability time controls eligibility;
- later restatements/corrections are not silently treated as historically known;
- point-in-time benchmark constituents/weights are mandatory;
- delisted names remain part of historical reality when applicable;
- current constituents may not be back-projected;
- missing historical identity/evidence/source provenance fails closed;
- portfolio/policy parameters are frozen before loading the replay month's return payload;
- replay failures remain results; do not skip inconvenient months after seeing performance.

## 11. Selecting the first three replay months without performance leakage

The first three-month validation window is selected by a **non-performance data-completeness rule** before return values for those months are loaded into the evaluation path.

Selection procedure:

1. enumerate candidate consecutive completed months;
2. inspect metadata/existence only for required point-in-time benchmark, evidence availability timestamps, identity mapping, monthly price/corporate-action source availability and benchmark-return source availability;
3. exclude months already used for market-value/schema inspection from headline validation if their values were viewed during engineering research;
4. select the most recent three consecutive months that pass the reproducibility prerequisites;
5. write and hash the replay-window manifest;
6. only then load candidate/benchmark return values for evaluation.

Months used previously to inspect source format (for example a month whose JPX price/index rows were manually inspected during parser research) may remain `ENGINEERING_VALIDATION` but are not promoted into the first headline replay window.

If no three consecutive months satisfy the information-integrity prerequisites, output `BLOCK_HISTORICAL_REPLAY_COVERAGE`; do not weaken the cutoff rules.

## 12. Expansion after the three-month replay

Only after the exact three-month path is reproducible and leak-safe:

- extend the same frozen method to 12 months;
- then optionally 24 months if source reconstruction remains affordable/reproducible;
- do not choose the extension length from observed performance;
- all policy arms use identical months and market data;
- method changes create a new version and do not rewrite earlier results.

Longer replay is for robustness and financial-consequence observation, not return optimization.

## 13. October 2026 remains a future holdout

The existing October 2026 forward interval remains valuable and is not discarded.

Its role changes:

- Historical Replay: rapid repeated validation of mechanics and policy transmission under past as-known states;
- October 2026: true prospective holdout using rules frozen before the period.

October performance must not be used to choose P0/P1/P2 semantics or the replay method.

## 14. Issue/roadmap restructuring if this spec is approved

The current #80 contract explicitly prohibits new policy semantics and constructor redesign, so it must not be implemented as written after this architecture is adopted.

Recommended transition:

1. mark #80 **SUPERSEDED** before implementation, preserving its design/plan as history;
2. create a new bounded issue for **Policy Compiler v0 + P0/P1/P2 current-snapshot transmission test**;
3. create a separate bounded issue for **three-month leak-safe Historical Replay qualification and execution**;
4. generalize #56 from "October-only market snapshot" into reusable monthly JPX parsing/normalization primitives while preserving October as the future-holdout instance;
5. update #51 so the first integrated report treats Policy Transmission metrics as primary and financial consequences as secondary, and can compare the preregistered policy family;
6. preserve #78's zero-cost/monthly/fail-closed source principles, amending only the single-period-only assumption when replay support is added explicitly.

One bounded issue remains active at a time.

## 15. Fast-path implementation order

```text
A. Policy Compiler v0
   + P0/P1/P2
   + Reallocation Mass / attribution
            ↓
B. Current accepted snapshot transmission proof
            ↓
C. Historical replay capability audit (metadata only)
            ↓
D. Freeze exact three-month replay window
            ↓
E. Run three-month replay
            ↓
F. Extend same engine to 12–24 months
            ↓
G. October 2026 true future holdout
```

This order minimizes waiting and avoids building broad history infrastructure before proving the core routing behavior.

## 16. Non-goals for this version

- no TOPIX100 canonical-universe shrink;
- no universal company peace score;
- no automatic `UNKNOWN = 0.5x` global rule;
- no positive-overweight ontology in the first compiler version;
- no daily return store;
- no real-time data;
- no expected-return model;
- no factor optimizer;
- no TE/covariance optimizer in v0;
- no UI requirement;
- no real-money trading;
- no return-driven policy tuning;
- no manual cherry-picking of replay months.

## 17. Required terminal states

At minimum:

- `FROZEN_POLICY_FAMILY`
- `POLICY_TRANSMISSION_OK`
- `POLICY_TRANSMISSION_ZERO`
- `BLOCK_INPUT_VERSION`
- `BLOCK_POLICY_INSTRUCTION`
- `BLOCK_POLICY_INFEASIBLE`
- `BLOCK_IDENTITY`
- `BLOCK_EVIDENCE_CUTOFF`
- `BLOCK_HISTORICAL_REPLAY_COVERAGE`
- `BLOCK_MARKET_DATA`
- `BLOCK_CORPORATE_ACTION`
- `BLOCK_REPRODUCIBILITY`

Missing evidence or data never becomes a clean/pass state.

## 18. Acceptance

Architecture is ready for implementation planning only when all are true:

- P0/P1/P2 semantics are fixed before return inspection;
- P1 preserves the current strict profile as a minimal-intervention arm;
- P2's WATCH underweight is clearly a user-policy choice, not a WA Commons moral score;
- current-snapshot transmission can be measured without market returns;
- historical replay month selection is performance-blind and preregistered before return loading;
- as-known evidence and point-in-time benchmark requirements remain fail-closed;
- October remains a distinct prospective holdout;
- old #80 is not silently rewritten or implemented under incompatible assumptions;
- #56/#51 responsibility changes are explicit and versioned;
- no selected-period performance has been used to justify this architecture.
