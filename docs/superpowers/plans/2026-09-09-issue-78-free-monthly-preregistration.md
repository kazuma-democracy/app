# Issue #78 Free Monthly Preregistration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Commit a zero-purchase, monthly, event-driven market-evaluation contract for October 2026 that Issue #56 can implement without selecting dates, sources, return arithmetic, or corporate-action semantics after observing performance.

**Architecture:** Issue #78 is a preregistration gate only. It creates a machine-checkable config and repo-safe provenance manifest that pin the corrected October calendar-month interval, free JPX source roles, held-security evidence priority, return arithmetic, failure states, and publication boundary. Actual JPX file ingestion, parsers, event resolution, and return calculation remain Issue #56 work.

**Tech Stack:** JSON + Markdown, Python 3.11 stdlib (`json`, `hashlib`, `pathlib`) and the existing pytest stack. No new runtime dependency, paid API, scraper, database, scheduler, or market-data framework.

**Spec:** `docs/superpowers/specs/2026-09-09-m3-3c-free-monthly-evaluation-design.md`

**Supersedes:** `docs/superpowers/plans/2026-09-09-issue-78-market-data-preregistration.md` from design commit `0bae64037619ab14241104fede6883899896f9c3`. Do not execute the superseded daily/paid-source plan.

## Global Constraints

- Benchmark identity remains `JPX:TOPIX_TOTAL_RETURN:6000`; no benchmark reselection occurs here.
- Benchmark component snapshot remains the accepted #50 snapshot effective `2026-07-31` with semantic mapping SHA-256 `1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409`.
- Portfolio-definition cutoff is `2026-09-29_CLOSE`.
- Execution/start valuation is `2026-09-30_CLOSE`.
- Canonical realized interval is `2026-10-01` through `2026-10-30`.
- Benchmark return is the official one-month dividend-included TOPIX ROI for October 2026.
- Scheduled rebalance inside the interval is `NONE_AFTER_INITIAL_ALLOCATION`.
- M3 v1 data acquisition is zero-purchase and zero-subscription.
- Raw JPX and issuer source rows/documents remain local-only.
- No October candidate return, benchmark return, tracking result, or other selected-period performance value may appear in the preregistration config or manifest.
- #78 must not implement a market-data parser, download October market rows, or calculate performance.
- Actual public release of market-performance numbers remains separately rights-gated.

---

### Task 1: Commit the corrected free-monthly preregistration config

**Files:**
- Create: `configs/m3-3c0-free-monthly-prereg-v0.1.json`
- Create: `tests/test_m3_3c0_free_monthly_preregistration.py`

**Interfaces:**
- Consumes: #50 benchmark manifest identity/hash and approved Issue #78 dates/source roles.
- Produces: `configs/m3-3c0-free-monthly-prereg-v0.1.json`, the sole machine-readable source of period/source/return-basis constants for later #56 work.

- [ ] **Step 1: Write the failing preregistration test.**

```python
import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_free_monthly_window_is_pinned_before_performance():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["artifact_version"] == "m3.3c0-free-monthly-prereg-v0.1"
    assert value["issue"] == 78
    assert value["benchmark_id"] == "JPX:TOPIX_TOTAL_RETURN:6000"
    assert value["benchmark_effective_date"] == "2026-07-31"
    assert value["benchmark_semantic_mapping_sha256"] == "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409"
    assert value["portfolio_definition_cutoff"] == "2026-09-29_CLOSE"
    assert value["execution_start_valuation"] == "2026-09-30_CLOSE"
    assert value["evaluation_start"] == "2026-10-01"
    assert value["evaluation_end"] == "2026-10-30"
    assert value["benchmark_period"] == "2026-10"
    assert value["return_basis"] == "MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY"
    assert value["rebalance_policy"] == "NONE_AFTER_INITIAL_ALLOCATION"
    assert value["purchase_authorized"] is False
    assert value["subscription_authorized"] is False
    assert value["selected_period_rows_ingested"] is False
    assert value["implementation_gate"] == "READY_FOR_ISSUE_56_AFTER_PREREG_VERIFICATION"
    forbidden = {
        "candidate_return",
        "benchmark_return",
        "excess_return",
        "tracking_error",
        "cumulative_return",
        "selected_period_performance",
    }
    assert forbidden.isdisjoint(value)
```

