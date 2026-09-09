# Issue #85 Leak-Safe Historical Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic metadata-only three-month replay-window qualifier/freeze gate, plus a separate frozen-window replay engine, without back-projecting current benchmark/evidence or selecting months from returns.

**Architecture:** Selection and execution are separate modules/interfaces. Window qualification consumes only point-in-time provenance/existence metadata and can return `BLOCK_HISTORICAL_REPLAY_COVERAGE`; the replay engine accepts market returns only after a `HISTORICAL_REPLAY_WINDOW_FROZEN` manifest exists. Existing #55 screening, #84 Policy Compiler, and #56 monthly-market payloads are reused rather than replaced.

**Tech Stack:** Python 3.11, stdlib `datetime`/`decimal`/`hashlib`/`json`/`pathlib`, pytest.

**Spec:** `docs/superpowers/specs/2026-09-09-peace-capital-policy-transmission-replay-design.md`

## Global Constraints

- Policy family semantics remain exactly P0/P1/P2 from `m3.3b2-policy-compiler-v0.1`.
- Window selection must not accept candidate/security/benchmark return values or price values.
- Point-in-time benchmark membership/weights must be explicitly versioned and available by the decision cutoff; current constituents may not be projected backward.
- Evidence/screening inputs must prove as-known cutoff completeness; event/evidence dates alone are not availability timestamps.
- `2026-07` is `ENGINEERING_VALIDATION_ONLY` and cannot enter the first headline window.
- `2026-10` remains the prospective holdout and cannot enter Historical Replay.
- Missing historical benchmark, screening/evidence availability, identity, or source provenance fails closed.
- Raw JPX rows and issuer evidence remain local-only; performance publication remains behind the #78/#56 rights boundary.
- No paid source, daily return store, expected-return model, factor optimizer, or real-money authority is introduced.

---### Task 1: Pin metadata-only qualification contract

**Files:**
- Create: `configs/m3-3c0-historical-replay-v0.1.json`
- Create: `src/wa_commons/portfolio/historical_replay.py`
- Create: `tests/test_historical_replay.py`

**Interfaces:**
- `load_historical_replay_config(path) -> dict`
- `qualify_candidate_month(candidate: Mapping[str, Any], config: Mapping[str, Any]) -> dict`
- Candidate metadata permits period/cutoff, point-in-time benchmark hashes/timestamps, cutoff-screening hashes/completeness, identity hashes, and market-source existence/locators only.

- [ ] **Step 1: Write RED tests** asserting `2026-07` -> `BLOCK_REPRODUCIBILITY`, `2026-10` -> `BLOCK_REPRODUCIBILITY`, missing benchmark -> `BLOCK_HISTORICAL_REPLAY_COVERAGE`, benchmark `available_at > decision_cutoff` -> `BLOCK_EVIDENCE_CUTOFF`, incomplete screening availability -> `BLOCK_EVIDENCE_CUTOFF`, mismatched identity hashes -> `BLOCK_REPRODUCIBILITY`, and complete metadata -> `CANDIDATE_QUALIFIED`.
- [ ] **Step 2: Write RED tests** proving qualification rejects numeric/performance-bearing candidate keys such as `benchmark_decimal_return`, `close_price`, `total_wealth_return`, and `performance` with `BLOCK_REPRODUCIBILITY`.
- [ ] **Step 3: Run** `python -m pytest tests/test_historical_replay.py -q` and verify RED failures are caused only by missing qualification code.
- [ ] **Step 4: Implement minimal qualification.** Parse ISO timestamps with `datetime.fromisoformat`, compare benchmark `available_at <= decision_cutoff`, require `screening_snapshot.decision_cutoff == decision_cutoff`, `availability_complete is True`, exact identity-hash agreement, and every required market-source metadata role to have `exists: true` plus non-empty locator.
- [ ] **Step 5: Use a strict recursive forbidden-key check** for performance-bearing names; source role names remain permitted, but numeric return/price fields never cross the qualification interface.
- [ ] **Step 6: Run focused tests GREEN.**
- [ ] **Step 7: Commit** `feat: add metadata-only historical replay qualification`.

### Task 2: Freeze the most recent eligible consecutive three-month window
**Files:**
- Modify: `src/wa_commons/portfolio/historical_replay.py`
- Modify: `tests/test_historical_replay.py`

