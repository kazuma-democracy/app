# Public Browser Extension v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first public WA Commons client as a privacy-minimizing browser extension that lets a user select a supported Japanese company, inspect source-grounded evidence, and view canonical precomputed policy results across Chrome, Edge, Firefox, and Safari packaging.

**Architecture:** Python remains the only authority for identity, Evidence, coverage, and policy evaluation. Release tooling creates a deterministic, field-level rights-filtered Public Evidence Pack; a framework-free WebExtensions client only searches and renders that pack and stores the selected profile locally. Browser-specific work is restricted to thin manifest/package overlays, while store publication and any source-permission request remain explicit human-approved external actions.

**Tech Stack:** Python 3.11+, existing WA Commons modules, `pytest`, `jsonschema`, JSON, HTML/CSS, vanilla JavaScript ES modules, Node.js built-in test runner only for pure browser-client logic tests, WebExtensions Manifest V3 where supported, Python standard-library ZIP packaging.

**Spec:** `docs/superpowers/specs/2026-09-11-public-browser-extension-v01-design.md`

**Issue:** #91 — `M2.5 Public Browser Extension v0.1 — ship evidence-first company checks`

## Global Constraints

- Reuse Evidence Model v0.1, `wa-conservative-v0.2`, Evidence Cards, existing coverage states, and `wa_commons.policy.evaluator`; no shadow JavaScript policy engine.
- `NONE` never means clean, safe, peaceful, approved, or PASS.
- Name-only, fuzzy, hostname, page title, or selected page text never establishes consequential entity identity; ambiguous candidates require explicit user selection.
- No universal moral, peace, boycott, or risk score.
- No trading, portfolio recommendation, return claim, brokerage action, account, telemetry, browsing-history collection, central always-on application server, or remote executable code.
- Page assistance is user-invoked and temporary through `activeTab`; persistent `<all_urls>` is forbidden for v0.1.
- Existing row-level #53/#54/#55 outputs remain local-only. Public data is a new projection containing only fields with an explicit public-client rights decision.
- Current official EDINET and NTA terms use PDL1.0-style reuse with attribution. Acquisition must obey each site's current retrieval rules.
- Current JPX terms prohibit unpermitted commercial-purpose data collection and secondary use. Do not republish JPX row-level identity fields or claim an exact JPX-derived public universe without a separate permission decision.
- Current UN/OHCHR guidance requires permission for reuse of online platform/database content. `ohchr-settlements-business` is blocked for public row-level packaging until explicit permission or an explicit applicable reuse license is recorded.
- A blocked source becomes `NOT_INTEGRATED`; it never becomes evidence of absence.
- Store submission and source-permission requests are not automated and require explicit human approval.
- Use focused tests at each task. Run one full repository suite only at the final #91 review gate.

---

### Task 1: Make #91 the durable current product increment

**Files:**
- Modify: `ROADMAP.md`
- Create: `configs/m2-5-public-browser-extension-v0.1.json`
- Test: `tests/test_public_browser_extension_config.py`

**Interfaces:**
- Consumes: approved #91 design, preserved open Issue #85.
- Produces: a machine-readable #91 scope/config contract used by all later tasks.

- [ ] **Step 1: Write the RED config test**

