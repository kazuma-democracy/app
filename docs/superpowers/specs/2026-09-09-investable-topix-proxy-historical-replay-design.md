# Historical Replay v0.2 — Investable TOPIX Proxy Control

Status: **APPROVED — implementation planning authorized in chat 2026-09-10**

Date: 2026-09-09
Issue: #85
Supersedes only the Historical Replay benchmark-input portion of:
`2026-09-09-peace-capital-policy-transmission-replay-design.md`

## 1. Why this design changes

The existing #85 implementation correctly fails closed because WA Commons does not possess three consecutive historical JPX TOPIX constituent-weight snapshots that were available at each historical decision cutoff.

The blocker cannot be removed by back-projecting the current TOPIX snapshot. JPX official historical month-end index master/weight data is a paid product, and public web-archive routes tested during the spike did not recover the required historical CSVs.

A new zero-purchase fact changes the feasible design space: BlackRock's official iShares Core TOPIX ETF (1475) holdings endpoint currently returns dated historical holdings CSVs for prior month-end dates, including the dates needed for a clean 2026-Q1 replay candidate.

This is not treated as reconstructed TOPIX. It is treated as an actual, investable, point-in-time TOPIX-tracking portfolio.

## 2. Goals

This design must preserve the original #85 integrity goals while replacing only the unavailable historical allocation input.

1. Use a real point-in-time investable control portfolio available for each decision cutoff.
2. Apply the already frozen P0/P1/P2 policy semantics without return-driven tuning.
3. Preserve TOPIX Total Return Index as the external financial benchmark family.
4. Preserve as-known-at-cutoff Evidence reconstruction and exact security identity.
5. Freeze the three-month window before loading headline-period return values.

## 3. What remains unchanged

The following contracts remain unchanged:

- Evidence First;
- Evidence and user-value judgment remain separate;
- P0/P1/P2 policy semantics and multipliers from #84 remain frozen;
- no policy choice may use replay returns;
- no current evidence or benchmark state may be projected backward;
- missing historical provenance fails closed;
- exact JPX security-code identity only;
- policy-transmission metrics remain primary;
- financial consequences remain secondary;
- October 2026 remains a separate true future holdout;
- paper research only; no trading authority;
- raw third-party market/source files remain local-only unless redistribution rights are explicitly cleared.

TOPIX Total Return Index remains the external market-performance benchmark. This design changes the replay control allocation source, not the market benchmark family.

## 4. New P0 allocation definition

For Historical Replay v0.2 only, P0 is the dated equity holdings basket of iShares Core TOPIX ETF (TSE:1475) at the decision cutoff.

The ETF is selected for methodology reasons fixed before headline replay returns are loaded:

- it explicitly seeks to track TOPIX Total Return Index;
- it is actually investable;
- its official holdings endpoint exposes historical as-of dates;
- the holdings rows include exact ticker, shares, market value and asset class;
- the source can be hashed and retained locally with retrieval metadata.
The replay allocation uses equity rows only. Cash, collateral, margin and futures rows are not silently converted into constituent weights.

Equity market values are normalized to 1.0 for the policy-allocation layer:

```text
b_i = equity_market_value_i / sum(equity_market_value_j)
```

P0 uses `m_i = 1.0`. P1/P2 use the already frozen multipliers from #84:

```text
raw_i = b_i * m_i
w_i = raw_i / sum(raw_j)
```

No ETF weight, multiplier, replay month or residual treatment is selected from observed headline-period performance.

## 5. Validation evidence for the proxy choice

The proxy choice was validated only on an engineering month already ineligible for the first headline replay.

For 2026-07-31, WA Commons compared the accepted JPX official TOPIX weight snapshot with the 1475 dated holdings basket:

- JPX TOPIX constituents: 1,637;
- 1475 equity holdings: 1,637;
- common security codes: 1,637 / 1,637;
- security codes present on only one side: 0;
- full-basket active share between normalized weights: approximately 0.148%.

For the six then-policy-relevant WATCH securities, the maximum absolute weight difference was approximately 0.017 basis points.

This engineering comparison supports use as an investable proxy; it does not assert that 1475 holdings are legally or mathematically identical to official TOPIX index weights.

## 6. Headline replay window integrity

The first v0.2 headline replay must not use months whose market-return values were inspected while choosing this method.

The following months are therefore engineering-only for the first headline result:

- 2026-04;
- 2026-05;
- 2026-06;
- 2026-07;
- 2026-08, because its 2026-07-31 starting holdings market values/weights were inspected during proxy-fidelity research.

