# M3 Pre-Return Portfolio Freeze Dependency Correction Design

Date: 2026-09-09
Status: proposed architecture for human review before implementation
Related: #49, #50, #55, #78, #56, #51, `docs/PAPER_PORTFOLIO_EVALUATION.md`

## Purpose

The first Peace Capital evaluation needs one immutable target portfolio before selected-period market returns are ingested.

The current dependency graph contains a responsibility cycle:

- #78 and #56 intentionally ingest market data only for securities actually held by the candidate portfolio;
- #51 currently says it selects the policy/profile and produces the resulting target portfolio;
- #51 also depends on #56.

That means #56 can require a held-security set that #51 has not yet produced, while #51 cannot run until #56 is complete.

This design removes the cycle without changing the adopted benchmark, policy language, constructor algorithm, evaluation period, or return basis.

## Adopted dependency graph

Add one bounded preregistration/freeze issue before #56:

```text
#55 TSE-wide screening
#49 constructor
#50 mapped TOPIX benchmark
#78 free-monthly period/source contract
        ↓
new: M3 pre-return portfolio freeze
        ↓
#56 held-security market-return/action ingestion
        ↓
#51 integrated evaluation
```

The new issue owns only the return-blind selection of the first base policy/profile and the deterministic target-weight artifact.

#56 owns selected-period market prices, benchmark monthly ROI, dividends, and corporate-action resolution.

#51 owns final integration, evaluation metrics, sensitivity reporting, limitations, and publication of the evaluation result subject to the existing rights gate.

## Frozen first-run policy

The first canonical base profile is fixed to the already-existing M2-selected example profile:

- profile ID: `example:strict-military-avoidance`;
- profile version: `1`;
- policy SHA-256: `7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c`;
- title: `Strict military-specific activity avoidance`;
- official status: `not_official`.

This is not selected because of financial performance. No selected-period candidate return, October benchmark return, tracking result, or portfolio performance is used to choose it.

The rationale is continuity: this profile was already the selected profile in the completed M2 explainability path before M3 return data existed. Reusing it avoids inventing a new value profile for the financial evaluation.

The base profile must not be replaced after selected-period return values are observed. Later user-selected profiles are separate runs, not a rewrite of the first canonical result.

## Frozen input lineage

The freeze consumes only already-versioned, return-blind inputs:

