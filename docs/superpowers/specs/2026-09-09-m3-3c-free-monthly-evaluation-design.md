# M3.3c Free Monthly Event-Driven Market Evaluation Design

Date: 2026-09-09
Status: proposed superseding architecture for human review before implementation
Related: #50, #78, #56, #51, `docs/PAPER_PORTFOLIO_EVALUATION.md`
Supersedes where conflicting: `2026-09-09-m3-3c-market-return-ingestion-design.md`

## Why the architecture changes

The earlier design assumed a daily return series plus a paid JPX corporate-action feed. New official-source evidence changed that cost/complexity premise before any selected-period portfolio return was inspected.

Official JPX pages establish a smaller free route:

- the TSE Monthly Stock Price Table is publicly available and the prior month is posted on the seventh business day;
- the TSE Monthly Statistics Report is publicly available around the 21st of the following month;
- that report includes company/security changes, ex-new/ex-rights information, and one-month ROI for dividend-included stock-price indices including TOPIX;
- TDnet public disclosures are viewable for 31 days, while issuer IR and EDINET provide additional primary evidence;
- JPX's historical daily-price page explicitly asks users to default to manual acquisition and avoid automated acquisition.

Therefore M3 v1 does not need an all-market daily return/corporate-action platform. The new design is calendar-month, held-security-only for event resolution, local-first, and zero-purchase.

No candidate portfolio return, benchmark return, tracking result, or favorable/unfavorable performance was used to choose this architecture.

## Period correction required by the free monthly benchmark

The previous preregistration used 2026-09-02 through 2026-09-30 because the daily architecture could align candidate and benchmark returns on those exact trading dates.

The free JPX dividend-included TOPIX ROI is a calendar-month return. For September it compares the August month-end with the September month-end. Keeping a 2026-09-02 candidate start would therefore compare different intervals unless WA Commons added a daily paid/rights-sensitive benchmark route or a proxy.

That interval mismatch is a broken assumption, not a performance-driven reason to change dates.

The corrected first canonical monthly evaluation is therefore:

- portfolio-definition cutoff: **2026-09-29 close**;
- execution/start valuation: **2026-09-30 close**;
- first realized return date: **2026-10-01**;
- final valuation: **2026-10-30 close**, the last TSE trading day of October 2026;
- canonical realized interval: **2026-10-01 through 2026-10-30**;
- scheduled rebalance inside the interval: **none after the initial allocation**;
- benchmark: official one-month dividend-included TOPIX ROI for October 2026.

This preserves a full trading day between the portfolio-definition cutoff and the execution close, keeps the already-adopted TOPIX Total Return benchmark, and aligns both candidate and benchmark to the same month-end-to-month-end wealth interval.

The September 2026 period is not repurposed as a headline result. Earlier September engineering work remains engineering evidence only.

## Free source set

### 1. Start valuation - September monthly price table

Source: TSE Monthly Stock Price Table for September 2026.

Purpose: exact 2026-09-30 closing prices for securities selected by the portfolio-definition cutoff.

Availability: the previous month is posted on the seventh business day of the following month.

Acquisition rule: one manual download. Store exact bytes locally with retrieval timestamp and SHA-256. Do not commit or republish the raw table.

The portfolio's target security set and target weights must already be frozen before the 2026-09-30 execution close. Later retrieval of the September table supplies the execution prices; it cannot change selection or weights.

### 2. End valuation - October monthly price table

Source: TSE Monthly Stock Price Table for October 2026.

Purpose: exact 2026-10-30 closing prices for held securities.

Acquisition rule: one manual download after publication. Store locally with SHA-256. Parse only the held-security rows needed by the run. Do not republish the source table.

### 3. Benchmark monthly total return

Source: JPX/TSE published ROI of dividend-included stock-price indices, available through the Monthly Statistics Report / related index data.

Purpose: official one-month TOPIX dividend-included return for October 2026, which is aligned to the same September-month-end to October-month-end interval as the candidate portfolio.

The benchmark value is consumed locally as a cited research input. WA Commons does not redistribute raw index tables or bulk time series.

### 4. Corporate-action detectors

Primary monthly JPX detectors:

- Monthly Statistics Report company/security changes, for listing/delisting and related status changes;
- Monthly Statistics Report ex-new/ex-rights list, for explicit split/allocation events and ratios.

These are detectors, not a complete cash-dividend amount source. Absence from one detector must never be interpreted as proof that no cash dividend occurred.

### 5. Held-security action evidence

For every held security, the resolver must establish either `NO_RELEVANT_ACTION_CONFIRMED` or an explicit event record for October 2026.

Evidence priority:

1. issuer IR / issuer primary disclosure;
2. TSE Listed Company Search / public TDnet disclosure; the former preserves older TDnet disclosures beyond the current 31-day public-view window;
3. EDINET filing/API when the needed fact is present there;
4. JPX monthly/daily rights information for dates, ratios, listing/delisting state.

Cash dividends require an explicit amount and applicable record/ex-date convention from primary evidence. Splits, mergers, share exchanges, cash acquisitions, squeeze-outs, and delistings require explicit terms. If the agent cannot establish the treatment from primary evidence, the security is `BLOCK_CORPORATE_ACTION`.

The user is not expected to research these manually. The monthly run creates an exception queue; the local/connected research agent resolves the queue and asks for human attention only when evidence remains ambiguous.

## Return arithmetic

M3 v1 uses one monthly holding-period wealth return rather than a daily return chain.

For each held position:

- start value uses frozen units/weights and the 2026-09-30 closing price;
- end value uses the 2026-10-30 closing price and action-adjusted units;
- explicit cash dividends or cash consideration attributable to the holding are added to position wealth;
- documented share-count changes are applied only from explicit action evidence;
- unresolved missing prices, missing dividend amounts, ambiguous conversion ratios, or unexplained delistings BLOCK the run.