During the feasibility spike, 1475 and/or TOPIX Total Return values for those months were inspected. They may be used for parser, proxy-fidelity and regression validation, but not promoted into the first headline replay.

The current clean candidate window is:

- evaluation 2026-01, decision cutoff 2025-12-30T15:30:00+09:00;
- evaluation 2026-02, decision cutoff 2026-01-30T15:30:00+09:00;
- evaluation 2026-03, decision cutoff 2026-02-27T15:30:00+09:00.

Before this window may be frozen, qualification may inspect only source existence, as-of dates, availability metadata, identities and hashes. It may not load 2026-01 through 2026-03 ETF, constituent or benchmark return values.

The BlackRock holdings endpoint was checked for successful dated-source existence at 2025-12-30, 2026-01-30 and 2026-02-27. Separately, the BlackRock all-history performance chart endpoint was fetched during proxy-fidelity research; therefore that chart is explicitly ineligible as the headline return source even though 2026-Q1 values were not printed or used for method selection. Headline P0 return must instead use the independent JPX-listed 1475 market-price route plus explicit distribution/corporate-action data, whose 2026-Q1 values have not been inspected during method selection.

If any one of the three months fails source, Evidence, identity or market-data prerequisites, the window blocks. The implementation may not skip that month after performance inspection and substitute a different month.

## 7. Financial consequence model — residual sleeve

Historical Replay v0.2 does not build a whole-market dividend database.

For each frozen month, let `C` be only the securities whose policy multiplier differs from 1.0 under the as-known screening snapshot. These are the directly changed securities for that month; they are not assumed to equal the six WATCH names seen in the later engineering snapshot.

Let:

- `b_i` = normalized P0 equity weight for changed security `i`;
- `w_i` = normalized policy target weight for changed security `i`;
- `R_i` = explicitly resolved total-wealth return for changed security `i`;
- `R_0` = 1475 exchange-traded total-wealth return for the evaluation month.

The unchanged remainder is represented as one residual sleeve. Its return is inferred only after the window and policy weights are frozen:

```text
B_C = sum(b_i for i in C)
R_residual = (R_0 - sum(b_i * R_i for i in C)) / (1 - B_C)
W_C = sum(w_i for i in C)
R_policy = sum(w_i * R_i for i in C) + (1 - W_C) * R_residual
```

This construction exactly reproduces `R_0` when policy weights equal P0 and avoids inventing individual returns for unaffected securities.

The residual sleeve deliberately absorbs the unchanged holdings plus the ETF's small cash/futures/tracking/fee effects. It is a research attribution device, not a claim that WA Commons physically replicates the ETF implementation stack.

If `C` is empty, the policy arm's financial return equals `R_0` and no constituent-level return is required.
For every `i in C`, `R_i` must use the existing #56 total-wealth semantics:

- exact JPX security code;
- start/end close from the pinned monthly source;
- explicit cash dividend when applicable;
- explicit split/merger/delisting treatment when applicable;
- no inference from price jumps;
- unresolved price, dividend or corporate action blocks the affected monthly replay.

The residual formula may not be used to hide an unresolved directly changed security.

## 8. TOPIX Total Return remains the external benchmark

The fund control and market benchmark have separate meanings:

- P0 allocation/control: dated 1475 investable equity basket;
- P0 financial return: 1475 exchange-traded total-wealth return under the existing #56 price/dividend/action semantics;
- market benchmark: TOPIX Total Return Index for the same month.

Required reporting therefore separates:

1. P1/P2 versus P0 investable-control consequences;
2. P0 tracking difference versus TOPIX Total Return;
3. P1/P2 versus TOPIX Total Return as a secondary external comparison.

A difference between 1475 and TOPIX is not silently attributed to WA Commons policy. Tracking difference is reported separately.

The engineering comparison of 2026-04 through 2026-06 fund and TOPIX returns was used only to validate proxy behavior. Those return values make those months ineligible for the first headline replay.

## 9. Historical identity contract

The dated 1475 holdings file is the point-in-time security universe for each replay cutoff. Every equity row must have a valid, unique TSE security code. Duplicate, missing or malformed security codes block the month.

Corporate identity is a separate bridge used to attach Evidence to a security. The current 2026-08/09 #53 identity snapshot may not be projected backward.

Historical strong-ID reconstruction uses only records available at or before the decision cutoff. Preferred free official route:

1. EDINET documents-list API records submitted on or before cutoff;
2. records that contain both `secCode` and `JCN` provide an exact securities-code ↔ Japanese corporate-number bridge;
3. conflicting strong identifiers block;
4. name-only linking is prohibited.