```python
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_m25_extension_config_freezes_scope():
    cfg = json.loads((ROOT / "configs/m2-5-public-browser-extension-v0.1.json").read_text())
    assert cfg["issue"] == 91
    assert cfg["artifact_version"] == "m2-5-public-browser-extension-v0.1"
    assert cfg["browsers"] == ["chrome", "edge", "firefox", "safari"]
    assert cfg["public_topics"] == ["military_defence", "ohchr_settlement_related"]
    assert cfg["permissions"]["forbidden"] == [
        "<all_urls>", "history", "cookies", "webRequest", "nativeMessaging"
    ]
    assert cfg["manual_search_required"] is True
    assert cfg["page_hint_identity_authority"] is False
    assert cfg["policy_evaluator_location"] == "python_release_time_only"
    assert cfg["telemetry"] is False
    assert cfg["account_required"] is False
    assert cfg["remote_executable_code"] is False
    assert cfg["store_submission_requires_human_approval"] is True
    assert cfg["source_rights_contract"] == "configs/public-client-sources-v0.1.json"
    assert cfg["preserved_issue"] == 85
```

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_public_browser_extension_config.py -q`

Expected: FAIL because the config does not exist.

- [ ] **Step 3: Add the minimal config and Roadmap delta**

The config contains the exact asserted values plus:

```json
{
  "evidence_pack_mode": "bundled_release_asset",
  "release_requires_all_public_topics_ready": true,
  "public_release_authority": "human_only"
}
```

Update only the current-position/dependency text in `ROADMAP.md` so #91 is `CURRENT PUBLIC-PRODUCT PRIORITY` and #85 is `OPEN / PRESERVED / PAUSED FOR PRODUCT SEQUENCING`. Do not change `GOALS.md` and do not mark #85 complete.

- [ ] **Step 4: Run GREEN**

Run: `python311 -m pytest tests/test_public_browser_extension_config.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ROADMAP.md configs/m2-5-public-browser-extension-v0.1.json tests/test_public_browser_extension_config.py
git commit -m "docs: make public extension current increment"
```

---

### Task 2: Encode the public-client source-rights contract

**Files:**
- Create: `configs/public-client-sources-v0.1.json`
- Create: `src/wa_commons/public_client/__init__.py`
- Create: `src/wa_commons/public_client/source_rights.py`
- Create: `docs/rights/OHCHR_PUBLIC_REUSE_REQUEST.md`
- Modify: `docs/SOURCE_REGISTRY.md`
- Test: `tests/test_public_client_source_rights.py`

**Interfaces:**
- Produces:

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


def load_public_source_rights(path: Path) -> dict[str, PublicSourceRights]: ...

def require_public_fields(
    source_id: str,
    fields: set[str],
    rights: Mapping[str, PublicSourceRights],
) -> None: ...
```

Allowed states are exactly `PUBLIC_FIELDS_ALLOWED`, `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED`, and `BLOCK_PUBLIC_REDISTRIBUTION_REVIEW`.

- [ ] **Step 1: Write RED rights tests**

```python

def test_current_rights_states_are_explicit():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    assert rights["jp-mod-procurement"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-nta-corporate-number"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-edinet"].state == "PUBLIC_FIELDS_ALLOWED"
    assert rights["jp-jpx-listed"].state == "BLOCK_PUBLIC_REDISTRIBUTION_REVIEW"
    assert rights["ohchr-settlements-business"].state == "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"


def test_blocked_and_undeclared_fields_fail_closed():
    rights = load_public_source_rights(ROOT / "configs/public-client-sources-v0.1.json")
    require_public_fields("jp-mod-procurement", {"source_url", "narrow_claim"}, rights)
    with pytest.raises(ValueError, match="not cleared for public client"):
        require_public_fields("jp-mod-procurement", {"raw_document_text"}, rights)
    with pytest.raises(ValueError, match="BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"):
        require_public_fields("ohchr-settlements-business", {"entity_name"}, rights)
```

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_public_client_source_rights.py -q`

Expected: FAIL on missing module/config.

- [ ] **Step 3: Implement the rights validator**

`load_public_source_rights()` rejects duplicate source IDs, unknown states, missing terms URL/date, `raw_rows_public=true` for a blocked source, and a non-empty `allowed_fields` list for a blocked source. `require_public_fields()` rejects unknown sources, blocked states, or any field not in the exact allowlist.

- [ ] **Step 4: Record the current v0.1 source decisions**

Use `checked_at="2026-09-11"` and these exact boundaries:

- `jp-mod-procurement`: `PUBLIC_FIELDS_ALLOWED`; allow normalized narrow claim, publisher, source URL/locator, contract date, contract subject/classification, adjudication/provenance fields; raw document/row false; attribution required; each source record still requires no contrary third-party-rights marker.
- `jp-nta-corporate-number`: `PUBLIC_FIELDS_ALLOWED`; allow corporate number, legal name, source URL/snapshot; attribution required.
- `jp-edinet`: `PUBLIC_FIELDS_ALLOWED`; allow EDINET code, securities code, filer name, corporate number, source URL/snapshot; attribution required; no scraping where EDINET requires its download/API path.
- `jp-jpx-listed`: `BLOCK_PUBLIC_REDISTRIBUTION_REVIEW`; allow no row fields.
- `ohchr-settlements-business`: `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED`; allow no row fields.

Update `docs/SOURCE_REGISTRY.md` only with these public-client rights observations; evidentiary scope stays unchanged.

- [ ] **Step 5: Draft the OHCHR permission request without sending it**

`docs/rights/OHCHR_PUBLIC_REUSE_REQUEST.md` asks for written permission to distribute only normalized fields needed by a free/open-source WA Commons browser extension: company name/identifier where present, OHCHR-defined activity category, source date, source document/page locator, and attribution. State explicitly that raw PDFs are not redistributed and that the extension will preserve OHCHR wording/scope rather than create a generic pro/anti-Israel label.

The document starts with `STATUS: DRAFT — HUMAN APPROVAL REQUIRED BEFORE SENDING`.

- [ ] **Step 6: Run GREEN**

Run: `python311 -m pytest tests/test_public_client_source_rights.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add configs/public-client-sources-v0.1.json src/wa_commons/public_client docs/SOURCE_REGISTRY.md docs/rights/OHCHR_PUBLIC_REUSE_REQUEST.md tests/test_public_client_source_rights.py
git commit -m "feat: gate public client fields by source rights"
```

---

### Task 3: Build a public-safe company identity projection

**Files:**
- Create: `src/wa_commons/public_client/identity_projection.py`
- Create: `scripts/build_public_company_identity.py`
- Test: `tests/test_public_company_identity.py`
- Test: `tests/test_public_company_identity_cli.py`

**Interfaces:**
- Consumes: local #53 canonical identity, EDINET code-list rows, NTA rows, Task 2 rights map.
- Produces:

```python
def build_public_company_identity(
    *,
    canonical_identity: Mapping[str, Any],
    edinet_rows: Sequence[Mapping[str, Any]],
    nta_rows: Sequence[Mapping[str, Any]],
    rights: Mapping[str, PublicSourceRights],
    code_commit: str,
) -> dict[str, Any]: ...
```

Output public company rows contain `entity_id`, `corporate_number`, `canonical_name`, `security_code`, `edinet_code`, source IDs, and identity state. Display name comes from NTA when corporate-number-resolved; securities code comes from EDINET. No JPX row-level field is copied.

- [ ] **Step 1: Write concrete synthetic RED tests**

```python

