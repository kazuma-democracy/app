# WA Commons Public Browser Extension v0.1 Design

Status: **PROPOSED WRITTEN SPEC — user-approved direction, awaiting written-spec review**

Date: 2026-09-11
Base: `main@11ec8b2758a113ea91fc16e7ec881d20fd5fddbe`
Branch: `design/public-browser-extension-v01-20260911`

## 1. Decision summary

WA Commons will prioritize a small public browser extension before completing the longer Peace Capital Historical Replay path.

The extension is the first broadly usable public client of the already-completed Evidence / identity / policy / explainability stack. It does **not** replace Peace Capital, rewrite `GOALS.md`, or authorize real-money action. Issue #85 work remains preserved and resumable; the sequencing change is to ship a practical company-information client first.

The first-class publication targets are:

1. Google Chrome / Chrome Web Store;
2. Microsoft Edge / Microsoft Edge Add-ons;
3. Mozilla Firefox / addons.mozilla.org;
4. Apple Safari / App Store Safari Web Extension packaging.

The architecture uses one shared WebExtensions codebase, with browser-specific manifest/package deltas only where required.

## 2. Product purpose

A person browsing the web should be able to invoke WA Commons voluntarily and quickly answer:

- Which listed company am I trying to inspect?
- What relevant, source-grounded evidence does WA Commons currently have?
- What does my selected policy profile do with that evidence?
- What is unknown, unresolved, disputed, expired, or not integrated?
- Where can I inspect the supporting source and challenge/correct the record?

The product must reduce research friction without becoming a universal company morality score or opaque blacklist.

## 3. Scope of v0.1

### In scope

- Japanese TSE domestic listed-company universe already established by the canonical identity path.
- Search by canonical company name and TSE security code.
- Verified aliases only where already present in accepted identity data; brand-to-company mappings are not invented.
- Toolbar popup as the universal UI surface.
- Optional explicit-user-gesture page assistance using the active tab only as a **search hint**, never as identity evidence.
- Two public evidence topics:
  - military / defence-related evidence, with contract-subject semantics preserved;
  - Israeli-settlement / occupied-Palestinian-territory-related evidence where supported by a rights-cleared, explicitly adopted OHCHR source path.
- Evidence Card-style source/provenance display.
- User-selectable, versioned policy profiles.
- Explicit uncertainty and coverage states.
- Bundled, versioned public Evidence Pack generated at release time.
- No account and no central WA Commons application server required for the core v0.1 experience.

### Out of scope

- automatic trading or brokerage integration;
- portfolio recommendations;
- price/return claims;
- universal moral, peace, safety, boycott, or risk score;
- automatic full-page surveillance or browsing-history collection;
- automatic company attribution from a page title/domain/name-only match;
- product/brand database creation;
- barcode scanning;
- retailer routing;
- arbitrary user-authored policy language in the browser;
- remote executable code;
- server-required personalized accounts;
- claims from sources whose redistribution/public-display rights are not cleared.

## 4. Reuse-first architecture

The extension must use **USE > EXTEND > ADAPT > REPLACE > BUILD**.

Reuse unchanged where possible:

- canonical TSE company identity artifacts;
- `wa-conservative-v0.2` identity decisions;
- Evidence Model v0.1;
- Source Registry semantics;
- Evidence Cards;
- existing policy evaluation and company research views;
- TSE-wide coverage/screening outputs;
- challenge/correction URLs and provenance conventions.

The extension does not create a second evidence model or a second authoritative policy evaluator.

New code should be limited to:

1. a release-time **Public Evidence Pack exporter** in the existing Python stack;
2. a plain WebExtensions client that searches and renders the precomputed pack;
3. small browser-specific packaging files;
4. release/store documentation and cross-browser verification.

## 5. Policy strategy: precompute, do not duplicate the engine

v0.1 does not reimplement the Python policy engine in JavaScript.

Instead, the release-time exporter runs the canonical WA Commons policy/evidence pipeline and packages precomputed company views for a small set of named, versioned profiles. The browser stores only the user's selected `profile_id` locally and selects the corresponding precomputed view.

Initial profile family:

1. `information-only` — show supported evidence without an avoidance action;
2. existing strict military-specific avoidance semantics;
3. settlement-related avoidance — reacts only to the exact adopted OHCHR settlement-related predicate(s), not ordinary Israel business presence;
4. combined military-specific + settlement-related avoidance.

Profile names shown in UI must make clear that these are user-selectable rule sets, not official WA Commons truth rankings.

A later version may add user-authored policy composition only after parity/reproducibility requirements are separately designed.

## 6. Company identity and page interaction

### Canonical identity

Consequential evidence is attached only through the existing conservative identity layer. Name-only fuzzy matches never become automatic identity facts.

### Search

The primary v0.1 workflow is:

```text
click WA Commons icon
        ↓
search company name / security code
        ↓
show deterministic candidate list from bundled canonical identities
        ↓
user selects company
        ↓
show evidence + coverage + selected policy result
```

### Current-page assistance

The extension may offer an explicit button such as `Use selected text/current page as search hint`.

Rules:

- access happens only after a user gesture;
- use temporary `activeTab` access, not persistent `<all_urls>` access;
- collect only the minimum query hint needed, such as selected text and, where needed, page title/hostname;
- page-derived text is a **query hint only**;
- it cannot directly attach a claim or automatically confirm a legal entity;
- if candidate identity is ambiguous, require user selection;
- do not persist or transmit browsing history.

The manual search flow remains the release-critical fallback on every browser even if a browser-specific page-assistance capability is unavailable.

## 7. Evidence semantics for military / defence

The extension must preserve the existing narrow-claim rule.

Examples:

- Ministry of Defense procurement evidence means a contract relationship was recorded;
- contract-subject classification may distinguish military-specific, dual-use, or ordinary/civilian context only under the existing versioned classifier;
- a MOD contract alone never becomes `weapons company = true`;
- SIPRI-style arms-revenue evidence, if later included, remains an attributed specialist estimate and requires its own public-display rights gate.

User-facing language should prefer factual labels such as:

- `防衛省との契約記録あり`;
- `軍事用途として分類された契約主題あり`;
- `民生/一般調達として分類`;
- `情報不足 / 未統合`.

Inflammatory or universal labels such as `war profiteer`, `bad company`, or equivalent are prohibited.

## 8. Evidence semantics for Israel / occupied Palestinian territory

v0.1 must not implement a broad predicate such as `supports Israel` or `Israel-related = bad`.

The initial public path is limited to evidence whose source and scope are explicitly reviewed and adopted, expected to begin with the existing Source Registry candidate:

`ohchr-settlements-business`

The displayed fact must retain the UN/OHCHR-defined activity scope, source date, status, and entity-resolution state.

Examples of acceptable wording:

- `国連OHCHRの占領地入植関連活動データに掲載`;
- `掲載された活動区分: <source-defined category>`;
- `出典日: <date>`;
- `企業同一性: confirmed / disputed / unresolved`.

Ordinary business presence in Israel, nationality, customer location, or unsourced campaign lists do not satisfy this predicate.

**Release gate:** the OHCHR dataset/page, exact terms, extraction method, public-display/redistribution boundary, update cadence, and identity mapping must move from the current `WATCH → ADOPT after exact review` state to an explicit adopted public-client contract before the v0.1 store release can claim this topic is supported.

If that gate fails, the extension must show the topic as `NOT_INTEGRATED`/unavailable rather than infer absence. Because Israel/OPT support is part of the agreed v0.1 product promise, store release should wait for this gate rather than silently omit it.

## 9. Public Evidence Pack

The extension does not embed raw restricted source files.

A deterministic release-time exporter creates a versioned public JSON pack containing only fields cleared for public redistribution/display.

Minimum conceptual structure:

```text
pack_manifest
  pack_version
  generated_at
  code_commit
  identity_semantic_sha256
  evidence_semantic_sha256
  coverage_semantic_sha256
  policy/profile hashes
  source-registry version/hash
  company_count
  pack_semantic_sha256

companies[]
  entity_id
  canonical_name
  TSE security code
  cleared search aliases
  coverage states by public topic/source
  precomputed policy views
  public-safe evidence cards
```

Every public evidence item preserves:

- narrow predicate/claim;
- source publisher;
- source URL/locator where legally appropriate;
- evidence/source date;
- retrieval/provenance date where appropriate;
- adjudication status;
- confidence/evidence state;
- entity-resolution status;
- policy rule that produced a non-NONE action;
- correction/challenge route.

### Rights gate

The pack exporter must fail closed when a candidate source lacks an explicit public-client rights state.

No raw PDF/CSV rows, restricted excerpts, or source fields marked local-only may be copied into the extension package.

`UNKNOWN`, `NO_MATCH`, `UNRESOLVED_IDENTITY`, `NOT_INTEGRATED`, `DISPUTED`, and `EXPIRED` remain distinct. Missing evidence never becomes clean/safe/PASS.

## 10. Data update strategy

v0.1 bundles the Evidence Pack inside each signed/store-reviewed extension package.

Reasons:

- no always-on WA server;
- no broad network permission;
- no remote-code ambiguity;
- deterministic reproduction of exactly what a user saw for an installed version;
- simpler multi-browser review and incident rollback.

Updating Evidence in v0.1 therefore means creating a new extension release with a new pack version.

A remote signed data-pack update mechanism is deliberately deferred. It may be designed later if release cadence becomes a user problem. Remote executable code remains prohibited.

## 11. Extension implementation shape

Prefer a framework-free WebExtensions client unless implementation evidence proves a framework is necessary.