- [ ] **Step 2: Run the test and verify RED.**

Run:
```bash
python -m pytest -q tests/test_m3_3c0_free_monthly_preregistration.py
```
Expected: FAIL because `configs/m3-3c0-free-monthly-prereg-v0.1.json` does not exist.

- [ ] **Step 3: Create the minimal config.**

Use exactly these top-level values plus the Task 2/3 nested contracts added later:

```json
{
  "artifact_version": "m3.3c0-free-monthly-prereg-v0.1",
  "issue": 78,
  "timezone": "Asia/Tokyo",
  "benchmark_id": "JPX:TOPIX_TOTAL_RETURN:6000",
  "benchmark_effective_date": "2026-07-31",
  "benchmark_semantic_mapping_sha256": "1cc4b239507b8285e0b5d9fd348fc31e9ccc26a71bc0bc217baa1c3a6fa24409",
  "portfolio_definition_cutoff": "2026-09-29_CLOSE",
  "execution_start_valuation": "2026-09-30_CLOSE",
  "evaluation_start": "2026-10-01",
  "evaluation_end": "2026-10-30",
  "benchmark_period": "2026-10",
  "return_basis": "MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY",
  "rebalance_policy": "NONE_AFTER_INITIAL_ALLOCATION",
  "purchase_authorized": false,
  "subscription_authorized": false,
  "selected_period_rows_ingested": false,
  "implementation_gate": "READY_FOR_ISSUE_56_AFTER_PREREG_VERIFICATION"
}
```

- [ ] **Step 4: Run the focused test and verify GREEN.**
- [ ] **Step 5: Scan the config for any observed October price/return/performance value.** It must contain none.
- [ ] **Step 6: Commit:** `docs: pin free monthly M3.3c0 evaluation contract`.

### Task 2: Pin free source roles and the local/public rights boundary

**Files:**
- Modify: `configs/m3-3c0-free-monthly-prereg-v0.1.json`
- Create: `docs/results/M3_3C0_FREE_MONTHLY_SOURCE_CONTRACT_V01.md`
- Create: `tests/test_m3_3c0_free_monthly_source_contract.py`

**Interfaces:**
- Consumes: Task 1 config.
- Produces: `source_contract` object containing exact free-source roles, acquisition mode, local/raw/public boundaries, and required source locators.

- [ ] **Step 1: Write the failing source-contract test.**

```python
import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_source_contract_is_zero_purchase_local_first_and_monthly():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    source = value["source_contract"]
    assert source["cost_model"] == "ZERO_PURCHASE_ZERO_SUBSCRIPTION"
    assert source["acquisition_mode"] == "MANUAL_MONTHLY_DOWNLOAD_THEN_LOCAL_HASH"
    assert source["raw_source_publication"] == "PROHIBITED_BY_PROJECT_POLICY"
    assert source["raw_storage"] == "LOCAL_ONLY"
    assert source["whole_market_daily_store"] is False
    assert source["automated_high_frequency_jpx_scraping"] is False
    roles = source["roles"]
    assert roles["start_price"]["source"] == "TSE_MONTHLY_STOCK_PRICE_TABLE"
    assert roles["start_price"]["period"] == "2026-09"
    assert roles["end_price"]["source"] == "TSE_MONTHLY_STOCK_PRICE_TABLE"
    assert roles["end_price"]["period"] == "2026-10"
    assert roles["benchmark"]["source"] == "JPX_DIVIDEND_INCLUDED_INDEX_MONTHLY_ROI"
    assert roles["benchmark"]["period"] == "2026-10"
    assert roles["action_detector"]["source"] == "TSE_MONTHLY_STATISTICS_REPORT"
    assert roles["held_security_primary_evidence"]["scope"] == "HELD_SECURITIES_ONLY"
```

