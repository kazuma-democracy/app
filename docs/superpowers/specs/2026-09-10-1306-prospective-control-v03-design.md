# 1306 Prospective Control v0.3 Design

Status: **PROPOSED — user-approved direction, written for review**

Date: 2026-09-10
Issue: #85
Base: `main@11ec8b2758a113ea91fc16e7ec881d20fd5fddbe`

## 1. Purpose

Unblock the real three-month leak-safe Historical Replay without weakening the existing zero-cost, point-in-time, as-known-at-cutoff, no-performance-selection or source-rights rules.

The adopted v0.2 capability is preserved. This design adds the smallest new control-source path needed for a **prospective** replay: NEXT FUNDS TOPIX ETF (1306) setting portfolios captured before each decision cutoff and bound to reproducible acquisition evidence.

This design does not retrofit 1306 into the existing 1475 contract and does not reinterpret historical 1475 availability.

## 2. Why v0.3 is needed

The real preregistered 2026-Q1 v0.2 replay is blocked for two independent reasons:

- Q1 was contaminated by preselection Market Value / Weight inspection;
- the original historical publication time of the dated 1475 holdings cannot be independently proven at the three decision cutoffs.

No Q1 return was loaded and no alternate period was selected from observed performance.

Research on 2026-09-10 found a better prospective route:

- the official 1306 product page publishes dated setting portfolios for future/current application dates;
- multiple same-date portfolios correspond to different provisional unit sizes rather than revision versions;
- the raw portfolio can be captured locally before the decision cutoff, hashed, and externally time-evidenced without publishing the raw file;
- the method can therefore create its own future point-in-time availability evidence instead of trying to reconstruct an unprovable historical publication timestamp.

## 3. Source role and factual scope

New source role:

`NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO`

Source: NEXT FUNDS TOPIX ETF (1306) setting portfolio published by Nomura Asset Management.

The source proves only the portfolio that Nomura publishes for physical creation of its ETF for the stated application date. It is **not** treated as official JPX TOPIX constituent weights.

P0 therefore remains an **investable control allocation**, while the external financial benchmark family remains TOPIX Total Return under the already approved architecture.

## 4. Selection rule for 001 / 002 / 003

The current official 1306 page exposes multiple setting portfolios for the same application date. On 2026-09-10 the observed mapping was:

- `001` -> 20 million provisional units;
- `002` -> 50 million provisional units;
- `003` -> 100 million provisional units.

The suffix itself is not the semantic rule.

Preregistered rule:

> For the selected application date, use the **largest published provisional-unit setting portfolio available before the decision cutoff**.

Consequences:

- never choose a suffix based on later returns, coverage, active share, or a preferred result;
- do not hard-code `003` as the meaning of the rule;
- if future Nomura publication structure changes, select by parsed provisional-unit size;
- if provisional-unit size cannot be identified deterministically, fail closed with `BLOCK_REPRODUCIBILITY`;
- if two distinct files claim the same maximum provisional-unit size without a deterministic primary-source distinction, fail closed rather than choose manually.

## 5. Application-date rule

For each replay evaluation period `YYYY-MM`, use the 1306 setting portfolio whose **application date equals the replay decision-cutoff trading date**.

The existing replay period semantics remain unchanged:

- target weights are frozen at the preceding month-end decision cutoff;
- the following calendar month is the evaluation period;
- market return data is loaded only after target freeze.

If no qualifying same-date setting portfolio is publicly available and captured before the cutoff, that candidate month blocks. Do not substitute a nearby date after seeing performance.

## 6. Availability evidence contract

`as_of_date` or application date alone never establishes historical availability.

A prospective source capture must record at minimum:

- `source_kind`;
- canonical source locator;
- application date;
- provisional-unit size;
- source retrieval timestamp with timezone;
- byte length;
- SHA-256 of the exact raw bytes;
- HTTP `Last-Modified` if exposed;
- HTTP `ETag` if exposed;
- HTTP status/content-type where useful to detect source drift;
- raw-local path outside the public repository;
- source-rights state;
- acquisition-manifest commit SHA and commit timestamp;
- optional OpenTimestamps proof state.

Qualification requires both:

1. the observed source retrieval timestamp is at or before the decision cutoff; and
2. a repo-safe acquisition manifest containing the locator + exact raw-byte SHA-256 is committed to GitHub at or before the decision cutoff.

The public Git commit is the required independent time evidence for v0.3. HTTP server metadata strengthens the provenance when exposed but does not replace the observed retrieval event. If the manifest is first committed after the cutoff, the month fails closed even when the local file claims an earlier retrieval time.