def test_projection_uses_only_cleared_display_sources():
    canonical = {
        "manifest": {"semantic_identity_sha256": "a" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1001",
            "review_state": "CONFIRMED",
            "identifiers": [{"scheme": "JP_CORPORATE_NUMBER", "value": "1234567890123"}],
        }],
    }
    edinet = [{
        "EDINETコード": "E00001", "証券コード": "10010",
        "提出者法人番号": "1234567890123", "提出者名": "合成株式会社"
    }]
    nta = [{"法人番号": "1234567890123", "商号又は名称": "合成株式会社"}]
    payload = build_public_company_identity(
        canonical_identity=canonical, edinet_rows=edinet, nta_rows=nta,
        rights=allowed_rights_fixture(), code_commit="abc123",
    )
    row = payload["companies"][0]
    assert row["canonical_name"] == "合成株式会社"
    assert row["security_code"] == "1001"
    assert row["display_name_source"] == "jp-nta-corporate-number"
    assert row["security_code_source"] == "jp-edinet"
    assert "JPX_SECURITY_CODE" not in json.dumps(payload)


def test_projection_does_not_resolve_name_only_entity():
    canonical = canonical_without_corporate_number_fixture()
    payload = build_public_company_identity(
        canonical_identity=canonical,
        edinet_rows=edinet_same_name_fixture(),
        nta_rows=nta_same_name_fixture(),
        rights=allowed_rights_fixture(),
        code_commit="abc123",
    )
    assert payload["manifest"]["resolved_public_company_count"] == 0
    assert payload["manifest"]["unresolved_count"] == 1
```

The helper fixtures named above are fully defined in the test file using synthetic values; no real row-level source data is committed.

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_public_company_identity.py -q`

Expected: FAIL because the module is absent.

- [ ] **Step 3: Implement strong-ID-only projection**

Algorithm:

```text
canonical entity
→ exactly one confirmed JP_CORPORATE_NUMBER
→ exact NTA corporate-number row supplies public legal name
→ exact EDINET corporate-number row supplies EDINET code and normalized securities code
→ any missing/duplicate/conflicting strong ID becomes unresolved
```

Reuse `normalize_edinet_security_code()` and `build_nta_corporate_index()` from `wa_commons.identity.enrich`. Never call a fuzzy matcher.

The manifest records input semantic/source hashes, rights-contract hash, resolved count, unresolved count, and a canonical public-projection SHA-256. The hash excludes run timestamp but includes source snapshot versions.

- [ ] **Step 4: Add the CLI and CLI tests**

`build_public_company_identity.py` accepts five required paths/values: `--canonical-identity`, `--edinet-code-list`, `--nta`, `--rights`, `--output`, plus `--code-commit`. The CLI test creates every input under `tmp_path`, invokes `main()` with monkeypatched `sys.argv`, and asserts only the public projection is written. The CLI prints aggregate counts/hashes only.