- [ ] **Step 2: Run the new test and verify RED** because `source_contract` is absent.
- [ ] **Step 3: Add `source_contract` to the config** with these exact locator families:
  - `https://www.jpx.co.jp/markets/statistics-equities/price/`
  - `https://www.jpx.co.jp/markets/statistics-equities/monthly/`
  - `https://www.jpx.co.jp/markets/indices/related/ratio/`
  - `https://www.jpx.co.jp/equities/listing/disclosure/tdnet/index.html`
  - `https://www.jpx.co.jp/listing/disclosure/01.html`
  - `https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WEEK0060.html`
  - `https://www.jpx.co.jp/listing/others/ex-rights/index.html`
- [ ] **Step 4: Set primary-evidence priority exactly as:** `ISSUER_IR`, `TSE_LISTED_COMPANY_SEARCH_OR_TDNET`, `EDINET`, `JPX_RIGHTS_LISTING_INFO`.
- [ ] **Step 5: Write the source-contract result doc** documenting why paid DataCube/J-Quants Pro is not adopted, why raw files stay local, why absence from a monthly detector is not proof of no cash dividend, and why publication of actual performance numbers remains a separate rights check.
- [ ] **Step 6: Run Tasks 1-2 tests and verify GREEN.**
- [ ] **Step 7: Commit:** `docs: pin zero-cost JPX monthly source contract`.

### Task 3: Pin return arithmetic, evidence states, and fail-closed behavior

**Files:**
- Modify: `configs/m3-3c0-free-monthly-prereg-v0.1.json`
- Modify: `docs/results/M3_3C0_FREE_MONTHLY_SOURCE_CONTRACT_V01.md`
- Create: `tests/test_m3_3c0_free_monthly_return_contract.py`

**Interfaces:**
- Consumes: Task 2 source roles.
- Produces: `return_contract` and `terminal_states` that #56 must implement exactly.

- [ ] **Step 1: Write the failing return-contract test.**

```python
import json
from pathlib import Path

CONFIG = Path("configs/m3-3c0-free-monthly-prereg-v0.1.json")


def test_monthly_return_contract_is_total_wealth_and_fail_closed():
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = value["return_contract"]
    assert contract["basis"] == "MONTHLY_GROSS_TOTAL_WEALTH_RETURN_JPY"
    assert contract["start_price_date"] == "2026-09-30"
    assert contract["end_price_date"] == "2026-10-30"
    assert contract["cash_distribution_treatment"] == "RETAIN_AS_CASH_TO_ENDPOINT"
    assert contract["synthetic_reinvestment"] is False
    assert contract["infer_action_from_price_jump"] is False
    assert contract["missing_value_treatment"] == "BLOCK"
    assert contract["name_only_relink"] == "PROHIBITED"
    held = set(value["terminal_states"]["held_security"])
    assert held == {
        "RETURN_OK_NO_ACTION",
        "RETURN_OK_ACTION_EXPLAINED",
        "BLOCK_START_PRICE",
        "BLOCK_END_PRICE",
        "BLOCK_DIVIDEND_EVIDENCE",
        "BLOCK_CORPORATE_ACTION",
        "BLOCK_IDENTITY",
    }
    snapshot = set(value["terminal_states"]["snapshot"])
    assert snapshot == {
        "BLOCK_SOURCE_UNAVAILABLE",
        "BLOCK_BENCHMARK_MONTHLY_RETURN",
        "BLOCK_RIGHTS_PUBLICATION",
    }
```

- [ ] **Step 2: Run the test and verify RED** because `return_contract` and `terminal_states` are absent.
- [ ] **Step 3: Add `return_contract`** that explicitly states:
  - start wealth uses frozen position units/weights and 2026-09-30 close;
  - end wealth uses 2026-10-30 close and only explicitly evidenced action-adjusted units;
  - explicit cash dividends/cash consideration add to wealth;
  - cash remains cash through endpoint;
  - split/reverse split, merger/share exchange, cash acquisition/squeeze-out and delisting require explicit primary evidence;
  - unresolved evidence blocks the run.
