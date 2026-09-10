# 1306 Prospective Control v0.3 Design

Status: **APPROVED DIRECTION — rights-hardened after exact primary-source review**

Date: 2026-09-10
Issue: #85
Base: `main@11ec8b2758a113ea91fc16e7ec881d20fd5fddbe`

## 1. Purpose

Unblock the real three-month leak-safe Historical Replay without weakening the existing zero-cost, point-in-time, as-known-at-cutoff, no-performance-selection, source-rights, or fail-closed rules.

The adopted v0.2 capability is preserved. v0.3 adds the smallest new control-source path needed for a **prospective** replay: NEXT FUNDS TOPIX ETF (1306) setting portfolios captured before each decision cutoff and bound to reproducible acquisition evidence.

This design does not retrofit 1306 into the existing 1475 contract and does not reinterpret historical 1475 availability.

## 2. Why v0.3 is needed

The preregistered 2026-Q1 v0.2 replay is blocked for two independent reasons:

- Q1 was contaminated by preselection Market Value / Weight inspection;
- the original historical publication time of the dated 1475 holdings cannot be independently proven at the three decision cutoffs.

No Q1 return was loaded and no alternate period was selected from observed performance.

Research on 2026-09-10 established a prospective alternative:

- the official 1306 product page publishes dated setting portfolios for application dates;
- multiple same-date portfolios correspond to different provisional unit sizes rather than revision versions;
- the raw portfolio can be captured locally before the decision cutoff;
- a non-reconstructive acquisition commitment can be timestamped publicly without publishing source rows or the raw-source digest;
- future point-in-time availability can therefore be observed prospectively instead of reconstructed later.

## 3. Source role and factual scope

New source kind:

`NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO`

Canonical product page:

`https://nextfunds.jp/lineup/1306/`

Source: NEXT FUNDS TOPIX ETF (1306) setting portfolio published by Nomura Asset Management.

The source proves only the portfolio Nomura publishes for physical creation of its ETF for the stated application date. It is **not** official JPX TOPIX constituent weights.

P0 therefore remains an **investable control allocation**. The external financial benchmark family remains TOPIX Total Return under the already approved architecture.

## 4. Selection rule for same-date portfolios

The official 1306 page currently exposes three setting portfolios for the same application date. On 2026-09-10 the observed semantic sizes were:

- 20 million provisional units;
- 50 million provisional units;
- 100 million provisional units.

Observed file suffixes such as `001`, `002`, and `003` are not the rule.

Preregistered rule:

> For the selected application date, use the **largest published provisional-unit setting portfolio available before the decision cutoff**.

Consequences:

- never choose a suffix based on later returns, coverage, active share, or preferred output;
- do not hard-code `003` as meaning "largest";
- parse provisional-unit size from primary-source metadata;
- if unit size cannot be identified deterministically, block;
- if two distinct files claim the same maximum size without a deterministic primary-source distinction, block rather than choose manually.

Recommended blocker reasons:

- `CONTROL_PROVISIONAL_UNITS_UNRESOLVED`
- `CONTROL_MAX_UNIT_SELECTION_AMBIGUOUS`

## 5. Application-date rule

For replay evaluation period `YYYY-MM`, use the 1306 setting portfolio whose **application date equals the replay decision-cutoff trading date**.

Existing replay period semantics remain unchanged:

- target weights are frozen at the preceding month-end decision cutoff;
- the following calendar month is the evaluation period;
- market return data is loaded only after target freeze.

If no qualifying same-date setting portfolio is publicly available and captured before the cutoff, that candidate month blocks. Do not substitute a nearby date after seeing performance.

## 6. Availability evidence contract

Application date alone never establishes historical availability.

Each local private capture manifest must record at minimum:

- `source_kind`;
- canonical source locator;
- application date;
- provisional-unit size;
- retrieval timestamp with timezone;
- byte length;
- SHA-256 of the exact raw bytes;
- HTTP `Last-Modified` if exposed;
- HTTP `ETag` if exposed;
- HTTP status/content-type where useful for drift detection;
- raw-local path outside the public repository;
- source-rights state;
- random commitment nonce;
- private capture semantic SHA-256;
- public commitment SHA-256;
- public timestamp reference and timestamp.

Qualification requires both:

1. observed retrieval at or before the decision cutoff; and
2. a matching **blinded public commitment** timestamped at or before the cutoff.

If either side is missing or after cutoff, fail closed.

## 7. Blinded public commitment

Exact NEXT FUNDS site terms were rechecked on 2026-09-10 after the initial design draft. The site policy states that site content is copyrighted and restricts unauthorized reproduction, quotation, republication, or transfer. The 1306 product page also prohibits processing, reuse, or redistribution for third-party provision. Therefore v0.3 must not publish raw rows, excerpts, share counts by security, or the exact raw-source SHA-256 as its timestamp artifact.

