# M3 Pre-Return Portfolio Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one deterministic, return-blind target-portfolio freeze artifact for Issue #80 before Issue #56 ingests the selected-period market data.

**Architecture:** Reuse the completed #49 constructor, #50 mapped benchmark, #55 row-level screening, and #78 period/source contract. Add one narrow assembler that validates exact input hashes, selects the pinned strict profile, joins benchmark rows to screening rows through existing canonical IDs only, calls `construct_paper_portfolio(...)`, and writes a local full artifact plus a repo-safe aggregate manifest. No market-price or return input is accepted anywhere in this flow.

**Tech Stack:** Python 3.11, stdlib `json`/`decimal`/`hashlib`/`pathlib`, existing `wa_commons.portfolio.constructor`, existing JPX identity/mapping data structures, pytest, jsonschema, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-09-m3-pre-return-portfolio-freeze-design.md`

## Global Constraints

- Frozen base profile: `example:strict-military-avoidance` version `1`, SHA-256 `7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c`.
- #50 semantic mapping SHA-256: `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.
- #55 TSE screening SHA-256: `aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c`.
- #49 constructor: `benchmark-l2-projection` v0.1; config path `configs/portfolio/benchmark-l2-projection-v0.1.json`; config semantic SHA-256 `82ea5cfd50139ccecafb8d35b0b654e02fa0c7c45e0b962b6873b2ecbbe8c6be`.
- #78 benchmark/period contract remains `JPX:TOPIX_TOTAL_RETURN:6000`, portfolio-definition cutoff `2026-09-29_CLOSE`, start valuation `2026-09-30_CLOSE`, evaluation `2026-10-01` through `2026-10-30`.
- The selected strict policy currently has no preferences; `preference_signals=[]` is required for every row. If the policy file gains preferences or the policy hash changes, return `BLOCK_INPUT_VERSION`.
- Join only through existing exact benchmark/canonical entity identifiers. Name-only relinking is prohibited.
- No market-price, dividend, corporate-action, benchmark-return, or selected-period performance input may be accepted by the freeze runner.
- Do not add top-N, minimum-weight pruning, sparsity penalties, or any post-constructor weight editing.
- The full row-level frozen target artifact is local-only. Public repo output is aggregate/provenance only.
- One full repository test suite is required at final completion, not after every small task.

---

### Task 1: Pin the machine-readable #80 freeze contract

**Files:**
- Create: `configs/m3-3b2-pre-return-portfolio-freeze-v0.1.json`
- Create: `tests/test_m3_pre_return_portfolio_freeze_contract.py`

**Interfaces:**
- Consumes: accepted #49/#50/#55/#78 identifiers and hashes.
- Produces: `load_freeze_config(path: str | Path) -> dict[str, Any]` contract inputs for later tasks.

- [ ] **Step 1: Write the failing contract tests**

Create tests asserting the config contains exactly:

```python
assert config["artifact_version"] == "m3.3b2-pre-return-freeze-v0.1"
assert config["issue"] == 80
assert config["benchmark_semantic_mapping_sha256"] == "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409"
assert config["tse_screening_sha256"] == "aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c"
assert config["policy_profile_id"] == "example:strict-military-avoidance"
assert config["policy_profile_version"] == "1"
assert config["policy_sha256"] == "7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c"
assert config["constructor_id"] == "benchmark-l2-projection"
assert config["constructor_version"] == "0.1"
assert config["constructor_config_sha256"] == "82ea5cfd50139ccecafb8d35b0b654e02fa0c7c45e0b962b6873b2ecbbe8c6be"
assert config["portfolio_definition_cutoff"] == "2026-09-29_CLOSE"
assert config["selected_period_market_data_allowed"] is False
assert config["public_row_level_output_allowed"] is False
```