Proposed repository boundary:

```text
src/wa_commons/...                 canonical Python evidence/policy logic
scripts/...                        release-time evidence-pack exporter
clients/browser-extension/
  common/
    manifest.base.json
    popup.html
    popup.css
    popup.js
    page-hint.js
    data/wa-public-evidence-pack.json
  chrome/
  edge/
  firefox/
  safari/
```

The common client should use standards-based HTML/CSS/JavaScript with no runtime framework and no remotely hosted code.

Browser package generation may use a small existing/Python standard-library script rather than introducing a Node build system solely for packaging.

If implementation inspection shows an adopted repository tool already solves packaging, use it instead.

## 12. Browser permissions

v0.1 targets the smallest practical permission set.

Expected common permissions:

- `storage` — local selected profile/preferences;
- `activeTab` — temporary access only after explicit user action for page hinting;
- `scripting` only if required to retrieve selected text/page hint.

Avoid by default:

- `<all_urls>` persistent host access;
- `tabs` when `activeTab` is sufficient;
- browsing-history APIs;
- cookies;
- webRequest interception;
- clipboard read;
- native messaging;
- background page surveillance.

Permission differences discovered during browser certification must be handled by browser-specific manifest deltas without weakening the common privacy contract.

## 13. Multi-browser strategy

### Chrome

- Manifest V3.
- Chrome Web Store publication.
- Packaged JavaScript only; no remotely hosted executable code.

### Edge

- Reuse Chromium/MV3 implementation.
- Browser-specific manifest/store metadata only where required.
- Microsoft documents Chrome-to-Edge extension compatibility as requiring minimal changes when APIs are supported.

### Firefox

- Reuse WebExtensions implementation.
- Use Firefox-specific manifest metadata only where required for signing/store compatibility.
- Test API differences explicitly rather than assuming Chromium parity.

### Safari

- Reuse the same extension resources through Safari Web Extension packaging.
- Treat App Store packaging/signing as a distribution wrapper, not a fork of product logic.
- Current Apple tooling permits web-based Safari Web Extension packaging through App Store Connect without requiring a Mac/Xcode for that packaging route, while Apple Developer Program/App Store requirements still apply.

### Other Chromium browsers

Brave/Vivaldi/Opera compatibility may be tested opportunistically against the Chromium package, but separate store publication is not a v0.1 release gate unless a later explicit issue adds it.

## 14. Privacy contract

v0.1 is local-first.

The extension must not:

- collect browsing history;
- upload the user's page URL/query/profile choice to a WA Commons server;
- create a user account;
- persist page content;
- scan unrelated tabs;
- perform continuous background page inspection.

The selected policy profile is stored locally in browser extension storage.

The extension may open source URLs when the user chooses to inspect evidence; that navigation is user-directed and not telemetry.

Telemetry is absent in v0.1. Any later telemetry requires a separate explicit privacy design and opt-in review.

## 15. Security and reputational safety

The browser release inherits the project threat model and adds these public-client gates:

- no consequential publication from name-only identity matches;
- no raw allegation count used as a ranking score;
- no inflammatory labels;
- every adverse/avoidance display must identify the exact factual predicate and source;
- disputed/unresolved identity must be visibly distinguished;
- source rights must permit the exact fields shipped in the public pack;
- challenge/correction route must be visible from every company detail view;
- evidence-pack semantic hash must be reproducible from the release build inputs;
- store package must contain no secret/API credential;
- browser permission manifest must be auditable and minimal.

## 16. User interface v0.1

### Popup landing state

- WA Commons name/logo.
- Search box: `企業名・証券コードで検索`.
- Selected policy profile control.
- Optional `選択中の文字から候補を探す` action.
- Evidence Pack version/date indicator.

### Company result

Top area:

- canonical company name;
- TSE security code;
- identity status;
- selected policy result: `EXCLUDE`, `WATCH`, `NONE`, or informational-only state;
- plain warning that `NONE` is not proof of safety/absence.

Topic cards:

- military/defence;
- OHCHR settlement-related activity.

Each topic displays one of:

- confirmed evidence available;
- disputed;
- expired;
- no-match only when the source contract supports that interpretation;
- unresolved identity;
- not integrated / unavailable.

Evidence detail expands to source/provenance, narrow claim, status, and challenge link.

### Search ambiguity

When multiple companies match the query, show candidates and require the user to select. Never silently choose by fuzzy similarity for consequential display.

## 17. Accessibility and language

Japanese is the primary v0.1 UI language.

The implementation must keep strings externalizable so English can be added without rewriting logic. Store listings may initially be Japanese-first, but the extension architecture must not hard-wire Japanese text into evidence semantics.

Minimum accessibility requirements:

- keyboard-operable popup;
- visible focus states;
- semantic labels for controls;
- status not conveyed by color alone;
- readable source/provenance text at common browser zoom levels.

