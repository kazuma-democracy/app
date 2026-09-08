# M3.3c Market-Return and Corporate-Action Ingestion Design

Date: 2026-09-09
Status: proposed architecture for human review
Related: #50, #56, #51, `docs/PAPER_PORTFOLIO_EVALUATION.md`

## Problem

Issue #56 requires a deterministic market-return/corporate-action snapshot for an explicitly bounded evaluation period, but its current text says that period is defined by #50. The completed #50 artifact pins the TOPIX component-weight snapshot effective 2026-07-31; it does **not** pin a return-evaluation interval.

Starting #56 without repairing that contract would allow the evaluation period to be selected after market returns are available, weakening the no-look-ahead and no-benchmark-gaming guarantees already adopted by M3.1.

A second independent risk is data licensing. Price availability, dividend/corporate-action completeness, storage rights and public redistribution rights differ by JPX product. A technically convenient feed must not be silently treated as authorized project data.

## Design decision

Introduce one preregistration step before #56 implementation:

**M3.3c0 — Pin first evaluation window and market-data source/rights contract**

This preregistration is methodology, not market-data ingestion. It must be committed before #56 reads the selected evaluation-window return values.

The first canonical evaluation window is:

- benchmark snapshot: TOPIX component weights effective **2026-07-31** from completed #50;
- benchmark availability floor: **2026-08-31 16:20 JST**;
- timezone: `Asia/Tokyo`;
- decision-lag convention: at least one full TSE trading day after the benchmark data becomes available;
- initial decision/execution boundary: **2026-09-01 close**;
- first realized daily return: **2026-09-02**;
- last realized daily return: **2026-09-30**;
- canonical evaluation interval: **2026-09-02 through 2026-09-30, inclusive of TSE trading days only**;
- scheduled rebalance inside this first bounded interval: **none after the initial allocation**.

The partial interval 2026-09-02 through 2026-09-08 may be used only as **ENGINEERING_VALIDATION**. It is not a canonical headline performance interval and must never replace the 2026-09-30 endpoint because its result looks favorable or unfavorable.

## Why this period

The period is selected from the information-availability contract, not from observed investment performance:

1. #50 fixes the benchmark snapshot effective 2026-07-31.
2. The adopted public-weight route records that snapshot as available only after 2026-08-31 16:20 JST.
3. M3.1 requires a minimum one-trading-day decision lag.
4. The first return therefore starts on 2026-09-02.
5. The first bounded evaluation ends at the September month-end, rather than choosing a later endpoint after observing results.

No benchmark return, candidate-portfolio return, tracking result or policy-performance comparison may be used to revise this period.

## Provider strategy

### Priority A — JPX file-first

Use provider-native JPX files as local inputs wherever an appropriate rights-cleared product can supply the required primitives for the fixed period.

The preferred price candidate is J-Quants DataCube `東証株式四本値` because it is an official JPX product, is available as a bounded all-symbol monthly file, and fits the file/hash/local-row pattern already proven by #50.

Current published DataCube pricing identifies separate usage categories. The implementation must **not** assume which category applies to WA Commons. Before acquisition, the preregistration record must pin:

- exact product name/version;
- exact month;
- exact price/license category actually purchased or authorized;
- terms/license URL and retrieval date;
- whether raw bytes may be retained locally;
- whether raw rows may be redistributed;
- whether derived returns/aggregates may be published;
- attribution requirements.

No purchase is authorized by this design document.

### Priority B — J-Quants Pro only if required

J-Quants Pro is the preferred escalation route if the bounded period cannot be reproduced from appropriately licensed file products. Its official datasets include Stock Prices (OHLC), adjusted/unadjusted prices and adjustment factors, plus Corporate Action Data covering cash dividends, splits and multiple reorganization/delisting events.

Pro is not the default because it introduces a broader subscription/license commitment than the bounded one-month #56 task needs.

### Rejected as canonical default — individual/private-use API

Do not adopt an individual/private-use J-Quants account as the canonical WA Commons data route unless its exact current terms are reviewed and explicitly found compatible with the project's intended use, storage and publication model. Convenience or low price is not sufficient evidence of project-use rights.

### Third-party vendors

A third-party market-data vendor may be evaluated only if JPX routes cannot legally/reproducibly supply the required bounded inputs. Any substitution requires a separate source-review decision before ingestion; #56 itself may not silently switch providers.

## Return-basis contract

