# 1306 Prospective Control v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend #85 Historical Replay with a prospective, leak-safe 1306 investable-control path that can preregister 2026-11 / 2026-12 / 2027-01 without publishing restricted NEXT FUNDS source rows or raw-source digests.

**Architecture:** Reuse the existing v0.2 Historical Replay qualification, freeze, historical identity/evidence, Policy Compiler, monthly-market, frozen-target, and investable-proxy replay pipeline. Add one source-specific 1306 adapter, a blinded acquisition-commitment contract, one v0.3 prepare CLI, and the smallest genericization needed for both 1475 and 1306 to use the same downstream investable-control path.

**Tech Stack:** Python 3.11+, stdlib (`csv`, `hashlib`, `json`, `secrets`, `urllib.request` only for public GitHub comment verification if needed), existing `pytest`, existing WA Commons portfolio/evidence/identity modules. No new dependency, downloader, scheduler, database, or optimizer.

**Spec:** `docs/superpowers/specs/2026-09-10-1306-prospective-control-v03-design.md` at design commit `e87315fd7e5cc2be49ac216a5278a62e98a51490`.

## Global Constraints

- Preserve #85's no-performance-selection rule: candidate qualification and window freeze must not read evaluation-period return values.
- Preserve 2026-10 as the separate #78 future holdout.
- First headline candidate window is exactly `2026-11`, `2026-12`, `2027-01`; do not slide it after performance is known.
- Raw 1306 CSV bytes, row-level holdings/share counts, exact raw-source SHA-256, private capture hash, and nonce remain local/private under the current NEXT FUNDS rights interpretation.
- Public timestamp evidence contains only an opaque capture id, method version, and blinded commitment digest.
- Use source kind `NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO` and rights state `LOCAL_PRIVATE_RESEARCH_ONLY` consistently in config, registry, code, tests, and manifests.
- Use the existing JPX monthly-market price primitive for cutoff valuation; do not build a second price parser.
- Keep v0.2 1475 behavior byte-semantically compatible where practical and test it explicitly.
- Use TDD per task: RED test first, verify RED for the intended reason, minimal implementation, focused GREEN, then commit.
- Do not run the full repository suite after each task. Run one final full suite at the #85 review gate only.

## File Map

**Create**
- `configs/m3-3c0-historical-replay-v0.3.json`
- `src/wa_commons/portfolio/nextfunds_1306.py`
- `scripts/build_1306_capture_commitment.py`
- `scripts/verify_1306_public_commitment.py`
- `scripts/run_historical_replay_v03_prepare.py`
- `tests/test_nextfunds_1306.py`
- `tests/test_1306_capture_commitment_cli.py`
- `tests/test_historical_replay_v03.py`
- `tests/test_historical_replay_v03_prepare_cli.py`
- `docs/1306_PROSPECTIVE_CAPTURE.md`

**Modify**
- `docs/SOURCE_REGISTRY.md`
- `src/wa_commons/portfolio/investable_proxy.py`
- `src/wa_commons/portfolio/historical_replay.py`
- `scripts/run_historical_replay.py`
- `tests/test_investable_proxy.py`
- `tests/test_historical_replay_cli.py`

**Reuse unchanged unless a failing focused test proves otherwise**
- `scripts/run_historical_replay_qualification.py`
- `src/wa_commons/portfolio/monthly_market.py`
- `src/wa_commons/evidence/historical_cutoff.py`
- `src/wa_commons/identity/historical_edinet.py`
- `src/wa_commons/portfolio/policy_compiler.py`
- `scripts/run_historical_replay_v02_prepare.py`

---

## Task 1: Freeze the v0.3 source/rights/config contract

**Files:**
- Create: `configs/m3-3c0-historical-replay-v0.3.json`
- Modify: `docs/SOURCE_REGISTRY.md`
- Create: `tests/test_historical_replay_v03.py`

- [ ] **Step 1: Write RED config-contract tests**

Add tests that load `configs/m3-3c0-historical-replay-v0.3.json` and require exactly:

```python
assert config["artifact_version"] == "m3.3c0-historical-replay-v0.3"
assert config["headline_candidate_periods"] == ["2026-11", "2026-12", "2027-01"]
assert config["future_holdout_periods"] == ["2026-10"]
assert config["allocation_source"]["kind"] == "NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO"
assert config["allocation_source"]["security_id"] == "TSE:1306"
assert config["allocation_source"]["rights_required_state"] == "LOCAL_PRIVATE_RESEARCH_ONLY"
assert config["allocation_source"]["public_commitment_mode"] == "BLINDED_SHA256_V1"
assert config["allocation_source"]["public_timestamp_required"] is True
assert config["selection_rule"] == "EXACT_PREREGISTERED_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS"
assert config["performance_values_allowed_during_selection"] is False
assert "2026-09" in config["preselection_contaminated_periods"]
```

Also assert `2026-10` is not in headline or engineering periods.

- [ ] **Step 2: Verify RED**

Run:

```bash
pytest -q tests/test_historical_replay_v03.py
```

Expected: FAIL because v0.3 config does not yet exist.

- [ ] **Step 3: Add the minimal v0.3 config**

Base policy contract and required market-source roles on v0.2 unchanged. Set:

```json
"headline_candidate_periods": ["2026-11", "2026-12", "2027-01"],
"engineering_validation_periods": ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"],
"future_holdout_periods": ["2026-10"],
"preselection_contaminated_periods": ["2026-01", "2026-02", "2026-03", "2026-09"]
```

Do not add a performance result or real source capture.

- [ ] **Step 4: Add a distinct Source Registry row**