A later verification must re-hash the preserved local raw file and obtain the same SHA-256 frozen in the pre-cutoff manifest.

## 7. OpenTimestamps role

OpenTimestamps is **strengthening evidence, not a required gate** for v0.3.

When operational:

- timestamp the exact raw-file digest without publishing the raw 1306 CSV;
- preserve the `.ots` proof locally or in a repo-safe form if it contains no restricted source rows;
- verify that the proof binds to the exact raw-file digest;
- never treat OpenTimestamps as proof that Nomura itself published the file at a particular time.

A failed or delayed OpenTimestamps anchor does not invalidate an otherwise valid capture because the required independent cutoff proof is the pre-cutoff public Git acquisition-manifest commit. This rule is fixed now, before any headline replay return is observed.

## 8. Rights and storage boundary

Nomura / NEXT FUNDS site terms restrict reuse and redistribution of site information.

Until an exact later rights review establishes broader permission:

- raw 1306 setting-portfolio CSV bytes remain **local-only**;
- raw rows are not committed to GitHub;
- public repository artifacts contain only repo-safe methodology and provenance facts such as locator, dates, unit size, byte length, cryptographic hashes, acquisition state and aggregate derived diagnostics where rights-cleared;
- normalized row-level holdings are local replay inputs, not public source mirrors;
- publication of aggregate financial results remains subject to the existing source-rights/publication contract.

The Source Registry must add this source explicitly rather than silently broadening the 1475 row.

## 9. Reuse of v0.2 architecture

USE / EXTEND is preferred over BUILD.

Keep unchanged where possible:

- candidate qualification flow;
- exact-three-consecutive-month window freeze;
- pre-return freeze manifest;
- historical identity reconstruction;
- historical evidence cutoff logic;
- P0/P1/P2 Policy Compiler semantics;
- policy-transmission metrics;
- monthly market parser / corporate-action handling;
- frozen target verification;
- financial evaluation flow;
- fail-closed terminal states;
- no-performance-field guards.

Add only:

1. a 1306 control-source parser / adapter;
2. a prospective acquisition-evidence manifest schema;
3. a new v0.3 config source kind and qualifier branch;
4. tests proving semantic portfolio selection, hash binding, cutoff behavior and no v0.2 regression.

Do not fork the entire replay engine into a parallel implementation.

## 10. Control adapter output

The adapter should emit the same downstream conceptual information used by the current investable-control mapping path, with source-specific provenance separated from normalized holdings.

Minimum normalized control manifest fields:

```text
source_kind
security_id = TSE:1306
application_date
provisional_units
retrieved_at
source_locator
source_sha256
source_bytes
rights_state
acquisition_manifest_commit_sha
acquisition_manifest_committed_at
timestamp_proof_state
semantic_snapshot_sha256
```

Each holding row should preserve the source security code and share count required to construct relative control weights after the existing price/identity process.

The adapter must not invent market value from the source and must not inspect replay-period return values during source selection.

## 11. Weight construction

1306 setting portfolios publish share quantities rather than final benchmark weights.

The v0.3 control-weight rule is fixed as:

```text
raw_value_i = setting_shares_i * cutoff_valuation_price_i
control_weight_i = raw_value_i / sum(raw_value_j)
```

Requirements:

- cutoff valuation prices come from the already adopted monthly-market / point-in-time price source contract;
- price dates must not exceed the decision cutoff;
- missing required price or unresolved corporate action fails closed;
- no return value from the evaluation month enters the calculation;
- residual/unmapped sleeve behavior reuses the v0.2 investable-proxy contract rather than introducing an optimizer;
- all inputs and semantic hashes are frozen before evaluation-month returns are loaded.

Because this rule uses cutoff prices, merely inspecting source share counts is not equivalent to inspecting candidate financial performance. However, headline periods used for schema/row inspection before preregistration remain conservatively excluded.

## 12. First headline candidate window

Canonical exclusions already established:

- 2026-01 through 2026-03: contaminated / historical availability unresolved;
- 2026-04 through 2026-08: engineering-validation periods;
- 2026-09: conservatively non-headline because 1306 structure and at least one share-count row were inspected during the feasibility Spike;
- 2026-10: separate true future holdout under #78.

Preregister the earliest clean prospective candidate window as:

```text
2026-11
2026-12
2027-01
```

Under the existing period semantics, these use decision cutoffs at the preceding month-end trading dates in late October, November and December 2026.

This does not repurpose the October holdout. The October holdout remains the independently preregistered 2026-10-01 through 2026-10-30 realized interval with its existing portfolio definition and return contract.

