# M2.5 Public Browser Extension v0.1 — capability result

Status: **CAPABILITY_READY — local capability verification complete**
Issue: #91
Measured capability code HEAD: `de42d5265c1b0b279329d0065785ef48d81c35c3`
Measurement generated at: `2026-09-10T20:30:53Z`

## Scope

This result measures the first WA Commons public browser-extension capability before any store submission.

The client is evidence-first and user-policy-driven. It does not assign a universal company morality, peace, boycott, or risk score. It does not perform trading, portfolio advice, background browsing-history collection, or automatic company identity confirmation from page text.

The measured package is built from the already-pinned local #53/#54 Ministry of Defense research path plus current public-client rights rules. No OHCHR company rows were ingested, parsed, or distributed.

## Canonical identity and public search projection

- Canonical TSE domestic-company universe: **3,707**
- Confirmed corporate-number identities in canonical #53 artifact: **3,699**
- Canonical unresolved identities retained: **8**
- Public searchable company identities: **3,699**
- Public unresolved identities retained: **8**
- NTA target corporate numbers: **3,699**
- NTA matched rows: **3,699**
- EDINET source rows read locally: **11,389**
- Public identity semantic SHA-256: `febbc732eed50d59490eca34a62659ab2614ebc4da4390c1231ce62466faf100`

One real duplicate-corporate-number EDINET case was encountered during capability measurement. It is resolved only because the canonical #53 identity already contains exactly one confirmed EDINET code and exactly one duplicate row matches that strong identifier. Name-only rescue matching remains forbidden.

## Evidence and coverage

- Canonical #54 coverage cells: **18,535**
- Canonical #54 coverage semantic SHA-256: `ccc77af755a6022031d5aca6bc8fbd1f53b7136eb460c0fd69d17e07263f0941`
- Public Evidence rows in the measured pack: **20**
- Source Evidence semantic SHA-256: `f165939ba1b784e5dc9c8f8a16a51762b4609395b3ec7cf6db9a015ada5b1f60`
- Source-rights contract SHA-256: `958e921b14bfdb81adf1351471d07b0c1c9d51ced235945eba3bf238456d75d1`

The public MOD projection is deliberately narrower than the canonical internal claim. Contract amounts, published supplier-name fields, corporate-number fields embedded inside a claim value, raw document text, and JPX security identifiers are not serialized into the public Evidence payload. Only explicitly rights-cleared narrow fields such as contract subject and contract-subject classification survive the public projection.


## Public policy measurement

Four versioned public profiles were evaluated with the existing canonical Python evaluator after a public-client-only relevance scope filter. The scope filter prevents uncertainty from an unrelated topic from affecting a profile that has no rule for that topic.

| Profile | EXCLUDE | WATCH | NONE |
| --- | ---: | ---: | ---: |
| `public:information-only:v1` | 0 | 0 | 3,707 |
| `public:strict-military-specific:v1` | 0 | 7 | 3,700 |
| `public:ohchr-settlement-avoidance:v1` | 0 | 0 | 3,707 |
| `public:military-and-settlement:v1` | 0 | 7 | 3,700 |

- Public screening views: **14,828** (`3,707 × 4`)
- Public screening semantic SHA-256: `c6fec3bbae59a267f5da478865fc1bcc5703428c58ec1ef78115bd255b19c35b`
- Current real MOD snapshot contains no measured `MILITARY_SPECIFIC` TSE-linked classification, so no public profile emits EXCLUDE from this snapshot.
- `NONE` is not PASS, clean, safe, peaceful, approved, or proof that relevant conduct does not exist.

The information-only profile intentionally has no consequential rule. The OHCHR-only profile cannot infer absence while its source is not integrated.

## Topic states

- Military / defence: **AVAILABLE**
  - Source: `jp-mod-procurement`
  - Company-level state still distinguishes observed / no-match / unresolved; no-match is not a clean-company judgment.
- Israel/OPT settlement-related topic: **NOT_INTEGRATED**
  - Source: `ohchr-settlements-business`
  - Reason: `BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED`

Capability: **CAPABILITY_READY**

Public release: **BLOCKED**
Blocker: **BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED / ohchr-settlements-business**
Israel/OPT topic: NOT_INTEGRATED

This report does not claim that no relevant OHCHR evidence exists for any company.

## Public Evidence Pack measurement

- Pack version: `wa-public-evidence-pack-v0.1`
- Pack state: `READY_FOR_CAPABILITY_TEST`
- Companies: **3,699**
- Evidence rows: **20**
- Pack semantic SHA-256: `730d954a2ccd70c18cc4b0bf8534dc227951987ab7ab1dfe1826c4f6e1cbf5bf`
- Measured local JSON size: **8,700,031 bytes**

The real measured pack remains a generated release input, not a committed source mirror. Restricted raw/local artifacts remain outside the repository.

## Four-target packaging

All packages use only:

- `storage`
- `activeTab`
- `scripting`

There are no persistent host permissions and no `<all_urls>` permission.

Measured package SHA-256 values from the same real pack:

| Target | SHA-256 | Certification |
| --- | --- | --- |
| Chrome | `11acb809c8557e21b9d16f9c0b1cf58df66b222c511401260a91d5c4f92b1762` | package generated; manual/store validation not yet performed |
| Edge | `11acb809c8557e21b9d16f9c0b1cf58df66b222c511401260a91d5c4f92b1762` | package generated; manual/store validation not yet performed |
| Firefox | `12c9e889b8d3ecc11b114481c1c8b79fb8bf5e57f9fb283b032358fa03849072` | package generated; manual/AMO validation not yet performed |
| Safari | `11acb809c8557e21b9d16f9c0b1cf58df66b222c511401260a91d5c4f92b1762` | resource package generated; Safari/App Store/TestFlight validation not yet performed |

Chrome, Edge and Safari are byte-identical at this resource-package layer because their current manifest overlays are empty. Firefox differs only by its Firefox-specific manifest settings.

## Privacy and execution boundary

v0.1:

- sends no browsing history or page text to a WA Commons server;
- has no telemetry;
- has no account requirement;
- has no central always-on application server;
- reads selected page text/title only after an explicit user action;
- limits that page hint to 256 characters;
- does not use hostname as identity authority;
- does not auto-confirm a company from a page hint;
- contains no remote executable JavaScript;
- stores only the selected local policy profile.

## Final verification

Fresh local verification on the #91 working tree:

- #91 Python focused set: **50 passed**
- dependency-free Node search tests: **3 passed**
- final repository suite: **379 passed**
- `git diff --check`: **clean** at the focused-test gate

The full suite was run once after the Task 9 capability files were present. This verifies the local capability tree; GitHub PR-head CI remains a separate remote gate.

## Public release state

**Not released.**

Store submission is a separate external side effect and requires explicit human approval. Current project configuration also requires all configured public topics to be ready; therefore the unresolved OHCHR public-reuse permission blocks store release under the current #91 scope.

No Chrome Web Store, Microsoft Edge Add-ons, addons.mozilla.org, or Apple App Store submission has been performed by this result.