Add `nomura-nextfunds-1306-setting-portfolio` as `WATCH` with narrow scope: prospective ETF creation/setting portfolio only, not official TOPIX weights. Record the checked NEXT FUNDS site-policy locator, `LOCAL_PRIVATE_RESEARCH_ONLY`, raw/row-level no-publication boundary, and blinded-commitment-only public provenance until a later explicit rights review changes it. Leave the existing 1475 row unchanged.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
pytest -q tests/test_historical_replay_v03.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add configs/m3-3c0-historical-replay-v0.3.json docs/SOURCE_REGISTRY.md tests/test_historical_replay_v03.py
git commit -m "feat: freeze 1306 prospective replay contract"
```

---

## Task 2: Implement the pure 1306 parser, semantic selector, and blinded commitment

**Files:**
- Create: `src/wa_commons/portfolio/nextfunds_1306.py`
- Create: `tests/test_nextfunds_1306.py`

- [ ] **Step 1: Write RED tests for semantic portfolio selection**

Use synthetic metadata only; do not copy live NEXT FUNDS rows. Define three entries with different suffixes/order and `provisional_units` 20_000_000 / 50_000_000 / 100_000_000. Require:

```python
selected = select_largest_setting_portfolio(entries, application_date="2026-10-30")
assert selected["provisional_units"] == 100_000_000
```

Reverse order and rename suffixes; selection must remain identical. Add a duplicate-max case that raises `ValueError("ambiguous maximum provisional units")`.

- [ ] **Step 2: Write RED tests for raw-byte parsing**

Define an explicitly synthetic CSV fixture in the test with only the minimal accepted source columns: security code, name, setting share quantity. Require exact-byte SHA binding, normalized `TSE:<code>` ids, deterministic row sort, duplicate-code rejection, positive integer quantities, and no `control_weight` before valuation.

Parser signature:

```python
def parse_nextfunds_1306_setting_csv(
    raw_bytes: bytes,
    *,
    application_date: str,
    provisional_units: int,
    retrieved_at: str,
    source_locator: str,
    rights_state: str,
) -> dict[str, Any]: ...
```

Require manifest `control_kind == "NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO"` and private `source_sha256` from the exact bytes.

- [ ] **Step 3: Write RED tests for blinded commitments**

Function signatures:

```python
def build_private_capture_core(snapshot: Mapping[str, Any]) -> dict[str, Any]: ...
def build_blinded_capture_commitment(private_capture_core: Mapping[str, Any], nonce_hex: str) -> dict[str, str]: ...
def build_public_commitment_record(capture_id: str, public_commitment_sha256: str) -> dict[str, str]: ...
```

Require fixed input + fixed 64-hex-char nonce to be deterministic; changing locator/date/bytes/hash/nonce changes the public digest. Serialized public record must not contain `source_sha256`, `private_capture_sha256`, nonce, security ids, quantities, raw rows, or source bytes.

- [ ] **Step 4: Verify RED**

Run:

```bash
pytest -q tests/test_nextfunds_1306.py
```

Expected: import/function failures only.

- [ ] **Step 5: Implement the smallest pure module**

Use stdlib only. Validate timezone-aware ISO timestamps, `YYYY-MM-DD` application date, positive integer provisional units/share quantities, unique TSE codes, exact-byte SHA-256, lowercase 64-hex digests, and a 32-byte/64-hex nonce. Keep private and public structures separate in code, not merely by documentation.

- [ ] **Step 6: Verify GREEN and regression boundary**

Run:

```bash
pytest -q tests/test_nextfunds_1306.py tests/test_investable_proxy.py
```

Expected: PASS; no 1475 regression.

- [ ] **Step 7: Commit**

```bash
git add src/wa_commons/portfolio/nextfunds_1306.py tests/test_nextfunds_1306.py
git commit -m "feat: add private 1306 control adapter and commitment"
```

---

## Task 3: Value 1306 share quantities at the cutoff and reuse investable-control mapping

**Files:**
- Modify: `src/wa_commons/portfolio/nextfunds_1306.py`
- Modify: `src/wa_commons/portfolio/investable_proxy.py`
- Modify: `tests/test_nextfunds_1306.py`
- Modify: `tests/test_investable_proxy.py`

- [ ] **Step 1: Write RED cutoff-valuation tests**

Add:

```python
def value_1306_setting_portfolio(
    setting_snapshot: Mapping[str, Any],
    cutoff_price_snapshot: Mapping[str, Any],
) -> dict[str, Any]: ...
```

For two synthetic holdings with quantities 2 and 1 and cutoff prices 100 and 200, require equal raw values and normalized weights of `0.500000000000` each. Require deterministic 12-decimal weights summing exactly to `1.000000000000` after the same residual-to-last-row convention used by existing portfolio code.

Add blocking/error cases for missing security price, duplicate price id, `PRICE_SNAPSHOT_OK` absent, price `close_date` after application/cutoff date, zero/negative price, and unexpected extra source-performance fields.

- [ ] **Step 2: Write RED mapping-regression tests**

In `tests/test_investable_proxy.py`, create a synthetic already-valued 1306 snapshot and require `map_investable_control_snapshot()` to preserve its manifest `control_kind`. Existing 1475 mapping must still report `ISHARES_1475_POINT_IN_TIME` exactly.

- [ ] **Step 3: Verify RED**

Run:

```bash
pytest -q tests/test_nextfunds_1306.py tests/test_investable_proxy.py
```

Expected: new tests FAIL because valuation/generic control-kind support is absent.

- [ ] **Step 4: Implement valuation and minimal mapping genericization**

Compute:

```text
raw_value_i = setting_shares_i * cutoff_close_price_i
control_weight_i = raw_value_i / sum(raw_value_j)
```

Do not add another price parser. Change `map_investable_control_snapshot()` only enough to copy an accepted `control_kind` from the snapshot manifest instead of hard-coding 1475. Fail closed on an unsupported/missing kind.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
pytest -q tests/test_nextfunds_1306.py tests/test_investable_proxy.py tests/test_monthly_market.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/portfolio/nextfunds_1306.py src/wa_commons/portfolio/investable_proxy.py tests/test_nextfunds_1306.py tests/test_investable_proxy.py
git commit -m "feat: value 1306 control at point-in-time cutoff"
```

---

## Task 4: Extend candidate qualification/freeze and frozen execution to 1306

**Files:**
- Modify: `src/wa_commons/portfolio/historical_replay.py`
- Modify: `scripts/run_historical_replay.py`
- Modify: `tests/test_historical_replay_v03.py`
- Modify: `tests/test_historical_replay_cli.py`

- [ ] **Step 1: Write RED 1306 qualification tests**

Add a dedicated synthetic candidate helper with `control_source_metadata.kind == "NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO"`. Require qualification only when:

```text
exists == true
locator present
application_date == decision_cutoff.date
retrieved_at <= decision_cutoff
rights_state == LOCAL_PRIVATE_RESEARCH_ONLY
public_commitment_sha256 valid
public_timestamp_verified == true
public_timestamp_at <= decision_cutoff
identity/evidence availability + semantic hashes valid
required market-source metadata present
```

Add one focused test per blocker reason: application-date mismatch, missing/late retrieval, wrong rights state, invalid commitment, unverified/late public timestamp. Preserve the existing performance-field guard.

- [ ] **Step 2: Write RED freeze-output privacy test**

Freeze the exact `2026-11/12/2027-01` synthetic window and assert each frozen month includes the public commitment and public timestamp reference/time, but excludes `source_sha256`, private capture hash, nonce, local path, and row-level holdings.

- [ ] **Step 3: Write RED frozen-execution routing test**

Update `tests/test_historical_replay_cli.py` so both accepted investable-control kinds require `--frozen-targets` before policy/market payloads are read. 1306 must route to `run_investable_proxy_replay`, not legacy `run_frozen_replay`. Keep the v0.2 assertion unchanged.

- [ ] **Step 4: Verify RED**

Run:

```bash
pytest -q tests/test_historical_replay_v03.py tests/test_historical_replay.py tests/test_historical_replay_cli.py
```

Expected: only the new v0.3 cases fail.

- [ ] **Step 5: Implement a dedicated 1306 qualifier and shared investable-control-kind predicate**

Add a small helper such as:

```python
_INVESTABLE_CONTROL_KINDS = {
    "ISHARES_1475_POINT_IN_TIME",
    "NOMURA_1306_PROSPECTIVE_SETTING_PORTFOLIO",
}
```

Keep the 1475 qualifier semantics untouched. Add `_qualify_1306_prospective_candidate()` rather than overloading 1475 field names. Update `_freeze_candidate_record()` so 1306 freezes only repo-safe public provenance. Update `run_investable_proxy_replay()` and the execution CLI to accept both kinds.

- [ ] **Step 6: Verify GREEN + v0.2 regression**

Run:

```bash
pytest -q tests/test_historical_replay_v03.py tests/test_historical_replay.py tests/test_historical_replay_v02.py tests/test_historical_replay_cli.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/wa_commons/portfolio/historical_replay.py scripts/run_historical_replay.py tests/test_historical_replay_v03.py tests/test_historical_replay_cli.py
git commit -m "feat: qualify and execute 1306 prospective replay"
```

---

## Task 5: Build the local capture-commitment and public-timestamp verification tools

**Files:**
- Create: `scripts/build_1306_capture_commitment.py`
- Create: `scripts/verify_1306_public_commitment.py`
- Create: `tests/test_1306_capture_commitment_cli.py`
- Create: `docs/1306_PROSPECTIVE_CAPTURE.md`

- [ ] **Step 1: Write RED builder-CLI tests**

The builder accepts an already-downloaded local file; it must not download NEXT FUNDS content itself.

Required CLI inputs:

```text
--raw-file
--application-date
--provisional-units
--source-locator
--retrieved-at
--rights-state
--nonce-hex   (optional; generate with secrets.token_hex(32) when omitted)
--private-output
--public-output
```

Require private output to contain source hash/private hash/nonce and public output to contain only `capture_id`, `method_version = BLINDED_SHA256_V1`, and `public_commitment_sha256`.

- [ ] **Step 2: Write RED GitHub-comment verifier tests**

The verifier accepts `--comment-id`, `--expected-commitment`, `--decision-cutoff`, and `--output`. Isolate HTTP retrieval behind an injectable pure function so tests never call GitHub. Given a synthetic GitHub API response, require:

```text
body contains exactly the expected commitment token
created_at <= decision_cutoff
updated_at == created_at
repository/issue target is kazuma-democracy/wa-commons#85
```

Edited, late, missing, malformed, or mismatched comments must return a fail-closed verification state.

- [ ] **Step 3: Verify RED**

Run:

```bash
pytest -q tests/test_1306_capture_commitment_cli.py
```

Expected: FAIL because scripts are absent.

