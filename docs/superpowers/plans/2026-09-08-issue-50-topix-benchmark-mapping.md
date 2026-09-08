# Issue #50 TOPIX Benchmark Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, local-input-only mapping of the pinned 2026-08-31 TOPIX month-end index master onto the #53 canonical TSE identity universe, with CMV-derived weights and aggregate-only publication.

**Architecture:** Extend the existing `wa_commons.portfolio` lane with one benchmark-snapshot module. Parse only the documented JPX DataCube TOPIX headers, reconstruct weights from `CMV`, normalize the provider five-character `Local Code` with the existing strong-code normalization, then map exactly to #53 `JPX_SECURITY_CODE`. Row-level licensed data stays local; Git history receives config, tests, code, CI, and aggregate/blocker documentation only.

**Tech Stack:** Python 3.11 stdlib (`csv`, `decimal`, `hashlib`, `json`), existing WA identity normalization and pytest.

**Spec:** GitHub Issue #50; `docs/results/M3_2A_BENCHMARK_SELECTION_V01.md`; `docs/results/M3_2B2_TSE_IDENTITY_SPINE_V01.md`; `docs/PAPER_PORTFOLIO_EVALUATION.md`.

## Global Constraints

- Benchmark is fixed: `JPX:TOPIX_TOTAL_RETURN:6000`, gross total return, JPY.
- Constituent source is the licensed/self-use TOPIX month-end index master; raw rows are never committed or publicly redistributed.
- Snapshot is preregistered as effective `2026-08-31`, available no earlier than `2026-09-01T16:20:00+09:00`.
- TOPIX constituent index code is exactly `0000`; component weights are reconstructed from provider `CMV`, not an invented weight column.
- Mapping uses exact provider `Local Code` -> canonical `JPX_SECURITY_CODE`; company/security names never create a link.
- Canonical unresolved/disputed identity remains explicit; no forced mapping.
- No market returns, corporate actions, optimizer behavior, portfolio construction, or performance inspection.
- Missing licensed raw snapshot blocks measured acceptance; it does not authorize a substitute source.

---
### Task 1: Pin the TOPIX snapshot contract and reconstruct weights

**Files:**
- Create: `configs/m3-3b-topix-benchmark-v0.1.json`
- Create: `src/wa_commons/portfolio/benchmark_snapshot.py`
- Create: `tests/test_topix_benchmark_snapshot.py`

**Interfaces:**
- Consumes: JPX DataCube CSV rows with documented headers `Date`, `Local Code`, `Name`, `ISIN`, `CMV`, `Index Code`, `Index Name`.
- Produces: `build_topix_snapshot(rows, config, source_sha256) -> dict` with deterministic local rows and semantic manifest.

- [ ] **Step 1: Write failing parser/weight tests.** Cover exact `20260831` date, `Index Code=0000`, duplicate code rejection, wrong-date/index rejection, positive finite CMV, order independence, `72030 -> 7203`, `130A0 -> 130A`, and exact 12-decimal weight sum.
- [ ] **Step 2: Run `python -m pytest -q tests/test_topix_benchmark_snapshot.py` and verify RED** because the module does not exist.
- [ ] **Step 3: Add the pinned config** with `benchmark_id=JPX:TOPIX_TOTAL_RETURN:6000`, `effective_date=2026-08-31`, `available_at=2026-09-01T16:20:00+09:00`, `index_code=0000`, `return_index_code=6000`, `weight_basis=CMV`, `semantic_weight_decimals=12`, and local-only rights flags.
- [ ] **Step 4: Implement minimal deterministic reconstruction.** Use `Decimal(str(row["CMV"]))`; divide by total CMV; quantize `ROUND_HALF_EVEN`; allocate any rounding residual to the largest weight with `security_id` tie-break; emit `security_id=f"TSE:{normalized_code}"`.
- [ ] **Step 5: Run the focused test and verify GREEN.**
- [ ] **Step 6: Commit:** `feat: add pinned TOPIX benchmark snapshot reconstruction`.

### Task 2: Map the snapshot to canonical TSE identities

**Files:**
- Modify: `src/wa_commons/portfolio/benchmark_snapshot.py`
- Create: `tests/test_topix_benchmark_mapping.py`

