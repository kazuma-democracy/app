# Historical Replay v0.2 — Investable TOPIX Proxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a leak-safe three-month 2026-Q1 Historical Replay using dated iShares Core TOPIX ETF (1475) equity holdings as the investable P0 allocation while retaining TOPIX Total Return as the external benchmark.

**Architecture:** Extend the existing #85 metadata-only qualification/freeze and #56 monthly-market primitives rather than replacing them. Build point-in-time 1475 control snapshots, rebuild security↔corporate identity and Evidence as-known at each cutoff, compile the unchanged #84 P0/P1/P2 family, freeze 2026-01 through 2026-03 before loading any headline return value, then calculate financial consequences with a residual-sleeve method that only needs individual total-wealth returns for directly changed securities.

**Tech Stack:** Python 3.11, stdlib `csv/json/hashlib/datetime/decimal`, `openpyxl`, `pypdf`, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-09-investable-topix-proxy-historical-replay-design.md`

## Global Constraints

- Preserve the frozen #84 P0/P1/P2 semantics and P2 `WATCH -> 0.5` multiplier exactly.
- TOPIX Total Return remains the external financial benchmark; 1475 is an investable control allocation, not reconstructed TOPIX.
- Headline candidate evaluations are 2026-01, 2026-02, 2026-03 with cutoffs `2025-12-30T15:30:00+09:00`, `2026-01-30T15:30:00+09:00`, `2026-02-27T15:30:00+09:00`.
- 2026-04 through 2026-08 are engineering-only for the first headline replay; 2026-10 remains the separate future holdout.
- Candidate qualification may inspect metadata/existence/hashes only; no candidate ETF, constituent, or TOPIX return value may be loaded before `HISTORICAL_REPLAY_WINDOW_FROZEN` is written and hashed.
- The BlackRock all-history performance chart is ineligible as a headline return source.
- Current #53 identity and current #55 screening may not be projected backward.
- Raw BlackRock, JPX, EDINET, MOD and political-finance source rows remain local-only unless an existing rights contract explicitly permits publication.
- Rights uncertainty fails closed as `BLOCK_SOURCE_RIGHTS`; missing historical identity/evidence/data never becomes a clean/pass state.
- Paper research only; no broker or real-money authority.
- USE > EXTEND > ADAPT > REPLACE > BUILD.

---

## File Structure

**Create**
- `configs/m3-3c0-historical-replay-v0.2.json` — preregistered proxy replay contract and engineering/holdout periods.
- `src/wa_commons/portfolio/investable_proxy.py` — 1475 holdings parser, equity normalization, proxy-universe/control mapping helpers, residual-sleeve arithmetic.
- `src/wa_commons/identity/historical_edinet.py` — cutoff-safe EDINET documents-list normalization into the existing identity-spine input format.
- `src/wa_commons/evidence/historical_cutoff.py` — source-availability filtering and historical MOD/coverage/screening assembly.
- `tests/test_investable_proxy.py` — holdings and residual-sleeve contracts.
- `tests/test_historical_edinet.py` — point-in-time strong-ID contracts.
- `tests/test_historical_cutoff.py` — Evidence availability and no-backprojection contracts.
- `tests/test_historical_replay_v02.py` — v0.2 qualification/freeze/execution contracts.
- `scripts/run_historical_replay_v02_market.py` — post-target-freeze market bundle runner for 1475 plus directly changed securities only.
- `tests/test_historical_replay_v02_market_cli.py` — fail-before-read and market-bundle CLI contracts.

**Modify**
- `docs/SOURCE_REGISTRY.md` — add the 1475 holdings source and fail-closed local-use/publication boundary.
- `src/wa_commons/evidence/mod_procurement.py` — parameterize source metadata/fiscal year while preserving current defaults.
- `src/wa_commons/portfolio/benchmark_snapshot.py` — reuse exact-code mapping through a proxy wrapper without claiming proxy weights are TOPIX weights.
- `src/wa_commons/portfolio/historical_replay.py` — add v0.2 control-snapshot qualification and residual-sleeve replay path while preserving v0.1.
- `src/wa_commons/portfolio/monthly_market.py` — accept four-character alphanumeric TSE codes in the held-security path.
- `scripts/run_historical_replay_qualification.py` — support the v0.2 candidate schema without adding any return-valued argument.
- `scripts/run_historical_replay.py` — support v0.2 frozen execution inputs and public-rights filtering.
- `tests/test_historical_replay.py`, `tests/test_historical_replay_cli.py`, `tests/test_monthly_market.py` — compatibility and no-leak regressions.
- `ROADMAP.md` and #85 result docs — update only after the real metadata-only qualification/execution outcome is known.

---

### Task 1: Freeze the v0.2 source/config contract

**Files:**
- Create: `configs/m3-3c0-historical-replay-v0.2.json`
- Modify: `docs/SOURCE_REGISTRY.md`
- Create: `tests/test_historical_replay_v02.py`

**Interfaces:**
- Consumes: approved v0.2 spec and existing `configs/m3-3c0-historical-replay-v0.1.json` policy contract.
- Produces: `load_historical_replay_config()`-compatible config with `allocation_source.kind = "ISHARES_1475_POINT_IN_TIME"`, exact headline candidates, engineering exclusions, required metadata roles, and rights gate.

- [ ] **Step 1: Write the failing config-contract tests**

```python
from pathlib import Path
from wa_commons.portfolio.historical_replay import load_historical_replay_config


