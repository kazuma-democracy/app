# Issue #78 Market-Data Preregistration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preregister the first Peace Capital return-evaluation window and select a rights-compatible JPX market-data/total-return/corporate-action contract before #56 ingests the selected period's return values.

**Architecture:** Treat #78 as a methodology/source-rights gate, not a market-data ingestion task. First commit a machine-checkable no-performance preregistration contract pinned to the accepted #50 benchmark artifact; then adjudicate official JPX product capabilities and rights from official documentation only. #56 may start only if #78 reaches `ADOPT`; otherwise #78 remains explicitly blocked without changing the window, benchmark, return basis, or provider family after observing performance.

**Tech Stack:** JSON + Markdown, Python 3.11 stdlib (`json`, `pathlib`, `datetime`) and existing pytest/jsonschema development stack. Official JPX/J-Quants product/terms pages are research inputs; no selected-period market-return rows are downloaded in #78.

**Spec:** `docs/superpowers/specs/2026-09-09-m3-3c-market-return-ingestion-design.md`; GitHub Issue #78; GitHub Issue #56; `docs/PAPER_PORTFOLIO_EVALUATION.md`; `docs/results/M3_3B_TOPIX_BENCHMARK_MAPPING_MANIFEST_V01.json`.

## Global Constraints

- Canonical evaluation interval is fixed at TSE trading days from `2026-09-02` through `2026-09-30`.
- Benchmark input remains `JPX:TOPIX_TOTAL_RETURN:6000`, effective `2026-07-31`, available at `2026-08-31T16:20:00+09:00`.
- Exact accepted benchmark mapping hash is `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.
- Decision/execution boundary is `2026-09-01 close`; first realized return is `2026-09-02`; minimum decision lag is one full TSE trading day.
- Return basis requirement is JPY gross total return compatible with the adopted TOPIX Total Return benchmark. No silent price-return downgrade.
- `2026-09-02` through `2026-09-08` is `ENGINEERING_VALIDATION` only and never replaces the canonical endpoint.
- #78 may inspect product specifications, terms, schemas, sample metadata and pricing, but must not ingest the selected-period security return rows or candidate-vs-benchmark performance.
- No purchase, subscription, trial activation or paid API call is authorized without explicit user approval.
- Source preference remains JPX file-first; J-Quants Pro is an escalation route only when evidenced necessary. Third-party substitution requires a separate source decision.
- Missing rights, total-return primitives or required corporate-action semantics become explicit BLOCK states, not inferred permissions or invented treatments.

---

### Task 1: Commit the no-performance preregistration contract

**Files:**
- Create: `configs/m3-3c0-market-data-prereg-v0.1.json`
- Create: `tests/test_m3_3c0_market_data_preregistration.py`

**Interfaces:**
- Consumes: accepted #50 manifest fields and approved architecture constants.
- Produces: a machine-readable preregistration contract with `source_contract_status` and `implementation_gate` state, but no observed return/performance values.

- [ ] **Step 1: Write the failing contract test.**

```python
import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-market-data-prereg-v0.1.json")


def test_first_evaluation_window_is_preregistered_without_performance():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["artifact_version"] == "m3.3c0-market-data-prereg-v0.1"
    assert value["issue"] == 78
    assert value["benchmark_id"] == "JPX:TOPIX_TOTAL_RETURN:6000"
    assert value["benchmark_effective_date"] == "2026-07-31"
    assert value["benchmark_available_at"] == "2026-08-31T16:20:00+09:00"
    assert value["benchmark_semantic_mapping_sha256"] == "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409"
    assert value["evaluation_start"] == "2026-09-02"
    assert value["evaluation_end"] == "2026-09-30"
    assert value["decision_execution_boundary"] == "2026-09-01_CLOSE"
    assert value["minimum_decision_lag_trading_days"] == 1
    assert value["return_basis_required"] == "GROSS_TOTAL_RETURN_JPY"
    assert value["rebalance_policy"] == "INITIAL_ALLOCATION_ONLY"
    assert value["engineering_validation_end"] == "2026-09-08"
    assert value["source_contract_status"] == "UNVERIFIED"
    assert value["implementation_gate"] == "BLOCKED_SOURCE_CONTRACT"
    forbidden = {
        "candidate_return",
        "benchmark_return",
        "cumulative_return",
        "tracking_difference",
        "tracking_error",
        "performance_selected_period",
    }
    assert forbidden.isdisjoint(value)
