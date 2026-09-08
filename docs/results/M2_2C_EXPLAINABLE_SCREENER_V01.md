# M2.2c Explainable company screener report v0.1

Status: **PASS candidate on Issue #44 branch — measured GitHub Actions evidence recorded; canonical M2 completion requires this PR to merge to `main`**  
Issue: #44  
Report version: `m2-2c-explainable-screener-v0.1`

## Purpose

M2.2c completes the bounded implementation path for the M2 explainable-company-screener milestone by rendering the already deterministic #43 company-level research views as a static Markdown report that a non-developer can inspect without reading JSON or code.

This remains research software only. It does not authorize real-money trading, does not produce a portfolio, and does not create an official WA Commons moral ranking.

## Measured GitHub-hosted run

Measured branch run:

- workflow: `m2-screener-report`
- run: `34183992488`
- head: `1f7ccd4688b635817acaec7ed68e3fed03201a15`
- focused Issue #44 tests: **10 passed**
- full repository tests on the same head: **109 passed** (`tests` run `34183992467`)
- `user-policy`: **SUCCESS** (`34183992485`)
- `m2-screening`: **SUCCESS** (`34183992470`)
- M2 screener-report workflow: **SUCCESS**
- output artifact: `m2-2c-explainable-screener`
- artifact ID: `10039888292`
- artifact ZIP digest: `sha256:8294e7758123e4f15dbb2f48ce6a6b3bfde67d2bd646fd3a3070d05f0bb04714`

Generated report SHA-256:

`9a820ad967fc8255439f26c1d18e08da6af3cf559b6067bcc799f6647551ee83`

## Pinned inputs

The report is tied to the same accepted inputs used by the preceding M2 steps:

- M1.1 100-company identity semantic payload: `589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f`
- Issue #44 display-only identity projection: `50a23df77b6b1fddb8d8634974105dcec0037fede6975273ddf647674d44af35`
- M1 canonical Evidence Graph: `0a4f9ed031eaa534e116dca9c441e08054be49047b4404832a14a48094cf2e15`
- #42 coverage matrix: `41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403`
- #43 identity bridge: `f12fb5bddd8b8a3f99fa47cc6f7da54b1112657d5b9b8a56260690c5ecd1e10e`
- #43 screening snapshot: `7bdfec9c733aa84940e23a8d93153b27f604ee0efc799e6cd9edf628d073971a`

The report runner fails closed if those accepted identity/screening/graph/coverage boundaries change without an explicit new version.

## Display identity provenance and the JPX URL change

The first #44 integration attempt intentionally tried to regenerate the accepted M1.1 identity pilot before rendering the report. In `m2-screener-report` run `34183710482`, the focused #44 tests passed, but the existing M1.1 retrieval stopped at the historical JPX source URL with `HTTP Error 404: Not Found`:

`https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls`

That observation does **not** invalidate the already accepted M1.1 semantic result, and #44 does not silently claim that live M1.1 retrieval is currently healthy. It also does not change the M1 identity-source implementation inside this bounded report issue.

Instead, #44 uses an immutable display-only projection derived from the previously accepted M1.1 GitHub Actions artifact:

- accepted M1.1 run: `32459258713`
- accepted artifact: `9438384412`
- artifact digest: `sha256:fba1edd656b3b55b1c2d82dee1333e56779d75b93ee910d0d89abf281e4f375e`
- derivation: only `entity_id`, `canonical_name`, `JPX_SECURITY_CODE`, and `JP_CORPORATE_NUMBER`
- projection file: `configs/m2-2c-display-identities-v0.1.json`
- projection semantic SHA-256: `50a23df77b6b1fddb8d8634974105dcec0037fede6975273ddf647674d44af35`

The runner recomputes the projection hash instead of trusting its recorded value, checks the original M1.1 semantic hash in provenance, requires exactly 100 entities, and requires the projected entity IDs to equal the #43 screening entity IDs.

This keeps the Issue #44 adaptation bounded to presentation data while preserving the upstream retrieval failure as explicit maintenance evidence rather than patching M1 inside M2.2c.

## Current 100-company result

The selected report profile is:

`example:strict-military-avoidance` v1 — **Strict military-specific activity avoidance**.

The report contains all **100** companies in the accepted engineering cohort. For this exact evidence snapshot:

- selected-profile `EXCLUDE`: **0**
- selected-profile `WATCH`: **0**
- selected-profile `NONE`: **100**
- M1 canonical claims: **11**
- claims mapped into the fixed 100-company cohort: **0**
- graph claims outside the cohort: **11**