def test_v02_preregisters_clean_q1_before_returns() -> None:
    config = load_historical_replay_config(
        Path("configs/m3-3c0-historical-replay-v0.2.json")
    )
    assert config["artifact_version"] == "m3.3c0-historical-replay-v0.2"
    assert config["allocation_source"]["kind"] == "ISHARES_1475_POINT_IN_TIME"
    assert config["headline_candidate_periods"] == ["2026-01", "2026-02", "2026-03"]
    assert config["engineering_validation_periods"] == [
        "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"
    ]
    assert config["future_holdout_periods"] == ["2026-10"]
    assert config["market_values_allowed_during_selection"] is False
    assert config["performance_values_allowed_during_selection"] is False
    assert config["paper_only"] is True
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m pytest tests/test_historical_replay_v02.py::test_v02_preregisters_clean_q1_before_returns -q`

Expected: FAIL because `configs/m3-3c0-historical-replay-v0.2.json` does not exist.

- [ ] **Step 3: Add the v0.2 config and Source Registry entry**

The config must copy the existing #84 policy hashes/arms verbatim and add:

```json
{
  "artifact_version": "m3.3c0-historical-replay-v0.2",
  "issue": 85,
  "window_length_months": 3,
  "headline_candidate_periods": ["2026-01", "2026-02", "2026-03"],
  "engineering_validation_periods": ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"],
  "future_holdout_periods": ["2026-10"],
  "allocation_source": {
    "kind": "ISHARES_1475_POINT_IN_TIME",
    "security_id": "TSE:1475",
    "raw_publication": false,
    "rights_required_state": "LOCAL_RESEARCH_ALLOWED"
  },
  "selection_rule": "EXACT_PREREGISTERED_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS",
  "market_values_allowed_during_selection": false,
  "performance_values_allowed_during_selection": false,
  "paper_only": true,
  "real_money_authority": false
}
```

In `docs/SOURCE_REGISTRY.md`, add `blackrock-ishares-1475-holdings` with publisher BlackRock Japan, scope “dated ETF holdings used only as investable control allocation”, low-frequency/manual retrieval, exact ticker as identifier, rights=`review_required` until local research retention is affirmatively checked, decision=`WATCH`, and the explicit rule that unresolved rights must emit `BLOCK_SOURCE_RIGHTS` rather than permit raw redistribution.

- [ ] **Step 4: Run focused contract tests**

Run: `python -m pytest tests/test_historical_replay_v02.py -q`

Expected: PASS for the config-only tests; no market/source values are read.

- [ ] **Step 5: Commit**

```bash
git add configs/m3-3c0-historical-replay-v0.2.json docs/SOURCE_REGISTRY.md tests/test_historical_replay_v02.py
git commit -m "docs: preregister investable proxy replay v0.2"
```
### Task 2: Parse and normalize dated 1475 equity holdings

**Files:**
- Create: `src/wa_commons/portfolio/investable_proxy.py`
- Modify: `src/wa_commons/portfolio/benchmark_snapshot.py`
- Create: `tests/test_investable_proxy.py`

**Interfaces:**
- Consumes: raw local 1475 holdings CSV text plus as-of/source metadata.
- Produces: `parse_ishares_1475_holdings_csv(csv_text: str, *, as_of_date: str, source_sha256: str, retrieved_at: str, source_locator: str) -> dict[str, Any]` with deterministic `control_weight` rows, and `map_investable_control_snapshot(snapshot, identity) -> dict[str, Any]` exposing the legacy `benchmark_weight` alias only at the existing policy-compiler boundary.

- [ ] **Step 1: Write failing parser tests**

```python
def test_1475_parser_keeps_equities_only_and_normalizes_market_value() -> None:
    payload = parse_ishares_1475_holdings_csv(
        HOLDINGS_FIXTURE,
        as_of_date="2026-01-30",
        source_sha256="a" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://1475/20260130",
    )
    assert payload["status"] == "INVESTABLE_CONTROL_SNAPSHOT_OK"
    assert [r["security_id"] for r in payload["rows"]] == ["TSE:130A", "TSE:7203"]
    assert sum(Decimal(r["control_weight"]) for r in payload["rows"]) == Decimal("1.000000000000")
    assert all(r["asset_class"] == "Equity" for r in payload["rows"])
```
Add regressions for duplicate code, malformed/blank market value, mismatched `Fund Holdings as of` date, input-order determinism, and exclusion of `Cash`, `Cash Collateral and Margins`, and `Futures` rows.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_investable_proxy.py -q`

Expected: FAIL because `wa_commons.portfolio.investable_proxy` does not exist.

- [ ] **Step 3: Implement the minimal holdings parser**

Use `csv.DictReader` after locating the exact `Ticker,Name,Asset Class,Market Value,Weight (%)` header. Normalize four-character TSE codes with the existing security-code conventions, including alphanumeric codes such as `130A`. Convert `Market Value` with `Decimal`, require positive values for Equity rows, sort by `security_id`, and normalize with the same 12-decimal deterministic remainder handling used by benchmark snapshots.

Canonical row shape:

```python
{
    "security_id": "TSE:7203",
    "security_code": "7203",
    "name": "TOYOTA MOTOR CORP",
    "asset_class": "Equity",
    "equity_market_value": "77097632600.00",
    "control_weight": "0.026900000000",
}
```

Manifest must include `control_kind="ISHARES_1475_POINT_IN_TIME"`, `as_of_date`, source locator/hash/retrieval time, equity count/value sum, `control_weight_sum`, and semantic snapshot SHA-256. Do not persist raw CSV rows in repository-safe output.
- [ ] **Step 4: Add a thin mapping wrapper for policy-compiler compatibility**

Do not duplicate `map_topix_snapshot`. Add `map_investable_control_snapshot()` that converts `control_weight` to the existing internal `benchmark_weight` field, calls the exact-code mapper, and restores proxy semantics in the manifest:

```python
def map_investable_control_snapshot(snapshot, identity):
    compatible = {
        "manifest": dict(snapshot["manifest"]),
        "rows": [
            {**row, "benchmark_weight": row["control_weight"]}
            for row in snapshot["rows"]
        ],
    }
    mapped = map_topix_snapshot(compatible, identity)
    mapped["manifest"]["allocation_role"] = "INVESTABLE_CONTROL"
    mapped["manifest"]["control_kind"] = "ISHARES_1475_POINT_IN_TIME"
    return mapped
```

The public/result wording must never call these weights official TOPIX weights.

- [ ] **Step 5: Run focused tests and legacy benchmark regressions**