Also assert no key contains `return`, `price`, `dividend`, `performance`, or `market_data` except the explicit boolean guard `selected_period_market_data_allowed`.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
pytest -q tests/test_m3_pre_return_portfolio_freeze_contract.py
```

Expected: FAIL because the config does not exist.

- [ ] **Step 3: Create the minimal JSON contract**

Use only the exact values above plus:

```json
{
  "preference_contract": "EMPTY_REQUIRED",
  "join_contract": "EXACT_CANONICAL_ENTITY_ID_ONLY",
  "target_weight_postprocessing": "PROHIBITED",
  "local_full_artifact": true,
  "public_manifest": "AGGREGATE_PROVENANCE_ONLY"
}
```

- [ ] **Step 4: Run focused test and verify GREEN**

Expected: all contract tests PASS.

- [ ] **Step 5: Commit**

```bash
git add configs/m3-3b2-pre-return-portfolio-freeze-v0.1.json tests/test_m3_pre_return_portfolio_freeze_contract.py
git commit -m "test: pin pre-return portfolio freeze contract"
```

---

### Task 2: Implement the return-blind freeze assembler

**Files:**
- Create: `src/wa_commons/portfolio/freeze.py`
- Modify: `src/wa_commons/portfolio/__init__.py`
- Create: `tests/test_m3_pre_return_portfolio_freeze.py`

**Interfaces:**
- Consumes:
  - `benchmark_mapping: Mapping[str, Any]` with `manifest` and local `rows` from #50;
  - `screening: Mapping[str, Any]` with local row-level `views` from #55;
  - `policy: Mapping[str, Any]` from the accepted policy file;
  - constructor config from `configs/portfolio/benchmark-l2-projection-v0.1.json`;
  - freeze config from Task 1.
- Produces:
  - `freeze_target_portfolio(...) -> dict[str, Any]` with `status`, `target_weights`, and `manifest`.

- [ ] **Step 1: Write failing tests for exact input validation**

Cover at minimum:

```python
assert freeze_target_portfolio(valid_inputs)["status"] == "FROZEN"
assert freeze_target_portfolio(wrong_benchmark_hash)["status"] == "BLOCK_INPUT_VERSION"
assert freeze_target_portfolio(wrong_screening_hash)["status"] == "BLOCK_INPUT_VERSION"
assert freeze_target_portfolio(wrong_policy_hash)["status"] == "BLOCK_INPUT_VERSION"
assert freeze_target_portfolio(policy_with_preferences)["status"] == "BLOCK_INPUT_VERSION"
```

- [ ] **Step 2: Write failing tests for identity/policy-row gates**

Use fixtures with one benchmark row missing from the selected-profile views, duplicate selected-profile views for one entity, disputed mapping, and inconsistent entity/security mapping. Expected states:

```python
"BLOCK_POLICY_ROW"
"BLOCK_POLICY_ROW"
"BLOCK_IDENTITY"
"BLOCK_IDENTITY"
```

Do not rescue any case by company name.

- [ ] **Step 3: Run RED tests**

```bash
pytest -q tests/test_m3_pre_return_portfolio_freeze.py
```

Expected: import/function missing failures.

- [ ] **Step 4: Implement canonical hashing/config validation helpers**

In `freeze.py` add:

```python
def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

and strict validators for the exact hashes/IDs from Task 1.

- [ ] **Step 5: Implement selected-profile indexing**

Build exactly one selected view per `entity_id` where:

```python
view["profile_id"] == freeze_config["policy_profile_id"]
view["profile_version"] == freeze_config["policy_profile_version"]
view["policy_sha256"] == freeze_config["policy_sha256"]
```

Any duplicate or missing selected row for a mapped benchmark entity returns `BLOCK_POLICY_ROW`.

- [ ] **Step 6: Assemble constructor rows without names or market data**

For every #50 local mapped row, produce only:

```python
{
    "security_id": benchmark_row["security_id"],
    "benchmark_weight": benchmark_row["benchmark_weight"],
    "mapping_state": benchmark_row["mapping_state"],
    "decision": selected_view["decision"],
    "preference_signals": [],
}
```

Require `mapping_state == "mapped"`, a non-empty `canonical_entity_id`, and an exact selected-view match on that entity ID.

- [ ] **Step 7: Call the existing constructor unchanged**

Invoke:

```python
result = construct_paper_portfolio(rows, provenance, constructor_config)
```

If the constructor does not return `OPTIMAL`, return `BLOCK_CONSTRUCTOR`. Do not edit its target weights.

- [ ] **Step 8: Build the freeze manifest**

Include exact upstream hashes, selected policy tuple, constructor tuple, constructor semantic target hash, `positive_weight_security_count`, `m3_holding_count_gt_1e8`, and `target_weight_sum`.

Count positive weights with `Decimal(weight) > 0`; separately count M3.1 holdings with `Decimal(weight) > Decimal("0.00000001")`.