**Interfaces:**
- `freeze_replay_window(candidates: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> dict`
- Output status is `HISTORICAL_REPLAY_WINDOW_FROZEN` or `BLOCK_HISTORICAL_REPLAY_COVERAGE`.

- [ ] **Step 1: Write RED tests** with synthetic metadata for `2026-04`, `2026-05`, `2026-06`, `2026-07`, and `2026-08`; assert the most recent qualified consecutive triple is selected while `2026-07` is excluded.
- [ ] **Step 2: Write RED tests** proving three individually qualified but non-consecutive months do not freeze, and a newer blocked month does not cause a later post-performance skip/reselection.
- [ ] **Step 3: Run the focused tests and verify RED.**
- [ ] **Step 4: Implement month arithmetic** using `(year * 12 + month)` ordinals, sort by period descending, and scan only fixed consecutive triples. Never inspect market-value fields.
- [ ] **Step 5: Freeze a semantic manifest** containing selected periods, exact decision cutoffs, benchmark/screening/identity hashes, qualification statuses, policy compiler config hash, policy/profile identity, and `window_semantic_sha256` computed from canonical sorted JSON.
- [ ] **Step 6: If no triple qualifies, return** `{"status":"BLOCK_HISTORICAL_REPLAY_COVERAGE","window":[],"candidate_results":[...]}` with all blocker reasons preserved.
- [ ] **Step 7: Run focused tests GREEN and reverse candidate input order; require identical frozen hash/result.**
- [ ] **Step 8: Commit** `feat: freeze leak-safe historical replay window`.

### Task 3: Add metadata-only capability-audit CLI and current blocked result

**Files:**
- Create: `scripts/run_historical_replay_qualification.py`
- Create: `tests/test_historical_replay_cli.py`
- Create: `docs/results/M3_3C0_HISTORICAL_REPLAY_CAPABILITY_MANIFEST_V01.json`
- Create: `docs/results/M3_3C0_HISTORICAL_REPLAY_CAPABILITY_V01.md`

**Interfaces:**
- CLI args: `--config`, `--candidate-metadata`, `--output`, `--code-commit` only.
- No price PDF, benchmark ROI, return payload, security return, or performance argument is permitted.
- [ ] **Step 1: Write RED CLI tests** proving only metadata-only arguments exist and candidate JSON containing return/price fields fails before selection.
- [ ] **Step 2: Add a repo-safe candidate inventory** for completed 2026 months using only known point-in-time metadata. Record the accepted #50 snapshot (`effective_date=2026-07-31`, `available_at=2026-08-31T16:20:00+09:00`, semantic mapping hash `1cc4b239...`) and mark absent historical benchmark/screening snapshots explicitly; do not open any return files.
- [ ] **Step 3: Run the qualifier against the current inventory.** Expected current status: `BLOCK_HISTORICAL_REPLAY_COVERAGE`, because only one free/local full TOPIX weight snapshot is reproducible and no three consecutive completed months have cutoff-complete benchmark/screening inputs.
- [ ] **Step 4: Record observed evidence honestly.** The three local TOPIX CSV copies all have SHA-256 `e8bb15ddbe6f65c11363fe1f816feabc125b8587c520f358dcf191a4e7db0ae7` and contain only `20260731`; JPX's public page documents latest-file replacement cadence and points historical constituent information to J-Quants DataCube. Do not adopt a paid substitute inside #85.
- [ ] **Step 5: Result docs must state** that July was already engineering-inspected, October is future holdout, current-constituent back-projection is prohibited, and the blocked result was reached without loading replay returns.
- [ ] **Step 6: Run focused CLI/unit tests GREEN and `git diff --check`.**
- [ ] **Step 7: Commit** `feat: record historical replay coverage gate`.

### Task 4: Implement frozen-window replay engine with synthetic fixtures

**Files:**
- Modify: `src/wa_commons/portfolio/historical_replay.py`
- Modify: `tests/test_historical_replay.py`

**Interfaces:**
- `run_frozen_replay(window_manifest, monthly_policy_payloads, monthly_market_payloads, config) -> dict`
- The function accepts market payloads only when `window_manifest.status == HISTORICAL_REPLAY_WINDOW_FROZEN`.

