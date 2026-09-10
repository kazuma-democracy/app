# WA Commons Development Roadmap

This roadmap turns the project goals in [`GOALS.md`](GOALS.md) into an implementation sequence.

WA Commons is **exit-criteria driven**. Dates may be added for planning, but phases are not considered complete because a calendar deadline passed.

## North Star

Build useful, voluntary software where repeated use can create a measurable peace-positive economic or practical signal.

The first proof vehicle is **Experiment 001 — Peace Capital**.

## Current position — 2026-09-10

- **M1 — Reproducible Evidence Graph: COMPLETE.** Measured clean reproduction is recorded in `docs/M1_ACCEPTANCE.md`.
- **M2 — Explainable company screener: COMPLETE.** #42 coverage, #43 deterministic company screening and #44 static explainability report are complete. Measured #44 acceptance is recorded in `docs/results/M2_2C_EXPLAINABLE_SCREENER_V01.md`; `NONE` remains explicitly distinct from PASS/clean/safe.
- **M2.5 — Public Browser Extension v0.1: CURRENT PUBLIC-PRODUCT PRIORITY (#91).** Ship a rights-gated, privacy-minimizing browser client over the existing Evidence / identity / policy stack. The approved first-store scope is military-first: `military_defence` is required, while `ohchr_settlement_related` may remain visibly `NOT_INTEGRATED` until reuse permission is cleared. #85 remains open and resumable; this sequencing change does not rewrite `GOALS.md` or complete M3.
- **M3 - Peace Capital paper portfolio: IN PROGRESS.** The Evidence/identity/screening, benchmark mapping, constructor foundation and zero-cost monthly evaluation contract are complete. Policy Compiler (#84) and reusable monthly market primitives (#56) are complete. Issue #85 leak-safe Historical Replay is **OPEN / PRESERVED / PAUSED FOR PRODUCT SEQUENCING** while #91 is the current public-product priority. The v0.2 investable-proxy capability is implemented, but the preregistered 2026-Q1 window cannot freeze: preselection holdings Market Value/Weight inspection contaminated Q1, and an independent metadata-only audit cannot prove the original 1475 holdings publication time at the three decision cutoffs. No Q1 return was loaded. #51 remains not-current.
- **Phase 5–6 future design:** a Purchase Route Router is preregistered as the first second-domain candidate. The current product strategy is **distribution-first / integration-first**: begin where users already browse or compare products, use thin browser/share/URL handoffs to invoke WA Commons, test books first, then electronics/PC parts, and treat standalone WA product search as an optional later client rather than the MVP acquisition surface. The first public purchasing experiment is also **local-first / serverless-friendly / ship-small**: core routing should not require an always-on WA Commons application server, v0 is affiliate-free, bounded retailer coverage is acceptable when explicit, and the first release should expose documented contribution paths so verified coverage can grow as a commons. See `docs/PURCHASE_ROUTER_PROPOSAL.md`. This is future design only and does not displace current M3 work or waive Phase 5/6 gates.
- **Phase 0 governance cleanup remains open.** #8 ideological-bias red-team and #9 Japanese/English terminology review are still required and are not considered completed by later technical progress.

The project intentionally allows preparatory specification work for a later phase when that work reduces benchmark gaming or implementation ambiguity. This does not waive earlier phase exit criteria or any real-money gate.

---

## Phase 0 — Public foundation

### Purpose
Make the project understandable, challengeable, and contributable before building a large system.

### Deliverables
- [x] Publish README and manifesto.
- [x] Publish governance, security, and contribution principles.
- [x] Publish Experiment 001 scope.
- [x] Open first contribution issues.
- [x] Establish reuse-before-invention policy.
- [ ] Publish short / medium / long-term goals.
- [ ] Audit Japanese/English terminology.
- [ ] Complete first ideological-bias red-team.
- [ ] Establish a lightweight decision-log convention.

### Exit condition
A newcomer can understand the mission, identify what is uncertain, challenge a claim, and make a useful contribution without private onboarding.

### Current issues
- #8 Red-team manifesto/governance.
- #9 Review Japanese/English framing.

---

## Phase 1 — Evidence foundation — COMPLETE

### Purpose
Prove that consequential company classifications can be reproduced from versioned evidence rather than opaque model judgment.

### Workstream 1A — Evidence schema — DONE
- Define minimal evidence object.
- Separate observation, evidence, inference, policy, action, and outcome.
- Support `CONFIRMED`, `DISPUTED`, `UNKNOWN`, `EXPIRED`.
- Preserve correction history rather than silently rewriting it.

**Issue:** #2

### Workstream 1B — Source registry — DONE for M1 bootstrap
- Inventory public/licensed data sources.
- Record publisher, scope, access, cadence, license/terms, identifiers, history, evidentiary strength, and limitations.
- Prefer primary/public sources where possible.
- Adopt / watch / reject each candidate explicitly.

Future sources still require exact license/terms review at onboarding; M1 completion does not imply that every candidate source is cleared for redistribution.

**Issue:** #4

### Workstream 1C — Entity resolution — DONE
- Review existing OSS before writing a matcher.
- Test Japanese company names, aliases, subsidiaries, parent ownership, ticker/legal-name differences, and historical names.
- Choose or adapt the smallest sufficient reusable stack.
- Demonstrate a deterministic 100-company Japanese listed-issuer identity pilot with conservative strong-ID rules.

**Issue:** #3

### Workstream 1D — Threat model — DONE for M1
- Data poisoning.
- Source compromise/disappearance.
- False entity matches.
- Coordinated manipulation.
- Defamation / unsupported accusation risk.
- Model/tool compromise.
- Permission escalation.
- Privacy leakage.
- Benchmark gaming and financial misrepresentation.

**Issue:** #7

### Milestone M1 — Reproducible Evidence Graph — COMPLETE
For a small fixed company universe, material claims can be regenerated from versioned sources and rules with disputes, corrections and expiry visible.

Measured acceptance is recorded in `docs/M1_ACCEPTANCE.md` and the M1 result reports.

### Gate to Phase 2 — PASSED
The evidence foundation exists. This does **not** authorize real-money trading.

---

## Phase 2 — User policy and classification engine — COMPLETE

### Purpose
Let different users apply different peace-related values to a shared evidence layer without creating one official WA Commons moral score.

### Workstream 2A — Policy language — DONE
A small human-readable and machine-readable policy format now covers:
- exclusions vs preferences;
- thresholds;
- `UNKNOWN`, `DISPUTED` and `EXPIRED` handling;
- policy versioning;
- shareable/forkable non-official profiles.

Policy v0.1 intentionally emits `EXCLUDE / WATCH / NONE`; it does not infer `PASS` from missing evidence.

**Issue:** #5 — completed.

### Workstream 2B — Deterministic screening — DONE
The bounded M2 implementation chain is complete:

1. **#42 — M2.2a:** 100-company evidence coverage matrix — completed.
2. **#43 — M2.2b:** same-snapshot user-policy evaluation and deterministic company-level research views — completed.
3. **#44 — M2.2c:** minimal non-developer-readable explainable screener report — completed with measured acceptance in `docs/results/M2_2C_EXPLAINABLE_SCREENER_V01.md`.

The completed implementation preserves these requirements:
- no consequential decision without an explicit rule;
- every non-NONE outcome explains which rule/evidence fired;
- policy and evidence versions are recorded;
- the same inputs reproduce the same result;
- missing coverage does not become clean/safe/PASS;
- LLMs may assist extraction/review but must not become the hidden source of truth.

The current fixed 100-company snapshot is also an explicit negative result: the current M1 canonical graph has no confirmed corporate-number-mapped claim inside the cohort, so the three current example policies all produce `NONE` for all 100 companies. The report exposes `no_match`, `unresolved_identity` and `not_integrated` coverage states rather than turning that absence into a positive moral classification.

### Workstream 2C — Evidence cards — DONE as a reusable component
Evidence Cards expose:
- entity;
- relevant claim;
- source/provenance;
- evidence/retrieval dates;
- status and confidence;
- entity-resolution state;
- correction history;
- policy-layer separation;
- challenge/correction path.

#44 reuses this component in the static 100-company screener instead of creating a second Evidence model.

### Milestone M2 — Explainable company screener — COMPLETE
Exit condition met:
A non-developer can choose a policy and understand the visible decision and evidence state for every company in the fixed 100-company pilot, with at least two meaningfully different profiles evaluated against the same evidence snapshot.

Measured evidence:
- all 100 companies have a human-readable report section;
- all three current example profiles are compared on the same deterministic #43 snapshot;
- visible `NONE` results retain incomplete/unresolved coverage rather than becoming PASS;
- report/Evidence/coverage/screening inputs and outputs are hash-pinned;
- challenge/correction paths are visible;
- no hidden moral/peace/safety score is introduced.

### Gate to full M3 integration — PASSED
#42 → #43 → #44 is complete. M3 work may now consume the completed M2 coverage and policy-screening semantics according to the existing dependency graph. This does **not** authorize real-money trading.

---

## Phase 3 - Peace Capital paper portfolio - IN PROGRESS

### Purpose
Prove that explicit user policy can change capital allocation reproducibly, then measure the financial consequences honestly without return-driven method selection.

### Workstream 3A - Evaluation specification - DONE
The financial evaluation contract was fixed before portfolio results are generated. It defines benchmark preregistration, point-in-time/as-known controls, concentration, return/risk/cost diagnostics, reproducibility and benchmark-gaming safeguards.

**Issue:** #6 - completed. See `docs/PAPER_PORTFOLIO_EVALUATION.md`.

### Workstream 3B - Canonical Japan-equity universe and policy screening - COMPLETE
1. **#46:** canonical domestic TSE Prime/Standard/Growth universe - 3,707 companies.
2. **#53:** conservative identity spine across the 3,707 companies.
3. **#54:** TSE-wide evidence coverage using explicit uncertainty states.
4. **#55:** deterministic policy screening across 3,707 companies x 3 profiles.

The 100-company cohort remains a regression/explainability fixture, not an investment-universe shortcut.

### Workstream 3C - Benchmark selection and mapping - COMPLETE
1. **#45:** TOPIX Total Return Index selected before performance inspection.
2. **#50:** official JPX snapshot effective 2026-07-31 mapped 1,637 / 1,637 onto canonical identities with zero unresolved/disputed/out-of-universe weight.

### Workstream 3D - Constructor foundation - COMPLETE
1. **#47:** OSS/constructor design completed.
2. **#49:** deterministic paper-only `benchmark-l2-projection` constructor implemented and tested.

The existing L2 constructor remains reusable financial-fidelity infrastructure. It is no longer assumed to be the only policy-to-allocation control surface.

### Workstream 3E - Policy Transmission compiler - COMPLETE
**#80:** superseded before implementation because its single minimal-intervention freeze could structurally collapse toward the benchmark.

**#84 - M3.3b2:** completed - Policy Compiler v0 preregisters P0/P1/P2 over the same accepted #50/#55 snapshot. Primary outputs are target weights plus Policy Transmission metrics computed before market returns:
- active share / reallocation mass;
- instruction-affected benchmark weight;
- changed-security count and maximum single-name change;
- unknown/unresolved evidence mass where supported;
- rule-level capital attribution.

P1 may honestly return `POLICY_TRANSMISSION_ZERO`. P2 uses the preregistered `WATCH -> 0.5x` user-policy instruction without treating it as a universal company score.

### Workstream 3F - Free monthly market primitives and leak-safe Historical Replay - BLOCKED / Q1_SELECTION_INTEGRITY_AND_CONTROL_AVAILABILITY
**#78 - M3.3c0:** completed - zero-purchase/monthly/fail-closed source, rights and return contract. October 2026 remains the true future holdout.

**#56 - M3.3c:** completed - reusable month-parameterized JPX price/benchmark-return/corporate-action primitives are validated against official June/July 2026 JPX files with deterministic, fail-closed behavior. Raw source rows remain local-only. See `docs/results/M3_3C_MONTHLY_MARKET_PRIMITIVES_V01.md`.

**#85 - M3.3c0 replay:** BLOCKED / Q1_SELECTION_INTEGRITY_AND_CONTROL_AVAILABILITY - v0.2 adds a dated 1475 investable-control path, cutoff-safe historical identity/evidence reconstruction, pre-return target freeze, residual-sleeve financial calculation and frozen execution. The real 2026-Q1 gate remains closed: Q1 is durably disqualified by preselection Market Value/Weight inspection, and the original 1475 holdings availability time cannot independently be proven at the three decision cutoffs. Returns were not loaded; no alternate month is substituted. See `docs/results/M3_3C0_HISTORICAL_REPLAY_V02.md`.

After the three-month replay is GREEN, extend the identical frozen method to 12 months and optionally 24 months if point-in-time reconstruction remains reproducible and affordable.

### Workstream 3G - Integrated policy-family evaluation - OPEN
**#51 - M3.3d:** combine completed versioned components without introducing new methodology. Policy Transmission is the primary outcome; financial consequences are secondary.

Required output includes:
- preregistered P0/P1/P2 policy family and hashes;
- evidence/screening/benchmark provenance;
- active share / reallocation mass and rule attribution;
- unknown/unresolved evidence mass and concentration/sector effects;
- matching-basis candidate/benchmark returns where available;
- Historical Replay and October 2026 future holdout as distinct result classes;
- blocked periods, negative findings, complete reproduction manifests and output hashes.

### Milestone M3 - Peace Capital v0 - NOT YET COMPLETE
A user can apply an explicit policy to shared Evidence, reproduce the resulting capital allocation, see exactly how much capital the policy moved and why, and inspect the financial consequences without hidden scoring, look-ahead, survivorship shortcuts or return-driven method selection.

### Gate to Phase 4
Demonstrate at least one concrete non-ideological user benefit such as research time saved, easier customization, clearer evidence, lower decision friction, or clearer visibility into the cost of expressing a policy.

---

## Universe expansion strategy

WA Commons expands **universes and evidence sources**, not hand-picked lists of interesting companies.

### Stage U1 — Fixed 100-company engineering cohort — CURRENT REGRESSION FIXTURE

The deterministic 100-company Japanese listed-issuer pilot remains the bounded cohort for M2 integration, regression work and explainability acceptance.

Purpose:
- stable identity regression target;
- coverage semantics;
- policy comparison;
- explainable screener completion.

It is not intended to be a representative hand-curated moral list or a permanent product universe.

### Stage U2 — Canonical TSE domestic company universe — NEXT

After the 100-company contracts are stable, #46 → #53 expands directly to the complete pinned domestic-company universe on TSE Prime, Standard and Growth.

Rules:
- use the official JPX listed-company universe, not maintainer preference or benchmark membership, to choose companies;
- pin the exact source snapshot/date and report the exact resulting company count rather than hard-coding an approximate count;
- preserve unresolved/disputed identities instead of forcing name-only matches;
- keep investment products and TOKYO PRO Market outside canonical v0.1 unless a later explicit scope issue changes that boundary;
- treat the canonical TSE universe as the reusable company-identity base for screening, benchmark mapping and future source adapters.

### Benchmark views — separate from universe expansion

A benchmark is not a coverage stage. #45 selects the benchmark for financial comparison and #50 maps its point-in-time constituents/weights onto canonical TSE identities.

This preserves two independent questions:

```text
Which Japanese listed companies can WA Commons identify and screen?
        -> canonical TSE universe (#46/#53/#54/#55)

What unconstrained portfolio should Peace Capital compare against?
        -> pinned benchmark view (#45/#50)
```

The benchmark may contain roughly hundreds or thousands of securities, but its size does not define the WA Commons company-coverage ceiling.

### Later universe expansion

After the TSE pipeline is stable, expansion can consider other Japanese exchanges/eligible security types and then international listed-company universes. Each expansion requires an explicit universe definition, source/rights review and identity acceptance rather than a hand-picked company list.

### Evidence expansion rule — source-by-source, universe-wide

Evidence should normally expand by adding one reviewed source adapter and applying it across the relevant whole canonical universe, for example:

```text
canonical TSE company universe
        ↓
SIPRI adapter across all eligible entities
        ↓
OECD NCP adapter across all eligible entities
        ↓
UFLPA / other official-list adapter across all eligible entities
        ↓
additional reviewed sources
```

Do **not** build the evidence graph by manually choosing companies because they are famous, controversial or personally interesting. Hand-picking would create selection and scrutiny bias.

For every source:
- preserve the source's narrow factual meaning;
- record coverage and source limitations;
- keep `UNKNOWN` / not-integrated / no-match states distinguishable;
- never translate missing records into innocence or guilt;
- complete licensing/terms review before redistribution/ingestion where required.

---

## Phase 4 — Product utility validation

### Purpose
Test the central adoption hypothesis: people must have a reason to use the product beyond supporting the mission.

### Workstream 4A — Pilot users
Recruit a small pilot group with diverse policy preferences.

Measure:
- time saved versus manual research;
- comprehension of evidence cards;
- correction/dispute rate;
- policy customization usage;
- repeated usage intent;
- portfolio trade-offs users consider acceptable/unacceptable.

### Workstream 4B — Adversarial evaluation
- False-positive hunt.
- False-negative hunt.
- Political/ideological bias review.
- Entity-resolution stress tests.
- Source-license audit.
- Accessibility and UX review.

### Workstream 4C — Publish negative results
If exclusions cause unacceptable concentration, evidence is too weak, or users do not find the tool useful, publish the finding rather than hiding it.

### Milestone M4 — Utility proof
There is evidence that at least one target user group wants the product for a practical reason.

### Kill / pivot rule
If no meaningful user benefit survives honest testing, do not proceed to financial execution. Reuse the Evidence Graph elsewhere or change the experiment.

---

## Phase 5 — Peace Router core

### Purpose
Extract the reusable infrastructure so Peace Capital becomes one client rather than the whole project.

### Core components
- Evidence Graph.
- Entity identity layer.
- User policy language.
- Explainable routing/ranking engine.
- Provenance and audit log.
- Appeals/corrections model.
- Domain adapter interface.

### Architecture target

```text
Sources
   ↓
Evidence + Identity
   ↓
User Policy
   ↓
Peace Router
   ↓
┌────────────┬─────────────┬──────────────┐
│ Investment │ Purchasing  │ Future domain│
└────────────┴─────────────┴──────────────┘
```

### Preregistered adapter test

The first future adapter candidate is the **Purchase Route Router** described in `docs/PURCHASE_ROUTER_PROPOSAL.md`.

Phase 5 must extract a genuinely domain-independent contract that can support both investment decisions and purchase-route decisions without duplicating the evidence/policy/audit stack. The purchasing proposal is therefore a test fixture for the abstraction, not authorization to fork a separate shopping architecture.

The purchasing client should also test two additional abstraction boundaries:

- **distribution surfaces are replaceable clients, not part of the Router core** — browser extensions, share targets, URL handoffs and any future standalone WA search feed the same product-identity handoff and routing contract;
- **deployment is not equivalent to central hosting** — user Policy and deterministic routing should be able to run primarily on the user's device, with versioned public Evidence/rule packs distributed through ordinary open infrastructure where practical.

### Milestone M5 — Domain-independent router
A second domain can reuse the core without duplicating the evidence/policy/audit stack.

---

## Phase 6 — Second economic experiment

### Purpose
Test whether the mechanism generalizes beyond investing.

The second domain is still subject to evidence and utility gates rather than maintainer preference. The **first preregistered candidate** is purchase-route selection using a **distribution-first / integration-first** entry: meet the user on an existing shopping, retailer, publisher, search or comparison surface, accept an explicit item handoff, and compare *where to buy that exact item* using shared organization Evidence plus the user's own Policy.

This is deliberately **not** a requirement to build a new general shopping search engine, marketplace, universal ethical-retailer score, or price-comparison crawler. A standalone WA product search page is an optional later client only if measured demand and source rights justify it.

See `docs/PURCHASE_ROUTER_PROPOSAL.md` for the full product hypothesis and non-goals.

### Selection criteria
1. Direct user benefit exists.
2. Repeated use could create a peace-positive externality.
3. Participation is voluntary.
4. Evidence and rules are auditable.
5. A large share can be built from existing OSS/data.
6. The system can be tested without granting dangerous authority.

If the purchasing candidate fails these criteria in measured use or data/rights feasibility, return to other candidates such as procurement/vendor choice, banking/financial-product comparison, donations or another voluntary economic decision rather than weakening Evidence rules.

### Workstream 6A — Books public Router experiment — PREREGISTERED

First test the routing mechanism on books while borrowing existing discovery behavior instead of asking users to begin shopping inside WA Commons.

The workstream is deliberately staged so the first useful public artifact can ship before broad coverage.

#### 6A0 — Public v0.1 vertical slice

Intended shape:
- user explicitly invokes WA Commons from a supported book page through a share-to-WA action, browser extension/side panel or URL handoff;
- ISBN direct entry remains a deterministic fallback;
- resolve the exact supported book/edition identity conservatively;
- enumerate a small, explicit set of legally/reproducibly discoverable purchase routes;
- keep seller, marketplace/platform and fulfillment actors distinct;
- resolve route organizations to WA Commons legal entities only where existing strong-ID rules support the match;
- apply user-owned Policy and explain which Evidence/rules fired;
- send the user to the external retailer to complete the purchase;
- do not require a first-party WA title-search catalog, user account or always-on WA Commons application server for core routing.

Version 0 is **affiliate-free** and has no checkout, payment credentials or autonomous ordering.

The public v0.1 gate is intentionally small. It is enough if:
1. a real user can resolve a supported book and open at least one alternative purchase route;
2. another person can reproduce the documented route from public code/data without private infrastructure or private onboarding;
3. an external contributor can add or propose one reviewed bookstore/route contribution through a documented path.

Bounded coverage must be stated as bounded coverage; v0.1 must not imply a complete market scan.

#### 6A1 — Books integration expansion

After the public vertical slice is usable and reproducible, expand supported entry surfaces, reviewed retailers, Evidence coverage and contributor tooling without changing the core routing semantics merely to increase breadth.

Before implementation, a dedicated source/terms/integration task must verify ISBN metadata, the minimum page/URL identity context that may be used from each candidate discovery surface, browser-extension or share-target constraints, retailer discovery/deep-link paths, deterministic route-link generation where applicable, availability/price reuse rights, caching limits and any pricing assumptions. A browser extension is not a loophole around a site's current terms. Brainstorming claims are not source-registry adoption decisions.

Mechanism evaluation should measure exact identity quality by entry surface, invocation-to-result friction, alternative-route coverage, entity-resolution coverage, user route-opening/route-change behavior, repeat utility, clean-install reproducibility, external-contributor extensibility and uncertainty/dispute states. Ideological-filter usage is not the primary success metric.

### Workstream 6B — Electronics and PC-parts extension — PREREGISTERED AFTER 6A

Only after the Books mechanism demonstrates useful routing behavior, extend the same integration-first pattern to electronics and PC parts.

Additional requirements:
- use exact JAN/GTIN/model identifiers where possible;
- do not merge bundles, revisions, capacities, colors, regional versions or parallel-import variants by title similarity alone;
- treat price, stock, shipping and delivery information as timestamped observations with source/freshness, not stable company Evidence;
- never claim global cheapest/best routing beyond actual coverage;
- where data supports it, expose the observed cost difference between an unconstrained route and a user-policy-compatible route.

This stage is where retailers such as electronics specialists, marketplaces, manufacturer-direct stores and independent sellers may become comparable routes, but their inclusion depends on source rights and exact entity Evidence rather than a hand-picked preferred-store list.

### Purchasing experiment guardrails

- no universal WA Commons retailer morality or "Japan contribution" score;
- no assumption that a Japanese seller/platform proves domestic manufacture or domestic value added;
- missing retailer/parent/fulfillment Evidence remains `UNKNOWN`/unresolved rather than favorable or unfavorable;
- no affiliate commissions in v0;
- no autonomous purchase or payment authority;
- no broad browsing-history collection; integration clients inspect only the page/item the user explicitly invokes and request minimum necessary permissions;
- local Policy/preferences stay on-device by default and core v0.1 routing does not require a central account;
- source and retailer terms/licensing must be reviewed before page-context extraction, ingestion, caching or redistribution;
- public data/rule packs must be versioned and verifiable if used for client-side updates;
- do not embed protected server-side API secrets in public clients;
- do not build a first-party product catalog or central proxy merely to compensate for a failed integration path;
- do not postpone the first public release merely to chase broad retailer coverage when a bounded, honest vertical slice can prove the mechanism;
- community growth must add verified Evidence/routes through reviewable contribution paths rather than unreviewed judgments;
- the current M3 issue order remains authoritative until those gates are complete.

### Milestone M6 — Two-domain proof
The same Peace Router core serves two different decision domains, and the second-domain experiment demonstrates direct user utility without duplicating the Evidence/Policy/audit stack, depending on one proprietary shopping surface, or requiring private central infrastructure for the core public mechanism.

---

## Phase 7 — Bounded autonomous maintenance

### Purpose
Add the agent capability that motivated WA Commons: persistence without broad authority.

### Agent jobs
- scheduled source re-checking;
- change detection;
- evidence expiry;
- revalidation;
- reopening unresolved evidence;
- detecting broken data sources;
- proposing entity merges/splits;
- preparing human review packets;
- applying reversible low-risk updates where explicitly authorized.

### Required guardrails
- least privilege;
- explicit action authority;
- rate limits;
- audit logs;
- reversible defaults;
- human approval for consequential financial/legal/political actions;
- no covert persuasion or impersonation.

### Milestone M7 — Relentless but weak agent
The system can maintain its evidence layer for an extended period with low human effort while remaining bounded and auditable.

---

## Phase 8 — Internationalization and ecosystem

### Purpose
Make the infrastructure usable beyond one country's politics, datasets, and assumptions.

### Workstreams
- multilingual documentation and UI;
- country/domain source adapters;
- local policy profiles;
- portable schemas and APIs;
- community-maintained data connectors;
- governance for disputes across jurisdictions;
- independent downstream implementations.

### Milestone M8 — Forkable commons
At least one independent group can operate or fork a compatible implementation without founder involvement.

---

## Phase 9 — Long-horizon peace infrastructure

This phase is intentionally exploratory. Candidates include:
- additional Peace Router domains;
- public-interest maintenance agents;
- commitment/evidence/resource/authority graphs;
- narrow ephemeral institutions with explicit budgets, permissions, expiry, and shutdown rules;
- interoperability standards for evidence, policy, audit, and agent authority.

The project should only enter these areas when earlier phases demonstrate user utility, safety, and governance capacity.

---

# Dependency order

```text
Phase 0 governance cleanup (#8, #9 remain open)

M1 Evidence foundation - COMPLETE
        ->
M2 Explainable screener - COMPLETE

M3 evaluation specification (#6) - COMPLETE

Canonical TSE path:
#46 -> #53 -> #54 -> #55 - COMPLETE

Financial foundation:
#45 -> #47 -> #49 - COMPLETE
  -> #50 benchmark mapping - COMPLETE
  -> #78 zero-cost monthly evaluation contract - COMPLETE

#49 + #50 + #55 + #78
        ->
#84 Policy Compiler v0 + current-snapshot Policy Transmission proof - COMPLETE
        ->
#56 reusable free-monthly market-return/corporate-action primitives - COMPLETE
        ->
#85 leak-safe three-month Historical Replay - BLOCKED / Q1_SELECTION_INTEGRITY_AND_CONTROL_AVAILABILITY
        ->
#51 integrated policy-family evaluation
        ->
M3 COMPLETE

2026-10 future holdout remains separate from Historical Replay and uses the same preregistered method after its data becomes available.
        ->
Phase 4 Utility validation -> Phase 5 Peace Router core -> Phase 6 second-domain experiment
        ->
Phase 7 bounded autonomous maintenance -> Phase 8 international ecosystem -> Phase 9 long-horizon infrastructure
```

## Agent-sized task contract

Roadmap phases and workstreams are **planning umbrellas, not worker assignments**. A strong autonomous coding/research model such as Claude Sonnet-class or GPT Luna MAX-class should receive one exact GitHub Issue at a time.

An Issue is ready for autonomous assignment only when all of these are true:

1. **One durable outcome:** one primary artifact, decision record, component or integration result can be reviewed independently.
2. **Durable prerequisites:** every required predecessor is complete and versioned; the worker is not asked to invent missing upstream contracts.
3. **One dominant uncertainty/failure family:** research selection, source licensing, parsing/ingestion, algorithm design, implementation and end-to-end acceptance are split when they can fail independently.
4. **Explicit inputs and outputs:** the Issue names which prior artifacts/contracts it consumes and what the next task may rely on.
5. **Finite Definition of Done:** completion is observable through hashes, counts, invariants, targeted tests, a decision table or another reproducible acceptance result.
6. **Stop/block conditions:** the worker knows when to stop rather than silently substituting data, weakening identity rules, expanding scope or redesigning methodology.
7. **Out-of-scope boundary:** adjacent discoveries become separate issues; they do not authorize opportunistic framework work.
8. **Proportional verification:** verification targets the changed claims/failure modes; broad suites are reserved for shared-core or milestone gates.
9. **Context-fit:** the task can be understood from the exact Issue, directly referenced contracts and the smallest relevant source/tests without loading the entire repository history.
10. **Durable handoff:** if a run cannot finish safely, it leaves `COMPLETED / OBSERVED / RULED_OUT / NEXT_ACTION / DEFERRED` evidence and a bounded Git checkpoint.

If an Issue fails this checklist, split or respec it **before** handing it to an autonomous worker. Do not compensate for an oversized task by giving the model a giant prompt or repeatedly relaunching it.

## Task-granularity audit - 2026-09-09

Current near-term M3 state:

- **#42 / #43 / #44 - COMPLETE:** M2 coverage, deterministic screening and explainability are merged.
- **#45 / #46 / #47 / #49 / #50 / #53 / #54 / #55 / #78 - COMPLETE:** M3 universe, identity, evidence, screening, benchmark, constructor foundation and zero-cost monthly evaluation contract are durable prerequisites.
- **#80 - SUPERSEDED / NOT PLANNED:** old single-portfolio freeze must not be implemented.
- **#84 - COMPLETE:** Policy Compiler v0 + current-snapshot Policy Transmission proof is merged and verified.
- **#56 - COMPLETE:** reusable month-parameterized free JPX market-return/corporate-action primitives are validated and ready for #85 consumption.
- **#85 - BLOCKED / POINT_IN_TIME_DATA_COVERAGE:** metadata-only qualification/freeze and leak-safe execution are implemented; the real replay remains blocked until three consecutive cutoff-valid point-in-time benchmark + screening/evidence snapshots exist under the adopted source contract.
- **#51 - READY only after #85 and other completed prerequisites:** pure integrated policy-family evaluation; methodology changes remain blockers.

Phases 4-9 are **not yet worker-ready as whole tasks**. `docs/PURCHASE_ROUTER_PROPOSAL.md` remains preregistered future design rather than current execution authority.

## Task-splitting discipline

To keep work bounded and failures local:

- one issue should have one clear artifact or integration goal;
- research/selection, implementation, data ingestion and end-to-end acceptance should remain separate when they can fail independently;
- later issues must consume completed, versioned outputs rather than silently redesigning earlier methodology;
- if an issue grows beyond its stated scope, split it instead of broadening acceptance criteria;
- each implementation issue should have targeted tests and exact changed-file review before merge;
- scaling row count alone does not require an artificial intermediate universe when the same deterministic pipeline can run over a complete source-defined universe.

## Hard gates

WA Commons should **not**:
- add real-money autonomous trading before evidence, reproducibility, threat modeling, user-utility validation, financial/legal review, credential architecture, risk controls and explicit governance approval;
- generalize into many domains before Experiment 001 teaches us what the reusable core actually is;
- treat the preregistered Purchase Route Router proposal as authority to bypass Phase 5 or the measured Phase 6 selection/utility gate;
- build custom infrastructure before an OSS reuse review;
- build a central purchasing backend merely because local/static distribution looks less conventional;
- delay a bounded honest public v0.1 solely to chase comprehensive retailer coverage;
- hide disputed evidence to make the product look cleaner;
- treat missing evidence as PASS/clean/safe;
- choose companies manually because they look controversial when a universe-level selection rule is available;
- insert an arbitrary intermediate company universe merely to reduce row count when the canonical source-defined universe is tractable;
- choose or replace a benchmark after observing performance to improve headline results;
- grant agents broad authority merely because the software is technically capable of it.

## Immediate next work

M2 is complete. The shortest M3 path is now explicit:

1. **#85 - three-month Historical Replay — BLOCKED / POINT_IN_TIME_DATA_COVERAGE:** capability is implemented; unblock only when three consecutive completed months have reproducible point-in-time benchmark, cutoff-complete screening/evidence, identity, and monthly source metadata. Then freeze before loading returns.
2. **12-24 month extension:** only after the three-month path is reproducible and leak-safe; extension length is not selected from observed performance.
3. **2026-10 future holdout:** preserve October as a distinct prospective test and do not use its results to tune the compiler/replay method.
4. **#51 - integrated policy-family evaluation:** report Policy Transmission first and financial consequences second, with blocked and unfavorable results preserved.

The historical M1.1 JPX retrieval URL observed returning 404 during #44 acceptance remains a separately scoped maintenance concern and does not modify this M3 sequence.

The Purchase Route Router remains **future preregistered design only** until the relevant Phase 5/6 gates are reached.
