# Public Browser Extension v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a privacy-minimizing, evidence-first browser-extension capability that lets a user deterministically select a supported Japanese company, inspect rights-cleared military/defence and narrowly scoped Israel/occupied-Palestinian-territory evidence, and view canonical precomputed user-policy results across Chrome, Edge, Firefox, and Safari packaging.

**Architecture:** Keep Python as the only authority for identity/evidence/policy semantics. A release-time exporter creates a deterministic, rights-filtered Public Evidence Pack; a framework-free WebExtensions client only searches and renders that pack, stores the selected profile locally, and optionally uses `activeTab` page text as a search hint. Browser-specific code is limited to manifest/package overlays, and store publication stays a separate human-approved side effect.

**Tech Stack:** Python 3.11+, existing WA Commons evidence/identity/policy modules, `pytest`, `jsonschema`, JSON, HTML/CSS/vanilla JavaScript, WebExtensions Manifest V3 where supported, Python standard-library ZIP packaging, Chrome/Edge/Firefox/Safari store tooling only at certification/release gates.

**Spec:** `docs/superpowers/specs/2026-09-11-public-browser-extension-v01-design.md`

**Issue:** #91 — `M2.5 Public Browser Extension v0.1 — ship evidence-first company checks`

## Global Constraints

- Reuse current Evidence Model, `wa-conservative-v0.2`, Evidence Cards, coverage states, and canonical Python policy evaluator; do not create a second evidence or policy engine.
- `NONE` is never displayed or encoded as clean, safe, peaceful, approved, or PASS.
- Name-only/fuzzy/page-derived text never establishes consequential entity identity; ambiguous matches require explicit user selection.
- No universal moral/peace/boycott/risk score.
- v0.1 has no trading, portfolio, return, brokerage, account, telemetry, browsing-history collection, central always-on application server, or remote executable code.
- Page assistance is user-invoked only and uses temporary `activeTab`; persistent `<all_urls>` is not an accepted v0.1 permission.
- Public package fields must have an explicit field-level public-client rights decision. Restricted/review-required/local-only rows fail closed.
- Existing row-level #53/#54/#55 artifacts remain local-only; the browser pack is a new public-safe projection, not a copy of those artifacts.
- Current official EDINET terms are PDL1.0-based with attribution requirements; current NTA public corporate-number terms are PDL1.0-based. Use only the exact cleared fields recorded in the source-rights contract.
- Current JPX terms prohibit unpermitted commercial-purpose data collection and secondary use. Do not ship JPX-derived row-level identity fields or claim exact JPX-derived coverage without a separate permission/rights decision.
- Current UN/OHCHR database reuse guidance requires permission. `ohchr-settlements-business` remains `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED` until explicit reuse permission/license is recorded.
- Store submission/release is not automated and requires explicit human approval.
- Use focused tests per task; run one full repository suite only at the final #91 review gate.

---

### Task 1: Make #91 the durable current product increment without erasing #85

**Files:**
- Modify: `ROADMAP.md`
- Create: `configs/m2-5-public-browser-extension-v0.1.json`
- Test: `tests/test_public_browser_extension_config.py`

**Interfaces:**
- Consumes: approved design at `docs/superpowers/specs/2026-09-11-public-browser-extension-v01-design.md`, Issue #91, preserved Issue #85.
- Produces: `configs/m2-5-public-browser-extension-v0.1.json` with `issue=91`, `artifact_version="m2-5-public-browser-extension-v0.1"`, four first-class browser targets, privacy invariants, source-rights contract path, and `store_submission_requires_human_approval=true`.

- [ ] **Step 1: Create the config contract test**

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_m25_extension_config_freezes_public_product_scope():
    cfg = json.loads((ROOT / "configs/m2-5-public-browser-extension-v0.1.json").read_text())
    assert cfg["issue"] == 91
    assert cfg["artifact_version"] == "m2-5-public-browser-extension-v0.1"
    assert cfg["browsers"] == ["chrome", "edge", "firefox", "safari"]
    assert cfg["permissions"]["forbidden"] == [
        "<all_urls>", "history", "cookies", "webRequest", "nativeMessaging"
    ]
    assert cfg["telemetry"] is False
    assert cfg["account_required"] is False
    assert cfg["remote_executable_code"] is False
    assert cfg["store_submission_requires_human_approval"] is True
    assert cfg["source_rights_contract"] == "configs/public-client-sources-v0.1.json"
    assert cfg["preserved_issue"] == 85
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `python311 -m pytest tests/test_public_browser_extension_config.py -q`

Expected: FAIL because `configs/m2-5-public-browser-extension-v0.1.json` does not exist.

