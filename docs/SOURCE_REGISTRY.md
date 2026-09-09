# Peace Capital Source Registry v0.1

Status: **bootstrap registry for M1**  
Related issue: #4

This registry distinguishes **publisher authority**, **evidentiary scope**, and **reuse rights**. A public webpage is not automatically open-licensed for bulk redistribution.

Statuses:

- **ADOPT** — suitable for initial integration, subject to the listed constraints.
- **WATCH** — useful but needs licensing, extraction, coverage, or methodology review before integration.
- **REJECT-AS-PRIMARY** — may help discovery, but should not be the authoritative evidence source.

## Registry

| ID | Source | Publisher | Scope | Access / cadence | Entity identifiers | Evidentiary strength | License / terms | Decision | Main limitation |
|---|---|---|---|---|---|---|---|---|---|
| `jp-jpx-listed` | JPX listed-company information / listed company data | Japan Exchange Group | Japanese listed issuer identity, market, ticker and listing metadata | Web/CSV; periodic updates | ticker, market, company name | High for listing identity | **Review required** before redistribution | **ADOPT** | Not a corporate-group/ownership registry |
| `jp-nta-corporate-number` | Corporate Number Publication Site | National Tax Agency, Japan | Japanese legal-entity identity and corporate number | Web/download/API-like published data; updates as registry changes | corporate number, name, address | Very high for Japanese legal identity | **Review required**; record source terms before mirroring | **ADOPT** | Does not establish listed-security identity or beneficial ownership by itself |
| `gleif-lei` | LEI Reference Data / Golden Copy | GLEIF | Global legal-entity identity and LEI reference data | Bulk files/API; regularly refreshed | LEI, legal name, addresses, registration authority IDs | Very high for entities with LEIs | Open-data terms are favorable; pin exact dataset terms/version in implementation | **ADOPT** | LEI coverage is not universal, especially for smaller private entities |
| `blackrock-ishares-1475-holdings` | iShares Core TOPIX ETF (1475) dated holdings | BlackRock Japan | Dated ETF holdings used only as an investable control allocation for Historical Replay | Official web/CSV; low-frequency manual retrieval of pinned dates | TSE ticker/security code | High for the ETF's own disclosed holdings, not evidence of issuer conduct | **Review required**; retain raw source locally only until local-research retention/reuse terms are affirmatively checked | **WATCH** | Not official TOPIX constituent weights; unresolved rights must emit `BLOCK_SOURCE_RIGHTS` and raw rows must not be redistributed |
| `jp-edinet` | EDINET filings / EDINET API | Financial Services Agency, Japan | Securities filings, annual reports, issuer disclosures | API + filing documents; event-driven | EDINET code, filer metadata, securities codes where available | Very high for filed disclosures | **Review required** for bulk storage/redistribution | **ADOPT** | Filed company statements may require interpretation; not every field is normalized |
| `jp-mod-procurement` | Procurement / contract information | Japan Ministry of Defense and agencies | Awarded procurement and contract records | Web/PDF/CSV depending agency/year; recurring | supplier names, contract metadata | High for the narrow fact of a government contract | **Review required** | **ADOPT** | **A contract with MOD does not imply weapons activity.** Civilian food, cleaning, office, logistics etc. may appear; contract subject must be classified separately |
| `sipri-arms-industry` | SIPRI Arms Industry Database | Stockholm International Peace Research Institute | Arms-producing and military-services companies; arms revenue estimates | Interactive/Excel; annual/revised data | company names; financial data | High-quality specialist secondary research | Terms/user rules must be recorded; **review required for redistribution/commercial use** | **ADOPT as specialist evidence** | Arms revenue can be estimated; company comparability and coverage are limited; not a primary filing |
| `sipri-arms-transfers` | SIPRI Arms Transfers Database | SIPRI | International transfers of major conventional arms | Database; periodically updated | supplier/recipient country and systems; company identity may be indirect | Strong for transfer context | **Review required** | **WATCH** | Not primarily a company-level issuer dataset; linking firms to transfers may require additional evidence |
| `jp-political-finance` | Political funds income/expenditure reports | Ministry of Internal Affairs and Communications and relevant election authorities | Reported Japanese political donations and political-fund transactions | Published reports; annual/event-based | donor/recipient names, addresses, amounts in filings | Very high for the disclosed transaction | **Review required** for automated extraction and redistribution | **ADOPT** | Entity names can be ambiguous; transaction does not imply endorsement of all recipient positions |
| `us-uflpa-entity-list` | UFLPA Entity List | U.S. Department of Homeland Security / U.S. Government | Entities officially listed under UFLPA enforcement framework | Official web/list; updated when designations change | company/entity names and list categories | Very high for the fact of official listing | U.S. government-source reuse generally favorable, but record exact page terms | **ADOPT** | A listing is a legal/regulatory fact; downstream ethical meaning remains user policy |
| `us-dol-forced-child-goods` | List of Goods Produced by Child Labor or Forced Labor | U.S. Department of Labor ILAB | Country × product risk evidence for forced/child labor | Official report/data; periodic | primarily country/product, not company ID | High for sector/geography risk context | Record exact dataset/report terms | **ADOPT as contextual risk evidence** | **Do not attribute a country/product risk directly to a company without supply-chain evidence** |
| `oecd-ncp-cases` | National Contact Point specific-instance database / case information | OECD and NCP network | Responsible-business-conduct complaints/cases and outcomes | Database/case records; ongoing | company/organization names, countries, case status | High for the fact a case was filed/handled; outcome-specific strength varies | **Review required** | **ADOPT** | A submitted case is not the same as a proven violation; encode procedural status precisely |
| `ohchr-settlements-business` | OHCHR database/update on business enterprises involved in listed settlement-related activities | UN Human Rights Office | Named business enterprises associated with specified activities related to Israeli settlements in the occupied Palestinian territory | UN reports/updates; periodic rather than continuous | company names and described activity categories | High intergovernmental-source evidence for inclusion in the published database | **Review required** for redistribution and update mechanics | **WATCH → ADOPT after exact current dataset/terms pinning** | Scope is legally/politically specific; must encode the UN-defined activity, date and source rather than a vague “pro/anti” label |
| `sec-companyfacts` | SEC EDGAR / Companyfacts APIs | U.S. Securities and Exchange Commission | U.S. issuer filings and structured financial facts | API; filing-driven | CIK, ticker mapping, filing identifiers | Very high for filed U.S. issuer facts | U.S. government data; record API fair-access requirements | **ADOPT for U.S. expansion** | U.S.-centric; not directly a peace-risk source |
| `company-primary-disclosures` | Annual reports, securities reports, contract announcements, sustainability/human-rights reports | The company itself | Company statements on revenue segments, contracts, policies, supply chains, political spending where disclosed | Company websites/filings; event/annual | issuer/company IDs vary | High for what the company states; medium for contested external claims | Source-specific copyright/terms | **ADOPT** | Self-reporting bias; should be cross-checked when the claim is contested |
| `opensanctions-data` | OpenSanctions datasets | OpenSanctions | Sanctions, PEPs, debarments and related entity graph | Bulk/API; frequent updates | FollowTheMoney entity IDs + many source IDs | Strong aggregator with provenance to many source datasets | Data is **CC BY-NC 4.0 for non-commercial bulk use**; business use needs licensing; software is separately MIT | **WATCH** | Dataset license could constrain future commercial/user-benefit services; prefer source-level ingestion where feasible |

