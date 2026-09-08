# M3.2a Japan-equity benchmark selection v0.1

Status: **ADOPT — TOPIX Total Return Index**  
Issue: #45  
Decision date: 2026-09-08  
Decision basis: source/data-rights research only; **no portfolio performance was inspected**.

## Decision

WA Commons adopts the **TOPIX Total Return Index (配当込みTOPIX)** as the primary benchmark for the first Peace Capital Japan-equity paper evaluation.

Pinned benchmark identity:

- provider / administrator: JPX Market Innovation & Research, Inc. (JPX総研)
- benchmark: TOPIX Total Return Index / 配当込みTOPIX
- local benchmark ID for WA manifests: `JPX:TOPIX_TOTAL_RETURN:6000`
- JPX DataCube index code for the total-return close series: `6000`
- currency: JPY
- weighting method: free-float adjusted market capitalization
- return variant: **gross total return / dividend-inclusive**, not the price-return TOPIX and not the net-total-return variant (`6095`)
- constituent/weight source for point-in-time reconstruction: **TOPIX month-end index master (TOPIX月末指数マスタ)**
- first month available in the published DataCube specification for the month-end master: **2015-11**
- total-return close-series history in the published DataCube specification: **1989-01-04 onward**

This choice is fixed before portfolio construction, return ingestion, or backtest results. A later unfavorable result does not authorize replacing the primary benchmark.

## Why TOPIX Total Return is adopted

TOPIX is explicitly described by JPX as a market benchmark that broadly covers the Japanese stock market while retaining functionality as an investable index. It is free-float adjusted market-cap weighted. The second-stage TOPIX revision further expands the selection universe across TSE Prime, Standard and Growth and emphasizes liquidity, which is directionally aligned with the separate WA Commons canonical TSE company universe while preserving the distinction between **product universe** and **financial benchmark**.

The decisive operational advantage is not brand familiarity. JPX exposes a reproducible official data route for the information required by `docs/PAPER_PORTFOLIO_EVALUATION.md`:

1. TOPIX month-end constituent information is available as the `TOPIX月末指数マスタ` through J-Quants DataCube.
2. The specification says the master contains constituent-level information as of the last business day of each month and is available from 2015-11 onward.
3. The master includes local security code, name, ISIN and index fields needed for later deterministic mapping in #50.
4. JPX separately provides the dividend-inclusive TOPIX close series; DataCube identifies `配当込みTOPIX 終値` with index code `6000` and history from 1989-01-04.
5. JPX offers an explicit paid self-use route. Therefore a researcher can retain the licensed input locally and pin provider-native identifiers plus local content hashes even when raw licensed benchmark rows are not published by WA Commons.

The first headline evaluation period must consequently be no earlier than the period for which point-in-time constituent/weight inputs can be reproduced under the adopted route. For the month-end master route documented here, that means **2015-11 or later**, unless a later issue adopts a separately licensed earlier point-in-time source before results are inspected.

## Critical as-known-at-cutoff rule

The DataCube file specification says the TOPIX month-end master records information for the last business day of the prior month and is posted **after 16:20 on the first business day of the next month**.

Therefore a historical evaluation must not pretend that a month-end master was available before that publication time. In particular:

- a first-business-day trade cannot use that newly published master if the assumed execution occurs before its actual availability;
- #50 must record the source's `available_at` semantics, not just the economic effective date;
- #51 must apply the M3.1 minimum decision lag and use the next legitimately tradable decision/execution point, or another preregistered timing convention that is no earlier than the source availability.

This is a look-ahead control, not an implementation convenience.

## Data rights and storage boundary

The adopted route is **licensed/self-use first**, not open redistribution of benchmark rows.

JPX's general historical-data overview describes J-Quants DataCube as available to individuals and corporations and distinguishes self-use from external distribution. More specifically, the current DataCube price sheet marks the **TOPIX month-end index master** with the note that it cannot be used for external-distribution purposes. The month-end master must therefore be treated conservatively as a licensed local input unless a later explicit permission/license establishes a broader right.

For the first paper evaluation:

- allowed project record: provider, product name, product/index code, snapshot/effective date, availability timestamp rule, local SHA-256, row/count reconciliation, mapping coverage, and aggregate evaluation outputs where legally permitted;
- do **not** commit the purchased raw TOPIX month-end master to the public repository;
- do **not** publish a substitute reconstructed constituent/weight table merely to avoid the provider restriction;
- #50 must preserve the same rights boundary when mapping benchmark securities to WA Commons identities;
- if #50 requires public redistribution of constituent-level weights, it must stop and obtain a license/permission decision rather than silently expanding this #45 decision.