- [ ] **Step 3: Add the minimal config and Roadmap sequencing change**

Create the config with the exact fields asserted above plus:

```json
{
  "manual_search_required": true,
  "page_hint_identity_authority": false,
  "policy_evaluator_location": "python_release_time_only",
  "evidence_pack_mode": "bundled_release_asset",
  "public_topics": ["military_defence", "ohchr_settlement_related"],
  "release_requires_all_public_topics_ready": true
}
```

Update `ROADMAP.md` current position to state:

```text
M2.5 Public Browser Extension v0.1 — CURRENT PUBLIC-PRODUCT PRIORITY (#91)
#85 Historical Replay — OPEN / PRESERVED / PAUSED FOR PRODUCT SEQUENCING
```

Do not mark #85 complete and do not change `GOALS.md`.

- [ ] **Step 4: Re-run the focused test**

Run: `python311 -m pytest tests/test_public_browser_extension_config.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ROADMAP.md configs/m2-5-public-browser-extension-v0.1.json tests/test_public_browser_extension_config.py
git commit -m "docs: make public extension current increment"
```

---

### Task 2: Encode a fail-closed public-client source-rights contract

**Files:**
- Create: `configs/public-client-sources-v0.1.json`
- Create: `src/wa_commons/public_client/__init__.py`
- Create: `src/wa_commons/public_client/source_rights.py`
- Modify: `docs/SOURCE_REGISTRY.md`
- Test: `tests/test_public_client_source_rights.py`

**Interfaces:**
- Consumes: Source Registry IDs `jp-mod-procurement`, `ohchr-settlements-business`, `jp-jpx-listed`, `jp-nta-corporate-number`, `jp-edinet`.
- Produces: `load_public_source_rights(path: Path) -> dict[str, PublicSourceRights]`, `require_public_fields(source_id: str, fields: set[str], rights: Mapping[str, PublicSourceRights]) -> None`, and exact states `PUBLIC_FIELDS_ALLOWED`, `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED`, `BLOCK_PUBLIC_REDISTRIBUTION_REVIEW`.

- [ ] **Step 1: Write RED tests for exact rights states and field filtering**

```python
from pathlib import Path
import pytest

from wa_commons.public_client.source_rights import (
    load_public_source_rights,
    require_public_fields,
)

ROOT = Path(__file__).resolve().parents[1]


def test_current_public_client_rights_are_fail_closed():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    assert rights["jp-mod-procurement"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-nta-corporate-number"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-edinet"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-jpx-listed"].state == "BLOCK_PUBLIC_REDISTRIBUTION_REVIEW"
    assert rights["ohchr-settlements-business"].state == "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"


def test_blocked_or_undeclared_fields_cannot_enter_public_pack():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    require_public_fields("jp-mod-procurement", {"source_url", "narrow_claim"}, rights)
    with pytest.raises(ValueError, match="not cleared for public client"):
        require_public_fields("jp-mod-procurement", {"raw_document_text"}, rights)
    with pytest.raises(ValueError, match="BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"):
        require_public_fields("ohchr-settlements-business", {"entity_name"}, rights)
```

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_public_client_source_rights.py -q`

Expected: import/file failure because public-client rights code/config do not exist.

- [ ] **Step 3: Implement immutable rights records**

Use a frozen dataclass:

```python
@dataclass(frozen=True)
class PublicSourceRights:
    source_id: str
    state: str
    terms_url: str
    checked_at: str
    allowed_fields: frozenset[str]
    attribution_required: bool
    raw_rows_public: bool
    note: str