1. #50 mapped benchmark:
   - benchmark ID `JPX:TOPIX_TOTAL_RETURN:6000`;
   - effective date `2026-07-31`;
   - 1,637 mapped constituents;
   - semantic mapping SHA-256 `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.
2. #55 TSE-wide screening:
   - TSE screening SHA-256 `aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c`;
   - evidence graph SHA-256 `f165939ba1b784e5dc9c8f8a16a51762b4609395b3ec7cf6db9a015ada5b1f60`;
   - exact selected policy tuple above.
3. #49 constructor:
   - constructor ID `benchmark-l2-projection`;
   - version `0.1`;
   - config path `configs/portfolio/benchmark-l2-projection-v0.1.json`;
   - semantic config SHA-256 `82ea5cfd50139ccecafb8d35b0b654e02fa0c7c45e0b962b6873b2ecbbe8c6be`.
4. #78 evaluation contract:
   - portfolio-definition cutoff `2026-09-29 close`;
   - execution/start valuation `2026-09-30 close`;
   - realized interval `2026-10-01` through `2026-10-30`;
   - return basis `MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY`.

## Freeze timing and no-look-ahead gate

The target portfolio may be generated as soon as the inputs above are available, and must be durably hash-pinned before any selected-period market-return value is used by the methodology.

For the first canonical run:

- the latest permissible portfolio-definition cutoff remains `2026-09-29 close` from #78;
- an earlier durable freeze is permitted because all selected inputs are already fixed and known before that cutoff;
- no September 30 start price, October end price, October TOPIX ROI, October dividend amount, or selected-period return may influence the policy/profile, benchmark, constructor config, or target weights;
- historical non-selected-period data may be used only for parser engineering and tests.

The July 2026 JPX PDFs inspected during architecture work are engineering-schema evidence only. They are not candidate-performance inputs and must never appear as the first evaluation period.

## Portfolio assembly contract

The new freeze issue reuses the existing #49 constructor. It must not add a second optimizer or change the objective.

The assembler must:

1. read the authorized local full #50 mapping artifact;
2. read the authorized local full #55 row-level screening artifact;
3. select only `example:strict-military-avoidance` version `1`;
4. join by the existing exact JPX security/entity identity spine, never by company name;
5. produce one constructor input row per #50 benchmark constituent with `security_id`, `benchmark_weight`, `mapping_state`, selected policy decision, and any already-existing preference signals;
6. call `construct_paper_portfolio(...)` from #49 with the pinned v0.1 config;
7. fail closed on any missing, duplicate, disputed, or inconsistent identity/policy row;
8. emit the constructor's exact target weights and semantic target hash without post-processing them for convenience.

No selected-period price or return is an input to this function.

## Dense-portfolio consequence

The #49 constructor is not a sparsifying constructor. The fixed #55 result for the selected profile currently has:

- `EXCLUDE = 0`;
- `WATCH = 7`;
- `NONE = 3,700`.

WATCH and NONE are both eligible with no automatic tilt under the pinned #49 config. Therefore the first target portfolio may be dense and may include most or all 1,637 TOPIX benchmark securities.

The exact nonzero holding count is an output of the freeze run, not an assumption. It must be measured from the target artifact.

This discovery does not authorize adding a minimum-weight rule, top-N rule, sparsity penalty, heuristic truncation, or a different constructor. If the dense held-security set makes the zero-cost #56 action-resolution contract operationally infeasible, #56 must BLOCK and report that evidence rather than changing the portfolio after the fact.

## Market-data scope handed to #56

#56 consumes the immutable local target-weight artifact.

For market-data coverage, a required security is every target row whose exact Decimal target weight is greater than zero. The M3.1 reporting metric `holding count > 1e-8` remains a reporting metric only and must not be used to drop smaller positive positions from return coverage.

#56 may derive normalized position units after the 2026-09-30 start close using a unit initial wealth convention, for example:

```text
normalized_units_i = target_weight_i / start_close_i
```

This does not change target weights and does not require a real-money portfolio notional.

Every positive-weight security must end in one of the #78 held-security terminal states. Missing or unresolved market/action evidence remains a run blocker.

## Corporate-action scale rule

The free #78 source contract remains authoritative even if the frozen portfolio is dense.

Known official-source behavior relevant to implementation:

- the TSE Monthly Stock Price Table supplies month-end prices and can show multiple rows for one security around rights/split events;
- the Monthly Statistics Report contains the official dividend-included TOPIX one-month ROI, listed-company changes, and ex-rights/split information;
- the JPX ex-dividend/ex-rights service identifies upcoming ex-dividend/ex-rights dates but retains only a short recent public window;
- exact dividend amounts still require the #78 primary-evidence route unless another zero-purchase official source is separately reviewed and adopted before return inspection.

The freeze issue does not solve or weaken these #56 evidence requirements. Its output makes the true held-security workload explicit before return ingestion.

## Output artifacts

The new issue produces two layers.

### Local full freeze artifact

Local-only and required by #56/#51. It contains:

- artifact version;
- freeze timestamp and Git commit;
- #50/#55/#49/#78 input identifiers and hashes;
- selected policy ID/version/hash;
- constructor ID/version/config hash;
- all `security_id` + `target_weight` rows;
- constructor manifest;
- semantic target-weight hash;
- exact positive-weight security count;
- M3.1 `>1e-8` holding count;
- target-weight sum and numerical invariants.

### Repo-safe public manifest

The public repo may contain only aggregate/provenance facts that do not reconstruct the licensed/raw benchmark row set. At minimum:

- selected policy tuple;
- constructor tuple;
- benchmark and screening semantic hashes;
- target semantic hash;
- constituent input count;
- positive-weight holding count;
- M3.1 holding count;
- aggregate decision counts/weights where already permitted;
- target-weight sum, minimum/maximum aggregate diagnostics, and status;
- explicit statement that row-level security IDs and target weights remain local-only.

No public artifact may include the complete security list or row-level target weights unless a later rights review explicitly permits it.

## Required freeze states

Snapshot-level status is exactly one of:

- `FROZEN`;
- `BLOCK_INPUT_VERSION`;
- `BLOCK_IDENTITY`;
- `BLOCK_POLICY_ROW`;
- `BLOCK_CONSTRUCTOR`;
- `BLOCK_PUBLICATION_BOUNDARY`.

A blocked freeze emits no canonical held-security list for #56.

## #56 contract correction

After the freeze issue is accepted, #56 must be minimally amended so its inputs include the frozen target artifact.

#56 must then:

- consume #78 for dates/source/return/action semantics;
- consume the new freeze artifact for the exact positive-weight security set and target weights;
- never reconstruct or reselect the portfolio from market data;
- never shrink the held-security set because source resolution is inconvenient;
- remain OPEN until the future September/October/November publication-dependent inputs are available and verified.

The #56 engine/parser can be implemented and regression-tested before those future files exist, but #56 cannot be closed on fixtures alone.

## #51 contract correction

#51 must stop owning base policy/profile selection and base target-weight construction.

Its first-run inputs become:

- completed #44 explainability milestone;
- completed #49 constructor implementation;
- completed #50 benchmark mapping;
- completed #55 screening;
- completed #78 period/source contract;
- completed pre-return portfolio-freeze artifact;
- completed #56 monthly return/action artifact.

#51 consumes the already-frozen base profile and target weights. It may still perform the preregistered threshold-sensitivity analysis from M3.1, but sensitivity results are never allowed to replace the frozen base result because they perform better.

For the fixed #55 snapshot, the selected strict profile has zero EXCLUDE results and no existing return-driven tuning is permitted. Any future sensitivity variant that would require securities outside the #56 return-coverage set must BLOCK that sensitivity slice or become a separately preregistered data extension; it must not trigger silent return substitution.

## Issue and roadmap changes after spec approval

After this written spec is approved:

1. create one new bounded GitHub issue for the pre-return portfolio freeze;
2. amend #56 to depend on and consume that issue's frozen artifact;
3. amend #51 so base policy/profile and base target construction are no longer in its scope;
4. update `ROADMAP.md` Workstreams 3D/3E/3F to show the corrected dependency order and the fact that #49 is already completed;
5. create an implementation plan for the freeze issue before touching implementation code.

The new issue should be completed and merged before #56 ingests canonical selected-period return values.

## Tests required by the freeze issue

The implementation plan must cover focused tests proving:

- exact selected profile ID/version/hash;
- exact #50 and #55 semantic input hashes;
- exact identity join only, with name-only relinking prohibited;
- missing/duplicate/disputed rows BLOCK;
- no market-price/return input is accepted by the freeze runner;
- constructor config hash is pinned;
- input ordering does not change semantic target hash;
- clean rerun reproduces target weights and hash;
- target weights sum to `1.000000000000` within the existing constructor contract;
- public manifest contains no security IDs, provider local codes, names, or row-level target weights;
- full row-level freeze artifact remains local-only.

A full repository suite is required once before completion, not after every small change.

## Stop conditions

Stop without substitution if:

- the exact #50 or #55 local row-level artifact cannot be reproduced from their accepted hashes;
- the selected policy tuple differs from the pinned tuple;
- the constructor/config differs from #49 v0.1;
- any benchmark row cannot be joined through the existing exact identity spine;
- deterministic reruns produce different target hashes;
- implementing the freeze would require selected-period market returns;
- a desired change would add sparsification, a new policy, a new benchmark, or a new constructor after observing performance.

A later operational blocker in #56 is evidence about the zero-cost route. It is not authority to alter this freeze retroactively.

## Non-goals

This design does not:

- ingest September or October market prices;
- inspect October benchmark performance;
- calculate portfolio performance;
- add a new user policy;
- change #49 constructor mathematics;
- add a sparse/top-N portfolio rule;
- change the #50 benchmark;
- change the #78 October evaluation interval;
- weaken corporate-action evidence requirements;
- authorize paid data or subscriptions;
- authorize real-money trading or broker integration.

## Architecture acceptance criteria

This correction is accepted only if:

- the dependency cycle is removed;
- the base policy/profile is fixed before selected-period returns;
- target weights are produced only from #49/#50/#55/#78 return-blind inputs;
- the exact held-security set is durable before #56 canonical ingestion;
- dense holdings remain an honest output rather than a reason to invent sparsity;
- #56 preserves fail-closed market/action evidence semantics;
- #51 becomes integration/evaluation only for the base run;
- local/public rights boundaries remain explicit;
- no financial result is used to select or revise the method.
