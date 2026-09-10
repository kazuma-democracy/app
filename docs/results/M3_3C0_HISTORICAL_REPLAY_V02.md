# M3.3c0 Historical Replay investable-proxy real-data gate v0.2

Issue: #85
Status: `BLOCK_HISTORICAL_REPLAY_COVERAGE`
Selection mode: `METADATA_ONLY_NO_RETURNS`
Code under qualification: `c6659992978cbda3d2c88cc162d4ce10db6d84c9`

## Result

The approved investable-proxy implementation reached the real Q1 qualification gate, but the preregistered 2026-01 through 2026-03 headline window did not freeze.

The terminal gate is fail-closed. All three months return `BLOCK_REPRODUCIBILITY / PRESELECTION_MARKET_VALUE_INSPECTION`, so the frozen window is empty. An independent metadata-only availability audit, with the known contamination guard disabled solely to isolate source timing, returns `BLOCK_EVIDENCE_CUTOFF / CONTROL_AVAILABILITY_UNVERIFIED` for all three months.

No Q1 security return, 1475 return, TOPIX Total Return value, market-price performance series, or replay financial result was loaded after the gate. The market-data and replay-execution stages were not entered.

This is not a negative investment-performance result. It is a source/selection-integrity result.

## Why Q1 is no longer headline-eligible

The original v0.2 preregistration treated 2026-01, 2026-02 and 2026-03 as the clean candidate window. During the real-data qualification work on 2026-09-10, a metadata-inspection command accidentally printed one holdings row from each dated 1475 CSV, including Market Value and Weight, before the window had frozen.

The approved design prohibits pre-freeze market-value inspection. The implementation now records `preselection_contaminated_periods = [2026-01, 2026-02, 2026-03]` and blocks those periods even if a later operator supplies otherwise valid candidate metadata. This prevents the same Q1 window from being silently rehabilitated later.
## Independent availability blocker

Q1 is independently blocked even if the contamination guard is disabled for diagnostic purposes. The dated BlackRock holdings CSVs are still retrievable today, but the original publication time for the 2025-12-30, 2026-01-30 and 2026-02-27 snapshots could not be established at or before the respective decision cutoffs.

Current HTTP responses expose neither historical `Last-Modified` nor ETag metadata, and the checked web archive route did not provide a Q1 capture. The file's holdings `as_of_date` therefore cannot be substituted for `available_at`.

With only the contamination guard disabled, all three months deterministically return `BLOCK_EVIDENCE_CUTOFF / CONTROL_AVAILABILITY_UNVERIFIED`. This is a second, independent reason that Q1 cannot freeze.

## Source-rights boundary

BlackRock Japan's site terms were checked on 2026-09-10. Private-use storage, display and analysis are permitted within the checked terms, while redistribution/publication remains restricted. WA Commons therefore treats the dated 1475 raw holdings as `LOCAL_RESEARCH_ALLOWED_RAW_LOCAL_ONLY` and does not commit raw third-party rows.

This rights result does not cure the historical availability blocker. Rights to analyze a file today are separate from proof that the file was historically available by a replay cutoff.

## What v0.2 capability now provides

The v0.2 path can parse dated 1475 holdings deterministically, rebuild historical EDINET strong-ID bridges, select MOD evidence by cutoff availability, bind the frozen #84 P0/P1/P2 semantics, freeze targets before returns, calculate the residual-sleeve policy consequence model, and execute a frozen investable-proxy replay after all pre-return gates pass.

The 1475 allocation remains an investable proxy control, not an assertion of official historical TOPIX constituent weights. TOPIX Total Return remains a separate external benchmark. These capabilities are validated synthetically and by focused regression tests; the real Q1 result remains BLOCKED.
## Preserved leak-safe boundaries

- No Q1 return, market-price performance series, TOPIX Total Return value or replay financial result was loaded after the qualification gate.
- No later month was substituted after Q1 failed.
- 2026-04 through 2026-08 remain engineering-validation periods for the first headline replay.
- 2026-10 remains the separate true future holdout.
- Current constituents, current screening states and current corporate bridges are not projected backward.
- Missing historical `available_at` remains a blocker rather than being inferred from the holdings date.

## Repository-safe audit hashes

The real qualification used code commit `c6659992978cbda3d2c88cc162d4ce10db6d84c9`.

- candidate inventory SHA-256: `7deeab63effb11ba20a9e7fa5512a82d1c5077c3a1ce6cc4a8e4f13f85565998`
- qualification output SHA-256: `7117b6f80489f20fb59daa9b7b0043e0f2e5e08948a2652c1c20e741f5d538b8`
- independent availability audit SHA-256: `2fec9cc2daf70289ec77ddaa054c21036dd64730996b63379a04ffd94ab843bb`
- v0.2 config SHA-256 at qualification: `6d5c6507219777931fb4ce1ceaac0f29f8ad39a45c06310e55bf5aed39a9ba81`
- repository-safe result semantic SHA-256: `14eb30b5fab8ae58767470b977fb3fca7bcfd195d195da759fb0c3c2e81ba12a`

The dated 1475 source-byte hashes are recorded in `M3_3C0_HISTORICAL_REPLAY_V02_MANIFEST.json`; the raw CSV rows remain local-only.

## Current issue state

Issue #85 remains OPEN. The implementation capability is substantially complete, but the real three-month Historical Replay definition of done has not been reached because no headline window is frozen and no real replay financial result exists.

The next valid headline attempt requires a newly preregistered three-consecutive-month window whose point-in-time control availability can be proven before each decision cutoff and whose selection inputs have not been inspected beyond the allowed metadata boundary. The method must not be chosen or changed using observed returns.
