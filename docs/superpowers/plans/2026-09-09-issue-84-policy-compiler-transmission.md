# Issue #84 Policy Compiler v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, market-data-free Policy Compiler that turns the accepted #50 TOPIX weights plus #55 policy screening into frozen P0/P1/P2 target allocations and Policy Transmission metrics.

**Architecture:** Add a small compiler beside the existing portfolio constructor rather than modifying or deleting `benchmark-l2-projection`. The compiler joins #50 and #55 only by canonical entity identity, applies preregistered decision multipliers with Decimal arithmetic, reports coverage uncertainty separately, attributes all active weight changes to direct policy instructions or deterministic normalization redistribution, and writes row-level output locally while publishing aggregate/provenance only.

**Tech Stack:** Python 3.11, stdlib `decimal/hashlib/json/pathlib`, pytest. No new runtime dependency.

**Spec:** `docs/superpowers/specs/2026-09-09-peace-capital-policy-transmission-replay-design.md`

## Global Constraints

- Paper/research only; no broker or real-money authority.
- Compiler API accepts no price, return, dividend, corporate-action or market-data inputs.
- Pin benchmark semantic mapping SHA `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.
- Pin screening SHA `aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c`.
- Pin strict profile `example:strict-military-avoidance` version `1`, policy SHA `7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c`.
- P0: all decisions 1.0. P1: EXCLUDE 0.0, WATCH/NONE 1.0. P2: EXCLUDE 0.0, WATCH 0.5, NONE 1.0.
- `unknown`, `unresolved_identity`, and `not_integrated` remain weight-neutral in v0 and are reported separately; `no_match` is not relabeled safe.
- No multiplier above 1.0, no top-N/min-weight pruning, no expected-return or TE optimizer.
- 12-decimal semantic weights, `ROUND_HALF_EVEN`, deterministic ordering/hashes.
- Existing `src/wa_commons/portfolio/constructor.py` remains unchanged unless a test proves a shared helper is strictly necessary.

---
### Task 1: Pin the compiler contract and fail-closed input validation

**Files:**
- Create: `configs/m3-3b2-policy-compiler-v0.1.json`
- Create: `src/wa_commons/portfolio/policy_compiler.py`
- Create: `tests/test_policy_compiler.py`

**Interfaces:**
- Consumes: #50 benchmark mapping payload, #55 local screening payload, compiler config.
- Produces: `load_policy_compiler_config(path) -> dict` and `compile_policy_family(benchmark_mapping, screening, config) -> dict`.

- [ ] **Step 1: Write failing contract tests**

```python
def test_config_pins_three_preregistered_arms():
    config = load_policy_compiler_config(CONFIG)
    assert [arm["arm_id"] for arm in config["arms"]] == ["P0", "P1", "P2"]
    assert config["arms"][2]["decision_multipliers"]["WATCH"] == "0.5"
    assert config["market_data_inputs_allowed"] is False


def test_wrong_input_hash_blocks():
    benchmark, screening, config = minimal_inputs()
    benchmark["manifest"]["semantic_mapping_sha256"] = "0" * 64
    result = compile_policy_family(benchmark, screening, config)
    assert result["status"] == "BLOCK_INPUT_VERSION"
```

- [ ] **Step 2: Run `python -m pytest tests/test_policy_compiler.py -q` and verify RED because the module/config do not exist.**
- [ ] **Step 3: Add the exact config and minimal validation implementation.** Reject duplicate benchmark entities/security IDs, missing strict-profile views, non-confirmed benchmark identities, unsupported decisions/multipliers, wrong input hashes, and all-zero allocation.
- [ ] **Step 4: Re-run the focused tests and verify GREEN.**
- [ ] **Step 5: Commit `test/feat: pin Policy Compiler v0 contract`.**

### Task 2: Compile deterministic allocations, transmission metrics, and attribution

**Files:**
- Modify: `src/wa_commons/portfolio/policy_compiler.py`
- Modify: `tests/test_policy_compiler.py`

**Interfaces:**
- `compile_policy_family(...)` returns `{status, artifact_version, arms, manifest}`.
- Each arm returns `arm_id`, `status`, `target_weights`, `instructions`, `metrics`, and `semantic_target_sha256`.

- [ ] **Step 1: Add RED tests for P0/P1/P2 arithmetic and ordering.**

```python
def test_p2_underweights_watch_and_reports_reallocation():
    result = compile_policy_family(*three_security_fixture())
    p2 = next(arm for arm in result["arms"] if arm["arm_id"] == "P2")
    assert p2["status"] == "POLICY_TRANSMISSION_OK"
    assert p2["metrics"]["active_share"] == p2["metrics"]["reallocation_mass"]
    assert p2["metrics"]["underweighted_benchmark_weight"] == "0.200000000000"
    assert p2["metrics"]["changed_security_count"] == 3