**Interfaces:**
- Consumes: Task 1 snapshot plus #53 `tse-identity-local.json` shape.
- Produces: `map_topix_snapshot(snapshot, identity) -> dict` with `mapped/unmapped/disputed` constructor-compatible state plus explicit mapping reason.
- [ ] **Step 1: Write failing mapping tests.** Exact code + `CONFIRMED` -> `mapped/exact_jpx_security_code`; exact code + `UNRESOLVED` -> `unmapped/canonical_identity_unresolved`; exact code + `DISPUTED` -> `disputed/canonical_identity_disputed`; absent code -> `unmapped/out_of_canonical_universe`; duplicate canonical security identifiers fail closed; same name with wrong code never maps.
- [ ] **Step 2: Run `python -m pytest -q tests/test_topix_benchmark_mapping.py` and verify RED.**
- [ ] **Step 3: Implement exact mapping.** Build one index from canonical identifier scheme `JPX_SECURITY_CODE`; preserve `canonical_entity_id` only in local output; never compare `Name` or aliases.
- [ ] **Step 4: Add aggregate reconciliation.** Report count and benchmark weight for mapped, unresolved-identity, disputed, and out-of-universe buckets; require total benchmark weight `1.000000000000`.
- [ ] **Step 5: Run Task 1+2 tests and verify GREEN.**
- [ ] **Step 6: Commit:** `feat: map TOPIX benchmark to canonical TSE identities`.

### Task 3: Enforce local-only publication and add operator CLI

**Files:**
- Modify: `src/wa_commons/portfolio/benchmark_snapshot.py`
- Create: `scripts/run_topix_benchmark_mapping.py`
- Create: `tests/test_topix_benchmark_mapping_cli.py`
- Create: `.github/workflows/topix-benchmark-mapping.yml`

**Interfaces:**
- Consumes: local licensed CSV, local #53 identity JSON, committed config.
- Produces: local row-level JSON plus public aggregate manifest containing no component identifiers or weights.

- [ ] **Step 1: Write failing IO/CLI tests.** Same output path fails; public JSON contains no `rows`, `entity_id`, `isin`, `local_code`, or 4/5-character constituent list; CLI has no downloader/network option.
- [ ] **Step 2: Run CLI tests and verify RED.**
- [ ] **Step 3: Implement `write_topix_benchmark_mapping(...)`.** Local JSON retains mapped rows; public JSON retains source SHA, config hash, identity hash, effective/available timestamps, aggregate mapping counts/weights, and semantic hash only.
- [ ] **Step 4: Implement local-input-only CLI.** Required args: `MASTER_CSV IDENTITY_JSON LOCAL_OUTPUT PUBLIC_OUTPUT`; optional `--config` defaults to the pinned config.
- [ ] **Step 5: Add focused GitHub Actions workflow** running the three #50 test files and `--help` network-boundary check.
- [ ] **Step 6: Run focused tests and full suite.**
- [ ] **Step 7: Commit:** `feat: add local TOPIX benchmark mapping runner`.
### Task 4: Record the measured-input blocker without weakening acceptance

**Files:**
- Create: `docs/results/M3_3B_TOPIX_BENCHMARK_MAPPING_V01.md`
- Modify only after real licensed run: `docs/results/M3_3B_TOPIX_BENCHMARK_MAPPING_MANIFEST_V01.json`
- Modify only after acceptance: `ROADMAP.md`

**Interfaces:**
- Consumes: results of Tasks 1-3 and presence/absence of the licensed `2026-08-31` TOPIX master.
- Produces: truthful public status; no synthetic fixture is promoted to measured acceptance.

- [ ] **Step 1: Search authorized local storage for the licensed 2026-08-31 TOPIX month-end master.** If absent, record `M3_3B_BENCHMARK_MAPPING = BLOCKED_INPUT` and the exact required product/snapshot; do not buy data or substitute another source without user authorization.
- [ ] **Step 2: If the licensed file is present, run the CLI twice.** Require identical semantic hashes, exact weight reconciliation, and explicit mapped/unresolved/disputed/out-of-universe counts and weights.
- [ ] **Step 3: If absent, leave Issue #50 open and do not mark ROADMAP complete.** Publish only implementation verification and the input blocker.
- [ ] **Step 4: Run `git diff --check` and `python -m pytest -q`; inspect public files for row-level leakage.**
- [ ] **Step 5: Push a branch/PR.** Use Draft if measured acceptance remains blocked; Ready only when real licensed input has passed acceptance.

## Self-review

- Spec coverage: parser/weights, exact strong-ID mapping, unresolved/disputed/out-of-universe reporting, no-look-ahead timestamps, rights boundary, deterministic rerun, CLI, CI, and blocker behavior are each assigned to a task.
- Placeholder scan: no implementation step relies on TBD/TODO behavior.
- Type consistency: Task 1 emits `security_id` and `benchmark_weight`; Task 2 adds constructor-compatible `mapping_state`; Task 3 serializes the same payload; Task 4 consumes it without changing semantics.

Execution choice resolved from the user's repeated `続けて`: **Inline Execution** in this session, using `superpowers:executing-plans` with TDD checkpoints.