```

`require_public_fields()` must reject an unknown source, any non-`PUBLIC_FIELDS_ALLOWED` state, or any requested field outside `allowed_fields`.

- [ ] **Step 4: Create the exact v0.1 rights config**

Record these decisions with `checked_at="2026-09-11"`:

- `jp-mod-procurement`: `PUBLIC_FIELDS_ALLOWED`; public fields limited to normalized narrow claim, source publisher, source URL/locator, contract date/subject classification, adjudication/provenance metadata; raw documents/rows false; attribution required; exact source-page third-party exceptions remain a per-record gate.
- `jp-nta-corporate-number`: `PUBLIC_FIELDS_ALLOWED`; public identity fields limited to corporate number and legal name needed for the extension projection; attribution required.
- `jp-edinet`: `PUBLIC_FIELDS_ALLOWED`; public identity fields limited to EDINET code, securities code, filer/legal display name and source metadata needed for the projection; attribution required; acquisition must follow EDINET download/API rules rather than prohibited scraping.
- `jp-jpx-listed`: `BLOCK_PUBLIC_REDISTRIBUTION_REVIEW`; no row-level allowed fields.
- `ohchr-settlements-business`: `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED`; no row-level allowed fields until explicit permission/license changes this versioned decision.

Update `docs/SOURCE_REGISTRY.md` with these narrower public-client observations without changing the evidentiary meaning of any source.

- [ ] **Step 5: Run focused GREEN**

Run: `python311 -m pytest tests/test_public_client_source_rights.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add configs/public-client-sources-v0.1.json src/wa_commons/public_client docs/SOURCE_REGISTRY.md tests/test_public_client_source_rights.py
git commit -m "feat: gate public client fields by source rights"
```

---

### Task 3: Build a public-safe company identity projection without copying #53 rows

**Files:**
- Create: `src/wa_commons/public_client/identity_projection.py`
- Create: `scripts/build_public_company_identity.py`
- Test: `tests/test_public_company_identity.py`
- Test: `tests/test_public_company_identity_cli.py`

**Interfaces:**
- Consumes: operator-supplied local #53 identity artifact; independently loaded EDINET code-list rows; independently loaded NTA corporate-number rows; Task 2 rights contract.
- Produces: `build_public_company_identity(*, canonical_identity, edinet_rows, nta_rows, rights, code_commit) -> dict`, with public IDs keyed by corporate number where resolved, public display/search fields sourced only from EDINET/NTA, an explicit unresolved list/count, provenance/hashes, and no JPX row-level source fields.

- [ ] **Step 1: Write RED tests using synthetic EDINET/NTA/canonical fixtures**

```python

def test_public_identity_uses_cleared_sources_and_preserves_unresolved():
    payload = build_public_company_identity(
        canonical_identity=canonical_fixture(),
        edinet_rows=edinet_fixture(),
        nta_rows=nta_fixture(),
        rights=rights_fixture(),
        code_commit="abc123",
    )
    assert payload["manifest"]["identity_policy_version"] == "wa-conservative-v0.2"
    assert payload["companies"][0]["display_name_source"] == "jp-nta-corporate-number"
    assert payload["companies"][0]["security_code_source"] == "jp-edinet"
    assert "JPX_SECURITY_CODE" not in str(payload["companies"])
    assert payload["manifest"]["unresolved_count"] == 1


def test_public_identity_rejects_name_only_join_and_jpx_public_fields():
    with pytest.raises(ValueError, match="strong identifier"):
        build_public_company_identity(...name_only_fixture...)
    with pytest.raises(ValueError, match="jp-jpx-listed"):
        build_public_company_identity(...fixture_requesting_jpx_display_field...)
```

Use concrete synthetic fixtures in the test file; do not use real row-level source data as test fixtures.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_public_company_identity.py -q`

Expected: FAIL because `identity_projection` does not exist.

- [ ] **Step 3: Implement the projection with strong-ID joins only**

Required logic:

```python
canonical entity
  -> exactly one confirmed JP_CORPORATE_NUMBER
  -> exact NTA corporate-number row for public legal name
  -> exact EDINET corporate-number/EDINET-code relation already established by accepted identity provenance
  -> EDINET securities code used only when uniquely associated
```

Never use fuzzy/name similarity to fill missing display fields. Preserve unresolved entries separately instead of force-filling them.

The manifest must include semantic hashes of the public projection and each input source snapshot. The public semantic hash excludes retrieval timestamps but includes source snapshot/version and rights-contract hash.

- [ ] **Step 4: Add CLI with local inputs and one public output**

```bash
python311 scripts/build_public_company_identity.py \
  --canonical-identity <local-identity.json> \
  --edinet-code-list <local-edinet.json> \
  --nta <local-nta.json> \
  --rights configs/public-client-sources-v0.1.json \
  --output <public-identity.json> \
  --code-commit <sha>
```

The CLI must refuse an output path equal to any local raw-input path and print only aggregate counts/hashes.

- [ ] **Step 5: Add CLI contract tests and run both focused files**

Run: `python311 -m pytest tests/test_public_company_identity.py tests/test_public_company_identity_cli.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/public_client/identity_projection.py scripts/build_public_company_identity.py tests/test_public_company_identity.py tests/test_public_company_identity_cli.py
git commit -m "feat: build public-safe company identity projection"
```

---

### Task 4: Add public-client policy profiles without changing existing profile behavior

**Files:**
- Create: `configs/public-browser-extension-policies-v0.1.json`
- Test: `tests/test_public_browser_extension_policies.py`
- Reuse unchanged: `src/wa_commons/policy/evaluator.py`

**Interfaces:**
- Consumes: existing `example:strict-military-avoidance` semantics and user-policy v0.1 schema.
- Produces: four exact browser profile IDs: `public:information-only:v1`, `public:strict-military-specific:v1`, `public:ohchr-settlement-avoidance:v1`, `public:military-and-settlement:v1`.

