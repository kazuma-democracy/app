# M2.2b Policy Screening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce deterministic company-level research views for all 100 fixed companies across all current example user-policy profiles using the completed #42 coverage artifact and current M1 Evidence Graph.

**Architecture:** Reuse the existing claim-level `evaluate_claim` evaluator. A new company-view layer maps M1 corporate-number subjects onto the fixed TSE identity cohort through a pinned derived bridge, aggregates claim results per company/profile, and carries #42 coverage states alongside the decision so `NONE` never means PASS. The measured workflow regenerates both the M1 graph and #42 coverage artifact before screening.

**Tech Stack:** Python 3.11, existing WA Commons policy/evidence modules, pytest, GitHub Actions.

**Spec:** GitHub Issue #43.

## Global Constraints

- Implement only #43; do not start #44 or M3 work.
- Use existing example policies, existing Evidence Graph, and completed #42 coverage semantics.
- Add no new evidence adapter or entity resolver.
- Preserve `EXCLUDE / WATCH / NONE`, claim-level reasons, and `UNKNOWN / DISPUTED / EXPIRED / unresolved_identity / no_match / not_integrated` distinctions.
- Every non-`NONE` company decision must carry claim, rule, and source references.
- Record Evidence Graph hash plus policy id/version/hash.
- Missing coverage or zero linked claims must never become PASS/clean/safe.

---

### Task 1: Company-level aggregation contract

**Files:**
- Create: `tests/test_company_policy_screening.py`
- Create: `src/wa_commons/policy/company_view.py`

**Interfaces:**
- Consumes: #42 coverage artifact dict, M1 canonical graph dict, example policy dicts, fixed identity bridge dict.
- Produces: `build_company_research_views(...) -> dict` and deterministic `canonical_sha256(...)`.

- [ ] Write failing tests for 100%-explicit company/profile views, EXCLUDE>WATCH>NONE aggregation, UNKNOWN/DISPUTED/EXPIRED handling through the existing evaluator, traceable non-NONE references, coverage uncertainty retention, zero-evidence NONE semantics, and deterministic input-order independence.
- [ ] Run `python -m pytest -q tests/test_company_policy_screening.py` and record RED because `wa_commons.policy.company_view` does not yet exist.
- [ ] Implement the smallest aggregation layer that satisfies those tests without changing claim-level evaluator semantics.
- [ ] Run the focused test file and require PASS.

### Task 2: Fixed 100-company identity bridge and real-snapshot runner

**Files:**
- Create: `configs/m2-2b-identity-bridge-v0.1.json`
- Create: `scripts/run_m2_2b_screening.py`
- Create: `tests/test_m2_2b_screening_snapshot.py`

**Interfaces:**
- Consumes: accepted M1.1 identity artifact provenance, generated #42 `coverage.json`, generated M1 `canonical-graph.json`, `schemas/examples/user-policy.examples.json`.
- Produces: deterministic machine-readable `screening.json`.

- [ ] Pin all 100 `wa:org:jp:tse:*` entities to their accepted Japanese corporate numbers without names or upstream source rows; require all links `CONFIRMED`.
- [ ] Test that the bridge covers exactly the #42 cohort, that current M1 graph overlap is measured rather than assumed, and that all three example policies are hashed and evaluated against the same graph/coverage snapshot.
- [ ] Implement CLI loading the two generated artifacts plus policies/bridge and writing the screening artifact.
- [ ] Require the measured current snapshot to report 100 companies, 3 profiles, 300 views, zero mapped claims, all company decisions `NONE`, while retaining 100 `unresolved_identity` political-finance coverage cells and 300 `not_integrated` cells.

### Task 3: Reproduction workflow and result record

**Files:**
- Create: `.github/workflows/m2-screening.yml`
- Create: `docs/results/M2_2B_SCREENING_V01.md`

**Interfaces:**
- Workflow regenerates M1 graph with existing `run_m1_reproduction.py`, regenerates #42 coverage with existing `run_m2_2a_coverage.py`, then runs #43 screening.
- Result doc records only measured successful run IDs/hashes after CI.

- [ ] Add a dedicated PR workflow scoped to #43 files plus relevant upstream policy/coverage files.
- [ ] Install the same fixed OCR/runtime dependencies required by the existing M1 reproduction path; do not create a new data route.
- [ ] Run focused #43 tests, regenerate M1 graph and #42 coverage, generate screening output, verify pinned counts/hashes, upload derived `screening.json` only.
- [ ] Record the measured negative result honestly: the current Evidence Graph has no corporate-number overlap with the fixed 100-company cohort, so all profile decisions are `NONE`; this is not evidence of safety or absence beyond the pinned coverage snapshot.
- [ ] Inspect final diff for #44/M3 or unrelated changes, then leave a bounded PR against `main`.