This is an honest negative result, not a safety finding. `NONE` means only that this exact profile produced no EXCLUDE/WATCH decision from canonical claims linked to the company in this exact snapshot. It is explicitly **not** PASS, clean, safe, peaceful, or proof that relevant activity does not exist outside the covered sources/snapshot.

Every company retains the current #42 coverage state in the visible report:

- `jp-mod-procurement`: `no_match`
- `jp-political-finance`: `unresolved_identity`
- `sipri-arms-industry`: `not_integrated`
- `us-uflpa-entity-list`: `not_integrated`
- `oecd-ncp-cases`: `not_integrated`

The M2 exit workflow verifies those states for all 100 company sections rather than allowing the visible `NONE` result to hide incomplete or unresolved coverage.

## Policy comparison on one evidence snapshot

All three current example profiles are shown against the same #43 evidence snapshot:

1. `example:strict-military-avoidance` — excludes sufficiently confident confirmed `military_specific` contract-subject claims and routes UNKNOWN/DISPUTED/EXPIRED to WATCH.
2. `example:controversial-weapons-only` — reserves exclusion for the narrower `controversial_weapons` category and treats UNKNOWN as NONE while routing DISPUTED/EXPIRED to WATCH.
3. `example:transparency-first` — WATCHes confirmed military-contract and political-finance claims rather than excluding them, with a separate soft avoid preference for human-rights evidence.

These are meaningfully different rule sets. In the current fixed 100-company snapshot, however, all three pairwise company-decision comparisons have `decision_difference_count = 0` because no M1 canonical claim maps into the cohort. The report states this as a property of the evidence snapshot, not as evidence that the profiles are equivalent.

## What a non-developer can inspect

The static Markdown report provides:

- selected policy title, ID, version and hash;
- Evidence Graph, coverage and screening hashes;
- selected-profile EXCLUDE/WATCH/NONE counts;
- same-snapshot profile comparison;
- an index of all 100 company names and TSE security codes;
- one detail section for every company;
- visible decision and human-readable reason;
- all five coverage states for that company;
- relevant claim/rule/Evidence Card details when mapped claims exist;
- source publisher, URL and locator from the existing Evidence Card component;
- adjudication status/confidence and correction history when present;
- a challenge/correction path for both claim-backed and no-claim company views.

No new Evidence model is introduced; the report reuses the existing `card_from_claim()` component and existing challenge URL.

## No hidden score or action layer

The renderer and workflow explicitly prohibit a hidden moral shortcut. The report states that it produces no:

- moral score;
- peace score;
- safety score;
- company ranking;
- benchmark result;
- portfolio recommendation.

It is a presentation of Evidence → adjudication → selected user policy research output. It does not authorize a trade or other consequential action.

## TDD and failure evidence

Issue #44 was developed with explicit RED/GREEN evidence:

- report contract RED — run `34183207519`: **6 failed / 99 passed**, because `wa_commons.policy.screener_report` did not yet exist;
- after the renderer existed, two over-broad test assertions were corrected without changing production semantics;
- report core GREEN — run `34183416882`: **105 passed**;
- runner contract was deliberately reset to TDD order; run `34183582364`: **3 failed / 105 passed**, because the report runner was absent;
- display-projection contract RED — run `34183900900`: **1 failed / 108 passed**, because `display_identity_inputs` did not yet exist;
- first full integration — run `34183710482`: #44 focused tests passed, then the historical JPX URL returned 404; no M1 source-code patch was made inside #44;
- measured successful adaptation — run `34183992488`: focused #44 tests **10 passed**, all reproduction/report gates passed, artifact published;
- same-head full suite — run `34183992467`: **109 passed**.

## M2 exit review

The M2 exit condition is:

> A non-developer can choose a policy and understand the visible decision and evidence state for every company in the fixed 100-company pilot, with at least two meaningfully different profiles evaluated against the same evidence snapshot.

Measured #44 evidence satisfies that condition on the branch:

- all 100 companies are present with human-readable names/codes;
- the selected policy and its version/hash are explicit;
- every visible company decision has a reason and coverage state;
- mapped claim paths use Evidence Cards and rule/source traceability;
- no-evidence/coverage gaps remain visible and cannot become PASS;
- all three current, meaningfully different profiles are compared on the same screening snapshot;
- challenge/correction paths are visible for every company;
- output is deterministic and tied to versioned hashes;
- no hidden moral score is introduced;
- the implementation remains a static report and does not start M3 portfolio construction.

Therefore **M2 is ready to be marked COMPLETE when this Issue #44 change is merged to `main`**. The historical JPX M1.1 live-retrieval 404 remains a separate recorded maintenance fact and is not falsely represented as repaired by this milestone.