- [ ] **Step 1: Write RED policy-schema/parity tests**

```python

def test_public_profiles_are_versioned_and_existing_military_semantics_are_unchanged():
    profiles = load_profiles()
    by_id = {p["profile_id"]: p for p in profiles}
    strict = by_id["public:strict-military-specific:v1"]
    assert strict["exclusions"][0]["match"] == {
        "categories": ["military_contract"],
        "predicates": ["contract_subject_classification"],
    }
    assert strict["exclusions"][0]["condition"]["value"] == "military_specific"


def test_settlement_profile_matches_only_exact_settlement_predicate():
    p = profile("public:ohchr-settlement-avoidance:v1")
    exact = synthetic_claim(category="human_rights", predicate="ohchr_settlement_related_activity", status="confirmed")
    ordinary = synthetic_claim(category="human_rights", predicate="business_presence_in_israel", status="confirmed")
    assert evaluate_claim(p, exact).decision == "EXCLUDE"
    assert evaluate_claim(p, ordinary).decision == "NONE"
```

Also validate all four profiles against `schemas/user-policy.v0.1.schema.json` with `jsonschema`.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_public_browser_extension_policies.py -q`

Expected: FAIL because the public profile file does not exist.

- [ ] **Step 3: Add the four profile definitions**

Rules:
- information-only: no exclusions; confirmed relevant claims render informationally; uncertainty remains visible but does not invent PASS.
- strict military: exactly mirrors existing strict military-specific classification behavior.
- settlement avoidance: only exact `ohchr_settlement_related_activity` confirmed claims can trigger EXCLUDE; unknown/disputed/expired route to WATCH.
- combined: union of the two exact exclusion rules; no generic `Israel-related` rule.

- [ ] **Step 4: Run focused GREEN**

Run: `python311 -m pytest tests/test_public_browser_extension_policies.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add configs/public-browser-extension-policies-v0.1.json tests/test_public_browser_extension_policies.py
git commit -m "feat: add public extension policy profiles"
```

---

### Task 5: Add the settlement-source interface but keep real OHCHR publication blocked

**Files:**
- Create: `src/wa_commons/evidence/ohchr_settlements.py`
- Test: `tests/test_ohchr_settlements.py`
- Modify: `src/wa_commons/evidence/tse_coverage.py`
- Modify: `src/wa_commons/policy/tse_screening.py`
- Test: `tests/test_tse_evidence_coverage.py`
- Test: `tests/test_tse_policy_screening.py`

**Interfaces:**
- Consumes: synthetic normalized records shaped as `entity_name`, `source_native_id`, `activity_category`, `source_date`, `source_url`, `identity_decision`, and optional strong IDs.
- Produces: `settlement_claim(record: Mapping[str, Any]) -> dict[str, Any] | None` with category `human_rights`, predicate `ohchr_settlement_related_activity`, source ID `ohchr-settlements-business`; TSE coverage/screening can accept an optional normalized settlement-observation sequence without weakening existing MOD-only behavior.

- [ ] **Step 1: Write synthetic RED tests for narrow semantics**

```python

def test_settlement_claim_preserves_source_defined_scope():
    claim = settlement_claim(synthetic_confirmed_record())
    assert claim["category"] == "human_rights"
    assert claim["predicate"] == "ohchr_settlement_related_activity"
    assert claim["value"]["activity_category"] == "synthetic-category-a"
    assert claim["evidence"][0]["source_id"] == "ohchr-settlements-business"


def test_name_only_or_unresolved_record_does_not_create_confirmed_claim():
    assert settlement_claim(synthetic_name_only_record()) is None
```

No real OHCHR company rows may be committed as fixtures.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_ohchr_settlements.py -q`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the minimal normalized-record adapter**

Require either an already-confirmed canonical `entity_id` or one aligned strong identifier under the existing identity policy. The adapter must never infer a company from an English name alone.

- [ ] **Step 4: Extend coverage/screening through optional parameters**

Add optional arguments with empty defaults so existing callers remain unchanged:

```python
build_tse_coverage(..., settlement_observations: Iterable[Mapping[str, object]] = ())
build_tse_policy_screening(..., settlement_observations: Sequence[Mapping[str, Any]] = ())
```

When no settlement observations are supplied, existing #54/#55 semantic output behavior must remain unchanged apart from deliberately versioned fields required by #91. A real OHCHR run is not performed while Task 2 rights state is blocked.

- [ ] **Step 5: Add regression tests and run focused set**

Run: `python311 -m pytest tests/test_ohchr_settlements.py tests/test_tse_evidence_coverage.py tests/test_tse_policy_screening.py -q`

