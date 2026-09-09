# Issue #56 Monthly Market Primitives Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic, month-parameterized, zero-cost JPX price / benchmark-return / corporate-action primitives that can feed #85 Historical Replay and the October 2026 future holdout without daily data or return-driven selection.

**Architecture:** Add a focused `monthly_market.py` module beside the existing portfolio code. It reads explicit local JPX PDFs, extracts only requested JPX security codes, normalizes month-end prices and event detectors, parses official dividend-included TOPIX one-month ROI, and assembles fail-closed held-security return records only when explicit evidence resolves dividends/actions. Raw rows remain local-only.

**Tech Stack:** Python 3.11, stdlib `decimal/hashlib/json/pathlib/re`, `pypdf==6.18.0`, pytest.

**Spec:** `docs/superpowers/specs/2026-09-09-peace-capital-policy-transmission-replay-design.md`; source/return authority is `configs/m3-3c0-free-monthly-prereg-v0.1.json` and Issue #56.

## Global Constraints

- Zero purchase / zero subscription; local files only.
- No daily market store, high-frequency JPX scraping, benchmark reselection, replay-window selection, or performance tuning.
- Exact JPX security-code identity only; name-only relinking is prohibited.
- Raw JPX/issuer rows remain local-only; public output is aggregate/provenance only.
- Missing price, benchmark ROI, dividend evidence, identity, or required corporate-action evidence fails closed.
- Current constituents/evidence must never be projected backward; #85 owns point-in-time replay orchestration.
- July 2026 is engineering validation only because its schema was already inspected; it cannot become the first headline replay window.
- PDF parser dependency is pinned to `pypdf==6.18.0`, previously validated research-only against the real JPX July PDFs.

---
### Task 1: Pin reusable monthly contract and local PDF/provenance boundary

**Files:**
- Modify: `pyproject.toml`
- Create: `configs/m3-3c-monthly-market-v0.1.json`
- Create: `src/wa_commons/portfolio/monthly_market.py`
- Create: `tests/test_monthly_market.py`

**Interfaces:**
- `load_monthly_market_config(path) -> dict`
- `extract_pdf_text(path) -> str`
- `source_provenance(path, locator, retrieved_at) -> dict`

- [ ] **Step 1: Write RED tests** asserting `pypdf==6.18.0`, zero-cost/local-only flags, exact-code identity, no name relink, no network/download argument, source SHA/retrieval timestamp/locator provenance, and missing local source -> `BLOCK_SOURCE_UNAVAILABLE`.
- [ ] **Step 2: Run `python -m pytest tests/test_monthly_market.py -q` and verify RED because config/module do not exist.**
- [ ] **Step 3: Add the pinned dependency/config and minimal helpers.** `extract_pdf_text` accepts only an existing local `Path`; it never downloads. `source_provenance` hashes raw bytes with SHA-256.
- [ ] **Step 4: Re-run focused tests and verify GREEN.**
- [ ] **Step 5: Commit `feat: pin reusable monthly market contract`.**

### Task 2: Parse month-end prices with corporate-action duplicate handling

**Files:**
- Modify: `src/wa_commons/portfolio/monthly_market.py`
- Modify: `tests/test_monthly_market.py`

**Interfaces:**
- `parse_stock_price_table_text(text, period, valuation_date, security_ids, price_role) -> dict`
- Output row: `{security_id, security_code, close_price, close_date, source_row_count, selection_reason}`.
- [ ] **Step 1: Add RED fixtures** reproducing real July text shapes: normal `1301` row and duplicate `2163` ex-rights rows. Assert July 31 selects `1301=4540.00` and the unique `2163` row whose Close Date is 31 (`951.00`), not the pre-rights row ending July 29.
- [ ] **Step 2: Add RED cases** for requested code absent -> `BLOCK_END_PRICE`/`BLOCK_START_PRICE`, duplicate rows with no unique valuation-date match -> `BLOCK_CORPORATE_ACTION`, and exact code only (`2163` must not match names/other codes).
- [ ] **Step 3: Implement parser.** Match lines beginning `YYYY/MM <code>`, parse the fixed numeric tail from the right, retain every candidate, then choose exactly one candidate with `close_date == valuation_date.day`. Do not silently choose the last row when ambiguous.
- [ ] **Step 4: Sort requested/output codes deterministically and compute a semantic row hash independent of input ordering.**
- [ ] **Step 5: Run focused tests GREEN and commit `feat: parse JPX monthly month-end prices`.**

### Task 3: Parse official TOPIX monthly ROI and JPX event detectors

**Files:**
- Modify: `src/wa_commons/portfolio/monthly_market.py`
- Modify: `tests/test_monthly_market.py`

**Interfaces:**
- `parse_topix_monthly_roi_text(text, period) -> dict`
- `parse_ex_rights_text(text, period, security_ids) -> dict`
- `parse_listed_company_changes_text(text, period, security_ids) -> dict`

- [ ] **Step 1: RED benchmark fixture** from July `03_sisu2607.pdf`: section `ROI of Dividend-Included Stock Price Indices (As of the End of Jul. 2026)` and `TOPIX ... 0.22 ...`; assert one-month percent `0.22` and decimal return `0.002200000000`.
- [ ] **Step 2: RED benchmark blockers:** missing section/TOPIX row, wrong requested period, or multiple conflicting TOPIX one-month rows -> `BLOCK_BENCHMARK_MONTHLY_RETURN`.
- [ ] **Step 3: RED ex-rights fixture:** July `17_kenri2607.pdf` row for `2163` must normalize ex-rights date `2026-07-30`, record date `2026-07-31`, split ratio `1:2`; requested codes not present return no event rather than inventing one.
- [ ] **Step 4: RED listed-change fixture:** July `16_idou2607.pdf` must detect `3681` under `Delisting`; unrelated margin/name-change rows do not become delisting actions.
- [ ] **Step 5: Implement deterministic parsers and commit `feat: parse JPX monthly benchmark and action detectors`.**
### Task 4: Assemble fail-closed held-security total-wealth return records