EDINET's official API specification exposes both `secCode` and `JCN` in document-list records, so a point-in-time bridge can be reconstructed without using the later #53 identity snapshot.

A security with no historical corporate bridge may remain explicitly `unresolved_identity` and policy-neutral under the already frozen unknown semantics. It must contribute to unresolved/unknown benchmark mass and may not be relabeled `no_match` or safe.

Any security receiving an active policy instruction must have an exact historical security identity and a consequential Evidence path traceable through a strong bridge. Otherwise the arm/month blocks with `BLOCK_IDENTITY`.

## 10. Historical Evidence reconstruction

Historical screening is rebuilt for every decision cutoff. The current #55 screening artifact is not projected backward.

### Ministry of Defense procurement

Reuse the existing MOD adapter and contract-subject classifier. For cutoff `t`:

1. enumerate only official monthly MOD files whose authoritative availability metadata is at or before `t`;
2. pin URL, HTTP/source publication metadata, retrieval timestamp and SHA-256;
3. parse each eligible file with the existing adapter;
4. union eligible observations/claims available by `t`;
5. run the existing subject classifier and policy evaluator;
6. exclude any monthly file whose availability cannot be established at or before `t`.

The feasibility spike confirmed that official FY2025 monthly workbooks remain downloadable and expose historical `Last-Modified` metadata. Examples include January 2026 contracts last modified 2026-03-10, February last modified 2026-04-10 and March last modified 2026-04-27.

The implementation must not assume that contract month equals publication month. Availability metadata controls.

### Political finance

The adopted fixed political-finance source was published 2024-11-29 and is therefore potentially eligible for 2026-Q1 cutoffs, but its unresolved/review-required identity state remains unchanged. It does not become a consequential claim merely because it is historically available.

### Not-integrated categories

Sources not integrated at a cutoff remain `not_integrated`. Missing research is never converted to `no_match`, NONE-as-safe, or negative evidence.

## 11. Source-rights and storage boundary

This design does not declare BlackRock holdings content open-licensed.

Before production adoption, Source Registry must add the 1475 holdings source with publisher, locator family, retrieval method, terms URL, cadence, storage/publication boundary and `license_status`.

Until rights review says otherwise:

- acquisition is low-frequency/manual for the three preregistered snapshots;
- no high-frequency crawler is introduced;
- raw BlackRock holdings CSVs remain local-only;
- raw BlackRock page/performance payloads remain local-only;
- committed artifacts contain only WA Commons-created normalized hashes, source locators, counts, aggregate metrics and methodology metadata where appropriate;
- actual third-party market-performance values remain subject to the existing separate publication-rights check.

If local research use or required retention cannot be supported under the adopted source terms, the replay blocks rather than silently substituting a weaker source.

EDINET, JPX, MOD and political-finance sources retain their existing Source Registry decisions and redistribution boundaries.

## 12. Metadata-only qualification order

Qualification remains physically separated from return execution.

For each candidate month, qualification may read only:

- dated 1475 holdings source existence/as-of metadata and source hash;
- security-code validity and duplicate checks;
- historical identity-source availability and semantic hash;
- historical Evidence source availability metadata and semantic hash;
- JPX 1475 start/end price-source existence;
- distribution/corporate-action detector source existence;
- TOPIX Total Return benchmark-source existence;
- source-rights status required for local replay.

Qualification may not read:

- 1475 start/end price values;
- 1475 distribution amounts;
- directly changed constituent price/dividend/action values;
- TOPIX Total Return values;
- any candidate-period return or performance metric.

Only after three consecutive months qualify is the exact window written and hashed as `HISTORICAL_REPLAY_WINDOW_FROZEN`.

The execution CLI must accept the frozen window artifact. It must not contain candidate-month selection logic.

## 13. Return-loading order after freeze

After the frozen-window hash exists, execution proceeds month by month:

1. load the already frozen P0/P1/P2 target weights;
2. identify `C`, the directly changed securities for that month;
3. load 1475 start/end market prices and explicit cash distribution/corporate-action data;
4. compute P0 exchange-traded total-wealth return;
5. load individual total-wealth inputs only for securities in `C`;
6. compute the residual-sleeve return and P1/P2 financial consequences;
7. load the TOPIX Total Return benchmark value;
8. report policy-transmission metrics first, financial consequences second.

A market or action failure for a directly changed security blocks the affected month. The implementation may not replace that security's return with zero, price-only return or the residual sleeve.

P0/P1/P2 for all three months use identical policy semantics and the same month set.

## 14. Required states

Existing #85 states remain valid:

- `HISTORICAL_REPLAY_WINDOW_FROZEN`
- `HISTORICAL_REPLAY_OK`
- `BLOCK_EVIDENCE_CUTOFF`
- `BLOCK_HISTORICAL_REPLAY_COVERAGE`
- `BLOCK_MARKET_DATA`
- `BLOCK_CORPORATE_ACTION`
- `BLOCK_REPRODUCIBILITY`

The v0.2 path also uses:

- `BLOCK_IDENTITY`
- `BLOCK_SOURCE_RIGHTS`

A new state is not a way to bypass a prior blocker. It makes the precise failure reason visible.

## 15. Compatibility with existing work

- #84 P0/P1/P2 instruction semantics are unchanged.
- #50 official TOPIX mapping remains the accepted current-snapshot TOPIX mapping and the engineering fidelity reference.
- #56 monthly price/dividend/corporate-action primitives are reused for 1475 and directly changed securities.
- #78 zero-purchase/local-first/fail-closed rights rules remain in force.
- The existing #85 v0.1 blocked capability result remains historical evidence and is not rewritten.
- October 2026 forward holdout remains on its separately preregistered path; this Historical Replay proxy change does not silently redefine the future holdout.

Historical Replay v0.2 gets a new config/artifact version. Earlier hashes remain immutable.

## 16. Tests and verification

Minimum focused coverage:

1. holdings parser accepts dated 1475 equity rows and rejects duplicate/malformed TSE codes;
2. equity normalization is deterministic and input-order independent;
3. policy compiler preserves frozen P0/P1/P2 semantics on proxy weights;
4. qualification artifacts reject any price/return/performance-bearing selection input;
5. historical identity bridge accepts only strong point-in-time identifiers and preserves unresolved identity;
6. Evidence cutoff excludes MOD files published after the cutoff;
7. residual-sleeve formula exactly reproduces P0 when `w_i == b_i`;
8. empty changed set returns P0 without constituent return loading;
9. unresolved directly changed security dividend/action blocks;
10. TOPIX tracking difference is reported separately from policy effect;
11. raw BlackRock/JPX/MOD source rows never enter repository-safe public artifacts;
12. engineering-only months cannot enter the first headline window.

Before any real headline return is loaded, one metadata-only real qualification run must show whether 2026-01 through 2026-03 can be frozen. A qualification BLOCK is a valid result and must not trigger a weaker substitute rule.

After implementation, run focused tests first and one final full repository suite once before completion.

## 17. Non-goals

- no claim that 1475 equals official TOPIX weights exactly;
- no retroactive reconstruction of paid JPX index master data;
- no all-market dividend warehouse;
- no high-frequency BlackRock/JPX scraping;
- no return-driven choice among ETFs or months;
- no use of the later #55 screening snapshot as historical truth;
- no name-only corporate identity matching;
- no change to P2's 0.5 WATCH multiplier;
- no change to October 2026 future-holdout rules;
- no real-money replication or broker integration.

## 18. Acceptance for implementation planning

This design is ready for implementation planning only if all remain true:

- the user-approved choice is A: investable 1475 point-in-time control with TOPIX Total Return retained as the external benchmark;
- headline replay uses no month whose return values influenced this method choice;
- 2026-01 through 2026-03 remain candidates, not a claimed frozen window, until metadata-only qualification passes;
- the BlackRock all-history performance chart is not used as the headline return source;
- headline P0 return is reconstructed from independent 1475 exchange-traded price/distribution/action inputs after the window is frozen;
- historical Evidence is reconstructed from availability-at-cutoff sources rather than today's screening;
- historical corporate bridges use point-in-time strong identifiers rather than today's #53 mapping;
- policy-transmission metrics remain primary and financial results secondary;
- proxy tracking difference from TOPIX is separated from policy effect;
- source rights and raw-data boundaries remain fail-closed;
- no real return value is loaded during candidate selection.

## 19. Implementation handoff

After written-spec review, create an implementation plan that reuses existing #84/#56/#85 code wherever possible.

Preferred implementation order:

```text
A. Source Registry + v0.2 config contracts
B. dated 1475 holdings parser / normalized allocation snapshot
C. historical EDINET strong-ID bridge
D. historical MOD/political-finance cutoff screening
E. metadata-only 2026-Q1 qualification
F. freeze window if and only if qualification passes
G. 1475 + changed-security monthly market payloads
H. residual-sleeve financial calculation
I. TOPIX TR external comparison
J. final result / ROADMAP / verification
```

USE > EXTEND > ADAPT > REPLACE > BUILD remains mandatory. The existing v0.1 Historical Replay engine and monthly-market primitives should be extended rather than replaced unless a focused incompatibility is demonstrated.