Expected: PASS, including a test proving ordinary Israel business presence cannot trigger the settlement predicate.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/evidence/ohchr_settlements.py src/wa_commons/evidence/tse_coverage.py src/wa_commons/policy/tse_screening.py tests/test_ohchr_settlements.py tests/test_tse_evidence_coverage.py tests/test_tse_policy_screening.py
git commit -m "feat: add narrow settlement evidence interface"
```

---

### Task 6: Build the deterministic Public Evidence Pack exporter

**Files:**
- Create: `src/wa_commons/public_client/browser_pack.py`
- Create: `scripts/build_public_browser_pack.py`
- Test: `tests/test_public_browser_pack.py`
- Test: `tests/test_public_browser_pack_cli.py`

**Interfaces:**
- Consumes: Task 3 public identity projection; local coverage/screening/evidence inputs; Task 4 profile IDs; Task 2 rights contract; existing `wa_commons.evidence.cards.card_from_claim()`.
- Produces:

```python
build_public_browser_pack(
    *,
    public_identity: Mapping[str, Any],
    coverage: Mapping[str, Any],
    screening: Mapping[str, Any],
    evidence_graph: Mapping[str, Any],
    source_rights: Mapping[str, PublicSourceRights],
    profile_ids: Sequence[str],
    generated_at: str,
    code_commit: str,
) -> dict[str, Any]

validate_public_browser_pack(pack: Mapping[str, Any]) -> None
write_public_browser_pack(pack: Mapping[str, Any], output: Path) -> None
```

- [ ] **Step 1: Write RED tests for deterministic pack and rights filtering**

```python

def test_pack_is_deterministic_and_contains_no_local_only_fields():
    a = build_pack_fixture(input_order="forward")
    b = build_pack_fixture(input_order="reverse")
    assert a["manifest"]["pack_semantic_sha256"] == b["manifest"]["pack_semantic_sha256"]
    assert a["companies"] == b["companies"]
    serialized = json.dumps(a)
    assert "raw_document_text" not in serialized
    assert "JPX_SECURITY_CODE" not in serialized


def test_pack_blocks_uncleared_evidence_instead_of_publishing_it():
    pack = build_pack_fixture(include_blocked_ohchr=True)
    assert pack["manifest"]["release_state"] == "BLOCK_SOURCE_RIGHTS"
    assert pack["topics"]["ohchr_settlement_related"]["state"] == "NOT_INTEGRATED"
    assert "synthetic-company-from-blocked-source" not in json.dumps(pack)
```

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_public_browser_pack.py -q`

Expected: FAIL because `browser_pack` does not exist.

- [ ] **Step 3: Implement pack projection using existing Evidence Cards**

For each public company:
1. map only by confirmed public identity/canonical entity relation;
2. select the requested precomputed profile views from canonical screening output;
3. build evidence cards with `card_from_claim()` only for rights-cleared source fields;
4. map blocked topic sources to explicit `NOT_INTEGRATED` metadata without copying their row data;
5. sort companies by `(canonical_name, corporate_number)` and evidence by `claim_id`;
6. hash a canonical JSON projection excluding `generated_at`, while retaining code/input/profile/source-rights hashes.

Release states are exactly:
- `READY_FOR_CAPABILITY_TEST`
- `BLOCK_SOURCE_RIGHTS`
- `BLOCK_PUBLIC_IDENTITY_RIGHTS`
- `BLOCK_IDENTITY_COVERAGE`

The exporter must never emit `READY_FOR_STORE_SUBMISSION` by itself.

- [ ] **Step 4: Add CLI and fail-closed output rules**

The CLI accepts local row-level inputs but only writes the filtered public pack. It prints aggregate counts, release state, and semantic SHA; it must not print claim text or company rows.

- [ ] **Step 5: Run focused tests**

Run: `python311 -m pytest tests/test_public_browser_pack.py tests/test_public_browser_pack_cli.py tests/test_evidence_cards.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/public_client/browser_pack.py scripts/build_public_browser_pack.py tests/test_public_browser_pack.py tests/test_public_browser_pack_cli.py
git commit -m "feat: export rights-filtered browser evidence pack"
```

---

### Task 7: Implement the common framework-free extension popup

**Files:**
- Create: `clients/browser-extension/common/manifest.base.json`
- Create: `clients/browser-extension/common/popup.html`
- Create: `clients/browser-extension/common/popup.css`
- Create: `clients/browser-extension/common/popup.js`
- Create: `clients/browser-extension/common/messages.ja.json`
- Create: `clients/browser-extension/common/data/README.md`
- Create: `tests/test_browser_extension_static.py`
- Create: `tests/fixtures/public-browser-pack.synthetic.json`