Run: `python -m pytest tests/test_investable_proxy.py tests/test_topix_benchmark_mapping.py tests/test_topix_public_weight_snapshot.py -q`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/portfolio/investable_proxy.py src/wa_commons/portfolio/benchmark_snapshot.py tests/test_investable_proxy.py
git commit -m "feat: add dated investable control snapshots"
```
### Task 3: Rebuild point-in-time security↔corporate identity from EDINET

**Files:**
- Create: `src/wa_commons/identity/historical_edinet.py`
- Create: `tests/test_historical_edinet.py`

**Interfaces:**
- Consumes: dated 1475 snapshot rows, EDINET documents-list records, decision cutoff, `SourceRef`, code commit.
- Produces: `build_historical_proxy_identity(control_snapshot: Mapping[str, Any], edinet_records: Sequence[Mapping[str, Any]], *, decision_cutoff: str, edinet_source: SourceRef, code_commit: str) -> dict[str, Any]` in the existing `build_tse_identity_spine()` shape, with every control security represented and only cutoff-eligible `secCode`/`JCN` links attached.

- [ ] **Step 1: Write failing cutoff/strong-ID tests**

```python
def test_edinet_rows_after_cutoff_are_excluded() -> None:
    rows = normalize_edinet_document_rows(
        [
            {"submitDateTime": "2026-01-20 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
            {"submitDateTime": "2026-02-02 09:00", "secCode": "67580", "JCN": "2222222222222", "edinetCode": "E00002"},
        ],
        decision_cutoff="2026-01-30T15:30:00+09:00",
    )
    assert rows == [
        {"security_code": "72030", "corporate_number": "1111111111111", "edinet_code": "E00001"}
    ]
```
Also test that two cutoff-eligible records for the same normalized four-character security code with different nonblank JCNs raise `ValueError("conflicting historical corporate number")`, while a control security with no eligible JCN remains present in identity output without a `JP_CORPORATE_NUMBER` identifier.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_historical_edinet.py -q`

Expected: FAIL because the module/functions do not exist.

- [ ] **Step 3: Implement EDINET record normalization**

```python
def normalize_edinet_document_rows(
    records: Sequence[Mapping[str, Any]],
    *,
    decision_cutoff: str,
) -> list[dict[str, str]]:
    cutoff = datetime.fromisoformat(decision_cutoff)
    if cutoff.tzinfo is None:
        raise ValueError("decision_cutoff must be timezone-aware")
    candidates: dict[str, list[dict[str, str]]] = {}
    for record in records:
        submitted = datetime.fromisoformat(str(record["submitDateTime"]).replace(" ", "T"))
        if submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        if submitted > cutoff:
            continue
        raw_code = str(record.get("secCode", "")).strip()
        normalized_code = normalize_edinet_security_code(raw_code)
        if not normalized_code:
            continue
        candidates.setdefault(normalized_code, []).append({
            "security_code": raw_code,
            "edinet_code": str(record.get("edinetCode", "")).strip(),
            "corporate_number": str(record.get("JCN", "")).strip(),
        })

    output: list[dict[str, str]] = []
    for normalized_code in sorted(candidates):
        rows = candidates[normalized_code]
        corporate_numbers = sorted({row["corporate_number"] for row in rows if row["corporate_number"]})
        edinet_codes = sorted({row["edinet_code"] for row in rows if row["edinet_code"]})
        if len(corporate_numbers) > 1:
            raise ValueError("conflicting historical corporate number")
        if len(edinet_codes) > 1:
            raise ValueError("conflicting historical EDINET code")
        output.append({
            "security_code": sorted(row["security_code"] for row in rows)[0],
            "edinet_code": edinet_codes[0] if edinet_codes else "",
            "corporate_number": corporate_numbers[0] if corporate_numbers else "",
        })
    return output
```

Use `normalize_edinet_security_code()` for conflict grouping, but pass the source-format security code accepted by `build_edinet_security_index()` so the existing enrichment path remains authoritative. Do not use issuer name matching.

- [ ] **Step 4: Build a proxy universe and reuse `build_tse_identity_spine()`**

Create one `wa:org:jp:tse:<code>` entity per 1475 equity row using `entity_id_from_tse_code()` and a `JPX_SECURITY_CODE` identifier sourced to the dated holdings snapshot. Call `build_tse_identity_spine()` with cutoff-filtered EDINET rows and no later NTA/GLEIF snapshot inputs. This preserves `wa-conservative-v0.2` and keeps missing corporate numbers unresolved rather than guessed.
- [ ] **Step 5: Verify determinism and no current-snapshot leakage**

Run: `python -m pytest tests/test_historical_edinet.py tests/test_identity_enrichment.py tests/test_tse_identity_spine.py -q`

Expected: PASS; reversing EDINET record order yields the same historical identity semantic SHA-256.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/identity/historical_edinet.py tests/test_historical_edinet.py
git commit -m "feat: add cutoff-safe historical identity bridge"
```

### Task 4: Generalize MOD monthly parsing and rebuild cutoff Evidence

**Files:**
- Modify: `src/wa_commons/evidence/mod_procurement.py`
- Create: `src/wa_commons/evidence/historical_cutoff.py`
- Create: `tests/test_historical_cutoff.py`
- Modify: `tests/test_mod_procurement_adapter.py`

**Interfaces:**
- Consumes: operator-pinned MOD workbook source manifests, local workbook paths, decision cutoff, historical identity, existing coverage source catalog and policies.
- Produces: `build_historical_screening(*, identity: Mapping[str, Any], mod_sources: Sequence[Mapping[str, Any]], decision_cutoff: str, coverage_source_catalog: Sequence[Mapping[str, Any]], policies: Sequence[Mapping[str, Any]], code_commit: str) -> dict[str, Any]` containing cutoff-complete coverage/screening plus `decision_cutoff`, `availability_complete`, source/hash provenance.
- [ ] **Step 1: Write failing availability and adapter-parameterization tests**

```python
def test_mod_source_after_cutoff_is_not_parsed(tmp_path: Path) -> None:
    selected = select_sources_available_at_cutoff(
        [
            {"snapshot_version": "fy2025-01", "available_at": "2026-03-10T12:08:58+09:00"},
            {"snapshot_version": "fy2025-02", "available_at": "2026-04-10T10:28:20+09:00"},
        ],
        decision_cutoff="2026-03-31T15:30:00+09:00",
    )
    assert [s["snapshot_version"] for s in selected] == ["fy2025-01"]
```

Add an adapter regression asserting a FY2025 workbook parsed with `fiscal_year=2025`, custom `source_url`, and custom `snapshot_version` stores those values, while the existing no-argument metadata defaults still produce the current FY2026-04 behavior.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_historical_cutoff.py tests/test_mod_procurement_adapter.py -q`

Expected: new tests FAIL because the cutoff module/parameterized adapter do not exist; existing adapter tests remain PASS.

- [ ] **Step 3: Parameterize `parse_workbook()` without changing defaults**

```python
def parse_workbook(
    path: str | Path,
    *,
    retrieved_at: str,
    source_url: str = SOURCE_URL,
    source_page_url: str = SOURCE_PAGE_URL,
    snapshot_version: str = SNAPSHOT_VERSION,
    fiscal_year: int = 2026,
) -> list[ProcurementObservation]:
    # Retain the current worksheet/header iteration. Replace these exact assignments inside it:
    contract_date = _contract_date(
        values[columns["date"]] if columns["date"] < len(values) else "",
        fiscal_year=fiscal_year,
    )
    observation = ProcurementObservation(
        observation_id=f"wc:obs:mod:{snapshot_version}:{ws.title}:{row_no}",
        subject=subject,
        supplier_name=supplier_name,
        supplier_address=supplier_address,
        corporate_number=corporate_number,
        contract_date=contract_date,
        contract_amount_jpy=_amount(values[columns["contract_amount"]]),
        planned_price_jpy=_amount(values[columns["planned_price"]]) if "planned_price" in columns else None,
        contracting_authority=authority or CONTRACTING_AUTHORITY,
        source_url=source_url,
        source_page_url=source_page_url,
        source_locator=f"sheet={ws.title};row={row_no}",
        retrieved_at=retrieved_at,
        source_sha256=digest,
        snapshot_version=snapshot_version,
        identity_decision=decision,
        entity_id=entity_id,
    )
```

Also replace the hardcoded claim ID with:

```python
"claim_id": f"wc:claim:mod:{observation.snapshot_version}:{stable_key}",
```

Pass `fiscal_year` into `_contract_date()` and explicit source metadata into every `ProcurementObservation`. Build `observation_id` as `wc:obs:mod:{snapshot_version}:{sheet}:{row}` and change `observation_to_claim()` to build `claim_id` from `observation.snapshot_version`, so historical months cannot retain the hardcoded `fy2026-04` identity. Do not infer publication time from contract date.
- [ ] **Step 4: Implement cutoff source selection and historical screening assembly**

`select_sources_available_at_cutoff()` must require timezone-aware ISO `available_at`; invalid/missing availability returns a blocker rather than treating the file as eligible. `build_historical_screening()` must:

1. select only eligible MOD source manifests;
2. parse only their pinned local workbooks with the generalized adapter;
3. reuse `build_tse_coverage()` with the existing five-source coverage semantics;
4. keep political-finance `integration_state=integrated` but `identity_linkage_state=unresolved` from the fixed 2024-11-29 source;
5. keep SIPRI/UFLPA/OECD `not_integrated` exactly as current coverage semantics require;
6. reuse `build_tse_policy_screening()` with the unchanged policy files;
7. attach `decision_cutoff`, `availability_complete=True`, selected-source locators/hashes/availability timestamps, and a canonical `evidence_provenance_sha256`.

No current #55 views may be an input.

- [ ] **Step 5: Test cutoff changes across adjacent dates**

Use fixtures where the same historical identity/policy receives one more MOD source after its publication timestamp. Assert the earlier screening cannot see the later observation and the later screening can, without changing policy semantics.

Run: `python -m pytest tests/test_historical_cutoff.py tests/test_mod_procurement_adapter.py tests/test_tse_evidence_coverage.py tests/test_tse_policy_screening.py -q`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/evidence/mod_procurement.py src/wa_commons/evidence/historical_cutoff.py tests/test_historical_cutoff.py tests/test_mod_procurement_adapter.py
git commit -m "feat: rebuild evidence at historical cutoffs"
```
### Task 5: Compile monthly policy families on the proxy control

**Files:**
- Modify: `src/wa_commons/portfolio/investable_proxy.py`
- Modify: `tests/test_investable_proxy.py`
- Modify: `tests/test_policy_compiler.py`

**Interfaces:**
- Consumes: mapped investable control, cutoff screening, base `configs/m3-3b2-policy-compiler-v0.1.json`.
- Produces: `bind_policy_compiler_inputs(base_config: Mapping[str, Any], mapped_control: Mapping[str, Any], screening: Mapping[str, Any]) -> dict[str, Any]` and normal `compile_policy_family(benchmark_mapping: Mapping[str, Any], screening: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]` output with unchanged arm/profile/policy semantics; `directly_changed_security_ids(policy_payload: Mapping[str, Any], arm_id: str) -> list[str]` selects only rows whose instruction is not `NEUTRAL`.

- [ ] **Step 1: Write failing binding tests**

```python
def test_binding_changes_only_input_hashes() -> None:
    bound = bind_policy_compiler_inputs(BASE_CONFIG, MAPPED_CONTROL, SCREENING)
    assert bound["arms"] == BASE_CONFIG["arms"]
    assert bound["input_contract"]["policy_sha256"] == BASE_CONFIG["input_contract"]["policy_sha256"]
    assert bound["input_contract"]["benchmark_semantic_mapping_sha256"] == MAPPED_CONTROL["manifest"]["semantic_mapping_sha256"]
    assert bound["input_contract"]["screening_sha256"] == SCREENING["tse_screening_sha256"]
```

Add a test that `directly_changed_security_ids()` excludes neutral securities that only move because of normalization redistribution.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_investable_proxy.py tests/test_policy_compiler.py -q`

Expected: new binding/direct-change tests FAIL; existing compiler tests PASS.
- [ ] **Step 3: Implement immutable input binding and direct-change extraction**

`bind_policy_compiler_inputs()` must `deepcopy()` the base config and replace only the two snapshot hash fields. Before returning, compare a semantic projection containing `artifact_version`, profile/policy identifiers, `arms`, quantization and policy rules; if that projection differs from the base, raise `ValueError("policy semantics changed during input binding")`.

`directly_changed_security_ids()` must inspect the selected arm's `target_weights` and return sorted security IDs where `instruction in {"EXCLUDE", "UNDERWEIGHT"}` and `multiplier != 1`. Do not use nonzero `allocation_delta` because neutral rows also move during normalization.

- [ ] **Step 4: Verify the normal compiler remains the only compiler**

Compile two months with different control/screening hashes. Assert both return `FROZEN_POLICY_FAMILY`, the same `profile_id`, `profile_version`, `policy_sha256`, arm IDs and allocation policy IDs, while snapshot/config semantic hashes may differ.

Run: `python -m pytest tests/test_investable_proxy.py tests/test_policy_compiler.py -q`

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/wa_commons/portfolio/investable_proxy.py tests/test_investable_proxy.py tests/test_policy_compiler.py
git commit -m "feat: bind frozen policy semantics to historical inputs"
```

### Task 6: Extend metadata-only qualification and freeze v0.2 Q1

**Files:**
- Modify: `src/wa_commons/portfolio/historical_replay.py`
- Modify: `scripts/run_historical_replay_qualification.py`
- Modify: `tests/test_historical_replay_v02.py`
- Modify: `tests/test_historical_replay.py`
- Modify: `tests/test_historical_replay_cli.py`
**Interfaces:**
- Consumes: v0.2 candidate metadata only; no price/return payload.
- Produces: existing `freeze_replay_window()` result with `HISTORICAL_REPLAY_WINDOW_FROZEN` only when exactly the preregistered Q1 triple qualifies.

V0.2 candidate metadata shape (strictly metadata-only; these are fixture values, not claims about the real source publication time):

```python
{
    "evaluation_period": "2026-01",
    "decision_cutoff": "2025-12-30T15:30:00+09:00",
    "control_source_metadata": {
        "kind": "ISHARES_1475_POINT_IN_TIME",
        "as_of_date": "2025-12-30",
        "available_at": "2025-12-30T14:00:00+09:00",
        "exists": True,
        "locator": "fixture://blackrock/1475/2025-12-30",
        "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "rights_state": "LOCAL_RESEARCH_ALLOWED"
    },
    "identity_source_metadata": {
        "availability_complete": True,
        "semantic_source_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    },
    "evidence_source_metadata": {
        "availability_complete": True,
        "semantic_source_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    },
    "market_source_metadata": {
        "start_price": {"exists": True, "locator": "fixture://jpx/price/start/2026-01"},
        "end_price": {"exists": True, "locator": "fixture://jpx/price/end/2026-01"},
        "benchmark": {"exists": True, "locator": "fixture://jpx/topix-tr/2026-01"},
        "action_detector": {"exists": True, "locator": "fixture://jpx/actions/2026-01"}
    }
}
```

The candidate record must not contain holdings market values/weights, screening decisions, target weights, price values, dividends, NAVs or returns. Those are post-window inputs.

- [ ] **Step 1: Write failing v0.2 qualification tests**

Add tests that:
- `control_snapshot.available_at > decision_cutoff` blocks with `BLOCK_EVIDENCE_CUTOFF`;
- missing/invalid original availability blocks rather than treating `as_of_date` as availability;
- `rights_state != LOCAL_RESEARCH_ALLOWED` blocks with `BLOCK_SOURCE_RIGHTS`;
- identity hash mismatch between control and screening blocks;
- any nested candidate key named `benchmark_return`, `portfolio_return`, `start_price`, `end_price`, `total_wealth_return` or `performance` blocks before selection;
- the exact three periods 2026-01/02/03 freeze only when all three qualify;
- 2026-04..08 and 2026-10 can never enter the headline window.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_historical_replay_v02.py tests/test_historical_replay.py tests/test_historical_replay_cli.py -q`

Expected: v0.2 cases FAIL while existing v0.1 cases remain PASS.

- [ ] **Step 3: Extend qualification version-safely**

In `qualify_candidate_month()`, branch on `config["allocation_source"]["kind"]` only for v0.2. Keep the current `benchmark_snapshot` contract untouched for v0.1. For v0.2 validate `control_source_metadata`, authoritative `available_at`, `as_of_date <= cutoff.date()`, rights state, source hashes, identity/evidence availability metadata and generic market-source existence. Do not require or compute a holdings-weight mapping hash or screening decision hash during qualification.

Do not accept `as_of_date` as a substitute for `available_at`.
- [ ] **Step 4: Make v0.2 freeze exact, not opportunistic**

For `selection_rule == "EXACT_PREREGISTERED_THREE_CONSECUTIVE_METADATA_QUALIFIED_MONTHS"`, require the qualified periods to contain exactly `headline_candidate_periods` in chronological order. Do not search for a substitute older/newer triple when one Q1 month blocks. Return `BLOCK_HISTORICAL_REPLAY_COVERAGE` with all candidate results preserved.

The frozen semantic record must contain only:
- evaluation period and decision cutoff;
- control source as-of/availability/locator/source hash and rights state;
- identity-source and Evidence-source availability semantic hashes;
- fixed policy contract identifiers/hashes;
- no prices, distributions, returns, NAVs or performance metrics.

- [ ] **Step 5: Keep the CLI metadata-only**

`run_historical_replay_qualification.py` may gain v0.2 candidate-schema validation, but its CLI arguments must remain only config, candidate metadata, output and code commit. Add no price, return, distribution or performance arguments.

- [ ] **Step 6: Run focused tests**

Run: `python -m pytest tests/test_historical_replay_v02.py tests/test_historical_replay.py tests/test_historical_replay_cli.py -q`

Expected: all PASS, including v0.1 regressions and input-order/hash determinism.

- [ ] **Step 7: Commit**

```bash
git add src/wa_commons/portfolio/historical_replay.py scripts/run_historical_replay_qualification.py tests/test_historical_replay_v02.py tests/test_historical_replay.py tests/test_historical_replay_cli.py
git commit -m "feat: qualify investable proxy replay without returns"
```
### Task 7: Separate security returns from benchmark loading and add residual-sleeve math

**Files:**
- Modify: `src/wa_commons/portfolio/monthly_market.py`
- Modify: `src/wa_commons/portfolio/investable_proxy.py`
- Create: `scripts/run_historical_replay_v02_market.py`
- Create: `tests/test_historical_replay_v02_market_cli.py`
- Modify: `tests/test_monthly_market.py`
- Modify: `tests/test_investable_proxy.py`

**Interfaces:**
- Consumes: frozen P0/P1/P2 monthly payload, JPX start/end price snapshots, explicit dividend/action resolutions for `TSE:1475` and directly changed securities.
- Produces: `_build_security_return_rows(period: str, held_security_ids: list[str], start_prices: dict[str, Any], end_prices: dict[str, Any], events: list[dict[str, Any]], evidence_resolutions: dict[str, dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]` extracted from the existing held-security loop; `build_security_total_wealth_payload(period: str, held_security_ids: list[str], start_prices: dict[str, Any], end_prices: dict[str, Any], events: list[dict[str, Any]], evidence_resolutions: dict[str, dict[str, Any]], provenance: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]` without benchmark dependency; `compute_residual_sleeve_financial(*, p0_total_return: Decimal, control_rows: Sequence[Mapping[str, Any]], policy_rows: Sequence[Mapping[str, Any]], changed_returns: Mapping[str, Decimal]) -> dict[str, Any]`; and a post-freeze `run_market_bundle(*, frozen_targets_path: str | Path, period: str, start_price_pdf: str | Path, end_price_pdf: str | Path, benchmark_pdf: str | Path, ex_rights_pdf: str | Path, listed_changes_pdf: str | Path, evidence_resolutions_path: str | Path, source_manifest_path: str | Path, config_path: str | Path, output_path: str | Path) -> dict[str, Any]` CLI path that derives held securities from frozen targets instead of accepting an arbitrary held-security list.

- [ ] **Step 1: Write failing benchmark-separation tests**

```python
def test_security_returns_do_not_require_benchmark_value() -> None:
    result = build_security_total_wealth_payload(
        period="2026-01",
        held_security_ids=["TSE:1475"],
        start_prices=START,
        end_prices=END,
        events=[],
        evidence_resolutions=RESOLUTIONS,
        provenance=PROVENANCE,
        config=MARKET_CONFIG,
    )
    assert result["status"] == "SECURITY_RETURNS_OK"
    assert result["rows"][0]["state"] == "RETURN_OK_NO_ACTION"
```

Add a regression that `TSE:130A` passes identity/price parsing and action detection. Introduce one shared four-character security-code pattern `[0-9A-Z]{4}` and use it consistently in `_PRICE_LINE_RE`, `_canonical_security_ids()`, the ex-rights fixture/real code groups, the listed-company-change row pattern, and `TSE:<code>` identity validation. Numeric codes such as `1475` must remain unchanged.
- [ ] **Step 2: Run tests and verify RED**

Run: `python -m pytest tests/test_monthly_market.py tests/test_investable_proxy.py -q`

Expected: new tests FAIL because the benchmark-free security-return helper and residual function do not exist.

- [ ] **Step 3: Factor the existing return-row logic without changing semantics**

Move the held-security loop from `build_monthly_return_payload()` into:

```python
def build_security_total_wealth_payload(
    period: str,
    held_security_ids: list[str],
    start_prices: dict[str, Any],
    end_prices: dict[str, Any],
    events: list[dict[str, Any]],
    evidence_resolutions: dict[str, dict[str, Any]],
    provenance: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    rows = _build_security_return_rows(
        period=period,
        held_security_ids=held_security_ids,
        start_prices=start_prices,
        end_prices=end_prices,
        events=events,
        evidence_resolutions=evidence_resolutions,
        config=config,
    )
    status = "SECURITY_RETURNS_OK" if all(
        str(row.get("state", "")).startswith("RETURN_OK_") for row in rows
    ) else "BLOCK_MARKET_DATA"
    return {"status": status, "period": period, "rows": rows, "provenance": provenance}
```

It must retain all existing `BLOCK_IDENTITY`, `BLOCK_START_PRICE`, `BLOCK_END_PRICE`, `BLOCK_DIVIDEND_EVIDENCE`, `BLOCK_CORPORATE_ACTION`, `RETURN_OK_NO_ACTION` and `RETURN_OK_ACTION_EXPLAINED` behavior. Then make `build_monthly_return_payload()` call this helper and append validated TOPIX benchmark return exactly as before, preserving all #56 tests.
- [ ] **Step 4: Write failing residual-sleeve tests**

```python
def test_residual_sleeve_reproduces_p0_when_weights_are_unchanged() -> None:
    result = compute_residual_sleeve_financial(
        p0_total_return=Decimal("0.010000000000"),
        control_rows=[{"security_id": "TSE:1001", "benchmark_weight": "0.200000000000"}],
        policy_rows=[{"security_id": "TSE:1001", "benchmark_weight": "0.200000000000", "target_weight": "0.200000000000", "instruction": "UNDERWEIGHT", "multiplier": "0.500000000000"}],
        changed_returns={"TSE:1001": Decimal("0.020000000000")},
    )
    assert result["policy_return"] == "0.010000000000"
```

Use a second fixture with `target_weight != benchmark_weight` and verify the formula numerically. Add tests for missing changed-security return, duplicate changed security, `B_C >= 1`, negative/invalid weights, and empty changed set returning P0 exactly.

- [ ] **Step 5: Implement the Decimal residual formula**

Compute `C` from direct non-neutral instructions, then `B_C`, `W_C`, `R_residual`, and `R_policy` exactly as the spec defines. Quantize only repository-semantic output at 12 decimals; use full `Decimal` precision internally. Never substitute residual return for a missing directly changed security.

- [ ] **Step 6: Write the post-freeze market-runner RED test**

```python
def test_v02_market_runner_rejects_unfrozen_targets_before_source_access(tmp_path: Path) -> None:
    targets = tmp_path / "targets.json"
    targets.write_text('{"status":"BLOCK_REPRODUCIBILITY"}', encoding="utf-8")
    with pytest.raises(ValueError, match="frozen targets"):
        run_market_bundle(
            frozen_targets_path=targets,
            period="2026-01",
            start_price_pdf=tmp_path / "missing-start.pdf",
            end_price_pdf=tmp_path / "missing-end.pdf",
            benchmark_pdf=tmp_path / "missing-topix.pdf",
            ex_rights_pdf=tmp_path / "missing-rights.pdf",
            listed_changes_pdf=tmp_path / "missing-changes.pdf",
            evidence_resolutions_path=tmp_path / "missing-resolutions.json",
            source_manifest_path=tmp_path / "missing-source-manifest.json",
            config_path=Path("configs/m3-3c-monthly-market-v0.1.json"),
            output_path=tmp_path / "market.json",
        )
```

Run: `python -m pytest tests/test_historical_replay_v02_market_cli.py -q`

Expected: FAIL because the v0.2 market runner does not exist.

- [ ] **Step 7: Implement the post-freeze market runner**

`run_market_bundle()` must load and validate `HISTORICAL_REPLAY_TARGETS_FROZEN` before opening any market file. For the requested period, derive `held_security_ids` as sorted unique `TSE:1475` plus the frozen P1/P2 direct-changed IDs. Then reuse `source_provenance()`, `extract_pdf_text()`, `parse_stock_price_table_text()`, `parse_ex_rights_text()`, `parse_listed_company_changes_text()`, `build_security_total_wealth_payload()` and `parse_topix_monthly_roi_text()`.

Write exactly this local bundle shape:

```python
{
    "status": "PROXY_MARKET_BUNDLE_OK",
    "period": period,
    "security_returns": security_returns,
    "topix_roi": topix_roi,
    "source_hashes": sorted(source_hashes),
}
```

No held-security CLI argument is allowed. Any blocked security return or TOPIX ROI returns a fail-closed status instead of dropping that security.

- [ ] **Step 8: Run focused and legacy tests**

Run: `python -m pytest tests/test_monthly_market.py tests/test_investable_proxy.py tests/test_historical_replay_v02_market_cli.py tests/test_historical_replay.py -q`

Expected: all PASS.

- [ ] **Step 9: Commit**

```bash
git add src/wa_commons/portfolio/monthly_market.py src/wa_commons/portfolio/investable_proxy.py scripts/run_historical_replay_v02_market.py tests/test_monthly_market.py tests/test_investable_proxy.py tests/test_historical_replay_v02_market_cli.py
git commit -m "feat: add proxy residual financial calculation"
```
### Task 8: Freeze three months of control/identity/Evidence/policy targets before returns

**Files:**
- Create: `scripts/run_historical_replay_v02_prepare.py`
- Create: `tests/test_historical_replay_v02_prepare_cli.py`
- Modify: `src/wa_commons/portfolio/historical_replay.py`

**Interfaces:**
- Consumes: `HISTORICAL_REPLAY_WINDOW_FROZEN`, local pre-return source manifest, base policy config, `schemas/examples/user-policy.examples.json`.
- Produces: local monthly control/identity/coverage/screening/policy artifacts, `monthly_policy_payload_map.json`, and `HISTORICAL_REPLAY_TARGETS_FROZEN` manifest containing only hashes/metrics/changed-security IDs and no returns.

- [ ] **Step 1: Write the CLI fail-before-read test**

```python
def test_prepare_rejects_unfrozen_window_before_source_access(tmp_path: Path) -> None:
    window = tmp_path / "window.json"
    window.write_text('{"status":"BLOCK_HISTORICAL_REPLAY_COVERAGE"}', encoding="utf-8")
    with pytest.raises(ValueError, match="frozen window"):
        run_prepare(
            frozen_window_path=window,
            pre_return_input_manifest_path=tmp_path / "does-not-exist.json",
            policy_config_path=Path("configs/m3-3b2-policy-compiler-v0.1.json"),
            policies_path=Path("schemas/examples/user-policy.examples.json"),
            local_output_dir=tmp_path / "out",
            targets_manifest_path=tmp_path / "targets.json",
            code_commit="a" * 40,
        )
```
- [ ] **Step 2: Run the CLI test and verify RED**

Run: `python -m pytest tests/test_historical_replay_v02_prepare_cli.py -q`

Expected: FAIL because the prepare script does not exist.

- [ ] **Step 3: Implement the post-window pre-return preparation flow**

For each frozen period, in this order:

1. read the already-pinned local holdings CSV and parse equity weights;
2. read cutoff-scoped EDINET documents-list data and build historical identity;
3. map the control snapshot to that identity;
4. read only cutoff-eligible MOD workbooks and build coverage/screening;
5. bind monthly input hashes into a deepcopy of the fixed #84 compiler config;
6. call the existing `compile_policy_family()`;
7. record sorted directly changed security IDs for P1/P2;
8. write local row-level artifacts and repository-safe hashes/counts separately.

Do not open any JPX price, distribution, corporate-action, TOPIX ROI, NAV or performance file in this script.

- [ ] **Step 4: Add a frozen-target manifest verifier**

Add `verify_frozen_target_manifest(window_manifest, target_manifest) -> str | None` to `historical_replay.py`. It must require all three periods, exact window hash, identical policy semantics signature, monthly control/identity/screening hashes, policy payload hashes, and no performance-bearing fields. Success state is `HISTORICAL_REPLAY_TARGETS_FROZEN`; otherwise return `BLOCK_REPRODUCIBILITY`.
- [ ] **Step 5: Verify no return-bearing input exists in prepare CLI**

Inspect `build_parser()` in the new script and assert its option strings contain none of: `price`, `return`, `dividend`, `distribution`, `benchmark-value`, `performance`, `nav`.

Run: `python -m pytest tests/test_historical_replay_v02_prepare_cli.py tests/test_historical_replay_v02.py -q`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/run_historical_replay_v02_prepare.py tests/test_historical_replay_v02_prepare_cli.py src/wa_commons/portfolio/historical_replay.py
git commit -m "feat: freeze proxy replay targets before returns"
```

### Task 9: Execute v0.2 financial consequences only from frozen targets

**Files:**
- Modify: `src/wa_commons/portfolio/historical_replay.py`
- Modify: `scripts/run_historical_replay.py`
- Modify: `tests/test_historical_replay_v02.py`
- Modify: `tests/test_historical_replay_cli.py`

**Interfaces:**
- Consumes: frozen window, `HISTORICAL_REPLAY_TARGETS_FROZEN`, monthly policy map, post-freeze security-return payloads and TOPIX ROI payloads.
- Produces: `run_investable_proxy_replay(window_manifest: Mapping[str, Any], frozen_targets: Mapping[str, Any], monthly_policy_payloads: Mapping[str, Mapping[str, Any]], monthly_market_payloads: Mapping[str, Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]` with policy-transmission metrics first, P0/P1/P2 financial consequences second, and TOPIX tracking difference separately.
- [ ] **Step 1: Write failing synthetic v0.2 execution tests**

Use a two-security synthetic control where one security is `UNDERWEIGHT` in P2. The monthly market payload shape is:

```python
{
    "2026-01": {
        "security_returns": {
            "status": "SECURITY_RETURNS_OK",
            "rows": [
                {"security_id": "TSE:1475", "state": "RETURN_OK_NO_ACTION", "total_wealth_return": "0.010000000000"},
                {"security_id": "TSE:1001", "state": "RETURN_OK_NO_ACTION", "total_wealth_return": "0.020000000000"}
            ]
        },
        "topix_roi": {"status": "BENCHMARK_ROI_OK", "decimal_return": "0.009000000000"}
    }
}
```

Assert `policy_effect_vs_p0 = P2 - P0` and `p0_tracking_difference_vs_topix = P0 - TOPIX` are separate fields. Add tests for missing `TSE:1475`, missing changed-security row, blocked changed-security action/dividend, invalid TOPIX ROI, policy-semantics drift and input-order determinism.

- [ ] **Step 2: Run the new execution tests and verify RED before market access**

Use an exploding mapping/path fixture. `run_investable_proxy_replay()` and CLI must reject any target manifest not in `HISTORICAL_REPLAY_TARGETS_FROZEN` before touching market payloads.

Run: `python -m pytest tests/test_historical_replay_v02.py tests/test_historical_replay_cli.py -q`

Expected: new v0.2 tests FAIL; v0.1 execution tests remain PASS.
- [ ] **Step 3: Implement `run_investable_proxy_replay()`**

For each frozen month:

1. verify target-manifest/window/policy hashes;
2. read the `TSE:1475` total-wealth return as P0;
3. get direct changed-security IDs from the already frozen policy payload;
4. require `RETURN_OK_*` rows for every direct changed security;
5. call `compute_residual_sleeve_financial()` for P1/P2;
6. validate and then read TOPIX Total Return;
7. update cumulative wealth deterministically;
8. emit policy-transmission metrics before the `financial` object.

Do not recompute policy decisions or target weights inside execution.

- [ ] **Step 4: Extend the existing execution CLI version-safely**

Add optional `--frozen-targets`. When config v0.2 is loaded it is required; v0.1 behavior stays unchanged. Load/verify frozen window and frozen targets before opening `--market-payload-map`. The CLI remains execution-only and contains no candidate selection argument or logic.

`build_public_payload()` must continue hiding all financial and TOPIX/tracking values unless `publication.performance_rights_cleared` is true. Policy-transmission metrics/hashes/blockers remain publishable when allowed by existing source contracts.

- [ ] **Step 5: Run focused execution tests**

Run: `python -m pytest tests/test_historical_replay_v02.py tests/test_historical_replay.py tests/test_historical_replay_cli.py tests/test_investable_proxy.py tests/test_monthly_market.py -q`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/portfolio/historical_replay.py scripts/run_historical_replay.py tests/test_historical_replay_v02.py tests/test_historical_replay_cli.py
git commit -m "feat: execute frozen investable proxy replay"
```
### Task 10: Run the real Q1 gate, then returns only if the gate freezes

**Files:**
- Create/Update: local-only `local-artifacts/m3-3c0-v02/` source/input/output tree (never commit raw third-party files).
- Create: `docs/results/M3_3C0_HISTORICAL_REPLAY_V02_MANIFEST.json`
- Create: `docs/results/M3_3C0_HISTORICAL_REPLAY_V02.md`
- Modify: `ROADMAP.md`
- Modify: Issue #85 only after the repository result is committed and CI-verified.

**Interfaces:**
- Consumes: all implementation tasks above plus operator-pinned official/authorized source files.
- Produces: either an exact blocked result with no return loading, or a three-month `HISTORICAL_REPLAY_OK` result whose window/targets were frozen first.

- [ ] **Step 1: Establish 1475 source rights and original availability before qualification**

For each required holdings as-of date (`2025-12-30`, `2026-01-30`, `2026-02-27`), record a source manifest containing locator, source SHA-256, retrieval time, original/public availability time evidence, and rights state. `as_of_date` alone is not availability evidence.

If local research retention cannot be affirmatively supported, set `rights_state=REVIEW_REQUIRED`; qualification must emit `BLOCK_SOURCE_RIGHTS` and STOP. If original availability at or before the corresponding decision cutoff cannot be established, qualification must emit `BLOCK_EVIDENCE_CUTOFF`/coverage blocker and STOP. Do not move the cutoff after seeing returns.

- [ ] **Step 2: Build metadata-only Q1 candidate inventory**

Write `local-artifacts/m3-3c0-v02/q1-candidate-metadata.json` with only source locators/existence/availability/hashes for:
- 1475 holdings source;
- EDINET historical identity source coverage;
- MOD/political-finance Evidence source coverage;
- JPX 1475 start/end monthly price-table source existence;
- distribution/corporate-action detector source existence;
- TOPIX Total Return source existence.

Do not parse holdings market values or any return value in this step.
- [ ] **Step 3: Run the metadata-only qualification gate**

Run:

```powershell
$env:PYTHONPATH='src'
python scripts/run_historical_replay_qualification.py `
  --config configs/m3-3c0-historical-replay-v0.2.json `
  --candidate-metadata local-artifacts/m3-3c0-v02/q1-candidate-metadata.json `
  --output local-artifacts/m3-3c0-v02/q1-frozen-window.json `
  --code-commit (git rev-parse HEAD)
```

Expected successful gate: `status=HISTORICAL_REPLAY_WINDOW_FROZEN`, window exactly `2026-01,2026-02,2026-03`. Any BLOCK is a valid terminal result for the real-data path. If BLOCK, skip Steps 4-7 and go directly to Step 8 with the blocker evidence.

- [ ] **Step 4: After freeze only, build and hash all three monthly target portfolios**

Run:

```powershell
python scripts/run_historical_replay_v02_prepare.py `
  --frozen-window local-artifacts/m3-3c0-v02/q1-frozen-window.json `
  --pre-return-input-manifest local-artifacts/m3-3c0-v02/q1-pre-return-inputs.json `
  --policy-config configs/m3-3b2-policy-compiler-v0.1.json `
  --policies schemas/examples/user-policy.examples.json `
  --local-output-dir local-artifacts/m3-3c0-v02/pre-return `
  --targets-manifest local-artifacts/m3-3c0-v02/q1-frozen-targets.json `
  --code-commit (git rev-parse HEAD)
```

Verify `HISTORICAL_REPLAY_TARGETS_FROZEN` and that `monthly_policy_payload_map.json` contains exactly 2026-01/02/03 before opening any market-performance source.

- [ ] **Step 5: After target freeze only, build market inputs**

Arrange each month's pinned local files under `local-artifacts/m3-3c0-v02/market/<period>/` with filenames `start-price.pdf`, `end-price.pdf`, `topix-roi.pdf`, `ex-rights.pdf`, `listed-changes.pdf`, `evidence-resolutions.json`, and `source-manifest.json`. Then run:

```powershell
foreach ($period in @('2026-01','2026-02','2026-03')) {
  $dir = "local-artifacts/m3-3c0-v02/market/$period"
  python scripts/run_historical_replay_v02_market.py `
    --frozen-targets local-artifacts/m3-3c0-v02/q1-frozen-targets.json `
    --period $period `
    --start-price-pdf "$dir/start-price.pdf" `
    --end-price-pdf "$dir/end-price.pdf" `
    --benchmark-pdf "$dir/topix-roi.pdf" `
    --ex-rights-pdf "$dir/ex-rights.pdf" `
    --listed-changes-pdf "$dir/listed-changes.pdf" `
    --evidence-resolutions "$dir/evidence-resolutions.json" `
    --source-manifest "$dir/source-manifest.json" `
    --config configs/m3-3c-monthly-market-v0.1.json `
    --output "$dir/proxy-market-bundle.json"
}
```

Assemble the three already-produced bundles without recalculation:

```python
from pathlib import Path
import json

root = Path("local-artifacts/m3-3c0-v02/market")
periods = ("2026-01", "2026-02", "2026-03")
payload = {
    period: json.loads((root / period / "proxy-market-bundle.json").read_text(encoding="utf-8"))
    for period in periods
}
Path("local-artifacts/m3-3c0-v02/q1-market-map.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
```

Every unresolved direct-security dividend/action remains a blocker; do not use price-only or zero-dividend substitution.
- [ ] **Step 6: Execute the replay from frozen targets**

Run:

```powershell
python scripts/run_historical_replay.py `
  --frozen-window local-artifacts/m3-3c0-v02/q1-frozen-window.json `
  --frozen-targets local-artifacts/m3-3c0-v02/q1-frozen-targets.json `
  --policy-payload-map local-artifacts/m3-3c0-v02/pre-return/monthly_policy_payload_map.json `
  --market-payload-map local-artifacts/m3-3c0-v02/q1-market-map.json `
  --config configs/m3-3c0-historical-replay-v0.2.json `
  --local-output local-artifacts/m3-3c0-v02/q1-replay-local.json `
  --public-output local-artifacts/m3-3c0-v02/q1-replay-public.json
```

Local output may contain financial values; public output must apply the existing rights gate.

Required successful result fields:
- `status = HISTORICAL_REPLAY_OK`;
- exact three-month window and frozen hashes;
- per-month Policy Transmission metrics first;
- P0/P1/P2 monthly and cumulative financial consequences;
- `p0_tracking_difference_vs_topix` separated from `policy_effect_vs_p0`;
- blockers/limitations preserved even when the overall run succeeds.

- [ ] **Step 7: Reproduce the real run once from the same frozen inputs**

Rerun preparation/execution from identical pinned local inputs into a second local output directory. Assert window hash, target hashes, changed-security sets and repository-safe semantic result hash are identical. Do not reselect the window.

- [ ] **Step 8: Write the public result according to the actual terminal state**

`docs/results/M3_3C0_HISTORICAL_REPLAY_V02_MANIFEST.json` must contain only repository-safe provenance, hashes, counts, terminal status, blocker reasons, window/target hashes, and financial values only if publication rights are cleared.

`docs/results/M3_3C0_HISTORICAL_REPLAY_V02.md` must state explicitly whether:
- the real Q1 window froze;
- returns were never loaded because qualification blocked; or
- the three-month replay completed;
- 1475 is an investable proxy control, not official TOPIX constituent weights;
- TOPIX TR remained the external benchmark;
- 2026-04..08 remained engineering-only and October remained future holdout.
- [ ] **Step 9: Update ROADMAP from evidence, not intent**

If real qualification BLOCKS, keep #85 OPEN and set the precise blocker in `ROADMAP.md` (for example source rights, original availability, identity, Evidence cutoff or market coverage). Do not mark #51 current merely because v0.2 code exists.

If and only if the three-month real replay reaches `HISTORICAL_REPLAY_OK`, mark #85 complete subject to final CI and move the roadmap according to the existing dependency order. Do not change October 2026 holdout status.

- [ ] **Step 10: Run final verification once on the final tree**

Run focused first:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests/test_investable_proxy.py tests/test_historical_edinet.py tests/test_historical_cutoff.py tests/test_historical_replay_v02.py tests/test_historical_replay_v02_prepare_cli.py tests/test_historical_replay.py tests/test_historical_replay_cli.py tests/test_monthly_market.py tests/test_policy_compiler.py -q
```

Then one full repository suite:

```powershell
python -m pytest -q
```

Expected: focused and full repository suites both PASS. Also run `git diff --check` and parse every new/modified committed JSON with `json.loads()`.

- [ ] **Step 11: Commit the actual terminal result and push**

```bash
git add ROADMAP.md docs/results/M3_3C0_HISTORICAL_REPLAY_V02_MANIFEST.json docs/results/M3_3C0_HISTORICAL_REPLAY_V02.md
git commit -m "docs: record investable proxy historical replay result"
git push
```

Before claiming completion, use `superpowers:verification-before-completion`; before merging the implementation branch, use `superpowers:finishing-a-development-branch`. Do not use `Closes #85` unless the real three-month replay, final suite and PR-head CI all pass.