- [ ] **Step 5: Run GREEN**

Run: `python311 -m pytest tests/test_public_company_identity.py tests/test_public_company_identity_cli.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/public_client/identity_projection.py scripts/build_public_company_identity.py tests/test_public_company_identity.py tests/test_public_company_identity_cli.py
git commit -m "feat: build public-safe company identity projection"
```

---

### Task 4: Freeze public policy profiles and the two topic contracts

**Files:**
- Create: `configs/public-browser-extension-policies-v0.1.json`
- Create: `src/wa_commons/public_client/topics.py`
- Test: `tests/test_public_browser_extension_policies.py`
- Test: `tests/test_public_browser_extension_topics.py`
- Reuse unchanged: `src/wa_commons/policy/evaluator.py`

**Interfaces:**
- Produces four exact profile IDs: `public:information-only:v1`, `public:strict-military-specific:v1`, `public:ohchr-settlement-avoidance:v1`, `public:military-and-settlement:v1`.
- Produces `PUBLIC_TOPICS` metadata. Military source state comes from actual rights/coverage; OHCHR topic reports `NOT_INTEGRATED` while its source rights state is blocked.

- [ ] **Step 1: Write RED policy tests**

```python

def test_strict_military_profile_preserves_existing_semantics():
    strict = profile("public:strict-military-specific:v1")
    rule = strict["exclusions"][0]
    assert rule["match"] == {
        "categories": ["military_contract"],
        "predicates": ["contract_subject_classification"],
    }
    assert rule["condition"]["value"] == "military_specific"


def test_settlement_profile_matches_only_exact_narrow_predicate():
    p = profile("public:ohchr-settlement-avoidance:v1")
    exact = synthetic_claim("human_rights", "ohchr_settlement_related_activity", "confirmed")
    ordinary = synthetic_claim("human_rights", "business_presence_in_israel", "confirmed")
    assert evaluate_claim(p, exact).decision == "EXCLUDE"
    assert evaluate_claim(p, ordinary).decision == "NONE"
```

Validate all four profiles with `schemas/user-policy.v0.1.schema.json` using `jsonschema`.

- [ ] **Step 2: Write the topic-state RED test**

```python

def test_blocked_ohchr_rights_become_not_integrated_not_no_match():
    topics = build_public_topic_states(blocked_ohchr_rights_fixture())
    assert topics["ohchr_settlement_related"]["state"] == "NOT_INTEGRATED"
    assert topics["ohchr_settlement_related"]["reason"] == "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED"
```

- [ ] **Step 3: Run RED**

Run: `python311 -m pytest tests/test_public_browser_extension_policies.py tests/test_public_browser_extension_topics.py -q`

Expected: FAIL on missing config/module.

- [ ] **Step 4: Add the four profiles and topic metadata**

The strict military profile copies the existing strict military-specific rule semantics. Settlement profiles react only to `ohchr_settlement_related_activity`; `business_presence_in_israel` is never a matching predicate. Unknown/disputed/expired states stay explicit according to the user-policy schema.

`topics.py` contains metadata only; it does not parse or ingest OHCHR data. Do not create an OHCHR source adapter while public reuse permission is blocked. If written permission later changes Task 2 rights state to allowed, adding the real adapter is a separate reviewed increment before public release.

- [ ] **Step 5: Run GREEN**

Run: `python311 -m pytest tests/test_public_browser_extension_policies.py tests/test_public_browser_extension_topics.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add configs/public-browser-extension-policies-v0.1.json src/wa_commons/public_client/topics.py tests/test_public_browser_extension_policies.py tests/test_public_browser_extension_topics.py
git commit -m "feat: freeze public extension policy and topic contracts"
```

---

### Task 5: Build the deterministic Public Evidence Pack exporter

**Files:**
- Create: `src/wa_commons/public_client/browser_pack.py`
- Create: `scripts/build_public_browser_pack.py`
- Test: `tests/test_public_browser_pack.py`
- Test: `tests/test_public_browser_pack_cli.py`

**Interfaces:**

```python
def build_public_browser_pack(
    *,
    public_identity: Mapping[str, Any],
    coverage: Mapping[str, Any],
    screening: Mapping[str, Any],
    evidence_graph: Mapping[str, Any],
    source_rights: Mapping[str, PublicSourceRights],
    profile_ids: Sequence[str],
    generated_at: str,
    code_commit: str,
) -> dict[str, Any]: ...


def validate_public_browser_pack(pack: Mapping[str, Any]) -> None: ...

def write_public_browser_pack(pack: Mapping[str, Any], output: Path) -> None: ...
```