**Interfaces:**
- Consumes: Task 6 Public Evidence Pack JSON.
- Produces: popup UI with deterministic `searchCompanies(pack, query)`, `renderCompany(company, profileId)`, and local profile selection; no network fetch except opening a source/challenge URL by explicit user action.

- [ ] **Step 1: Write static RED tests for manifest/privacy/UI contract**

```python

def test_common_manifest_has_minimal_permissions():
    manifest = load_json(COMMON / "manifest.base.json")
    assert manifest["manifest_version"] == 3
    assert set(manifest["permissions"]) <= {"storage", "activeTab", "scripting"}
    assert "host_permissions" not in manifest or manifest["host_permissions"] == []


def test_popup_copy_never_calls_none_safe_or_good():
    js = (COMMON / "popup.js").read_text(encoding="utf-8")
    assert "NONE" in js
    for forbidden in ("安全な会社", "問題なし", "peace score", "moral score"):
        assert forbidden not in js
```

Also assert no external `<script src="https://...">`, no analytics URL, and Japanese strings are loaded from `messages.ja.json` rather than hard-coded throughout logic.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_browser_extension_static.py -q`

Expected: FAIL because common extension files do not exist.

- [ ] **Step 3: Implement popup structure**

`popup.html` contains:
- search input `企業名・証券コードで検索`;
- policy-profile selector;
- candidate list;
- selected company header;
- identity state;
- selected policy result;
- explicit `NONEは安全・問題なしを意味しません` notice;
- military/defence topic card;
- settlement-related topic card;
- evidence detail/source link;
- correction/challenge link;
- pack version/date.

`popup.js` loads `data/wa-public-evidence-pack.json`, normalizes only whitespace/case/full-width ASCII necessary for lookup, performs exact securities-code match first, then deterministic substring/prefix candidate search over cleared names/aliases, and never auto-selects when more than one candidate remains.

- [ ] **Step 4: Add a synthetic development pack only**

`tests/fixtures/public-browser-pack.synthetic.json` is the test input. `clients/browser-extension/common/data/README.md` states that the real release pack is generated and copied at package-build time and must not be hand-authored or sourced from local restricted rows.

Do not commit a real row-level public pack in this task.

- [ ] **Step 5: Run focused static tests**

Run: `python311 -m pytest tests/test_browser_extension_static.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add clients/browser-extension/common tests/test_browser_extension_static.py tests/fixtures/public-browser-pack.synthetic.json
git commit -m "feat: add common browser extension company viewer"
```

---

### Task 8: Add user-invoked `activeTab` search hints without identity authority

**Files:**
- Create: `clients/browser-extension/common/page-hint.js`
- Modify: `clients/browser-extension/common/popup.html`
- Modify: `clients/browser-extension/common/popup.js`
- Modify: `tests/test_browser_extension_static.py`
- Create: `tests/test_browser_page_hint_contract.py`

**Interfaces:**
- Consumes: current active tab only after the user clicks `選択中の文字から候補を探す`.
- Produces: `{selectedText: string, title: string, hostname: string}` search hint; popup passes a trimmed hint into `searchCompanies()` and never directly into `renderCompany()`.

- [ ] **Step 1: Write RED contract tests**

```python

def test_page_hint_is_search_only_and_not_persisted():
    popup = (COMMON / "popup.js").read_text(encoding="utf-8")
    hint = (COMMON / "page-hint.js").read_text(encoding="utf-8")
    assert "executeScript" in popup
    assert "searchCompanies" in popup
    assert "renderCompany(pageHint" not in popup
    assert "storage.local.set" not in hint
    assert "fetch(" not in hint
```

Add an assertion that `manifest.base.json` still has no persistent host permission.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_browser_page_hint_contract.py -q`

Expected: FAIL because `page-hint.js` is absent.

- [ ] **Step 3: Implement the page-hint function**

`page-hint.js` returns at most 256 characters of selected text, at most 256 characters of document title, and hostname. It does not inspect forms, cookies, page storage, hidden DOM, other tabs, or network resources.

The popup asks for the hint only from a click handler. Search priority is selected text, then title; hostname may be displayed as context but is not an identity key in v0.1.

- [ ] **Step 4: Run focused GREEN**

Run: `python311 -m pytest tests/test_browser_page_hint_contract.py tests/test_browser_extension_static.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add clients/browser-extension/common/page-hint.js clients/browser-extension/common/popup.html clients/browser-extension/common/popup.js tests/test_browser_page_hint_contract.py tests/test_browser_extension_static.py
git commit -m "feat: add explicit active-tab company search hints"
```

---