**Files:**
- Modify: `src/wa_commons/portfolio/monthly_market.py`
- Modify: `tests/test_monthly_market.py`

**Interfaces:**
- `build_monthly_return_payload(period, held_security_ids, start_prices, end_prices, benchmark_roi, events, evidence_resolutions, provenance, config) -> dict`
- Evidence resolution per security: `{identity_state, dividend_status, dividend_cash_per_start_unit, evidence_refs, action_resolution?}`.
- Generic action resolution: `{status, end_units_per_start_unit, cash_consideration_per_start_unit, terminal_security_id, evidence_refs}`.

- [ ] **Step 1: RED no-action arithmetic:** start `100`, end `110`, confirmed no dividend/action -> `RETURN_OK_NO_ACTION`, total-wealth return `0.100000000000`.
- [ ] **Step 2: RED cash-dividend arithmetic:** start `100`, end `105`, confirmed dividend `2` -> wealth `107`, return `0.070000000000`; no synthetic reinvestment.
- [ ] **Step 3: RED split arithmetic:** detector `1:2` plus explicit resolution `end_units_per_start_unit=2`; start `200`, post-split end `105` -> wealth `210`, return `0.050000000000`, state `RETURN_OK_ACTION_EXPLAINED`.
- [ ] **Step 4: RED blockers:** missing start/end price, unresolved identity, missing dividend evidence, detector/action-resolution mismatch, unsupported/ambiguous action, and missing benchmark ROI map exactly to #78 terminal states.
- [ ] **Step 5: Implement Decimal arithmetic and source/evidence attribution.** Do not infer any dividend/action term from price movement. Sort security rows and hash semantic payload independent of input ordering.
- [ ] **Step 6: Run focused GREEN and commit `feat: assemble fail-closed monthly total-wealth returns`.**

### Task 5: Add local-input CLI and publication boundary

**Files:**
- Create: `scripts/run_monthly_market.py`
- Modify: `tests/test_monthly_market.py`

**Interfaces:**
- CLI args: `--period`, `--start-price-pdf`, `--end-price-pdf`, `--benchmark-pdf`, `--ex-rights-pdf`, `--listed-changes-pdf`, `--held-securities`, `--evidence-resolutions`, `--source-manifest`, `--config`, `--local-output`, `--public-output`, `--code-commit`.
- [ ] **Step 1: RED CLI/publication tests:** identical local/public path rejected; help exposes no URL/download/network option; public artifact contains no security IDs, row prices, dividend/action evidence text, candidate/benchmark return values when `performance_publication_rights != CLEARED`.
- [ ] **Step 2: Implement CLI using only explicit local files.** `source-manifest` carries locators/retrieval timestamps; CLI hashes each raw file and verifies declared period before parsing.
- [ ] **Step 3: Implement writer.** Local output contains full rows/evidence refs; public output contains artifact/config/code/source hashes, parser versions, aggregate status counts, semantic payload hash, paper-only/rights flags, and no raw/performance rows.
- [ ] **Step 4: Focused GREEN and commit `feat: add monthly market CLI and publication boundary`.**

### Task 6: Validate against official July 2026 JPX files and close #56

**Files:**
- Create: `docs/results/M3_3C_MONTHLY_MARKET_PRIMITIVES_V01.md`
- Create: `docs/results/M3_3C_MONTHLY_MARKET_PRIMITIVES_MANIFEST_V01.json`
- Modify: `ROADMAP.md` only to mark #56 COMPLETE and #85 CURRENT after acceptance.

**Local-only official inputs:**
- June Stock Quotations: official JPX `st_202606.pdf` (`.../t13vrt000001j2us-att/st_202606.pdf`).
- July Stock Quotations: existing `local-research/st_202607.pdf`.
- July index report: existing `03_sisu2607.pdf`.
- July listed-company changes: existing `16_idou2607.pdf`.
- July ex-rights: existing `17_kenri2607.pdf`.

- [ ] **Step 1: Download/save the June JPX PDF once, locally, record locator/retrieval timestamp/SHA; do not commit raw PDFs.**
- [ ] **Step 2: Run parser-only real-source validation for July 2026.** Verify normal month-end price extraction, `2163` duplicate-row selection, TOPIX one-month ROI `0.22%`, `2163` split detector `1:2`, and July delisting detector examples.
- [ ] **Step 3: Run the same real inputs twice and with reversed requested security order; semantic hashes must match.**
- [ ] **Step 4: Record only repo-safe parser/provenance facts.** July remains `ENGINEERING_VALIDATION_ONLY`; do not publish a candidate return or promote it to #85 headline replay.
- [ ] **Step 5: Run `python -m pytest tests/test_monthly_market.py -q`, full `python -m pytest -q`, and `git diff --check`.**
- [ ] **Step 6: Commit `docs: record reusable monthly JPX primitive validation`, open PR, require CI GREEN, merge, and close #56.**

## Self-review checklist

- Every #56 DoD item maps to a task: month parameters, explicit local inputs, price/ROI/action parsers, duplicate handling, fail-closed states, deterministic hashes, no daily store, publication boundary, and engineering-validation month.
- #85 replay-window selection and historical evidence cutoff orchestration are not implemented here.
- July performance is never used for policy/replay selection and is not published as a headline return.
- No placeholder marker remains; function names and payload fields are consistent across tasks.