The adopted benchmark is `JPX:TOPIX_TOTAL_RETURN:6000`, gross total return in JPY. The candidate security-return snapshot therefore must support a compatible **total-return** basis for the first canonical evaluation.

#56 must not silently downgrade the candidate series to price return while retaining a total-return benchmark.

If the selected rights-cleared inputs cannot reproduce cash distributions and capital adjustments required for compatible total returns, #56 is `BLOCKED_RETURN_BASIS` until the source contract is amended explicitly.

The normalized output must distinguish at least:

- provider security code;
- trading date;
- prior close / close inputs used for the return;
- provider adjustment factor or equivalent action primitive when applicable;
- cash dividend/distribution amount used when applicable;
- normalized capital-return component;
- normalized cash-distribution component;
- normalized total simple return;
- corporate-action state/reason;
- source provenance and source content hash.

The exact arithmetic convention for provider adjustment factors and dividends must be preregistered against the chosen provider's official field definitions before implementation fixtures are promoted to acceptance.

## Corporate-action semantics

Corporate actions are explanations for discontinuities, never excuses for silent data repair.

Baseline treatment:

- **split / reverse split:** apply only a provider-documented adjustment factor or explicit action record; no inferred factor from price jumps;
- **cash dividend:** include only an explicit provider amount and applicable ex-date/record convention fixed by the provider contract;
- **merger / share exchange / share transfer:** preserve the action explicitly; convert/continue the position only when security conversion terms are fully identified by the selected source contract;
- **cash acquisition / squeeze-out / cash proceeds:** convert to cash only when consideration and effective timing are explicitly evidenced;
- **delisting:** do not zero-fill the missing post-delisting return. Use documented proceeds/treatment or BLOCK;
- **unexplained missing held-security price/return:** BLOCK;
- **duplicate or conflicting provider action records:** BLOCK;
- **name-only security relinking:** prohibited.

Cash created by a documented action remains cash until the next scheduled rebalance; it is not automatically redistributed among surviving names inside the bounded interval.

## Architecture

Reuse the #50 pattern rather than creating a new market-data platform.

```text
Preregistered M3.3c0 contract
    |
    +-- evaluation window / lag / return basis
    +-- provider / product / rights metadata
    +-- corporate-action rules
    |
    v
Local provider file(s), exact bytes + SHA-256
    |
    v
Provider parser(s)
    |
    v
Canonical market-return normalizer
    |
    +-- exact JPX security-code mapping
    +-- total-return arithmetic
    +-- corporate-action state
    +-- missing-data fail-closed gate
    |
    v
Local full market-return artifact
    +
Public aggregate/provenance manifest
    |
    v
#51 consumes versioned artifact only
```

## Component boundaries

### 1. Preregistration config

A versioned config records the fixed period, benchmark input hash, return basis, provider product, license status, source URLs and corporate-action policy version.

It contains no observed performance statistics.

### 2. Provider parser

Each parser converts one provider-native file/schema into typed primitive records. It does not construct portfolios, apply WA policy or calculate headline performance.

### 3. Market-return normalizer

The normalizer maps provider security codes onto the existing exact security-code identity spine and produces deterministic daily simple returns plus explicit action states.

Use exact identifiers only. Existing five-character security-code normalization may be reused where the provider field uses the same JPX/EDINET convention.

### 4. Coverage/failure gate

For every required held security/date, output exactly one of:

- `RETURN_OK`;
- `ACTION_EXPLAINED` with explicit normalized treatment;
- `BLOCK_MISSING_RETURN`;
- `BLOCK_IDENTITY`;
- `BLOCK_CORPORATE_ACTION`;
- `BLOCK_SOURCE_RIGHTS` / `BLOCK_RETURN_BASIS` at snapshot scope when applicable.

No missing row becomes a zero return.

### 5. Output writer

Keep row-level prices, returns and corporate-action records local unless the pinned license explicitly permits redistribution.

The repository-safe manifest contains only provenance, hashes, date/coverage summaries, missing/block counts, action counts, schema/version identifiers and other non-row-level acceptance facts allowed by the source contract.

## OSS/reuse review

No new backtesting or dataframe framework is justified for #56.

Reuse:

- existing project file-first/hash/provenance patterns from #50;
- existing JPX security-code normalization and exact identity mapping;
- Python `csv`, `decimal`, `hashlib`, `datetime`, and existing `openpyxl`/`xlrd` dependencies when the selected file format requires them;
- existing pytest/jsonschema development stack.