- [ ] **Step 1: Write RED determinism/rights tests**

```python

def test_pack_is_order_independent_and_has_no_local_only_fields():
    a = build_pack_fixture(order="forward")
    b = build_pack_fixture(order="reverse")
    assert a["manifest"]["pack_semantic_sha256"] == b["manifest"]["pack_semantic_sha256"]
    assert a["companies"] == b["companies"]
    text = json.dumps(a)
    assert "raw_document_text" not in text
    assert "JPX_SECURITY_CODE" not in text


def test_blocked_ohchr_source_is_not_serialized():
    pack = build_pack_fixture(include_synthetic_blocked_ohchr_record=True)
    assert pack["manifest"]["release_state"] == "BLOCK_SOURCE_RIGHTS"
    assert pack["topics"]["ohchr_settlement_related"]["state"] == "NOT_INTEGRATED"
    assert "synthetic-blocked-company" not in json.dumps(pack)
```

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_public_browser_pack.py -q`

Expected: FAIL because `browser_pack` is absent.

- [ ] **Step 3: Implement the rights-filtered projection**

For each public company, map only through the confirmed public identity relation, select precomputed views for the configured profiles, and use existing `card_from_claim()` as the canonical Evidence Card source. Before serializing a card or claim field, call `require_public_fields()` for every source represented by that field. Serialize only the narrow public claim fields needed by the UI; never dump a canonical claim object wholesale.

Canonical ordering is `(canonical_name, corporate_number)` for companies and `claim_id` for evidence. The semantic hash excludes `generated_at` but includes code commit, identity/evidence/coverage/profile/source-rights hashes.

Release states are exactly `READY_FOR_CAPABILITY_TEST`, `BLOCK_SOURCE_RIGHTS`, `BLOCK_PUBLIC_IDENTITY_RIGHTS`, and `BLOCK_IDENTITY_COVERAGE`. The exporter never emits `READY_FOR_STORE_SUBMISSION`.

- [ ] **Step 4: Add CLI tests and implementation**

The CLI test writes synthetic identity/coverage/screening/evidence/rights inputs under `tmp_path`, invokes `main()`, then asserts the output validates and stdout contains only aggregate counts, release state, and SHA-256 values. No claim body or company row may be printed.

- [ ] **Step 5: Run GREEN**

Run: `python311 -m pytest tests/test_public_browser_pack.py tests/test_public_browser_pack_cli.py tests/test_evidence_cards.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/wa_commons/public_client/browser_pack.py scripts/build_public_browser_pack.py tests/test_public_browser_pack.py tests/test_public_browser_pack_cli.py
git commit -m "feat: export rights-filtered browser evidence pack"
```

---

### Task 6: Implement the shared browser-extension search and popup

**Files:**
- Create: `clients/browser-extension/common/manifest.base.json`
- Create: `clients/browser-extension/common/popup.html`
- Create: `clients/browser-extension/common/popup.css`
- Create: `clients/browser-extension/common/search.mjs`
- Create: `clients/browser-extension/common/popup.mjs`
- Create: `clients/browser-extension/common/_locales/ja/messages.json`
- Create: `clients/browser-extension/common/data/README.md`
- Create: `tests/fixtures/public-browser-pack.synthetic.json`
- Create: `tests/browser_extension_search.test.mjs`
- Create: `tests/test_browser_extension_static.py`

**Interfaces:**

```javascript
export function normalizeQuery(value) {}
export function searchCompanies(pack, query) {}
```

`searchCompanies()` returns a deterministically sorted candidate array only. Rendering requires a click on a candidate; search never establishes identity by itself.

- [ ] **Step 1: Write the JavaScript RED search tests with Node's built-in runner**

```javascript
import test from "node:test";
import assert from "node:assert/strict";
import { normalizeQuery, searchCompanies } from "../clients/browser-extension/common/search.mjs";

const pack = {
  companies: [
    { corporate_number: "2222222222222", canonical_name: "合成電機株式会社", security_code: "2002", aliases: [] },
    { corporate_number: "1111111111111", canonical_name: "合成株式会社", security_code: "1001", aliases: ["合成"] }
  ]
};

test("security code and name searches are deterministic", () => {
  assert.deepEqual(searchCompanies(pack, "１００１").map(x => x.security_code), ["1001"]);
  assert.deepEqual(searchCompanies(pack, "合成").map(x => x.security_code), ["1001", "2002"]);
});