Cash distributions remain portfolio cash through the endpoint unless a separately preregistered rule says otherwise. No synthetic reinvestment is inferred from a price move.

The candidate result is a gross holding-period total-wealth return. The benchmark is the official dividend-included TOPIX one-month ROI. This is a transparent economic benchmark comparison, not a claim that both sides use identical internal reinvestment mechanics. The report must disclose that candidate cash is retained at zero return through the endpoint.

## Failure states

For every held security at finalization, exactly one return state must be available:

- `RETURN_OK_NO_ACTION`;
- `RETURN_OK_ACTION_EXPLAINED`;
- `BLOCK_START_PRICE`;
- `BLOCK_END_PRICE`;
- `BLOCK_DIVIDEND_EVIDENCE`;
- `BLOCK_CORPORATE_ACTION`;
- `BLOCK_IDENTITY`.

At snapshot scope, also allow:

- `BLOCK_SOURCE_UNAVAILABLE`;
- `BLOCK_BENCHMARK_MONTHLY_RETURN`;
- `BLOCK_RIGHTS_PUBLICATION`.

No missing value becomes zero. No name-only relinking is allowed.

## Publication and rights boundary

The zero-cost route is designed first for local research and reproducible paper evaluation.

JPX website terms retain rights in site content, restrict commercial-purpose data collection/secondary use, and state that some third-party provision or publication of TOPIX data can require a license. Therefore the design does not assume a right to republish JPX source data merely because a file is publicly downloadable.

Rules:

- raw JPX files and issuer documents remain local-only;
- public repo artifacts may contain source locators, retrieval timestamps, hashes, parser/config versions, coverage counts, block counts, methodology, and WA Commons-created evidence provenance;
- no JPX raw security rows, raw index tables, or copied bulk time series are committed;
- public release of market-performance numbers must pass a separate publication-rights check and must not turn WA Commons into a market-data redistribution service;
- local #51 research evaluation may proceed without claiming that public redistribution rights have been granted.

This keeps ingestion/evaluation free without converting an unresolved publication right into an invented permission.

## Operational workflow

The recurring workflow is intentionally slow and simple:

1. Before 2026-09-30 close, freeze the initial portfolio security set and target weights.
2. After publication, manually save the September JPX monthly stock-price table and hash it.
3. After October ends, manually save the October JPX monthly stock-price table and hash it.
4. After the October Monthly Statistics Report is published, save the relevant monthly action/change and dividend-included-index ROI files and hash them.
5. Parse start/end prices only for held securities.
6. Intersect JPX action/change detectors with held security codes.
7. Resolve dividend/action evidence for held securities from official issuer/TDnet/EDINET/JPX sources.
8. Fail closed on unresolved evidence.
9. Calculate the portfolio monthly holding-period total return locally.
10. Read the official October one-month dividend-included TOPIX ROI locally.
11. Produce a local evaluation artifact and a repo-safe aggregate/provenance manifest.

For October 2026, canonical finalization occurs only after the later monthly JPX inputs are available. Because November 21, 2026 falls on a weekend followed by the November 23 market holiday, finalization is expected no earlier than the next publication business day, approximately 2026-11-24. Actual publication must be verified at run time rather than assumed.

## What M3 v1 gives up

The first free evaluation does not produce:

- daily tracking error;
- daily realized volatility;
- daily drawdown path;
- daily turnover/slippage diagnostics.

It still answers the primary first question: the Peace Capital portfolio's bounded monthly total return versus the preregistered TOPIX Total Return benchmark, with explicit corporate-action evidence and no look-ahead.

Adding daily metrics later is an extension and must not retroactively change the first monthly result.

## Implementation boundaries

Reuse the existing #50 file/hash/provenance patterns and exact JPX security-code identity spine.

The implementation should add only:

- a monthly evaluation preregistration config;
- parsers for the September and October JPX monthly reports;
- a held-security corporate-action evidence queue;
- deterministic monthly wealth-return calculation;
- repo-safe aggregate/provenance manifest output.

Do not add a database, scheduler, backtesting framework, paid API, high-frequency scraper, or whole-market daily return store for M3 v1.

## Official evidence locators reviewed for this redesign

- TSE Monthly Stock Price Table: https://www.jpx.co.jp/markets/statistics-equities/price/
- TSE Monthly Statistics Report: https://www.jpx.co.jp/markets/statistics-equities/monthly/
- Dividend-included index period ROI: https://www.jpx.co.jp/markets/indices/related/ratio/
- JPX ex-dividend/ex-rights information: https://www.jpx.co.jp/listing/others/ex-rights/index.html
- TDnet overview: https://www.jpx.co.jp/equities/listing/disclosure/tdnet/index.html
- TDnet public viewing service: https://www.jpx.co.jp/listing/disclosure/01.html
- TDnet/TSE Listed Company Search retention authority: https://www.jpx.co.jp/equities/listing/disclosure/tdnet/index.html
- EDINET API documentation: https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WEEK0060.html
- JPX site terms: https://www.jpx.co.jp/term-of-use/
- JPX October 2026 calendar: https://www.jpx.co.jp/calendar/202610.html

## Superseded route

The previously investigated DataCube plus paid Corporate Action Data route remains historical engineering evidence, but it is not adopted for M3 v1. No purchase was made and no selected-period return values were inspected before this change.

The previous daily architecture is superseded where it conflicts with this document. Its fail-closed principles, exact-identity requirement, no-look-ahead rule, local raw-data boundary, and evidence/provenance requirements remain authoritative.