Do **not** add Zipline, Backtrader, vectorbt, a database, workflow engine or scheduler for this bounded ingestion issue. Those systems solve broader concerns and would increase the rights/storage surface without improving #56 acceptance.

A new dependency is allowed only if a measured provider-file requirement cannot be handled reliably by the adopted stack and the reuse review documents why.

## No-look-ahead and information integrity

The normalized artifact must preserve, separately:

- `effective_date` / trading date;
- provider publication or as-known timestamp where available;
- local retrieval timestamp;
- source hash;
- code/config commit/hash.

A value published after the configured decision cutoff may not be used for that decision. Later corrections may create a new versioned research artifact but must not silently rewrite the original run.

#56 may generate market-return inputs, but it must not report candidate-vs-benchmark headline performance. #51 remains the integration/evaluation issue.

## Test strategy

Implementation must use TDD and focused tests before broader suite verification.

Required regression classes:

1. exact provider security-code mapping;
2. deterministic parsing and semantic hash reproduction;
3. period boundary: dates before 2026-09-02 and after 2026-09-30 excluded from the canonical first run;
4. no-look-ahead/publication timestamp rejection;
5. ordinary no-action daily total return;
6. cash-dividend treatment from explicit source fields;
7. split/reverse-split treatment from explicit factor/action fields;
8. merger/cash-acquisition/delisting fixture treatment for events actually needed in the bounded period;
9. unexplained held-security missing row => BLOCK;
10. duplicate/conflicting action => BLOCK;
11. rerun semantic hash equality;
12. public manifest leak check: no row-level prices, returns or canonical entity IDs when rights do not authorize them.

The full repository suite runs once before completion, not after every small edit.

## Issue decomposition

The architecture should be reflected in GitHub as follows:

1. **new preregistration issue — M3.3c0:** pin the first evaluation window and exact market-data source/rights/return-basis contract; no return values are ingested;
2. **#56 — M3.3c:** implement only the approved bounded ingestion/normalization contract;
3. **#51 — M3.3d:** consume the completed #56 artifact with the already completed benchmark, constructor and policy-screening artifacts; no new ingestion methodology.

The #56 issue text should be amended after the preregistration is accepted so it no longer falsely states that #50 itself defines the evaluation period.

## Stop/block conditions

Stop without methodological substitution when:

- source/license terms do not authorize the intended storage/use;
- the selected input cannot reproduce a compatible total-return basis;
- required corporate-action semantics for the period are absent or ambiguous;
- any held-security return is unexplained missing;
- security identity is unresolved/conflicting;
- source bytes/schema/date do not match the preregistered contract;
- reruns produce different semantic payloads.

A block creates evidence for a source-contract decision. It does not authorize another provider, longer period, price-return substitution or changed corporate-action rule inside #56.

## Non-goals

#56 does not:

- reselect TOPIX or change the accepted 2026-07-31 benchmark snapshot;
- change WA policy semantics or evidence screening;
- redesign the portfolio constructor;
- choose the first policy/profile based on returns;
- invent factor models;
- calculate headline investment performance;
- add real-money/broker capability;
- create a production market-data service or scheduler.

## Acceptance of this architecture

This design is ready for implementation planning when durable repository state confirms:

1. the first evaluation interval is preregistered as 2026-09-02 through 2026-09-30 before return inspection for methodology selection;
2. the benchmark input remains #50's accepted TOPIX snapshot effective 2026-07-31;
3. an exact source/product/rights decision is recorded before provider data ingestion;
4. total-return compatibility is explicitly required or the task blocks;
5. corporate-action/missing-return fail-closed semantics are fixed;
6. raw-row publication rights are separated from local processing rights;
7. #56 is amended to consume the preregistration contract rather than claiming #50 defines the period;
8. #51 remains integration-only and may not change these upstream rules after inspecting performance.

## Official source research recorded for the design

- JPX J-Quants DataCube pricing: https://db-ec.jpx.co.jp/client_info/JPX_DLSITE/html/datacube_price.pdf
- J-Quants Pro legal/terms: https://pro.jpx-jquants.com/termsofservice
- J-Quants Pro Stock Prices (OHLC): https://pro.jpx-jquants.com/datasets/9
- J-Quants Pro Corporate Action Data: https://pro.jpx-jquants.com/datasets/14
- J-Quants Pro Listed Shares Corporate Action Factors: https://pro.jpx-jquants.com/datasets/17

These URLs establish discovery and current provider capabilities only. The exact purchasable product terms and applicable license category must be pinned again in M3.3c0 before acquisition.