Primary policy page checked:

`https://nextfunds.jp/guide/`

The public proof is instead a one-way blinded commitment.

Canonical construction:

```text
private_capture_core = canonical_json({
  source_kind,
  source_locator,
  application_date,
  provisional_units,
  retrieved_at,
  source_bytes,
  source_sha256
})

private_capture_sha256 = SHA256(private_capture_core)
nonce = 32 random bytes
public_commitment_sha256 = SHA256(
  "wa-commons:1306:v0.3:" + private_capture_sha256 + ":" + nonce_hex
)
```

Rules:

- `source_sha256`, `private_capture_sha256`, and `nonce` remain local/private while rights remain restrictive;
- the public timestamp artifact contains only a capture identifier, method version, and `public_commitment_sha256`;
- it contains no raw row, security-level share count, raw-source digest, or reversible source excerpt;
- later local verification recomputes the commitment from the preserved raw file and private manifest;
- a mismatch is `CONTROL_SOURCE_HASH_MISMATCH` or `CONTROL_COMMITMENT_MISMATCH`;
- publication of anything richer remains blocked unless a later explicit rights review changes the registry state.

## 8. Public timestamp channel

The preferred v0.3 independent time evidence is a GitHub-server-timestamped record of the blinded commitment, created before the decision cutoff.

The implementation must separate:

- local/private acquisition evidence;
- public opaque commitment;
- replay qualification.

The public timestamp record must expose an externally observable creation time. A locally supplied timestamp is not sufficient by itself.

The implementation plan may use a GitHub API-created Issue comment or equivalent GitHub-server-timestamped record. If the chosen record is editable, later verification must fail closed when the record was altered after creation or otherwise cannot be shown to bind the same commitment.

OpenTimestamps may be used as strengthening evidence on the **blinded commitment**, but it is not the sole cutoff gate because a later Bitcoin anchor only proves existence no later than the anchor time.

## 9. Rights and storage boundary

Until a later explicit rights review establishes broader permission:

- downloaded 1306 CSV bytes remain **local/private research inputs**;
- raw rows and source-level security/share-count data are not committed to GitHub;
- exact raw-source SHA-256 remains private;
- normalized row-level holdings remain local replay inputs;
- public GitHub evidence is limited to methodology, source citation, non-reconstructive blinded commitments, blocker states, and rights-cleared aggregate results;
- any uncertainty about public source-derived output blocks publication rather than being silently treated as permitted.

The Source Registry must add 1306 explicitly as a separate `WATCH`-style source with the exact checked terms and the local/private boundary. Do not broaden the existing 1475 row.

## 10. Reuse of v0.2 architecture

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

1. a focused 1306 parser / adapter;
2. a private acquisition-manifest and blinded-commitment helper;
3. a v0.3 source kind and qualifier branch;
4. a v0.3 preparation path that reuses existing identity/screening/policy plumbing;
5. focused tests proving selection, commitment binding, cutoff behavior, rights boundaries, and v0.2 compatibility.

Do not fork the entire replay engine.

## 11. 1306 adapter output

Before price valuation, the parser emits source-specific holdings with share quantities but no weights.