- [ ] **Step 4: Add the exact `terminal_states` arrays asserted above.**
- [ ] **Step 5: Add a `parser_requirements` section** specifying exact JPX security-code identity mapping, held-security-only row extraction, source SHA-256/retrieval timestamp capture, duplicate/conflict detection, and no zero-fill. This is a contract only; do not implement parser code in #78.
- [ ] **Step 6: Run all three focused tests and verify GREEN.**
- [ ] **Step 7: Commit:** `docs: pin free monthly return and action semantics`.

### Task 4: Publish the preregistration manifest and hand off to #56

**Files:**
- Create: `docs/results/M3_3C0_FREE_MONTHLY_PREREGISTRATION_MANIFEST_V01.json`
- Modify: `ROADMAP.md` only to record #78 as the completed preregistration gate; do not mark #56 complete.
- GitHub metadata: update Issue #56 to consume #78 rather than claiming #50 defines the evaluation period.

**Interfaces:**
- Consumes: final config from Tasks 1-3.
- Produces: immutable repo-safe preregistration manifest and corrected #56 dependency wording.

- [ ] **Step 1: Compute the SHA-256 of the final preregistration config bytes** and record it in the manifest.
- [ ] **Step 2: Create the manifest** with exactly these categories: artifact/config version, Issue #78, benchmark identity/effective date/mapping hash, corrected October dates, source-role identifiers/locators, zero-cost acquisition mode, raw/public boundary, return-basis identifier, terminal-state schema version, config SHA-256, and `selected_period_rows_ingested=false`.
- [ ] **Step 3: Assert the manifest contains no keys named** `candidate_return`, `benchmark_return`, `excess_return`, `tracking_error`, `price_rows`, `dividend_rows`, or `performance_selected_period`.
- [ ] **Step 4: Update Issue #56 Inputs/Scope** so it consumes completed #78 for the evaluation interval, free source contract, return basis, parser requirements and failure states; preserve #56's existing no-look-ahead and fail-closed requirements.
- [ ] **Step 5: Update `ROADMAP.md`** with one bounded line showing #78 as the M3.3c0 prerequisite and #56 as its implementation consumer.
- [ ] **Step 6: Run focused verification:**

```bash
python -m pytest -q \
  tests/test_m3_3c0_free_monthly_preregistration.py \
  tests/test_m3_3c0_free_monthly_source_contract.py \
  tests/test_m3_3c0_free_monthly_return_contract.py
git diff --check
```

Expected: all focused tests PASS; diff check clean.

- [ ] **Step 7: Run the full repository suite once:**

```bash
python -m pytest -q
```

Record the fresh pass count in the PR body and #78 completion comment.

- [ ] **Step 8: Open a PR containing only** the approved free-monthly spec, this plan, preregistration config/tests, source-contract result, manifest and bounded ROADMAP update. Do not include raw JPX files, market rows, parser implementation, or performance results.
- [ ] **Step 9: Require clean CI and review the PR diff for raw-data/performance leakage.**
- [ ] **Step 10: Merge only after verification, close #78 as completed, and re-fetch `main` HEAD.** #56 becomes READY for a separate implementation plan; do not start #56 inside the #78 PR.

## Self-review

- Spec coverage: corrected October interval, benchmark alignment, zero-cost monthly sources, held-security-only evidence, local/raw publication boundary, total-wealth arithmetic, corporate-action evidence, terminal states, no-look-ahead, no performance inspection, and #56 handoff each map to an explicit task.
- Placeholder scan: no `TBD`, `TODO`, assumed paid product, invented provider field, or future parser implementation is required in #78.
- Type/state consistency: all tests refer to the same config path and the same period/state names; Task 4 consumes exactly the objects established in Tasks 1-3.
- Scope check: #78 stays methodology/source-contract only. Actual JPX parsing, held-security event resolution, monthly wealth calculation and performance evaluation remain #56/#51 work.