## 18. Release sequence

The implementation plan should stage release capability in this order:

1. preserve and document #85 implementation checkpoint; do not delete it;
2. add the proposed M2.5/Public Extension priority to ROADMAP after this written spec is approved;
3. complete exact rights/source onboarding for public military and OHCHR evidence;
4. generate a rights-cleared 3,707-company public Evidence Pack;
5. implement the common popup/search/evidence UI;
6. add activeTab page-hint path without automatic identity attribution;
7. package and test Chrome;
8. package/test Edge and Firefox from the same common code;
9. package/test Safari from the same common resources;
10. run privacy, identity, evidence, policy parity, source-rights, and cross-browser acceptance gates;
11. publish store packages only after each store's review prerequisites are satisfied.

Store submission itself is an external publication side effect and requires explicit human approval when the package is ready.

## 19. Acceptance criteria

The **capability implementation** is ready for store submission only when all of the following are demonstrated:

1. one common codebase produces installable Chrome, Edge, Firefox, and Safari-target packages/wrappers;
2. manual company search covers the canonical public-pack company set deterministically;
3. a user can inspect military/defence and OHCHR settlement-related topic states for a selected company;
4. all displayed claims come from rights-cleared public-pack fields and retain source/provenance;
5. the selected profile maps to precomputed canonical policy output; no JavaScript shadow policy engine exists;
6. `NONE` cannot be presented as safe/clean/peaceful;
7. ambiguous name matches require user selection;
8. page hints never establish legal identity by themselves;
9. no browsing history/account/telemetry/continuous scanning exists;
10. permission audit confirms no persistent `<all_urls>` requirement for the accepted v0.1 flow;
11. public Evidence Pack is reproducible and hash-pinned;
12. public-source rights checks pass for every shipped evidence field;
13. challenge/correction path is reachable from company results;
14. cross-browser focused tests/smokes pass on the four first-class targets;
15. store metadata truthfully describes coverage limits and evidence freshness.

The **public release** is complete only when at least the Chrome, Edge, Firefox, and Safari store submissions have been made through their normal review channels and accepted/released, or a store-specific external blocker is recorded without falsely claiming publication there.

## 20. Roadmap delta after written-spec approval

Do not rewrite the project's mission or erase M3.

Proposed sequence:

```text
M1 Evidence Graph                    COMPLETE
M2 Explainable company screener      COMPLETE
        ↓
M2.5 Public Browser Extension v0.1   NEW CURRENT PUBLIC-PRODUCT PRIORITY
        ↓
public user utility / correction feedback
        ↓
resume M3 / #85 Historical Replay
        ↓
Peace Capital integration
        ↓
future Peace Router domains
```

`GOALS.md` can continue to name Peace Capital as the first proof vehicle; the browser extension is an earlier public client of the same Evidence/Policy foundation and a direct user-utility test.

Issue #85 remains open/preserved, not cancelled and not declared complete.

## 21. Why this design is preferred

Alternative A: build a standalone web app first.

- simpler deployment but asks users to visit a new destination;
- weaker integration with ordinary browsing;
- user explicitly chose browser extensions instead.

Alternative B: build separate native implementations per browser.

- unnecessary duplicated logic and review burden;
- higher risk of policy/evidence drift between browsers.

**Chosen:** one small WebExtensions client + deterministic bundled Evidence Pack + thin browser packaging.

This maximizes reuse, minimizes permissions and infrastructure, keeps identity/evidence/policy authority in the existing Python pipeline, and creates a genuinely public utility before waiting for the longer investment validation horizon.

## 22. Authoritative references checked for this design

Repository authority:

- `ROADMAP.md`
- `GOALS.md`
- `GOVERNANCE.md`
- `MANIFESTO.md`
- `docs/PRINCIPLES.md`
- `docs/EVIDENCE_MODEL.md`
- `docs/ENTITY_RESOLUTION.md`
- `docs/SOURCE_REGISTRY.md`
- `docs/THREAT_MODEL.md`
- `docs/PURCHASE_ROUTER_PROPOSAL.md`
- `docs/results/M2_2C_EXPLAINABLE_SCREENER_V01.md`
- `src/wa_commons/policy/tse_screening.py`

Browser primary documentation checked 2026-09-11:

- Chrome Extensions — Manifest V3 / permissions / `activeTab`: `https://developer.chrome.com/docs/extensions/`
- Microsoft Edge Extensions — Manifest V3 and Chrome porting: `https://learn.microsoft.com/en-us/microsoft-edge/extensions/`
- Mozilla WebExtensions / manifest compatibility: `https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/`
- Apple Safari Web Extensions and App Store Connect packager: `https://developer.apple.com/documentation/safariservices/safari-web-extensions`

No implementation code was written as part of this design checkpoint.