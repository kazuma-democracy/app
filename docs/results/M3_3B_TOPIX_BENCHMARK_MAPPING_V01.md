# M3.3b TOPIX benchmark snapshot + TSE mapping v0.1

Status: **BLOCKED_PUBLICATION_LAG -- official public 2026-08-31 component-weight file not yet published**
Issue: #50
Implementation branch: `feat/issue-50-topix-benchmark-mapping`
Implementation checkpoint before this record: `8a47c4a`

## 2026-09-08 source-route amendment -- official public component weights

New official-provider evidence found after the original #45/#50 implementation changes the access blocker without changing the selected benchmark.

JPX's TOPIX page publishes the official TOPIX component-weight list at:

- source page: `https://www.jpx.co.jp/markets/indices/topix/`
- CSV: `https://www.jpx.co.jp/automation/markets/indices/topix/files/topixweight_j.csv`

JPX states that the component-weight list is updated **after 16:20 JST on the final business day of the following month**. JPX separately directs users who require FFW and related primitive index inputs to J-Quants DataCube.

For #50, the newly adopted bounded alternative is therefore the same-provider official published constituent-weight file. The benchmark identity, effective date, return variant and strong-ID mapping policy are unchanged. The original licensed DataCube/CMV path remains supported as an audit/primitive-input route; it is no longer the only route for obtaining official constituent weights.

The public-weight route is versioned as `configs/m3-3b-topix-benchmark-v0.2.json` and records:

- target effective date `2026-08-31`;
- source availability `2026-09-30T16:20:00+09:00` under the JPX publication rule;
- weight basis `PROVIDER_PUBLISHED_WEIGHT`;
- provider published weights preserved locally before normalization;
- explicit rounding tolerance and proportional re-scaling to an exact 12-decimal sum of 1.0;
- official source URL/page, source SHA-256 and aggregate-only public output.

The operator remains local-input-only: no live download is introduced into PR CI. `docs/TOPIX_MONTHLY_BENCHMARK_RUNBOOK.md` defines the bounded local-AI task that obtains and hashes the official CSV before invoking the mapping CLI.

### Live operator validation, not target acceptance

On 2026-09-08 the live JPX CSV was still effective **2026-07-31**, not the pinned 2026-08-31 target. The raw file SHA-256 was `e8bb15ddbe6f65c11363fe1f816feabc125b8587c520f358dcf191a4e7db0ae7`.

A non-canonical two-run validation against the canonical #53 local identity artifact produced:

- 1,637 official component rows;
- provider weight sum `0.999996`, rounding gap `0.000004`;
- normalized benchmark sum `1.000000000000`;
- exact mapping: 1,637 mapped / 0 unresolved / 0 disputed / 0 out-of-canonical-universe;
- identical semantic mapping SHA-256 both runs: `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.

This proves the free official operator path works end-to-end, but it does **not** satisfy #50 because the provider file has not yet advanced to the pinned 2026-08-31 effective date.

### Fresh verification after the public-weight extension

- focused Issue #50 tests: **23 passed**;
- the original licensed-master CLI path remains covered by the same focused suite;
- malformed dated public rows fail closed rather than being filtered away;
- stale public source dates return machine-readable `NOT_YET_PUBLISHED` and create no acceptance outputs;
- the live 2026-07-31 operator validation maps twice to the same semantic hash;
- aggregate public output contains no row list, canonical entity IDs, or provider row-level weights;
- `git diff --check` is required clean before delivery;
- no market return, benchmark return, portfolio construction or performance output was inspected.

### Current resume condition

#50 resumes when the official JPX public component-weight CSV itself reports `20260831`. Then run the v0.2 mapping twice against the same canonical #53 identity artifact, require identical semantic hashes, verify the provider weight rounding gap is within the pinned tolerance, verify exact normalized weight reconciliation, verify aggregate-only public output, and only then create the measured acceptance manifest and close #50.

No ETF proxy, current-constituent substitution, name-only mapping or automatic paid purchase is required for this path.

## Original preregistered input contract (preserved for audit)

The benchmark remains the #45 decision; this issue does not re-select it.

- provider: JPX Market Innovation & Research, Inc. (JPX総研)
- benchmark: TOPIX Total Return Index / 配当込みTOPIX
- WA benchmark ID: `JPX:TOPIX_TOTAL_RETURN:6000`
- return index code: `6000`
- constituent product: TOPIX End of month Master Of Index / TOPIX月末指数マスタ
- constituent index code: `0000`
- effective snapshot: **2026-08-31**
- source availability used for no-look-ahead control: **2026-09-01T16:20:00+09:00 or later**
- weight reconstruction: provider `CMV` / total provider `CMV`
- semantic weight precision: 12 decimal places, `ROUND_HALF_EVEN`
- rights mode: licensed local self-use; raw constituent/weight rows are not published

The 2026-08-31 date is preregistered before any portfolio result inspection and matches the canonical #53 TSE universe effective date.

## Original implemented licensed path (preserved for audit)

The implementation is ready to consume the licensed file without adding a downloader or alternate data route.

1. The documented DataCube headers `Date`, `Local Code`, `Name`, `ISIN`, `CMV`, `Index Code`, and `Index Name` are validated.
2. JPX/DataCube five-character local codes reuse the existing strong security-code normalization (`72030 -> 7203`, `130A0 -> 130A`).
3. Rows must match the pinned date and `Index Code=0000`; duplicate normalized codes and non-positive/non-finite CMV fail closed.
4. Component weights are reconstructed deterministically from `CMV` and reconcile exactly to `1.000000000000` after canonical rounding.
5. Mapping uses exact #53 `JPX_SECURITY_CODE` only. Name/alias similarity never creates a mapping.
6. Canonical `CONFIRMED` becomes constructor-compatible `mapped`; `UNRESOLVED` becomes `unmapped/canonical_identity_unresolved`; `DISPUTED` stays `disputed`; absent canonical code becomes `unmapped/out_of_canonical_universe`.
7. Local output may retain licensed component rows and canonical entity IDs. Public output contains aggregate manifest fields only.
8. The operator CLI accepts local file paths only; it has no URL/download acquisition option.

Relevant implementation:

- `configs/m3-3b-topix-benchmark-v0.1.json`
- `src/wa_commons/portfolio/benchmark_snapshot.py`
- `scripts/run_topix_benchmark_mapping.py`
- `tests/test_topix_benchmark_snapshot.py`
- `tests/test_topix_benchmark_mapping.py`
- `tests/test_topix_benchmark_mapping_cli.py`
- `.github/workflows/topix-benchmark-mapping.yml`

## Verification before measured input

Fresh branch verification after Tasks 1-3:

- focused Issue #50 tests: **15 passed**
- full repository tests: **181 passed**
- `git diff --check`: no content errors
- baseline before #50 changes: **166 passed**
- no portfolio return, benchmark return, Sharpe ratio, drawdown or optimization result was inspected

The synthetic test rows are engineering fixtures only. They are **not** a measured benchmark snapshot and are not promoted into a public M3.3b manifest.

## Input search and blocker

The connected authorized workstation was searched before declaring the blocker:

- filenames containing `TOPIX` across accessible `C:\` paths;
- CSV content containing the official `Local Code` header under `C:\Users\wetli\Downloads`;
- CSV content containing `Local Code` under `C:\AI`;
- accessible filenames containing `20260831` across `C:\`.

No licensed TOPIX month-end master was found in those accessible locations. Some system paths are permission-inaccessible, so this is not a claim about inaccessible storage; it is sufficient to establish that the adopted local input is not presently available to this authorized workflow.

Current JPX DataCube terms/pricing reviewed for this task continue to describe TOPIX month-end master as a paid self-use product and prohibit external distribution. No purchase was made automatically.

## Original resume condition (superseded by the public-weight route)

Measured acceptance can resume only when the operator supplies the licensed **TOPIX End of month Master Of Index effective 2026-08-31** to the local workflow.

At that point #50 must:

1. compute and record the raw file SHA-256;
2. run the mapping CLI twice against the canonical #53 identity artifact;
3. require identical semantic mapping hashes;
4. require exact benchmark-weight reconciliation;
5. report mapped, unresolved-identity, disputed and out-of-canonical-universe count and benchmark weight;
6. verify the public manifest contains no row-level licensed identifiers or component weights;
7. only then create `docs/results/M3_3B_TOPIX_BENCHMARK_MAPPING_MANIFEST_V01.json`, mark ROADMAP complete and close #50.

No alternate benchmark, current public constituent list, reconstructed substitute table or name-only mapping is authorized by this blocker.

## Original disposition (superseded)

`M3_3B_BENCHMARK_MAPPING = BLOCKED_INPUT`

Implementation: **READY FOR LICENSED INPUT**
Measured 2026-08-31 benchmark snapshot: **NOT RUN**
Issue #50: **must remain OPEN**
Public row-level benchmark data: **NONE**
Real-money/trading authority: **NONE**

## Current disposition

`M3_3B_BENCHMARK_MAPPING = BLOCKED_PUBLICATION_LAG`

Public official-weight implementation: **READY**
Live operator validation: **PASSED FOR 2026-07-31 ENGINEERING VALIDATION ONLY**
Measured 2026-08-31 benchmark snapshot: **NOT YET AVAILABLE FROM THE PUBLIC FILE**
Issue #50: **must remain OPEN**
Paid month-end master required for constituent/weight acceptance: **NO under the amended official public-weight route**
Public row-level benchmark data committed by WA Commons: **NONE**
Real-money/trading authority: **NONE**