## Source-quality rules

### 1. Narrow claim rule

A source supports only the claim it actually establishes.

Examples:

- MOD contract record → `company received contract X`.
- SIPRI arms revenue → `SIPRI estimates/reports arms revenue Y under its methodology`.
- OECD NCP case → `a specific instance was submitted/handled with status Z`.
- UFLPA list → `entity is officially listed under category Z`.

None of these facts automatically means `EXCLUDE`. Exclusion is a **user-policy decision**.

### 2. Allegation vs finding

Store distinct predicates for:

- allegation/complaint filed;
- investigation opened;
- official listing/designation;
- settlement/mediation outcome;
- judicial/administrative finding;
- company acknowledgment;
- third-party estimate.

Never collapse them into a generic `human_rights_violation=true` field.

### 3. Source hierarchy

Default preference order for narrow factual claims:

1. official registry / filing / contract / court or administrative record;
2. intergovernmental source with clear methodology;
3. company primary disclosure;
4. peer-reviewed/specialist research;
5. reputable civil-society research with transparent methodology;
6. reputable secondary reporting;
7. discovery-only sources.

This hierarchy is not absolute: a company disclosure is not automatically stronger than an independent source for a contested external impact.

### 4. Rights and storage

For every integrated source, implementation must record:

- URL and publisher;
- terms/license URL;
- retrieval method;
- whether raw content can be stored;
- whether extracted facts can be redistributed;
- attribution requirement;
- commercial-use restriction;
- API rate/fair-access rules;
- retention/update requirements.

If rights are unclear, store a locator/hash/derived normalized fact only where legally appropriate, and mark `license_status=review_required`.

## First integration order

1. `jp-jpx-listed` + `jp-nta-corporate-number` + `gleif-lei` — identity spine.
2. `jp-edinet` — issuer disclosures and additional identifiers.
3. `jp-mod-procurement` — first military-contract evidence adapter.
4. `jp-political-finance` — first political-finance adapter.
5. `sipri-arms-industry` — specialist comparison/arms-revenue evidence.
6. `us-uflpa-entity-list` / `oecd-ncp-cases` — human-rights/regulatory evidence pilots.
7. Additional sources only after evidence semantics and correction workflow are proven.

## Sources explicitly not sufficient on their own

- search-engine snippets;
- social-media posts;
- anonymous lists;
- unsourced activist or corporate blacklists;
- LLM-generated classifications;
- a company name appearing in an article without primary/source verification.

These may generate research leads, but must never directly trigger a consequential WA Commons classification.