### Task 9: Produce deterministic Chrome, Edge, Firefox, and Safari-target packages

**Files:**
- Create: `clients/browser-extension/chrome/manifest.overrides.json`
- Create: `clients/browser-extension/edge/manifest.overrides.json`
- Create: `clients/browser-extension/firefox/manifest.overrides.json`
- Create: `clients/browser-extension/safari/manifest.overrides.json`
- Create: `scripts/build_browser_extension_packages.py`
- Create: `tests/test_browser_extension_packaging.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: common extension resources plus a validated Task 6 pack path.
- Produces: deterministic staging directories and ZIPs under ignored `dist/browser-extension/<browser>/`; `build_browser_package(browser: str, pack_path: Path, output_root: Path) -> PackageResult` where `PackageResult` includes browser, manifest path, zip path, SHA-256, and permission set.

- [ ] **Step 1: Write RED packaging tests**

```python

def test_all_four_packages_share_common_logic_and_minimal_permissions(tmp_path):
    results = build_all_packages(SYNTHETIC_PACK, tmp_path)
    assert [r.browser for r in results] == ["chrome", "edge", "firefox", "safari"]
    for result in results:
        manifest = json.loads(result.manifest_path.read_text())
        assert set(manifest.get("permissions", [])) <= {"storage", "activeTab", "scripting"}
        assert manifest.get("host_permissions", []) == []
        assert result.sha256 == sha256_file(result.zip_path)
```

Add Firefox assertions:

```python
assert manifest["browser_specific_settings"]["gecko"]["id"] == "wa-commons@kazuma-democracy.github.io"
assert manifest["browser_specific_settings"]["gecko"]["data_collection_permissions"]["required"] == ["none"]
```

This satisfies the current AMO requirement for new submissions to declare data collection permissions.

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_browser_extension_packaging.py -q`

Expected: FAIL because package builder/overlays do not exist.

- [ ] **Step 3: Implement overlay merge and deterministic ZIP**

Use Python standard library only. Merge dictionaries recursively; arrays replace rather than concatenate unless the exact key is explicitly handled. ZIP entries are sorted and use a fixed timestamp `(1980, 1, 1, 0, 0, 0)` so identical inputs create identical bytes.

The builder must:
- reject a pack whose validator fails;
- copy common HTML/CSS/JS/messages plus the selected real/synthetic pack;
- apply one browser manifest overlay;
- run the forbidden-permission check after merge;
- reject absolute paths, symlinks, secrets-like filenames, and remote script declarations;
- never contact a store.

- [ ] **Step 4: Define thin browser overlays**

Chrome/Edge: no product-logic difference.

Firefox: add only `browser_specific_settings.gecko.id` and `data_collection_permissions.required=["none"]` plus any verified compatibility minimum required by the current Firefox manifest checker.

Safari: no forked JavaScript; overlay only keys actually required/accepted by Safari packaging. The generated extension-resource ZIP is the input to Apple's current Safari Web Extension Packager; the repository does not hand-maintain an Xcode fork.

- [ ] **Step 5: Run packaging tests twice and compare hashes**

Run: `python311 -m pytest tests/test_browser_extension_packaging.py -q`

Then run the package builder twice against the synthetic pack and assert the four ZIP hashes are identical between runs.

Expected: PASS and deterministic hashes.

- [ ] **Step 6: Commit**

```bash
git add clients/browser-extension/chrome clients/browser-extension/edge clients/browser-extension/firefox clients/browser-extension/safari scripts/build_browser_extension_packages.py tests/test_browser_extension_packaging.py .gitignore
git commit -m "feat: package browser extension for four targets"
```

---

### Task 10: Add cross-browser CI and acceptance evidence without auto-publishing

**Files:**
- Create: `.github/workflows/public-browser-extension.yml`
- Create: `docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md`
- Create: `docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md`
- Test: `tests/test_public_browser_extension_release_contract.py`

**Interfaces:**
- Consumes: Tasks 1-9 capability, focused tests, package hashes, rights states.
- Produces: CI that tests/builds packages but never submits them; an acceptance report with `CAPABILITY_READY` or explicit `BLOCK_*` states; human release runbook for Chrome/Edge/Firefox/Safari.

- [ ] **Step 1: Write RED release-contract tests**

```python

def test_ci_never_contains_store_publish_credentials_or_submit_steps():
    workflow = (ROOT / ".github/workflows/public-browser-extension.yml").read_text()
    lowered = workflow.lower()
    assert "chrome-webstore-upload" not in lowered
    assert "amo api key" not in lowered
    assert "app store connect api key" not in lowered


def test_result_report_cannot_claim_release_while_ohchr_rights_blocked():
    report = (ROOT / "docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md").read_text()
    assert "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED" in report
    assert "PUBLIC_RELEASE_COMPLETE" not in report
```

