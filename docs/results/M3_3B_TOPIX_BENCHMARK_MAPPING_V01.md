# M3.3b TOPIX benchmark snapshot + TSE mapping v0.1

Status: **BLOCKED_INPUT — licensed 2026-08-31 TOPIX month-end master required**  
Issue: #50  
Implementation branch: `feat/issue-50-topix-benchmark-mapping`  
Implementation checkpoint before this record: `8a47c4a`

## Pinned input contract

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

## Implemented bounded path

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

## Resume condition

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

## Disposition

`M3_3B_BENCHMARK_MAPPING = BLOCKED_INPUT`

Implementation: **READY FOR LICENSED INPUT**  
Measured 2026-08-31 benchmark snapshot: **NOT RUN**  
Issue #50: **must remain OPEN**  
Public row-level benchmark data: **NONE**  
Real-money/trading authority: **NONE**