The evaluation specification already permits this pattern: when licensing prevents redistribution of raw benchmark data, the run manifest may record provider-native version identifiers and local content hashes so an authorized party can verify possession of the same input.

The total-return/index-level data also remains JPX intellectual property. Any public display, third-party provision or commercial use must follow the applicable JPX licensing terms. This research decision does not grant rights beyond the provider terms.

## Candidate decision table

| Candidate | Breadth / investability | Point-in-time constituents & weights | Total-return route | Rights / reproducibility | Decision |
|---|---|---|---|---|---|
| **TOPIX Total Return Index** | JPX describes TOPIX as broad Japanese-market coverage with investable-index functionality; free-float market-cap weighted | Official TOPIX month-end master; documented from 2015-11; local codes/ISIN support #50 mapping | `配当込みTOPIX` DataCube code `6000`; documented history from 1989-01-04 | Explicit paid self-use route; raw month-end master is not for external distribution, so use local licensed input + hashes | **ADOPT primary** |
| **MSCI Japan IMI Index** (`664171`) | Large/mid/small; MSCI says about 99% of Japan free-float-adjusted market cap; 956 constituents at 2026-08-31 | MSCI Index API / Index Deep History provides constituent histories under entitlement | MSCI publishes gross/net variants and monthly NETR-based analytics | Website index data is informational/non-commercial and redistribution is prohibited without written permission; deep history/API needs separate licensing | **WATCH** — technically excellent fallback, but less transparent licensing/access path for this open reproducibility workflow |
| **FTSE Japan All Cap Index** | GEIS All Cap = Large + Mid + Small; strong broad-market design | FTSE Russell offers historical constituents/weights for a selection of indices via subscription; public current/periodic constituent materials exist | Historical FTSE index level/return data available through subscription | Need provider confirmation that Japan All Cap has the exact historical constituent/weight entitlement needed for the selected period and what may be redistributed | **WATCH** — viable licensed fallback, but exact deep-history entitlement not yet pinned |
| **Nikkei 225 Total Return Index** | 225-stock, price-weighted underlying benchmark; materially narrower than the broad Japan-equity opportunity set | Nikkei provides current public data and paid professional weight/history services | Nikkei 225 Total Return Index exists; licensed/professional data route is explicit | Rights and professional data procedures are clear, but breadth fails the primary benchmark objective | **REJECT as primary** — may be preregistered later only as a secondary robustness comparison |
| Nikkei All Stock Index | Historically broad | Not relevant for a current benchmark | Was total-return | Calculation ceased 2021-06-25 | **REJECT** |

## Why MSCI Japan IMI is not primary despite wider stated market coverage

MSCI Japan IMI is a strong benchmark candidate and is intentionally retained as `WATCH`, not rejected. MSCI states that it covers approximately 99% of Japan's free-float adjusted market capitalization and includes large, mid and small caps.

However, #45 is not a contest for the index with the highest coverage percentage. The selected benchmark must also support transparent point-in-time reproducibility and a practical rights path. MSCI's public web Index Data is expressly limited to informational/non-commercial use and prohibits reproduction/redistribution without written permission. MSCI offers Index APIs and an Index Deep History product with historical constituent information, but those are entitlement/license products. No exact WA Commons entitlement or redistribution boundary has been established in this issue.

TOPIX therefore wins this first selection on the combined evidence of domestic benchmark fit, official point-in-time source specification, local-code mapping compatibility, total-return availability, and a concrete paid self-use route.

## Why FTSE Japan All Cap remains WATCH

FTSE Japan All Cap is also structurally suitable. FTSE GEIS defines All Cap as Large + Mid + Small, and LSEG publishes a Japan All-Cap constituent list and offers historical index/constituent data subscriptions.

The blocker to primary adoption is narrower: LSEG states that historical constituents and weights are available for **a selection of indices**, and this issue did not establish a provider entitlement statement guaranteeing the exact Japan All Cap history needed for the first evaluation period together with the permitted downstream use. That can be resolved later if TOPIX becomes unavailable or an independently motivated robustness benchmark is desired.

## No-performance / anti-gaming declaration