- [ ] **Step 9: Add a test proving no market-data interface exists**

Inspect the public function signature with `inspect.signature(...)` and assert it has no parameter names containing `price`, `return`, `dividend`, `action`, or `market`.

- [ ] **Step 10: Add ordering determinism test**

Reverse both benchmark rows and screening views. Assert identical target rows after canonical sort and identical semantic target hash.

- [ ] **Step 11: Run GREEN tests**

```bash
pytest -q tests/test_m3_pre_return_portfolio_freeze.py tests/test_paper_portfolio_constructor.py
```

- [ ] **Step 12: Commit**

```bash
git add src/wa_commons/portfolio/freeze.py src/wa_commons/portfolio/__init__.py tests/test_m3_pre_return_portfolio_freeze.py
git commit -m "feat: add return-blind portfolio freeze assembler"
```

---

### Task 3: Add local/public artifact writer and operator CLI

**Files:**
- Modify: `src/wa_commons/portfolio/freeze.py`
- Create: `scripts/run_m3_pre_return_portfolio_freeze.py`
- Create: `tests/test_m3_pre_return_portfolio_freeze_cli.py`

**Interfaces:**
- Produces:
  - `write_frozen_portfolio(payload, local_output, public_output) -> None`;
  - CLI inputs `--benchmark-mapping`, `--screening`, `--policy`, `--freeze-config`, `--constructor-config`, `--local-output`, `--public-output`, `--code-commit`.

- [ ] **Step 1: Write failing local/public boundary tests**

Assert local and public paths must differ. Assert the public JSON contains no keys named `target_weights`, `security_id`, `security_code`, `provider_local_code`, `name`, or `rows` anywhere recursively.

- [ ] **Step 2: Write failing CLI fixture test**

Create tiny local fixture files and run the CLI twice. Assert both public outputs are byte-identical and both local semantic target hashes match.

- [ ] **Step 3: Implement writer**

Write the full payload to local output. Public output must include only:

```python
{
  "artifact_version": ...,
  "issue": 80,
  "status": ...,
  "code_commit": ...,
  "benchmark_id": ...,
  "benchmark_semantic_mapping_sha256": ...,
  "tse_screening_sha256": ...,
  "policy_profile_id": ...,
  "policy_profile_version": ...,
  "policy_sha256": ...,
  "constructor_id": ...,
  "constructor_version": ...,
  "constructor_config_sha256": ...,
  "semantic_target_hash": ...,
  "input_constituent_count": ...,
  "positive_weight_security_count": ...,
  "m3_holding_count_gt_1e8": ...,
  "target_weight_sum": ...,
  "target_min_weight": ...,
  "target_max_weight": ...,
  "row_level_output_local_only": true
}
```

- [ ] **Step 4: Implement local-input-only CLI**

The CLI must never download a URL. It reads only user-supplied local paths and prints only aggregate status/hash/counts.

- [ ] **Step 5: Run focused tests**

```bash
pytest -q tests/test_m3_pre_return_portfolio_freeze.py tests/test_m3_pre_return_portfolio_freeze_cli.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/portfolio/freeze.py scripts/run_m3_pre_return_portfolio_freeze.py tests/test_m3_pre_return_portfolio_freeze_cli.py
git commit -m "feat: add pre-return freeze artifacts and CLI"
```

---

### Task 4: Reproduce the accepted real inputs, freeze the canonical target, and publish aggregate acceptance

**Files:**
- Create: `docs/results/M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_V01.md`
- Create: `docs/results/M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_MANIFEST_V01.json`
- Create: `.github/workflows/m3-pre-return-portfolio-freeze.yml`
- Modify: `ROADMAP.md`

**Interfaces:**
- Consumes local full #50 and #55 artifacts reproduced from their accepted source/config/code hashes.
- Produces the canonical #80 local full artifact for #56 and a repo-safe public aggregate manifest.

- [ ] **Step 1: Reproduce or locate the accepted #50 local full mapping artifact**

Verify its manifest contains:

```text
benchmark_id = JPX:TOPIX_TOTAL_RETURN:6000
semantic_mapping_sha256 = 1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409
constituent_count = 1637
mapped_count = 1637
```

If the row-level artifact cannot be reproduced exactly, stop with `BLOCK_INPUT_VERSION` and do not continue.