- [ ] **Step 2: Run focused RED**

Run: `python311 -m pytest tests/test_public_browser_extension_release_contract.py -q`

Expected: FAIL because workflow/report/runbook do not exist.

- [ ] **Step 3: Add CI for capability verification**

Workflow jobs:
1. Python 3.11 focused #91 tests.
2. Build deterministic Chrome/Edge/Firefox/Safari-target resource ZIPs from the synthetic pack on ordinary CI.
3. Static manifest/privacy/remote-code audit.
4. Firefox manifest validation using a pinned `web-ext` version only if adding that tool passes the repository's reuse/dependency review; otherwise record manual AMO validation in the release runbook rather than introducing Node solely for linting.
5. Safari resource compatibility: validate common package statically on normal CI; optional macOS verification may call Apple's current `safari-web-extension-packager` if the hosted runner provides it, but absence of Apple signing credentials is not a code failure.

No job uploads to any browser store.

- [ ] **Step 4: Write the measured-result template with exact states**

The report must record:
- Issue #91 and exact HEAD;
- source-rights contract hash;
- public identity count / unresolved count;
- source/topic coverage states;
- Public Evidence Pack semantic hash;
- four package SHA-256 values;
- exact permissions per package;
- focused and final test results;
- current blockers.

At the first capability checkpoint, if OHCHR permission is still absent, state:

```text
Capability: READY_FOR_CAPABILITY_TEST or CAPABILITY_READY (only if code gates pass)
Public release: BLOCKED
Blocker: BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED / ohchr-settlements-business
```

Do not state that Israel/OPT evidence is absent for any company merely because the source is blocked.

- [ ] **Step 5: Write the human store-release runbook**

`docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md` contains separate manual checklists for:
- Chrome Web Store;
- Microsoft Edge Add-ons;
- Mozilla AMO signing/submission;
- Safari App Store Connect Safari Web Extension Packager/TestFlight/App Store review.

Each checklist begins with `HUMAN APPROVAL REQUIRED` and requires a fresh check of current store policies immediately before submission.

- [ ] **Step 6: Run the #91 focused test set**

Run:

```bash
python311 -m pytest \
  tests/test_public_browser_extension_config.py \
  tests/test_public_client_source_rights.py \
  tests/test_public_company_identity.py \
  tests/test_public_company_identity_cli.py \
  tests/test_public_browser_extension_policies.py \
  tests/test_ohchr_settlements.py \
  tests/test_public_browser_pack.py \
  tests/test_public_browser_pack_cli.py \
  tests/test_browser_extension_static.py \
  tests/test_browser_page_hint_contract.py \
  tests/test_browser_extension_packaging.py \
  tests/test_public_browser_extension_release_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Run the one final full repository suite**

Run: `python311 -m pytest -q`

Expected: all repository tests PASS. If any pre-existing/environment failure appears, record observation/evidence and diagnose before changing code; do not patch unrelated failures into #91.

- [ ] **Step 8: Verify generated packages and inspect diff**

Run the package builder with the current validated pack, record the four hashes, then inspect `git diff main...HEAD` and confirm no #85 implementation files, real restricted source rows, credentials, or unrelated refactors entered the branch.

- [ ] **Step 9: Commit the release-gate evidence**

```bash
git add .github/workflows/public-browser-extension.yml docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md tests/test_public_browser_extension_release_contract.py
git commit -m "test: add public extension release gates"
```

- [ ] **Step 10: Open a bounded PR for #91 capability review**

PR body must distinguish:
- code capability status;
- rights blockers;
- store submission status;
- #85 preserved state.

Do not close #91 unless its capability Definition of Done is met. Do not claim public release until human-approved store submissions are actually accepted/released or store-specific blockers are recorded.

---

## Execution Notes

- Implement on a fresh worktree created from `design/public-browser-extension-v01-20260911` after this plan is approved. Do not reuse `C:\AI\wa-commons-issue85-1306-v03`.
- Suggested implementation branch: `feat/issue-91-public-browser-extension-v01`.
- At Task 1 execution start, fetch `main` and compare it with the design base. If `main` moved, rebase/merge only after checking whether new commits change #91 contracts; never force-push.
- Preserve the #85 local worktree/branch untouched.
- Use synthetic fixtures for OHCHR until public reuse permission/license is recorded. Permission acquisition is an external dependency, not a reason to weaken the evidence or rights model.
- If a browser/store requirement changes during implementation, record the changed official requirement and make the smallest browser-specific overlay change; do not fork the product logic.
