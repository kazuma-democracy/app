# M3.3c0 Free Monthly Source Contract v0.1

Issue: #78
Status: PREREGISTERED_SOURCE_CONTRACT

## Decision

M3 v1 uses a zero-purchase, zero-subscription, calendar-month evaluation route. It does not adopt the previously investigated paid DataCube plus paid corporate-action service route.

The free route is intentionally local-first:

- September 2026 TSE Monthly Stock Price Table supplies the 2026-09-30 start close.
- October 2026 TSE Monthly Stock Price Table supplies the 2026-10-30 end close.
- JPX dividend-included index monthly ROI supplies the October 2026 TOPIX Total Return benchmark return.
- TSE Monthly Statistics Report and JPX ex-rights information act as corporate-action detectors.
- Issuer IR, TSE Listed Company Search / TDnet, EDINET, and JPX rights/listing information resolve held-security events from primary evidence.

## Acquisition boundary

All recurring JPX monthly source files are acquired manually after publication, then stored locally with retrieval timestamp and SHA-256. WA Commons does not run high-frequency scraping and does not maintain a whole-market daily return store for M3 v1.

Only held-security rows required by a run are parsed downstream. Raw JPX tables and issuer documents remain local-only and are not committed to the repository.

## Why paid products are not adopted

The earlier paid route solved a broader problem: daily all-market prices plus complete corporate-action infrastructure. M3 v1 only needs one preregistered monthly holding-period comparison and event resolution for securities actually held. The free official-source route satisfies that narrower requirement without a paid feed or subscription.

This change was made before any October candidate return, benchmark return, or tracking result was observed.

## Detector semantics

Monthly JPX action/change lists are detectors, not proof that no cash dividend exists. Absence from a detector never becomes `NO_RELEVANT_ACTION_CONFIRMED` by itself. Held-security evidence resolution must follow the configured primary-evidence priority and fail closed when an amount, date, ratio, consideration, or status remains unresolved.

## Publication boundary

Publicly downloadable does not mean unrestricted redistribution. Project policy therefore keeps raw market rows and raw issuer documents local-only. Repository-safe outputs may contain source locators, retrieval timestamps, hashes, methodology identifiers, coverage/block counts, and other WA Commons-created provenance or aggregate facts.

Publication of actual market-performance numbers is a separate rights check. The preregistration contract does not invent that permission.

## Official locator families

- TSE Monthly Stock Price Table: https://www.jpx.co.jp/markets/statistics-equities/price/
- TSE Monthly Statistics Report: https://www.jpx.co.jp/markets/statistics-equities/monthly/
- Dividend-included index monthly ROI: https://www.jpx.co.jp/markets/indices/related/ratio/
- TDnet overview: https://www.jpx.co.jp/equities/listing/disclosure/tdnet/index.html
- TDnet public viewing: https://www.jpx.co.jp/listing/disclosure/01.html
- EDINET API guide: https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WEEK0060.html
- JPX ex-rights information: https://www.jpx.co.jp/listing/others/ex-rights/index.html

## Handoff

Issue #78 fixes source roles and rights boundaries only. It does not download October market rows, implement parsers, resolve actual held-security events, or calculate performance. Those actions remain #56 work.

## Return and action semantics

The downstream #56 implementation must calculate one monthly gross total-wealth return. Start wealth is based on frozen position units/weights and the 2026-09-30 closing price. End wealth uses the 2026-10-30 closing price, only explicitly evidenced action-adjusted units, and explicit cash dividends or cash consideration attributable to the holding.

Cash distributions remain cash through the endpoint. Synthetic reinvestment is prohibited for M3 v1. A split ratio, merger conversion, cash-out amount, or delisting treatment may never be inferred from a price jump.

Any unresolved start/end price, dividend amount, action term, identity, or contradictory action record fails closed. Missing rows are never zero-filled and name-only security relinking is prohibited.

## Parser contract for #56

Issue #78 does not implement parsers. It requires #56 to:

- map only by exact JPX security code;
- extract only held-security rows needed by the run;
- record source SHA-256, retrieval timestamp, and source locator;
- detect duplicate/conflicting rows and BLOCK;
- never zero-fill a missing price/action;
- preserve the configured held-security and snapshot terminal states exactly.
