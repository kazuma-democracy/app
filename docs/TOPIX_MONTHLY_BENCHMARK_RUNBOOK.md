# TOPIX Monthly Benchmark Snapshot — local operator runbook

Status: **operator contract; no scheduler/runtime is created by this document**
Related: Issue #50 / M3.3b

## Purpose

Provide one bounded monthly task that an existing local AI/runtime can execute after JPX publishes the official TOPIX component-weight file.

The benchmark remains `JPX:TOPIX_TOTAL_RETURN:6000`. This task collects constituent membership/weights only; it does not ingest returns, construct portfolios, or make trading decisions.

## Official source

- page: `https://www.jpx.co.jp/markets/indices/topix/`
- CSV: `https://www.jpx.co.jp/automation/markets/indices/topix/files/topixweight_j.csv`
- JPX publication rule: the component-weight list is updated after 16:20 JST on the final business day of the following month.

Never infer readiness from the calendar alone. The downloaded CSV must itself contain the expected effective date.

## Local-AI task name

`TOPIX Monthly Benchmark Snapshot`

## Inputs

- expected effective date, e.g. `2026-08-31`;
- canonical #53 identity artifact;
- repository checkout at a verified commit;
- config `configs/m3-3b-topix-benchmark-v0.2.json` for the first pinned snapshot.

## Procedure

1. Fresh-read repository `main`, Issue #50, this runbook, and the pinned config.
2. Download the official CSV as exact bytes into a local evidence directory outside public Git history.
3. Record retrieval time and SHA-256 before parsing.
4. Parse only rows with an eight-digit `日付`, a security code, and a published percentage weight; footer/legal rows are not constituents.
5. Require every constituent row to match the expected effective date. If the file is still for an earlier month, stop with `NOT_YET_PUBLISHED` semantics; do not substitute current holdings or an ETF.
6. Map by exact canonical `JPX_SECURITY_CODE` only. Never use company-name similarity to create a link.
7. Preserve the provider-published rounded weight. Re-normalize only within the preregistered rounding tolerance and record the provider sum/gap and normalization method.
8. Run the mapping twice and require identical semantic mapping hashes.
9. Keep full rows local. Public output is aggregate manifest/provenance only.
10. If any identity is unresolved/disputed/outside the canonical universe, report its count and benchmark weight; do not hide it.

## Operator command

```powershell
python scripts/run_topix_benchmark_mapping.py `
  --public-weight <LOCAL_TOPIX_CSV> `
  --identity <LOCAL_TSE_IDENTITY_JSON> `
  --local-output <LOCAL_FULL_OUTPUT_JSON> `
  --public-output <PUBLIC_AGGREGATE_OUTPUT_JSON> `
  --code-commit <VERIFIED_GIT_SHA>
```

## Fail-closed conditions

Stop without producing acceptance if any of these occurs:

- source effective date is not the expected month-end;
- required headers are missing;
- duplicate normalized security codes exist;
- published weights are non-numeric/non-finite/negative;
- provider weight sum exceeds the pinned rounding tolerance;
- canonical identity has duplicate strong security IDs;
- repeated runs produce different semantic hashes;
- public output contains row-level constituent data or canonical entity IDs.

## Current validation evidence

On 2026-09-08, the live JPX CSV was still effective `2026-07-31`, so it is not the target #50 `2026-08-31` acceptance input.

A non-canonical operator validation against that live file produced:

- 1,637 constituent rows;
- raw SHA-256 `e8bb15ddbe6f65c11363fe1f816feabc125b8587c520f358dcf191a4e7db0ae7`;
- provider published weight sum `0.999996` and rounding gap `0.000004`;
- normalized benchmark sum `1.000000000000`;
- exact #53 mapping: 1,637 mapped, 0 unresolved, 0 disputed, 0 out-of-canonical-universe;
- identical semantic mapping SHA-256 on two runs: `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.

These numbers validate the operator path only. They are not the #50 target snapshot and must not be promoted to the M3.3b acceptance manifest.
