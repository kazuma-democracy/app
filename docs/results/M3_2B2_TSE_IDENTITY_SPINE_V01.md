# M3.2b2 — TSE-wide identity spine result v0.1

Status: **COMPLETE CANDIDATE — measured local reproduction verified**
Issue: #53
Date: 2026-09-08

## What was measured

The canonical #46 TSE universe for the 2026-08-31 snapshot was regenerated locally from the current official JPX workbook and passed through the existing conservative JPX / EDINET / NTA / GLEIF identity spine.

No name-only consequential AUTO_LINK was added. Row-level universe and identity outputs remain local-only; this repository records only aggregate verification facts and hashes.

## Measured result

- canonical TSE entities: **3,707**
- mapped to a unique Japanese corporate number: **3,699** (~99.8%)
- unresolved: **8**
- disputed strong-ID identities: **0**
- EDINET code present: **3,700**
- Japanese corporate number present: **3,699**
- NTA-confirmed corporate numbers: **3,699 / 3,699**
- exact GLEIF LEI matches (`RA001075`): **172**

The eight unresolved entities were intentionally retained instead of being force-matched:

- **7** had no matching EDINET security-code row;
- **1** had an EDINET code but no Japanese corporate number;
- **0** were resolved by name-only fallback.

## Source snapshots and hashes

### JPX canonical universe

- snapshot: `20260831`
- current workbook: `data_j.xlsx`
- source SHA-256: `fff94dd14057c8bfa36a3fbabd8e228bbed63751c7ecd10c1a8281f5385fcb78`
- universe semantic SHA-256: `831c879578fea7c31f72c0bbc418c2b8d983e46a13145ff0076e585db25ff086`
- generated universe count: `3707`

### EDINET

- downloaded: 2026-09-08
- code-list rows reported by the file: `11389`
- SHA-256: `65741739ae31557c5beabf39ffa33bd5ed0753c25efe8833c415ac743493af93`

### National Tax Agency corporate-number dataset

- nationwide Unicode snapshot: `2026-08-31`
- local ZIP SHA-256: `36bd4b1674093b5937bb7306b10557aadda7b3e1cd0e273fafefff2ad6a14875`
- all 3,699 corporate numbers emitted by the spine were present in the NTA snapshot.

### GLEIF

- Level 1 Golden Copy CSV snapshot: `2026-09-08T00:00:00Z`
- GLEIF record count advertised for that Golden Copy: `3,424,074`
- local ZIP SHA-256: `689357453902c1dbc558f6bb1d36837d28259279258542ba8f0bd36fc73e1f47`
- accepted registration authority: exact `RA001075` only
- LEI data license: `CC0-1.0`

## Reproducibility

Identity policy: `wa-conservative-v0.2`
Measured code commit: `84500ead1ece3d88d875c3a74ebab8c8bf4cf00a`

The full local run was executed twice from the same source snapshots with different retrieval/run timestamps. Both runs produced the same semantic identity hash:

`a74d81a27e19d3a746e1d3669842f7284f43ac45d3ae8601cdd6741d7ebe6733`

This verifies that retrieval-time metadata does not change the canonical semantic identity payload.

## CI / regression evidence

Before the measured local run, the #53 implementation head passed all eight relevant GitHub Actions workflows, including the dedicated `tse-identity-spine` gate. The general test suite passed with **149 tests**.

The fixture gates cover, among other things:

- every #46 row remains represented;
- mapped / unresolved / disputed counts partition the universe;
- duplicate JPX security codes fail closed;
- GLEIF uses exact Japanese registration-authority matching;
- semantic hashes are stable across input ordering and retrieval timestamps;
- local and public output paths cannot be the same;
- public output is manifest-only and does not contain row-level company identity data.

## Rights / publication boundary

The measured row-level JPX universe and enriched identity artifact were produced and retained only on the authorized local workstation. They are **not committed to the public repository and are not uploaded as CI artifacts**.

The public repository retains aggregate counts, source locators, snapshot identifiers and hashes sufficient to verify which inputs and rules produced the measured result. EDINET and NTA remain marked `review_required` in the current Source Registry for redistribution, so this result does not silently broaden redistribution rights.

## Source-format observation

During the measured reproduction, the current JPX workbook locator had changed from the historical `data_j.xls` filename to `data_j.xlsx`. The existing #46 reader already supports the current workbook format, so #53 was not blocked and no identity rule was weakened. The stale historical locator is tracked separately in Issue #69 rather than folded into identity semantics.

## Acceptance

#53 acceptance is met for the pinned local reproduction:

- every one of the 3,707 #46 entities is represented;
- mapped, unresolved and disputed counts are explicit;
- no name-only consequential AUTO_LINK was introduced;
- the semantic payload reproduced exactly on rerun;
- targeted regressions and CI are green;
- source snapshots, hashes, code commit and unresolved limitations are recorded.

This result expands identity coverage only. It does not add evidence claims, policy screening, benchmark mapping, market returns, portfolio construction or trading authority.