```

- [ ] **Step 2: Run `python -m pytest -q tests/test_m3_3c0_market_data_preregistration.py` and verify RED** because the config does not exist.
- [ ] **Step 3: Create the preregistration JSON** with exactly the fields asserted above plus `timezone="Asia/Tokyo"`, `provider_priority=["JPX_FILE_FIRST","J_QUANTS_PRO"]`, `raw_selected_period_ingestion=false`, `purchase_authorized=false`, and `methodology_change_after_return_inspection=false`.
- [ ] **Step 4: Run the focused test and verify GREEN.**
- [ ] **Step 5: Inspect the JSON manually for any selected-period price, return, portfolio, or performance value.** It must contain none.
- [ ] **Step 6: Commit:** `docs: pin M3.3c0 evaluation window before return ingestion`.

### Task 2: Adjudicate official JPX product capabilities and rights

**Files:**
- Create: `docs/results/M3_3C0_MARKET_DATA_SOURCE_RIGHTS_V01.md`
- Modify later in this task: `configs/m3-3c0-market-data-prereg-v0.1.json`

**Interfaces:**
- Consumes: official JPX/J-Quants documentation only, plus Task 1 preregistration.
- Produces: one evidence-backed source decision state and a rights matrix; it does not download September 2026 security-return rows.

- [ ] **Step 1: Re-fetch and timestamp the official product/terms sources before making the decision.** At minimum inspect:
  - DataCube price list: `https://db-ec.jpx.co.jp/client_info/JPX_DLSITE/html/datacube_price.pdf`;
  - DataCube file specification: `https://db-ec.jpx.co.jp/client_info/JPX_DLSITE/html/data_detail.pdf`;
  - J-Quants Pro Stock Prices (OHLC): `https://pro.jpx-jquants.com/datasets/9`;
  - J-Quants Pro Corporate Action Data: `https://pro.jpx-jquants.com/datasets/14`;
  - J-Quants Pro Listed Shares Corporate Action Factors: `https://pro.jpx-jquants.com/datasets/17`;
  - J-Quants Pro terms: `https://pro.jpx-jquants.com/termsofservice`.
- [ ] **Step 2: Build the result-document rights matrix** with one row per candidate product and explicit columns: publisher, exact product, delivery method, historical coverage, price fields, adjusted-price/factor support, cash-dividend support, merger/share-exchange support, cash-acquisition/squeeze-out support, delisting support, local raw-storage status, raw redistribution status, derived-output publication status, commercial-use status, minimum commitment, published price, terms URL, retrieval timestamp, and evidence citation/locator.
- [ ] **Step 3: Apply the `USE > EXTEND > ADAPT > REPLACE > BUILD` decision rule.** Record these fixed interpretations unless new official evidence disproves them:
  - DataCube `東証株式四本値` is a valid bounded official price primitive candidate but is **not sufficient by itself** for gross total return unless official documentation identifies the required dividend/corporate-action primitives in the purchased file/product set;
  - J-Quants Pro Stock Prices supplies adjusted/unadjusted OHLC and adjustment factors;
  - J-Quants Pro Corporate Action Data supplies cash dividends and multiple reorganization/delisting events;
  - J-Quants Pro is an escalation route, not an automatic purchase.
- [ ] **Step 4: Set exactly one source-contract terminal/preterminal state in the result doc and config:**
  - `ADOPT` — exact rights/product set is authorized and sufficient at schema/contract level;
  - `READY_FOR_USER_AUTHORIZATION` — exact sufficient paid product/rights set is known, but explicit user approval/purchase/subscription is still required;
  - `BLOCKED_RIGHTS` — intended local use/storage/publication cannot be established;
  - `BLOCKED_RETURN_BASIS` — rights-cleared candidate cannot support compatible gross total return;
  - `BLOCKED_CORPORATE_ACTION` — required bounded-period action semantics cannot be supplied unambiguously.