- [ ] **Step 4: Implement builder without network acquisition**

Reuse `nextfunds_1306` hashing/commitment functions. Never print the raw source SHA or nonce to stdout unless stdout is explicitly the requested private output; default user-facing summary should expose only paths/state and the blinded commitment.

- [ ] **Step 5: Implement public comment verification using stdlib GET only**

Use GitHub's public issue-comment API endpoint for the exact comment id. Do not add a GitHub token dependency or write/post/edit capability. Normalize the verified output to repo-safe fields: comment id/ref, `created_at`, `updated_at`, expected blinded commitment, and `public_timestamp_verified` boolean.

- [ ] **Step 6: Write the operational runbook**

Document the exact order:

```text
1. Manually obtain the correct official 1306 file locally before cutoff.
2. Run build_1306_capture_commitment.py.
3. Post only the public-output commitment to WA Commons Issue #85 before cutoff.
4. Record the returned GitHub comment id.
5. Run verify_1306_public_commitment.py before qualification.
6. Preserve raw file + private manifest locally; do not commit them.
7. Feed only verified repo-safe metadata into candidate qualification.
```

State explicitly that October 2026 returns must not be used to revise this method.

- [ ] **Step 7: Verify GREEN**

Run:

```bash
pytest -q tests/test_1306_capture_commitment_cli.py tests/test_nextfunds_1306.py
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/build_1306_capture_commitment.py scripts/verify_1306_public_commitment.py tests/test_1306_capture_commitment_cli.py docs/1306_PROSPECTIVE_CAPTURE.md
git commit -m "feat: add blinded 1306 capture proof workflow"
```

---

## Task 6: Add v0.3 pre-return target preparation without reading evaluation returns

**Files:**
- Create: `scripts/run_historical_replay_v03_prepare.py`
- Create: `tests/test_historical_replay_v03_prepare_cli.py`

- [ ] **Step 1: Write RED CLI-surface test**

Require v0.3 prepare inputs to be only pre-return inputs:

```text
--frozen-window
--pre-return-input-manifest
--policy-config
--policies
--local-output-dir
--targets-manifest
--code-commit
```

The pre-return manifest supplies per period: local private 1306 capture manifest/raw path, verified public timestamp receipt, cutoff price snapshot, EDINET metadata, and MOD sources. Assert the CLI has no evaluation-return, benchmark-return, end-price, or market-payload argument.

- [ ] **Step 2: Write RED private-binding tests**

Require the runner to fail before policy compilation when any of these differ from the frozen/public contract: raw byte SHA, application date, public blinded commitment, public timestamp verification, cutoff date, rights state, or local price snapshot. Require no output target manifest on failure.

- [ ] **Step 3: Write RED happy-path target-freeze test**

Using synthetic local fixtures only, require the same flow as v0.2:

```text
private 1306 raw -> verify commitment -> parse shares -> cutoff valuation
-> historical identity -> mapped investable control -> historical screening
-> bind Policy Compiler -> compile P0/P1/P2 -> freeze target manifest
```

Require artifact version `m3.3c0-historical-replay-targets-v0.3`, status `HISTORICAL_REPLAY_TARGETS_FROZEN`, exactly three months, stable policy semantics, and no raw-source/private commitment fields in the public/frozen target manifest.

- [ ] **Step 4: Verify RED**

Run:

```bash
pytest -q tests/test_historical_replay_v03_prepare_cli.py
```

Expected: FAIL because v0.3 prepare script is absent.

- [ ] **Step 5: Implement by adapting, not copying blindly, the v0.2 prepare flow**

Reuse `build_historical_proxy_identity`, `build_historical_screening`, `map_investable_control_snapshot`, `bind_policy_compiler_inputs`, `compile_policy_family`, `directly_changed_security_ids`, and `verify_frozen_target_manifest`. The new source-specific steps end at production of the same normalized mapped-control contract used downstream.

- [ ] **Step 6: Prove return-data isolation**

Add an exploding/missing evaluation-market path test: v0.3 prepare must freeze targets successfully without opening or importing an evaluation-period return payload. This is a required anti-leakage claim, not just CLI cosmetics.