- [ ] **Step 2: Reproduce or locate the accepted #55 local full screening artifact**

Verify:

```text
tse_screening_sha256 = aff7ea3437d2b19282e96b095e989f54d68bb7443eafc66e170396a9bcf2a17c
company_count = 3707
profile_count = 3
view_count = 11121
```

Also verify exactly one selected strict-profile view exists for every #50 canonical entity ID used by the run.

- [ ] **Step 3: Verify the selected policy file hash before running**

Compute its canonical policy hash with the same #55 convention. It must equal:

```text
7b2558875af5f23ae32061c218a15de94dce479badf239f6b412bd77ba51a72c
```

Verify `preferences == []`.

- [ ] **Step 4: Run the real freeze twice from the same local inputs**

Example:

```bash
python scripts/run_m3_pre_return_portfolio_freeze.py \
  --benchmark-mapping <LOCAL_ACCEPTED_50_JSON> \
  --screening <LOCAL_ACCEPTED_55_JSON> \
  --policy configs/policies/strict-military-avoidance.json \
  --freeze-config configs/m3-3b2-pre-return-portfolio-freeze-v0.1.json \
  --constructor-config configs/portfolio/benchmark-l2-projection-v0.1.json \
  --local-output <LOCAL_ONLY_FREEZE_JSON> \
  --public-output docs/results/M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_MANIFEST_V01.json \
  --code-commit <FEATURE_HEAD>
```

Use the repository's actual accepted policy path discovered at execution time; do not invent a second policy copy.

Run a second time to a temporary local/public pair and require identical semantic target hash and byte-identical public manifest aside from no varying timestamp field. If retrieval/runtime timestamps would make the public manifest nondeterministic, keep them out of the semantic/public payload.

- [ ] **Step 5: Record measured acceptance**

`M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_V01.md` must report:

- exact upstream hashes;
- selected policy tuple;
- exact input constituent count;
- measured positive-weight security count;
- measured `>1e-8` holding count;
- measured target-weight sum/min/max;
- semantic target hash;
- confirmation that zero selected-period market values were inputs;
- confirmation that no sparsification/post-processing occurred;
- confirmation that row-level target weights remain local-only;
- any blocked condition without hiding it.

Do not publish the security list or row-level weights.

- [ ] **Step 6: Update ROADMAP dependency order**

Set Workstream 3D to show #49 completed and #80 as the pre-return freeze. Set Workstream 3E to `#80 → #56`. Set Workstream 3F to consume completed #80 and #56 rather than selecting the base policy/portfolio itself.

- [ ] **Step 7: Add focused CI**

Create `.github/workflows/m3-pre-return-portfolio-freeze.yml` triggered by changes to the freeze config/module/CLI/tests/result manifest/roadmap. Run the three #80 focused test files plus the existing constructor regression tests.

- [ ] **Step 8: Run final verification**

```bash
pytest -q tests/test_m3_pre_return_portfolio_freeze_contract.py tests/test_m3_pre_return_portfolio_freeze.py tests/test_m3_pre_return_portfolio_freeze_cli.py tests/test_paper_portfolio_constructor.py
pytest -q
git diff --check
```

Expected: focused tests PASS, full repo suite PASS, diff check clean.

- [ ] **Step 9: Commit final acceptance**

```bash
git add configs/m3-3b2-pre-return-portfolio-freeze-v0.1.json src/wa_commons/portfolio/freeze.py src/wa_commons/portfolio/__init__.py scripts/run_m3_pre_return_portfolio_freeze.py tests/test_m3_pre_return_portfolio_freeze_contract.py tests/test_m3_pre_return_portfolio_freeze.py tests/test_m3_pre_return_portfolio_freeze_cli.py docs/results/M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_V01.md docs/results/M3_3B2_PRE_RETURN_PORTFOLIO_FREEZE_MANIFEST_V01.json .github/workflows/m3-pre-return-portfolio-freeze.yml ROADMAP.md
git commit -m "feat: freeze first Peace Capital target portfolio"
```

- [ ] **Step 10: PR/CI/merge gate**

Push the branch, open a PR referencing #80, verify final-head CI, inspect the public manifest for row-level leakage, and merge only if all checks are green. Close #80 only after the merged `main` artifact/hash is re-fetched and verified.