- [ ] **Step 5: If the state is `READY_FOR_USER_AUTHORIZATION`, stop before any purchase.** Present the exact product(s), usage category, current published cost/commitment and what each product unlocks. #78 remains open until the user explicitly authorizes the next action.
- [ ] **Step 6: If the state is a BLOCK state, leave #78 open and document the exact violated assumption.** Do not broaden the period or switch provider family inside #78.
- [ ] **Step 7: If the state is `ADOPT`, update the config** with exact `provider`, `product_ids_or_names`, `usage_category`, `terms_urls`, `rights_retrieved_at`, `raw_local_storage_allowed`, `raw_publication_allowed`, `derived_publication_allowed`, `attribution_requirement`, `source_contract_status="ADOPT"`, and `implementation_gate="READY_FOR_ISSUE_56"`.
- [ ] **Step 8: Run the Task 1 test plus a config parse check.** Expected: GREEN and no observed performance fields.
- [ ] **Step 9: Commit:** `docs: adjudicate M3.3c0 market-data source rights`.

### Task 3: Pin total-return and corporate-action semantics at the schema level

**Files:**
- Modify: `configs/m3-3c0-market-data-prereg-v0.1.json`
- Modify: `docs/results/M3_3C0_MARKET_DATA_SOURCE_RIGHTS_V01.md`
- Create: `tests/test_m3_3c0_return_basis_contract.py`

**Interfaces:**
- Consumes: Task 2 source decision and official provider field definitions.
- Produces: a source-specific arithmetic/action contract that #56 can implement without inventing methodology.

- [ ] **Step 1: Write the failing return-basis contract test.**

```python
import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-market-data-prereg-v0.1.json")


def test_adopted_source_contract_defines_total_return_and_action_fields():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if value["source_contract_status"] != "ADOPT":
        return
    contract = value["return_contract"]
    assert contract["basis"] == "GROSS_TOTAL_RETURN_JPY"
    assert contract["price_field"]
    assert contract["prior_price_field"]
    assert contract["cash_dividend_field"]
    assert contract["corporate_action_effective_date_field"]
    assert contract["security_code_field"]
    assert contract["unexplained_missing_return"] == "BLOCK"
    assert contract["duplicate_conflicting_action"] == "BLOCK"
    assert contract["name_only_relink"] == "PROHIBITED"
    assert value["implementation_gate"] == "READY_FOR_ISSUE_56"
```

- [ ] **Step 2: Run `python -m pytest -q tests/test_m3_3c0_return_basis_contract.py` and verify RED** when an adopted source lacks the source-specific return contract.
- [ ] **Step 3: Copy the exact provider field names and timing definitions from official documentation into `return_contract`.** Include security code, trading date, close/prior-close inputs, adjustment factor/action field where applicable, cash-dividend amount, ex/effective date, merger/share-exchange identifiers or event type, cash consideration where supplied, delisting date/status, and provider publication/as-known timestamp field if available.
- [ ] **Step 4: Record the arithmetic convention textually in the result doc.** Candidate total simple return must decompose into capital-return and explicit cash-distribution components on a source-defined basis; no factor may be inferred from a price jump and no missing dividend/action value may be guessed.
- [ ] **Step 5: Record action treatment:** split/reverse split only from provider factor/action; cash dividend only from explicit provider amount/timing; merger/share exchange only with fully identified conversion terms; cash acquisition/squeeze-out only with explicit consideration/effective timing; delisting without documented proceeds/treatment => BLOCK; cash created by action remains cash until next scheduled rebalance.
- [ ] **Step 6: Run both #78 focused tests.** Expected: GREEN for `ADOPT`; for non-ADOPT state, Task 1 stays GREEN and Task 3 documents the blocker without pretending readiness.
- [ ] **Step 7: Commit:** `docs: pin M3.3c0 total-return action contract`.