- [ ] **Step 1: Write RED test** asserting an unfrozen/blocked manifest returns `BLOCK_REPRODUCIBILITY` before reading any monthly market payload.
- [ ] **Step 2: Write RED three-month fixture** with P0/P1/P2 target weights and #56-shaped `MONTHLY_RETURN_OK` rows. For each arm/month compute `portfolio_return = sum(target_weight * total_wealth_return)` using `Decimal`; benchmark return comes from the #56 payload.
- [ ] **Step 3: Write RED blockers** for missing policy month -> `BLOCK_REPRODUCIBILITY`, `MONTHLY_RETURN_BLOCKED` -> `BLOCK_MARKET_DATA`, and any security row `BLOCK_CORPORATE_ACTION` -> `BLOCK_CORPORATE_ACTION`.
- [ ] **Step 4: Require policy semantics stability** across months: same P0/P1/P2 arm IDs, allocation-policy IDs/versions, profile ID/version, and policy hash. Historical target hashes may differ because benchmark/evidence states differ.
- [ ] **Step 5: Implement cumulative wealth deterministically** as the product of `(1 + monthly_return)` in frozen window order; freeze Policy Transmission metrics alongside each arm before secondary financial fields.
- [ ] **Step 6: Keep public rights boundary separate.** The core engine may return local numeric results, but public writer/manifest must omit financial numbers unless an explicit rights-cleared flag is true.
- [ ] **Step 7: Run focused tests GREEN and verify input-order invariance.**
- [ ] **Step 8: Commit** `feat: add frozen historical replay engine`.

### Task 5: Add replay execution CLI without combining selection and return loading

**Files:**
- Create: `scripts/run_historical_replay.py`
- Modify: `tests/test_historical_replay_cli.py`

**Interfaces:**
- CLI requires `--frozen-window`, `--policy-payload-map`, `--market-payload-map`, `--config`, `--local-output`, `--public-output`.
- It never accepts candidate metadata and never chooses a window.

- [ ] **Step 1: Write RED tests** proving the execution CLI rejects a non-frozen window and refuses identical local/public output paths.
- [ ] **Step 2: Write RED publication test** proving rights-uncleared public JSON contains status, hashes, period list, Policy Transmission metrics, blocker counts, and publication state but no security IDs, price values, benchmark return numbers, portfolio return numbers, or evidence text.
- [ ] **Step 3: Implement minimal CLI/writer** by calling `run_frozen_replay` only; no selection logic is duplicated.
- [ ] **Step 4: Run focused tests GREEN and `git diff --check`.**
- [ ] **Step 5: Commit** `feat: add frozen historical replay CLI`.

### Task 6: Final verification and blocked handoff

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/results/M3_3C0_HISTORICAL_REPLAY_CAPABILITY_V01.md`
- Modify: `docs/results/M3_3C0_HISTORICAL_REPLAY_CAPABILITY_MANIFEST_V01.json`

- [ ] **Step 1: Re-run the metadata-only current capability audit** before any real replay return loading. If it still blocks, preserve `BLOCK_HISTORICAL_REPLAY_COVERAGE`; do not download paid history or substitute current constituents.
- [ ] **Step 2: Run** `python -m pytest tests/test_historical_replay.py tests/test_historical_replay_cli.py -q`.
- [ ] **Step 3: Run one final full repository suite** `python -m pytest -q` and require zero failures.
- [ ] **Step 4: Run** `git diff --check` and JSON syntax validation for all new manifests/configs.
- [ ] **Step 5: Update ROADMAP** to `#85 BLOCKED / POINT_IN_TIME_DATA_COVERAGE` if no frozen window exists; #51 must remain not-current. If a real three-month window later qualifies, update only after the freeze manifest is committed before loading returns.
- [ ] **Step 6: Push a durable checkpoint PR** that does **not** use `Closes #85` while the real replay remains blocked. Add the exact unblock condition: three consecutive completed evaluation months with reproducible point-in-time benchmark + cutoff-complete screening/evidence + identity + monthly source metadata under the zero-cost contract.

## Self-review

- Spec coverage: metadata-only selection, engineering-month exclusion, three consecutive months, pre-return hash freeze, as-known cutoff, point-in-time benchmark, no survivorship back-projection, replay blockers, October holdout, and rights boundary are all assigned to explicit tasks.
- Placeholder scan: no TBD/TODO/future implementation placeholders are used as task instructions.
- Type consistency: qualification produces candidate results consumed only by `freeze_replay_window`; replay consumes only a frozen manifest plus local policy/market payload maps.
- Current expected real-world result is a reproducible blocker, not a fabricated three-month replay.