The 1306 method itself must be versioned and merged before October performance can be used to alter it.

## 13. Capture and freeze order

For each prospective cutoff:

1. discover only the official same-date setting-portfolio metadata necessary to identify candidate files and provisional-unit sizes;
2. select the largest published provisional-unit file by the preregistered semantic rule;
3. retrieve raw bytes locally before the cutoff;
4. compute SHA-256 and write the repo-safe acquisition manifest;
5. commit that acquisition manifest to GitHub before the cutoff;
6. preserve raw bytes locally and optionally create OpenTimestamps proof;
7. run candidate metadata qualification without evaluation-month performance values;
8. when all three candidate months are qualified, write/hash the exact replay-window manifest;
9. freeze P0/P1/P2 target weights for all three months;
10. only then load the following-month market/benchmark return payloads.

If one of the three months blocks after the method is frozen, preserve the block as a result. Do not slide the window forward or backward based on observed financial outcomes.

## 14. Required states

Reuse existing states and add source-specific blocker reasons only where they improve diagnostics without weakening semantics.

At minimum:

- `HISTORICAL_REPLAY_WINDOW_FROZEN`
- `HISTORICAL_REPLAY_TARGETS_FROZEN`
- `HISTORICAL_REPLAY_OK`
- `BLOCK_EVIDENCE_CUTOFF`
- `BLOCK_HISTORICAL_REPLAY_COVERAGE`
- `BLOCK_MARKET_DATA`
- `BLOCK_CORPORATE_ACTION`
- `BLOCK_REPRODUCIBILITY`
- `BLOCK_SOURCE_RIGHTS`

Recommended blocker reasons:

- `CONTROL_SOURCE_UNAVAILABLE`
- `CONTROL_AVAILABILITY_UNVERIFIED`
- `CONTROL_AVAILABLE_AFTER_CUTOFF`
- `CONTROL_APPLICATION_DATE_MISMATCH`
- `CONTROL_PROVISIONAL_UNITS_UNRESOLVED`
- `CONTROL_MAX_UNIT_SELECTION_AMBIGUOUS`
- `CONTROL_SOURCE_HASH_MISMATCH`
- `CONTROL_ACQUISITION_MANIFEST_AFTER_CUTOFF`
- `CONTROL_TIMESTAMP_PROOF_INVALID`

No missing source state becomes a clean/pass state.

## 15. Tests

Focused tests must cover at least:

- parse 1306 metadata and holdings from an engineering-only fixture;
- `001/002/003`-like inputs selected by largest provisional-unit size, not suffix;
- future suffix/order changes do not alter the semantic rule;
- duplicate maximum size blocks if ambiguous;
- application-date mismatch blocks;
- missing/after-cutoff `retrieved_at` blocks;
- missing/after-cutoff acquisition-manifest commit blocks;
- raw-file SHA mismatch blocks;
- OpenTimestamps verification can strengthen but cannot replace the required Git commit gate;
- source-rights mismatch blocks;
- current v0.2 1475 qualification behavior remains unchanged;
- preselection/performance-field guards still block leakage;
- target freeze occurs before evaluation-period market-return loading;
- exact three-month window rule remains deterministic.

Run focused tests during implementation. Run the one final full repository suite only at the issue/review gate required by #85.

## 16. Non-goals

- no reconstruction of exact official historical TOPIX weights;
- no claim that 1306 creation basket equals TOPIX constituent weights;
- no paid JPX reference-data purchase;
- no Common Crawl dependency;
- no daily market database;
- no new scheduler/orchestration platform;
- no policy changes to P0/P1/P2;
- no optimizer or return forecast;
- no publication of restricted raw source rows;
- no real-money trading.

## 17. Acceptance for implementation planning

This design is ready for implementation planning only if all are accepted:

- 1306 is explicitly a prospective investable control, not official TOPIX weights;
- source selection is fixed semantically as largest published provisional-unit portfolio for the cutoff application date;
- actual retrieval before cutoff is mandatory;
- the locator + exact source SHA-256 acquisition manifest must be publicly Git-committed before cutoff;
- OpenTimestamps is optional strengthening evidence, not the sole cutoff proof;
- raw bytes remain local-only and GitHub stores only repo-safe provenance/hash artifacts;
- v0.2 is extended rather than silently rewritten;
- weight construction uses only point-in-time cutoff inputs and is frozen before returns;
- 2026-11 / 2026-12 / 2027-01 is the first prospective headline candidate window;
- October 2026 remains the separate #78 future holdout;
- blocked months remain blocked and are never replaced based on performance;
- no replay return is inspected to select or revise these semantics.