### Task 4: Publish the preregistration manifest and hand off cleanly to #56

**Files:**
- Create only when `source_contract_status=ADOPT`: `docs/results/M3_3C0_MARKET_DATA_PREREGISTRATION_MANIFEST_V01.json`
- Modify only when `source_contract_status=ADOPT`: `ROADMAP.md`
- GitHub metadata mutation only when `source_contract_status=ADOPT`: Issue #56 body/dependency wording

**Interfaces:**
- Consumes: Tasks 1-3 final config/result state.
- Produces: immutable public preregistration provenance and a corrected #56 prerequisite contract; no market-return rows.

- [ ] **Step 1: If state is not `ADOPT`, do not create a READY manifest, do not amend ROADMAP to complete #78, and do not unlock #56.** Leave #78 open with the exact blocker/authorization gate recorded.
- [ ] **Step 2: If state is `ADOPT`, write the public manifest** containing: artifact/config version, Issue #78, benchmark ID/effective/available timestamps, benchmark semantic mapping hash, evaluation start/end, decision boundary, lag, return basis, provider/product identifiers, rights-mode summary, terms locators/retrieval timestamps, corporate-action policy version, config SHA-256, and `raw_selected_period_rows_ingested=false`.
- [ ] **Step 3: Verify the manifest contains no security-level price, dividend, return, portfolio-weight, candidate-performance or benchmark-performance rows.**
- [ ] **Step 4: Amend Issue #56** so its Inputs include completed #78 and its Scope says it consumes the evaluation period/source/rights/return-basis contract from #78, rather than falsely claiming #50 defines the evaluation period. Preserve all existing #56 fail-closed and out-of-scope rules.
- [ ] **Step 5: Amend `ROADMAP.md` Workstream 3E** to list #78 as the completed preregistration gate and #56 as the implementation consumer. Do not mark #56 complete.
- [ ] **Step 6: Run verification:**

```bash
python -m pytest -q tests/test_m3_3c0_market_data_preregistration.py tests/test_m3_3c0_return_basis_contract.py
git diff --check
```

Expected: all focused tests PASS; diff check clean.

- [ ] **Step 7: Run the full repository suite once before completion:** `python -m pytest -q`. Record the fresh pass count; do not rely on an older suite result.
- [ ] **Step 8: Open a PR containing only the approved architecture/spec, #78 plan, preregistration config/tests, source-rights result, and any ADOPT-only manifest/ROADMAP changes.** No selected-period market data, #56 parser, or performance code belongs in this PR.
- [ ] **Step 9: Require clean CI and review the PR diff for raw market-data leakage.**
- [ ] **Step 10: Merge only if #78 is `ADOPT`; close #78 as completed and re-fetch `main` HEAD.** If state is `READY_FOR_USER_AUTHORIZATION` or BLOCKED, keep the PR/Issue disposition truthful and do not claim #56 readiness.

## Self-review

- Spec coverage: period pin, benchmark provenance, source priority, rights boundary, total-return requirement, corporate-action semantics, no-look-ahead, no purchase without authorization, no return ingestion, fail-closed states and #56 handoff each have an explicit task.
- Placeholder scan: no `TBD`, `TODO`, invented provider field or assumed permission is required. Source-specific field names are copied only after official documentation is re-fetched in Task 3.
- Type/state consistency: Task 1 begins `UNVERIFIED/BLOCKED_SOURCE_CONTRACT`; Task 2 moves to exactly one of `ADOPT`, `READY_FOR_USER_AUTHORIZATION`, `BLOCKED_RIGHTS`, `BLOCKED_RETURN_BASIS`, `BLOCKED_CORPORATE_ACTION`; only `ADOPT` permits `READY_FOR_ISSUE_56` and Task 4 completion.
- Scope check: #78 and #56 remain separate plans. This plan intentionally does not specify #56 parser implementation because the exact provider schema/rights contract is an output of #78; a placeholder-free #56 implementation plan must be written only after #78 reaches `ADOPT`.