test("query normalization is limited and deterministic", () => {
  assert.equal(normalizeQuery("  ＡＢＣ　株式会社 "), "abc 株式会社");
});
```

- [ ] **Step 2: Write Python static RED tests**

Assert Manifest V3, `default_locale="ja"`, permissions subset of `storage/activeTab/scripting`, no persistent host permissions, no external script URL, no analytics endpoint, and no forbidden moral/safety copy.

- [ ] **Step 3: Run RED**

Run:

```bash
node --test tests/browser_extension_search.test.mjs
python311 -m pytest tests/test_browser_extension_static.py -q
```

Expected: both fail because client files are absent.

- [ ] **Step 4: Implement pure search logic**

`normalizeQuery()` uses `String.prototype.normalize("NFKC")`, lowercasing, whitespace collapse, and trim only. `searchCompanies()` returns exact securities-code matches first; otherwise it searches cleared canonical names/aliases and sorts by `(canonical_name, corporate_number)`. It never evaluates policy or reads page content.

- [ ] **Step 5: Implement the popup**

Use `<script type="module" src="popup.mjs">`. `popup.mjs` loads the bundled local pack through `chrome.runtime.getURL()` or the `browser` namespace equivalent, loads/stores only `profile_id` in extension-local storage, displays candidate buttons, and renders a company only after a candidate click.

Visible company state includes canonical name, securities code if present, identity state, selected precomputed policy result, `NONEは安全・問題なしを意味しません`, military/defence topic, settlement-related topic, evidence source/provenance, pack version/date, and correction/challenge link.

UI strings come from `_locales/ja/messages.json`; logic does not embed alternate moral labels.

`clients/browser-extension/common/data/README.md` states that the actual `wa-public-evidence-pack.json` is injected only by the package builder. Commit only the synthetic pack under `tests/fixtures`.

- [ ] **Step 6: Run GREEN**

Run:

```bash
node --test tests/browser_extension_search.test.mjs
python311 -m pytest tests/test_browser_extension_static.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add clients/browser-extension/common tests/fixtures/public-browser-pack.synthetic.json tests/browser_extension_search.test.mjs tests/test_browser_extension_static.py
git commit -m "feat: add common browser extension company viewer"
```

---

### Task 7: Add explicit `activeTab` page hints with no identity authority

**Files:**
- Create: `clients/browser-extension/common/page-hint.js`
- Modify: `clients/browser-extension/common/popup.html`
- Modify: `clients/browser-extension/common/popup.mjs`
- Create: `tests/test_browser_page_hint_contract.py`
- Modify: `tests/test_browser_extension_static.py`

**Interfaces:**
- Produces page hint object `{selectedText, title, hostname}`. The popup feeds the hint into `searchCompanies()` only; it never calls the company renderer from page-hint output.

- [ ] **Step 1: Write RED contract tests**

```python

def test_page_hint_is_search_only_and_private():
    popup = (COMMON / "popup.mjs").read_text(encoding="utf-8")
    hint = (COMMON / "page-hint.js").read_text(encoding="utf-8")
    assert "executeScript" in popup
    assert "searchCompanies" in popup
    assert "renderCompany(pageHint" not in popup
    assert "storage.local.set" not in hint
    assert "fetch(" not in hint
    assert "document.cookie" not in hint
```

Also assert the manifest still has no persistent host permissions.

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_browser_page_hint_contract.py -q`

Expected: FAIL because `page-hint.js` is absent.

- [ ] **Step 3: Implement the minimal injected function**

Return at most 256 characters of selected text, 256 characters of title, and the current hostname. Do not inspect forms, cookies, local/session storage, hidden DOM, other tabs, or network resources. Invocation occurs only inside the user's `選択中の文字から候補を探す` click handler through `scripting.executeScript`.

Selected text is the primary hint, title is fallback, hostname is context only and is not a matching key in v0.1. Even one candidate from a page hint still requires an explicit candidate click.

- [ ] **Step 4: Run GREEN**

Run: `python311 -m pytest tests/test_browser_page_hint_contract.py tests/test_browser_extension_static.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add clients/browser-extension/common/page-hint.js clients/browser-extension/common/popup.html clients/browser-extension/common/popup.mjs tests/test_browser_page_hint_contract.py tests/test_browser_extension_static.py
git commit -m "feat: add explicit active-tab company search hints"
```

---

### Task 8: Produce deterministic packages for four browser targets