Minimum private manifest fields:

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
private_capture_sha256
commitment_nonce
public_commitment_sha256
public_timestamp_ref
public_timestamp_at
semantic_snapshot_sha256
```

Each holding row preserves only the source fields required for local replay, including normalized TSE security code, name where available, and setting share count.

The adapter must not invent market value and must not inspect evaluation-period returns during selection.

## 12. Weight construction

1306 setting portfolios publish share quantities rather than final benchmark weights.

The v0.3 control-weight rule is fixed as:

```text
raw_value_i = setting_shares_i * cutoff_valuation_price_i
control_weight_i = raw_value_i / sum(raw_value_j)
```

Requirements:

- cutoff valuation prices come from the adopted monthly-market point-in-time price primitive;
- price dates must not exceed the decision cutoff;
- missing required price or unresolved corporate action blocks;
- evaluation-month returns never enter the calculation;
- residual/unmapped sleeve behavior reuses v0.2;
- all source, identity, price, screening, and target semantic hashes freeze before evaluation returns are loaded.

## 13. First headline candidate window

Canonical exclusions remain:

- 2026-01 through 2026-03: contaminated / historical availability unresolved;
- 2026-04 through 2026-08: engineering-validation periods;
- 2026-09: non-headline because 1306 structure and share-count data were inspected during the feasibility Spike;
- 2026-10: separate true future holdout under #78.

First clean prospective headline candidate window:

```text
2026-11
2026-12
2027-01
```

These use the preceding month-end decision cutoffs in late October, November, and December 2026 under the existing trading-calendar rule.

The October 2026 holdout remains independently defined under #78 and is not repurposed.

## 14. Capture and freeze order

For each prospective cutoff:

1. inspect only official same-date metadata needed to identify files and provisional-unit sizes;
2. select the largest published provisional-unit file by the fixed semantic rule;
3. retrieve raw bytes locally before cutoff;
4. compute the private source hash, private capture hash, nonce, and blinded public commitment;
5. create the public server-timestamped blinded commitment before cutoff;
6. preserve raw bytes and private manifest locally;
7. run metadata-only candidate qualification;
8. after all three months qualify, write/hash the exact replay-window manifest;
9. freeze P0/P1/P2 targets for all three months;
10. only then load following-month market and benchmark returns.

If one of the three months blocks after the method is frozen, preserve the block. Do not slide the window based on performance.

## 15. Required states

Reuse existing states:

- `HISTORICAL_REPLAY_WINDOW_FROZEN`
- `HISTORICAL_REPLAY_TARGETS_FROZEN`
- `HISTORICAL_REPLAY_OK`
- `BLOCK_EVIDENCE_CUTOFF`
- `BLOCK_HISTORICAL_REPLAY_COVERAGE`
- `BLOCK_MARKET_DATA`
- `BLOCK_CORPORATE_ACTION`
- `BLOCK_REPRODUCIBILITY`
- `BLOCK_SOURCE_RIGHTS`

Recommended reasons:

- `CONTROL_SOURCE_UNAVAILABLE`
- `CONTROL_AVAILABILITY_UNVERIFIED`
- `CONTROL_AVAILABLE_AFTER_CUTOFF`
- `CONTROL_APPLICATION_DATE_MISMATCH`
- `CONTROL_PROVISIONAL_UNITS_UNRESOLVED`
- `CONTROL_MAX_UNIT_SELECTION_AMBIGUOUS`
- `CONTROL_SOURCE_HASH_MISMATCH`
- `CONTROL_COMMITMENT_MISMATCH`
- `CONTROL_PUBLIC_TIMESTAMP_UNVERIFIED`
- `CONTROL_PUBLIC_TIMESTAMP_AFTER_CUTOFF`
- `CONTROL_SOURCE_RIGHTS_NOT_CLEARED`

No missing source state becomes PASS/clean/safe.

## 16. Focused tests

Implementation tests must cover at least:

- parse an engineering-only 1306 fixture;
- choose largest provisional-unit size independent of suffix/order;
- ambiguous duplicate maximum blocks;
- application-date mismatch blocks;
- missing/after-cutoff retrieval blocks;
- private raw SHA mismatch blocks;
- blinded commitment recomputes deterministically with fixed nonce;
- changing any private capture field changes the commitment;
- missing/after-cutoff public timestamp blocks;
- no raw source SHA or row-level source data is emitted in the public commitment artifact;
- rights mismatch blocks;
- cutoff price valuation produces deterministic normalized weights;
- missing cutoff price blocks before policy compilation;
- v0.2 1475 qualification remains unchanged;
- preselection/performance-field guards remain active;
- target freeze precedes evaluation-return access;
- exact 2026-11 / 2026-12 / 2027-01 window is deterministic.

Use focused tests during implementation. Run the final full repository suite only at the #85 review/acceptance gate.

## 17. Non-goals

- no exact historical official TOPIX-weight reconstruction;
- no claim that 1306 creation basket equals official TOPIX weights;
- no paid JPX reference-data purchase;
- no Common Crawl dependency;
- no daily market database;
- no new scheduler/orchestration framework;
- no P0/P1/P2 policy change;
- no optimizer or return forecast;
- no public raw or row-level Nomura source mirror;
- no real-money trading.

## 18. Acceptance for implementation planning

Implementation planning may proceed only under these fixed semantics:

- 1306 is a prospective investable control, not official TOPIX weights;
- source selection is largest published provisional-unit portfolio for the cutoff application date;
- actual retrieval before cutoff is mandatory;
- raw source bytes and raw-source SHA remain local/private under the current restrictive terms;
- public time evidence uses only a non-reconstructive blinded commitment;
- the blinded commitment must be externally server-timestamped before cutoff;
- OpenTimestamps is optional strengthening evidence, not the sole cutoff proof;
- v0.2 is extended, not silently rewritten;
- weights use only cutoff-time inputs and freeze before returns;
- 2026-11 / 2026-12 / 2027-01 is the first headline candidate window;
- October 2026 remains the separate #78 future holdout;
- blocked months are never performance-substituted;
- no replay return is inspected to select or revise these semantics.