def test_input_order_does_not_change_target_hash():
    left = compile_policy_family(*fixture(order="forward"))
    right = compile_policy_family(*fixture(order="reverse"))
    assert [a["semantic_target_sha256"] for a in left["arms"]] == [a["semantic_target_sha256"] for a in right["arms"]]
```

- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement Decimal reweighting:** sort by `security_id`, compute `raw = benchmark_weight * multiplier`, normalize, quantize to 12 decimals with half-even, and place any residual deterministically on the largest eligible target weight then `security_id`.
- [ ] **Step 4: Implement metrics:** `0.5 * sum(abs(target-benchmark))`, direct instruction benchmark weight, changed count, max absolute change, holding count, HHI/concentration summary, and coverage-state benchmark mass.
- [ ] **Step 5: Implement attribution:** direct non-neutral rows get deterministic instruction IDs from arm/entity/decision/multiplier/decisive claim refs; neutral rows changed only by renormalization carry `NORMALIZATION_REDISTRIBUTION` plus the sorted direct instruction IDs that caused redistribution. Every non-zero allocation delta must have non-empty attribution.
- [ ] **Step 6: Verify focused GREEN and commit `feat: compile policy transmission allocations`.**

### Task 3: Add CLI and local/public output boundary

**Files:**
- Create: `scripts/run_policy_compiler.py`
- Modify: `tests/test_policy_compiler.py`

**Interfaces:**
- CLI: `--benchmark`, `--screening`, `--config`, `--local-output`, `--public-output`, `--code-commit`.
- Writer: `write_policy_transmission(payload, local_output, public_output)`.

- [ ] **Step 1: Add RED tests that the CLI rejects identical local/public paths and that the public artifact contains no `target_weights`, `instructions`, claim text, or row-level company data.**
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement the CLI using existing JSON runner patterns.** It must load only benchmark/screening/config inputs; there is no market-data argument.
- [ ] **Step 4: Implement the writer.** Local output contains the complete compiler payload. Public output contains only artifact/version/input hashes, frozen policy-family hash, arm IDs/statuses/aggregate transmission metrics, target semantic hashes, paper-only flags and code commit.
- [ ] **Step 5: Run focused tests and commit `feat: add Policy Compiler CLI and publication boundary`.**

### Task 4: Run the accepted current snapshot and publish the pre-return result

**Files:**
- Create: `docs/results/M3_3B2_POLICY_TRANSMISSION_MANIFEST_V01.json`
- Create: `docs/results/M3_3B2_POLICY_TRANSMISSION_V01.md`
- Optionally create: `.github/workflows/policy-compiler.yml` only if it can validate repo-safe fixtures/config without requiring private local artifacts.

**Exact local inputs:**
- Benchmark source CSV: `C:\AI\wa-commons-m3-20260908\local-artifacts\topix-public-operator-validation-final\topixweight_j.csv`.
- Identity input for deterministic #50 regeneration: `C:\AI\wa-commons-m3-20260908\local-artifacts\tse-identity-local-rerun.json`.
- Accepted #55 screening: `C:\AI\wa-commons-m3-20260908\local-artifacts\tse-policy-screening-local-v01-rerun.json`.
- Regenerated #50 mapping must reproduce semantic SHA `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409` before compiler execution.

- [ ] **Step 1: Re-run #50 mapping locally into an external/local-only directory and verify the exact accepted semantic mapping SHA.**
- [ ] **Step 2: Run #84 compiler using the accepted #55 local artifact and exact config; do not load any return/price/dividend data.**
- [ ] **Step 3: Independently validate invariants:** all arm weights sum to exactly `1.000000000000`; P0 is zero-transmission; P1 reflects existing strict semantics; P2 result follows the fixed 0.5 WATCH multiplier; all non-zero deltas are attributable; public artifact has no row-level weights.
- [ ] **Step 4: Record measured counts/weights/hashes in the result document without claiming financial outperformance.** Current pre-implementation observation: strict WATCH intersects TOPIX in 6 securities with benchmark weight `0.012053048212`; this is a pre-return treatment fact, not a performance result.
- [ ] **Step 5: Run `python -m pytest tests/test_policy_compiler.py -q`, then the full `python -m pytest -q`, then `git diff --check`.**
- [ ] **Step 6: Commit `docs: record M3.3b2 policy transmission proof`.**

## Self-review checklist

- Every spec requirement for P0/P1/P2, no market input, fail-closed identity/versioning, deterministic hashes, attribution, coverage mass and publication boundary is assigned to a task.
- Historical Replay is absent from implementation tasks and remains #85.
- No positive overweight, TE optimizer, daily data store or TOPIX100 shrink is introduced.
- No placeholder marker remains in this plan.
- Function names and output fields are consistent across tasks.