**Files:**
- Create: `clients/browser-extension/chrome/manifest.overrides.json`
- Create: `clients/browser-extension/edge/manifest.overrides.json`
- Create: `clients/browser-extension/firefox/manifest.overrides.json`
- Create: `clients/browser-extension/safari/manifest.overrides.json`
- Create: `scripts/build_browser_extension_packages.py`
- Create: `tests/test_browser_extension_packaging.py`
- Modify: `.gitignore`

**Interfaces:**

```python
@dataclass(frozen=True)
class PackageResult:
    browser: str
    manifest_path: Path
    zip_path: Path
    sha256: str
    permissions: tuple[str, ...]


def build_browser_package(
    browser: str,
    pack_path: Path,
    output_root: Path,
) -> PackageResult: ...
```

- [ ] **Step 1: Write RED packaging tests**

```python

def test_four_packages_share_common_logic_and_minimal_permissions(tmp_path):
    results = build_all_packages(SYNTHETIC_PACK, tmp_path)
    assert [r.browser for r in results] == ["chrome", "edge", "firefox", "safari"]
    for result in results:
        manifest = json.loads(result.manifest_path.read_text())
        assert set(manifest.get("permissions", [])) <= {"storage", "activeTab", "scripting"}
        assert manifest.get("host_permissions", []) == []
        assert result.sha256 == sha256_file(result.zip_path)
```

Firefox-specific test requires:

```python
gecko = manifest["browser_specific_settings"]["gecko"]
assert gecko["id"] == "wa-commons@kazuma-democracy.github.io"
assert gecko["data_collection_permissions"]["required"] == ["none"]
```

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_browser_extension_packaging.py -q`

Expected: FAIL on missing package builder/overlays.

- [ ] **Step 3: Implement deterministic package assembly**

Use Python standard library only. Merge dictionaries recursively; arrays replace rather than concatenate. Copy common resources and the validated pack into a staging directory, apply exactly one browser overlay, then audit permissions and remote-script declarations.

ZIP entries are lexicographically sorted and use timestamp `(1980, 1, 1, 0, 0, 0)` so equal inputs produce equal bytes. Reject symlinks, absolute paths, secret-like filenames, invalid pack state, persistent host permissions, and external executable script URLs.

- [ ] **Step 4: Keep browser overlays thin**

Chrome and Edge have no product-logic differences. Firefox adds `browser_specific_settings.gecko.id` and current AMO `data_collection_permissions.required=["none"]`. Safari uses the same web-extension resources; its ZIP is intended for Apple's current Safari Web Extension Packager, whose current CLI name is `safari-web-extension-packager`. No Xcode project is maintained as a second source tree.

- [ ] **Step 5: Verify deterministic hashes**

Run packaging tests, then build all four packages twice from the same synthetic pack in two temporary output roots and assert all corresponding SHA-256 values are identical.

Run: `python311 -m pytest tests/test_browser_extension_packaging.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add clients/browser-extension/chrome clients/browser-extension/edge clients/browser-extension/firefox clients/browser-extension/safari scripts/build_browser_extension_packages.py tests/test_browser_extension_packaging.py .gitignore
git commit -m "feat: package browser extension for four targets"
```

---

### Task 9: Add CI, browser certification gates, and release evidence without auto-publishing

**Files:**
- Create: `.github/workflows/public-browser-extension.yml`
- Create: `docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md`
- Create: `docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md`
- Test: `tests/test_public_browser_extension_release_contract.py`

**Interfaces:**
- Produces a CI capability gate and a measured result with either `CAPABILITY_READY` or an exact `BLOCK_*` state. It never performs store submission.

- [ ] **Step 1: Write RED release-contract tests**

```python

def test_ci_contains_no_store_publish_step_or_credentials():
    workflow = (ROOT / ".github/workflows/public-browser-extension.yml").read_text().lower()
    assert "chrome-webstore-upload" not in workflow
    assert "amo api key" not in workflow
    assert "app store connect api key" not in workflow


def test_report_cannot_claim_public_release_while_ohchr_is_blocked():
    report = (ROOT / "docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md").read_text()
    assert "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED" in report
    assert "PUBLIC_RELEASE_COMPLETE" not in report
