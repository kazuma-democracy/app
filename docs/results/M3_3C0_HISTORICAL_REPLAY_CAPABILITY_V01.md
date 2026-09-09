# M3.3c0 Historical Replay capability audit v0.1

Issue: #85
Status: `BLOCK_HISTORICAL_REPLAY_COVERAGE`
Selection mode: `METADATA_ONLY_NO_RETURNS`
Code under validation: `20e8ce1568a6f05567c63bc37ed0d0a531c51bf6`

## Result

WA Commons cannot currently freeze a valid first three-month Historical Replay window under the approved leak-safe rules.

This is a fail-closed result, not a failed attempt to optimize performance. No candidate portfolio return, security return, benchmark return value, or market price was loaded to choose the window.

The metadata-only qualifier evaluated completed 2026 candidate months from January through August. January-June and August block because a reproducible point-in-time TOPIX constituent/weight snapshot is not available in the adopted local zero-cost evidence set. July is separately excluded because it was already used for parser/schema engineering validation under #56.

Therefore no three consecutive eligible months exist and the frozen window is empty.
## Benchmark evidence observed

The accepted #50 benchmark snapshot is effective `2026-07-31` and was available only after `2026-08-31T16:20:00+09:00`.

The three local TOPIX weight CSV copies inspected for this audit are byte-identical. Their SHA-256 is:

`e8bb15ddbe6f65c11363fe1f816feabc125b8587c520f358dcf191a4e7db0ae7`

All three are the same accepted #50 snapshot; they do not provide three historical month-end snapshots.

JPX documents that the public TOPIX component-weight list is replaced/updated after 16:20 JST on the final business day of the following month. JPX directs users seeking historical TOPIX constituent information to J-Quants DataCube / the end-of-month index master.

No paid or newly licensed historical substitute was adopted inside #85. The existing zero-cost source contract remains authoritative.

## Why current constituents are not substituted

Using the current TOPIX constituent list for an earlier replay month would create survivorship and look-ahead leakage. The approved design explicitly prohibits that shortcut.
Likewise, the current #55 screening output is not projected backward. A replay month needs a cutoff-complete screening/evidence artifact whose source availability is demonstrably at or before that month's decision cutoff.

An underlying contract or event having occurred earlier is not enough if WA Commons cannot prove when the evidence was historically available.

## Preserved boundaries

- July 2026 remains `ENGINEERING_VALIDATION_ONLY` and cannot become the first headline replay month.
- October 2026 remains the separate true future holdout.
- No current benchmark constituents or evidence states are back-projected.
- No return value is used to qualify, reject, or reorder candidate months.
- Missing point-in-time inputs remain blockers rather than zero-fill or silent substitution.

## Next capability step

The freeze engine and metadata-only gate are implemented. A real three-month replay becomes executable only when three consecutive cutoff-valid benchmark/screening snapshots can be reconstructed under the adopted source/rights contract.

The separate frozen-window replay engine may still be implemented and tested with synthetic fixtures without weakening this real-data BLOCK result.

## Reproduction

Inputs:

- `configs/m3-3c0-historical-replay-v0.1.json`
- `configs/m3-3c0-historical-replay-candidates-v0.1.json`

Output:

- `docs/results/M3_3C0_HISTORICAL_REPLAY_CAPABILITY_MANIFEST_V01.json`

Run `scripts/run_historical_replay_qualification.py` with only the config, candidate metadata, output path, and verified code commit. The qualification CLI intentionally has no price or return arguments.
