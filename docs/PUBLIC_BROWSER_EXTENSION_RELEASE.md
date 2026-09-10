# WA Commons Public Browser Extension v0.1 — release runbook

Issue: #91

This runbook separates **capability validation** from **store publication**. CI and package generation do not publish anything.

Current release blocker:

`BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED / ohchr-settlements-business`

Under `configs/m2-5-public-browser-extension-v0.1.json`, all configured public topics must be ready before public release. Therefore store submission remains blocked until the OHCHR reuse state changes through reviewed evidence, or a separately approved scope change removes that topic from the release requirement.

Before any store action below, perform a **fresh official store-policy check** and record the date and relevant requirement. Do not rely on this document as permanent store-policy authority.

## Common preflight

Before manual browser certification:

1. Confirm the branch/PR HEAD and Issue #91.
2. Confirm the Public Evidence Pack validates and records its semantic SHA-256.
3. Confirm source-rights state and that blocked-source rows are absent.
4. Confirm permissions are exactly the reviewed minimal set: `storage`, `activeTab`, `scripting`.
5. Confirm no persistent host permissions or `<all_urls>`.
6. Confirm no remote executable code, telemetry endpoint, credentials, signing key, or restricted raw source rows are inside the package.
7. Confirm `NONE` remains visibly described as not PASS/clean/safe.
8. Confirm manual search is the identity-critical path and page hints only produce candidates.
9. Record package SHA-256 before loading or uploading it.
10. Do not submit while the current project-level release blocker remains active.

## Chrome

**HUMAN APPROVAL REQUIRED**

Manual capability certification:

1. Build the Chrome target from the validated Public Evidence Pack.
2. Load the unpacked Chrome extension from the generated `chrome/extension` directory.
3. Search by an exact securities code and verify one deterministic candidate.
4. Search an ambiguous company-name fragment and verify that candidate selection is required.
5. Open one company with Evidence and verify:
   - source/provenance is visible;
   - policy result is precomputed;
   - `NONE` warning is visible when applicable;
   - blocked OHCHR topic displays `NOT_INTEGRATED`;
   - correction/challenge link is present.
6. Test the page-hint button:
   - it runs only after the click;
   - selected text takes precedence over title;
   - the result is still only a search candidate;
   - no page history is transmitted or persisted.
7. Re-check current official Chrome Web Store policies, Manifest V3 requirements, privacy disclosure, listing requirements, and developer-account requirements.
8. Record the validation result and package SHA.

Store action:

- **Do not submit without explicit human approval.**
- Under the current #91 configuration, do not submit while the OHCHR public-reuse blocker is active.
- Once both gates are satisfied, upload the reviewed ZIP to **Chrome Web Store** and record submission/review/release state separately from code capability.

## Edge

**HUMAN APPROVAL REQUIRED**

Manual capability certification:

1. Build the Edge target from the same validated Public Evidence Pack.
2. Load the unpacked Edge extension and repeat the Chrome behavioral checks.
3. Confirm the Edge package uses the same common search, popup, Evidence, and page-hint files.
4. Confirm there is no Edge-only identity, Evidence, or policy logic.
5. Re-check current official Microsoft extension policies, permissions/privacy declarations, package validation, and listing requirements.
6. Record the validation result and package SHA.

Store action:

- **Do not submit without explicit human approval.**
- Under the current #91 configuration, do not submit while the OHCHR public-reuse blocker is active.
- Once both gates are satisfied, upload the reviewed package to **Microsoft Edge Add-ons** and record the external review state.

## Firefox

**HUMAN APPROVAL REQUIRED**

Manual capability certification:

1. Build the Firefox target from the same validated Public Evidence Pack.
2. Inspect `manifest.json` and confirm the reviewed Firefox-specific `browser_specific_settings.gecko` values.
3. Temporarily install/load the extension in Firefox and repeat the same search, ambiguity, Evidence, NONE-warning, topic-state, challenge-link, and page-hint checks.
4. Confirm Firefox-specific packaging did not fork business logic.
5. Perform a fresh official addons.mozilla.org/AMO validation-policy check, including current signing and data-collection manifest requirements.
6. Run AMO validation or its current equivalent at the manual certification gate.
7. Record validation result and package SHA.

Store action:

- **Do not submit or sign for publication without explicit human approval.**
- Under the current #91 configuration, do not submit while the OHCHR public-reuse blocker is active.
- Once both gates are satisfied, submit through **addons.mozilla.org** and record signing/review/release state.

## Safari

**HUMAN APPROVAL REQUIRED**

Manual capability certification:

1. Use the Safari resource package generated from the same common extension resources and validated Public Evidence Pack.
2. Perform a fresh official Apple Safari Web Extension packaging/distribution check.
3. Use the current supported Safari Web Extension packaging path:
   - App Store Connect Safari Web Extension Packager when applicable; or
   - the current Apple `safari-web-extension-packager`/Xcode path when applicable.
4. Confirm no Safari wrapper introduces alternate identity, Evidence, policy, telemetry, or network behavior.
5. Test the extension behavior in Safari.
6. Test the packaged app/extension through **TestFlight** when required by the current Apple distribution path.
7. Record resource-package SHA, wrapper/build identity, signing identity reference, and validation result without committing signing credentials.

Store action:

- **Do not upload for App Store review without explicit human approval.**
- Under the current #91 configuration, do not submit while the OHCHR public-reuse blocker is active.
- Once both gates are satisfied, submit the reviewed Safari extension/app through the current Apple distribution flow and record review/release state.

## Evidence to record after human certification

For each browser, record separately:

- tested code/PR HEAD;
- Public Evidence Pack SHA-256;
- browser package SHA-256;
- browser/version tested;
- permission list;
- manual-search PASS/FAIL;
- ambiguous-name candidate-selection PASS/FAIL;
- Evidence/provenance rendering PASS/FAIL;
- `NONE` warning PASS/FAIL;
- OHCHR `NOT_INTEGRATED` rendering PASS/FAIL while blocked;
- page-hint privacy/identity-boundary PASS/FAIL;
- official store-policy check date;
- store validation status;
- submission status;
- review status;
- release status.

A generated or locally working package is not the same as a publicly released extension.