- [ ] **Step 7: Verify GREEN + v0.2 prepare regression**

Run:

```bash
pytest -q tests/test_historical_replay_v03_prepare_cli.py tests/test_historical_replay_v02_prepare_cli.py tests/test_historical_replay_v02.py
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/run_historical_replay_v03_prepare.py tests/test_historical_replay_v03_prepare_cli.py
git commit -m "feat: freeze v03 1306 policy targets before returns"
```

---

## Task 7: Integration verification, privacy scan, and durable review checkpoint

**Files:**
- Modify only if verification exposes a real defect: files changed above.
- Update documentation/result status only with measured facts; do not claim a real 3-month replay because the first clean window is future.

- [ ] **Step 1: Run focused feature suite**

```bash
pytest -q \
  tests/test_nextfunds_1306.py \
  tests/test_1306_capture_commitment_cli.py \
  tests/test_historical_replay_v03.py \
  tests/test_historical_replay_v03_prepare_cli.py \
  tests/test_investable_proxy.py \
  tests/test_historical_replay.py \
  tests/test_historical_replay_v02.py \
  tests/test_historical_replay_v02_prepare_cli.py \
  tests/test_historical_replay_cli.py \
  tests/test_monthly_market.py
```

Expected: PASS.

- [ ] **Step 2: Run a repository privacy/prohibited-field scan on tracked diff**

Check the branch diff for source-like row data and private fields. At minimum reject tracked additions containing real 1306 row-level holdings, real raw-source SHA-256, `commitment_nonce`, or local raw paths. Synthetic test fixtures must be visibly marked `SYNTHETIC` and use invented securities/quantities.

- [ ] **Step 3: Inspect diff and verify v0.2 is not rewritten**

```bash
git diff main...HEAD --stat
git diff main...HEAD -- src/wa_commons/portfolio/investable_proxy.py src/wa_commons/portfolio/historical_replay.py scripts/run_historical_replay.py
```

Confirm changes are bounded to dual-kind genericization and v0.3 source semantics; no policy multipliers, P0/P1/P2 semantics, benchmark family, October holdout, or return-selection rules changed.

- [ ] **Step 4: Run the one final full repository suite required by #85 review gate**

```bash
pytest -q
```

Expected: PASS. Record the exact test count and command output in the PR/Issue checkpoint. Do not substitute an earlier focused pass for this gate.

- [ ] **Step 5: Record the truthful current state**

The implementation can be called **v0.3 capability implemented** only if the code/tests above pass. #85 itself remains **not complete** until the preregistered three real prospective months can actually be captured/frozen/evaluated or explicitly block under the fixed method. Do not create a fake November/December/January result from current data.

- [ ] **Step 6: Commit any final docs-only measured checkpoint**

```bash
git add <only measured status/docs files actually changed>
git commit -m "docs: record 1306 prospective control verification"
```

Skip this commit if no documentation needs changing.

- [ ] **Step 7: Open a reviewable PR and update Issue #85**

PR body must state: design/spec commit, plan commit, exact rights boundary, focused/full test evidence, no real replay returns loaded, first future capture window, and that October remains separate. Keep #85 open unless its original Definition of Done is genuinely met.

---

## Plan Self-Review Checklist

- [ ] Every design acceptance item has a corresponding task/test.
- [ ] No task publishes real NEXT FUNDS raw rows, security/share-count data, exact raw-source SHA, nonce, or private capture hash.
- [ ] Public timestamp proof is server-time-based and cannot be satisfied by a local claimed timestamp alone.
- [ ] 1306 selection is by provisional-unit semantics, never suffix.
- [ ] 1306 valuation uses only cutoff prices and occurs before evaluation returns.
- [ ] `2026-11/12/2027-01` and October holdout separation are fixed in config tests.
- [ ] v0.2 1475 qualification, mapping, preparation, and replay remain under regression tests.
- [ ] No new external Python dependency, downloader, scheduler, database, optimizer, or trading surface is introduced.
- [ ] No placeholder `TODO`, `TBD`, `later choose`, or performance-dependent escape hatch remains in implementation requirements.
- [ ] Final completion language distinguishes "capability implemented" from "three-month replay completed".
