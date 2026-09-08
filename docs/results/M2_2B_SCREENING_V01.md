# M2.2b — 100-company Policy Screening v0.1

Status: **PR candidate — measured on Issue #43 branch; not canonical until merged**

Issue: #43  
Screening version: `m2.2b-screening-v0.1`

## Purpose

Apply the existing versioned example user policies to the same fixed 100-company Evidence snapshot and emit deterministic company-level research views without creating a UI or interpreting missing Evidence as a positive moral judgment.

The output decision vocabulary remains `EXCLUDE / WATCH / NONE`. `NONE` is **not** PASS, clean, safe, peaceful, or proof that relevant activity does not exist.

## Pinned inputs

The measured run reuses existing accepted inputs rather than creating a new evidence or identity route:

- fixed M1.1 100-company identity cohort: JPX snapshot `20260731`
- M1.1 identity semantic payload SHA-256: `589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f`
- #43 derived identity bridge SHA-256: `f12fb5bddd8b8a3f99fa47cc6f7da54b1112657d5b9b8a56260690c5ecd1e10e`
- completed #42 coverage matrix SHA-256: `41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403`
- current M1 canonical Evidence Graph SHA-256: `0a4f9ed031eaa534e116dca9c441e08054be49047b4404832a14a48094cf2e15`
- current M1 graph claims: **11**

The bridge contains only the accepted WA company entity ID, exact Japanese corporate number, and `CONFIRMED` review state for each of the 100 companies. It does not copy company names or upstream JPX/NTA/EDINET/GLEIF source rows.

### User-policy profiles

All current example profiles in `schemas/examples/user-policy.examples.json` are evaluated against the same graph and coverage snapshot:

| Profile | Version | Policy SHA-256 |
| --- | --- | --- |
| `example:controversial-weapons-only` | 1 | `e82cb9854bb4dec585aa9913166c8deea0977642cd06f098ddf1d518b7e879c0` |
| `example:strict-military-avoidance` | 1 | `7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c` |
| `example:transparency-first` | 1 | `441c15dc334771a1487366c806a5fd42fb3eca3af2f614757815a0cafd079a46` |

These policies are meaningfully different in their rules and uncertainty handling. The measured snapshot producing the same company-level decisions does not make the policies equivalent.

## Method

`src/wa_commons/policy/company_view.py` is a thin aggregation layer over the existing claim-level `evaluate_claim` policy evaluator.

For each company/profile pair it:

1. maps canonical Evidence Graph subjects to the fixed TSE cohort only through the confirmed corporate-number bridge;
2. evaluates every mapped claim with the existing policy evaluator;
3. preserves each claim decision, matched rule references, uncertainty reference, and Evidence source IDs;
4. aggregates company decisions with the existing priority `EXCLUDE > WATCH > NONE`;
5. carries all #42 coverage states into the company view;
6. records policy, Evidence Graph, coverage, and identity-bridge hashes;
7. emits pairwise policy comparison over the same 100 companies and same Evidence snapshot.

No source adapter, fuzzy resolver, policy rule, benchmark logic, portfolio logic, or UI was added.

## Measured result

GitHub Actions `m2-screening` run `34182502899` reproduced the current M1 graph, regenerated the completed #42 coverage artifact, generated the #43 screening artifact, verified the bounded result, and uploaded the derived output.

- focused #43 tests: **13 passed**
- companies: **100**
- profiles: **3**
- company/profile research views: **300**
- current M1 graph claims: **11**
- graph claims mapped into the fixed 100-company cohort: **0**
- graph claims outside the fixed 100-company cohort: **11**
- screening semantic SHA-256: `7bdfec9c733aa84940e23a8d93153b27f604ee0efc799e6cd9edf628d073971a`

Decision counts for every current profile are:

- `EXCLUDE`: **0**
- `WATCH`: **0**
- `NONE`: **100**

All three pairwise profile comparisons therefore have `decision_difference_count = 0` on this exact snapshot.

### Why the result is all `NONE`

This is a measured negative result, not a safety finding. The 11 claims in the current M1 canonical Evidence Graph have no confirmed corporate-number overlap with the fixed 100-company engineering cohort. There is therefore no canonical claim for the existing policy evaluator to turn into `EXCLUDE` or `WATCH` for these 100 companies.

The output deliberately does **not** convert that absence into PASS. Every company/profile view still exposes #42 coverage state:

- `jp-mod-procurement`: `no_match` — **1** cell per company
- `jp-political-finance`: `unresolved_identity` — **1** cell per company
- three catalogued but not integrated Evidence sources: `not_integrated` — **3** cells per company

So a company view with `decision = NONE` still visibly contains unresolved and not-integrated Evidence coverage.

The political-finance state is especially important: existing OCR/name-only observations remain identity-unresolved. They are not silently treated as evidence that a company had no relevant political-finance activity.

## Traceability and uncertainty tests

The targeted company-view tests prove behavior that is not exercised by the zero-overlap measured cohort:

- mapped confirmed claims can produce `EXCLUDE` or `WATCH` through the existing policy evaluator;
- every non-`NONE` claim result retains claim ID, source IDs, and matched rule reference or explicit uncertainty reference;
- `UNKNOWN`, `DISPUTED`, and `EXPIRED` claims route through profile uncertainty instead of being evaluated as confirmed facts;
- conflicting confirmed/uncertain claim results remain individually visible while company aggregation uses `EXCLUDE > WATCH > NONE`;
- zero-claim companies emit `NONE` only and never gain `pass`, `safe`, `clean`, or moral-score fields;
- input ordering does not change the screening semantic hash.

TDD evidence:

- RED: `tests` run `34182055856` — **7 failed / 86 passed** because the company-view implementation did not yet exist;
- intermediate reproducibility failure: `tests` run `34182182311` — **1 failed / 92 passed**, exposing input-order-sensitive graph/bridge hashing;
- fix: canonical ordering is restored before hashing without changing Evidence or policy semantics;
- GREEN on the first fully assembled branch: `tests` run `34182502860` — **99 passed**.

## Artifact

Measured Actions artifact:

- name: `m2-2b-screening`
- artifact ID: `10039398897`
- ZIP SHA-256: `c98dd639251945f5cbca5eb4aea8f9624c3b51e6841fdb9d0e3d0b7ab022a9b1`
- retention expiry: 2026-10-08

Only the derived machine-readable `screening.json` is published by the #43 workflow.

## Reproduction

The dedicated `.github/workflows/m2-screening.yml` performs the bounded reproduction path:

```bash
python -m pytest -q tests/test_company_policy_screening.py tests/test_company_policy_uncertainty.py tests/test_m2_2b_screening_snapshot.py
python scripts/run_m1_reproduction.py
python scripts/run_m2_2a_coverage.py --output artifacts/m2-coverage/coverage.json
python scripts/run_m2_2b_screening.py --output artifacts/m2-screening/screening.json
```

The workflow pins the expected graph, coverage, identity-bridge, and screening hashes and fails closed if those snapshot assumptions change.

## Scope boundary

This increment implements only M2.2b / Issue #43. It does not implement #44 reporting UI/output, M3 universe expansion, new Evidence adapters, new identity resolution logic, benchmark selection, market returns, or portfolio construction.