No candidate was chosen using historical return, Sharpe ratio, tracking performance, drawdown, or prospective WA Commons portfolio results. Search results or provider pages that happened to expose performance fields were not used as selection evidence.

The selection criteria were fixed by Issue #45 and `docs/PAPER_PORTFOLIO_EVALUATION.md`: breadth, investability, point-in-time membership/weights, total-return availability, reproducibility, and rights/access constraints.

`TOPIX Total Return Index` remains the primary benchmark even if the later Peace Capital portfolio compares poorly against it.

## Contract for downstream issues

### #47 — constructor research

#47 may now treat the primary benchmark selection as fixed. It must not replace TOPIX because another benchmark would make a constructor appear better.

### #50 — benchmark snapshot + TSE identity mapping

#50 must:

- acquire one explicitly pinned TOPIX month-end master through an authorized route;
- record effective date and actual source-availability semantics;
- retain the licensed raw file outside public Git history unless permission permits otherwise;
- compute and record a local SHA-256;
- map by strong identifiers onto #53 canonical TSE identities;
- report mapped/unmapped/disputed count and benchmark weight;
- fail closed if weights cannot be reconciled;
- not publish licensed constituent/weight rows unless the applicable permission expressly permits it.

### #56 / #51 — returns and integrated evaluation

Use the **TOPIX Total Return Index / 配当込みTOPIX (`6000`)** as the primary benchmark return basis. Candidate portfolio returns must be compared on the same total-return basis. Do not substitute the price-return TOPIX or Net Total Return (`6095`) silently.

The exact evaluation period and acquired source snapshots remain later bounded decisions, but they must be fixed before outcome inspection and must respect the 2015-11 point-in-time constituent-history boundary of the selected month-end-master route.

## Official sources reviewed

JPX:

- TOPIX overview / constituent information: https://www.jpx.co.jp/markets/indices/topix/
- TOPIX revisions: https://www.jpx.co.jp/markets/indices/revisions-indices/index.html
- TOPIX second-stage revisions: https://www.jpx.co.jp/markets/indices/revisions-indices/02.html
- J-Quants DataCube / historical information overview: https://www.jpx.co.jp/markets/paid-info-equities/historical/
- DataCube product/file specification (`TOPIX月末指数マスタ`, total-return index codes): https://db-ec.jpx.co.jp/client_info/JPX_DLSITE/html/data_detail.pdf
- DataCube price sheet / usage category notes: https://db-ec.jpx.co.jp/client_info/JPX_DLSITE/html/datacube_price.pdf
- JPX index licensing: https://www.jpx.co.jp/markets/indices/licence/
- index reference information / dividend-inclusive index service: https://www.jpx.co.jp/markets/paid-info-equities/reference/01.html

MSCI:

- MSCI Japan IMI Index (`664171`): https://www.msci.com/indexes/index/664171/msci-japan-imi-index
- MSCI Index Terms: https://www.msci.com/legal/index-terms
- MSCI Index API: https://developer.msci.com/apis/index-api
- MSCI Index Deep History: https://dataexplorer.msci.com/ui/products/DM_Index_Deep_History

FTSE Russell / LSEG:

- FTSE Global Equity Index Series / FTSE Japan All Cap: https://www.lseg.com/en/ftse-russell/indices/ftseall-world
- FTSE Russell index data subscriptions: https://www.lseg.com/en/ftse-russell/index-resources/indices-subscribe-data
- FTSE Japan All-Cap constituent list: https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ftse-all-cap-japan-index-constituent-list.pdf

Nikkei:

- Nikkei index licensing / professional data services: https://indexes.nikkei.co.jp/nkave/license/index.en.html
- Nikkei index data provision: https://indexes.nikkei.co.jp/nkave/data/index.en.html
- Nikkei 225 Total Return Index: https://indexes.nikkei.co.jp/en/nkave/index/profile?cid=4&idx=nk225tr

## Final disposition

`M3_2A_BENCHMARK_SELECTION = ADOPT`

Primary benchmark: **TOPIX Total Return Index / 配当込みTOPIX**  
Provider: **JPX Market Innovation & Research, Inc.**  
WA benchmark ID: **`JPX:TOPIX_TOTAL_RETURN:6000`**  
Return basis: **gross total return, JPY**  
Point-in-time constituent source: **TOPIX month-end index master, licensed local input, documented from 2015-11**  
Public raw constituent/weight redistribution: **not authorized by this decision**  
Portfolio performance inspected before decision: **NO**
