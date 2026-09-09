# M3.3b2 Policy Transmission Result v0.1

Date: 2026-09-09
Issue: #84
Status: `FROZEN_POLICY_FAMILY`
Scope: pre-return capital-allocation proof only; no price, return, dividend, corporate-action or performance input was loaded.

## Purpose

This result tests whether an explicit user policy can change capital allocation before any market outcome is observed. It does not test financial outperformance.

The accepted #50 TOPIX mapping and #55 TSE-wide screening snapshot are reused without changing Evidence, entity resolution, screening decisions or the accepted October-2026 holdout contract.

## Frozen inputs

- Benchmark: `JPX:TOPIX_TOTAL_RETURN:6000`
- Benchmark effective date: 2026-07-31
- Benchmark constituents: 1,637
- Benchmark semantic mapping SHA-256: `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`
- #55 screening SHA-256: `aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c`
- Screening profile: `example:strict-military-avoidance` v1
- Policy SHA-256: `7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c`
- Compiler artifact version: `m3.3b2-policy-compiler-v0.1`
- Compiler semantic config SHA-256: `bf5f68e8c528b77305b6a2b2e907abaf816546434d0f78b4161cc05b117cf636`
- Compiler code commit: `831fd7550598978646b5f3c297ae29494e1d4ed6`
- Frozen policy-family SHA-256: `6cef954a47173f6f5550b66ebb860a76583c3ee023d05b9399a8501a31cf574f`

The #50 mapping was regenerated from the accepted local-only JPX component-weight source and accepted #53 identity artifact before this run. It reproduced 1,637 / 1,637 mapped securities and the exact accepted semantic mapping hash above.

## Preregistered arms

- `P0`: benchmark control; all decision multipliers `1.0`.
- `P1`: strict minimal intervention; `EXCLUDE=0.0`, `WATCH=1.0`, `NONE=1.0`.
- `P2`: active avoidance; `EXCLUDE=0.0`, `WATCH=0.5`, `NONE=1.0`.

No multiplier above 1.0, expected-return input, top-N pruning, TE/covariance optimization or manual postprocessing was permitted.
## Measured Policy Transmission

| Arm | State | Active share / reallocation mass | Directly underweighted benchmark weight | Changed securities | Holdings | HHI | Target SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P0 | `POLICY_TRANSMISSION_ZERO` | 0.000000000000 | 0.000000000000 | 0 | 1,637 | 0.009457631118 | `d3e13f2700576bce9b8b271e6d5a4f03022373d98312a5769a9cee9b650b8e79` |
| P1 | `POLICY_TRANSMISSION_ZERO` | 0.000000000000 | 0.000000000000 | 0 | 1,637 | 0.009457631118 | `d3e13f2700576bce9b8b271e6d5a4f03022373d98312a5769a9cee9b650b8e79` |
| P2 | `POLICY_TRANSMISSION_OK` | 0.005989984910 | 0.012053048212 | 1,637 | 1,637 | 0.009520401652 | `8054523c83bbe420957e3f2115cbd2a7abbe782850f02946d341b5e173b2d8dc` |

P2 applies six direct `WATCH -> 0.5x` instructions covering 0.012053048212 of benchmark weight. Deterministic renormalization then redistributes the freed weight across the other 1,631 names, so every final target weight differs from the benchmark even though only six rows received a direct policy instruction.

The resulting P2 active share is 0.005989984910, approximately 0.5990% of portfolio capital. This is a policy-transmission quantity, not a return or performance result.

The maximum absolute single-security weight change is 0.003027047049.
## Coverage interpretation

Coverage-state benchmark weights are **not mutually exclusive** because each company has multiple source cells. A company may therefore contribute weight to more than one state.

Measured state-presence weights in the current benchmark are:

- `observed`: 0.012053048212
- `no_match`: 0.987745950984
- `unknown`: 0.000000000000
- `unresolved_identity`: 1.000000000000
- `not_integrated`: 1.000000000000
- union of configured insufficient states: 1.000000000000

`unresolved_identity=1.0` here does **not** mean that TOPIX company identity is unresolved. #50 mapped all 1,637 securities to confirmed canonical entities. The #55 coverage state records unresolved linkage for at least one evidence source; similarly, `not_integrated=1.0` records that at least one source family is not integrated for every benchmark company. These states remain explicit rather than being converted to clean/safe conclusions.
## Reproducibility checks

- All three arms sum to exactly `1.000000000000` after 12-decimal semantic rounding.
- Reversing both benchmark-row order and screening-view order reproduced the identical policy-family SHA and all three target SHA values.
- Every non-zero allocation delta has non-empty attribution.
- P2 attribution consists of six `DIRECT_POLICY_INSTRUCTION` rows and 1,631 `NORMALIZATION_REDISTRIBUTION` rows.
- P0 and P1 correctly preserve `POLICY_TRANSMISSION_ZERO`; zero transmission is not treated as failure.

During the real-snapshot run, one benchmark constituent (`TSE:417A`) exposed a semantic integration bug: #50 confirmed the canonical JPX security identity, while #55 marked its separate corporate-number/evidence bridge as unresolved. The compiler originally conflated those two states and blocked the run. The regression fix keeps #50 canonical identity as the hard portfolio-identity gate while retaining #55 unresolved evidence linkage as weight-neutral explicit coverage uncertainty.

## Publication boundary

The complete row-level target weights, instruction records, claim references and entity identifiers remain local-only. `M3_3B2_POLICY_TRANSMISSION_MANIFEST_V01.json` contains only aggregate metrics, hashes, versions and paper-only flags.

No market-return or performance figure is present in this result.
## Result

#84 establishes the first measured pre-return proof that the accepted Evidence + Policy stack can alter capital allocation reproducibly without a central company morality score or return-driven tuning.

The current strict minimal-intervention arm P1 honestly transmits zero capital change. The preregistered active-avoidance arm P2 transmits a non-zero change of approximately 0.5990% active share from the same Evidence snapshot.

This result does not establish that P2 is financially better, socially superior, or an endorsed universal policy. It establishes only that explicit policy instructions can be translated into deterministic, attributable capital allocation while uncertainty remains visible.

Next dependency: #56 reusable free-monthly market-return/corporate-action primitives, followed by #85 leak-safe Historical Replay. October 2026 remains the separate prospective holdout.