```

- [ ] **Step 2: Run RED**

Run: `python311 -m pytest tests/test_public_browser_extension_release_contract.py -q`

Expected: FAIL because workflow/report/runbook do not exist.

- [ ] **Step 3: Add capability CI**

CI runs Python 3.11 focused tests, Node 24 built-in search tests with no npm dependencies, deterministic four-target packaging from the synthetic pack, static permission/privacy/remote-code audits, and artifact hash recording. Do not add a Node package manager/build framework.

Firefox: use current AMO manifest requirements in the overlay. Add `web-ext lint` only if the executor's SEARCH BEFORE BUILD check concludes a pinned invocation gives material validation without introducing a maintained Node dependency; otherwise use AMO validation at the manual certification gate.

Safari: ordinary CI validates the resource package. A macOS runner may invoke `xcrun safari-web-extension-packager` when present, but absent Apple signing/account credentials are not a code failure. App Store Connect web packaging/TestFlight is a manual certification step.

- [ ] **Step 4: Write the measured result with exact current blockers**

Record Issue #91, exact HEAD, source-rights hash, public identity resolved/unresolved counts, topic states, pack SHA-256, four package SHA-256 values, exact permissions, focused/full-suite results, and cross-browser certification state.

If OHCHR rights are still blocked, use exactly:

```text
Capability: CAPABILITY_READY only if all code gates pass
Public release: BLOCKED
Blocker: BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED / ohchr-settlements-business
Israel/OPT topic: NOT_INTEGRATED
```

Do not write that no relevant OHCHR evidence exists for any company.

- [ ] **Step 5: Write the manual certification/release runbook**

The runbook has four sections beginning `HUMAN APPROVAL REQUIRED`:
1. Chrome: load unpacked package, manual search, ambiguous-name selection, NONE warning, source/challenge links, page hint, then Chrome Web Store validation/submission.
2. Edge: same checks from the Edge package, then Microsoft Edge Add-ons validation/submission.
3. Firefox: temporary/local install, same behavior checks, AMO manifest/signing validation, then submission.
4. Safari: upload common resource ZIP to the current App Store Connect Safari Web Extension Packager or use `safari-web-extension-packager` on macOS, test through TestFlight, then App Store review.

Each section requires a fresh official store-policy check immediately before submission.

- [ ] **Step 6: Run the #91 focused set**

```bash
python311 -m pytest tests/test_public_browser_extension_config.py tests/test_public_client_source_rights.py tests/test_public_company_identity.py tests/test_public_company_identity_cli.py tests/test_public_browser_extension_policies.py tests/test_public_browser_extension_topics.py tests/test_public_browser_pack.py tests/test_public_browser_pack_cli.py tests/test_browser_extension_static.py tests/test_browser_page_hint_contract.py tests/test_browser_extension_packaging.py tests/test_public_browser_extension_release_contract.py -q
node --test tests/browser_extension_search.test.mjs
```

Expected: PASS.

- [ ] **Step 7: Run the one final full repository suite**

Run: `python311 -m pytest -q`

Expected: all repository tests PASS. If a pre-existing/environment failure appears, record observation and diagnose it before changing code; do not patch unrelated failures into #91.

- [ ] **Step 8: Inspect the final diff and packages**

Compare against the current `main`. Confirm no #85 implementation files, real restricted source rows, credentials, remote executable code, or unrelated refactors entered #91. Confirm each package contains only common client assets, browser manifest delta, and the validated public pack.

- [ ] **Step 9: Commit the release-gate evidence**

```bash
git add .github/workflows/public-browser-extension.yml docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md tests/test_public_browser_extension_release_contract.py
git commit -m "test: add public extension release gates"
```

- [ ] **Step 10: Open a bounded #91 PR**

The PR body separately reports code capability status, rights blockers, browser-certification status, store-submission status, and preserved #85 state. Do not close #91 or claim public release until the applicable Definition of Done is actually satisfied.

---

## Execution Notes

- At execution time create a fresh worktree from `design/public-browser-extension-v01-20260911` using `superpowers:using-git-worktrees`.
- Implementation branch: `feat/issue-91-public-browser-extension-v01`.
- Do not reuse `C:\AI\wa-commons-issue85-1306-v03`; preserve the #85 worktree/branch untouched.
- Before Task 1 execution, fetch `main` and compare it with the design base. If `main` moved, inspect those commits for #91 contract changes before integrating them; never force-push.
- The current OHCHR blocker is an external rights dependency. Capability work proceeds with `NOT_INTEGRATED`; no real OHCHR row is committed, parsed, or distributed until permission/licensing changes the recorded source state.
- If a browser/store requirement changes, record the new official fact and make the smallest browser-specific packaging change. Do not fork identity, evidence, policy, or product logic.
- Before any store submission, re-check official Chrome, Edge, Firefox, and Apple documentation because store requirements are time-sensitive.
