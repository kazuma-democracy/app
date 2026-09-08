# M3.2d TSE-wide evidence coverage v0.1

Status: **MEASURED / ACCEPTANCE CANDIDATE**

Issue: #54

This result scales the existing #42 coverage-state machinery across the complete #53 canonical TSE identity universe. It does not add a new evidence source, policy rule, moral score, benchmark, portfolio method, or trading authority.

## Fixed inputs

- Canonical TSE identity entities: **3,707**
- Identity semantic SHA-256: `a74d81a27e19d3a746e1d3669842f7284f43ac45d3ae8601cdd6741d7ebe6733`
- Confirmed corporate-number identities available from #53: **3,699**
- Unresolved identities carried forward from #53: **8**
- Coverage sources/categories: **5**
- Coverage cells: **18,535** (`3,707 × 5`)
- Generator commit used for the final local measurement: `e2268900aef5bfdfbaf7ac3723a4a967af9d7a4e`

The public aggregate machine-readable result is `docs/results/M3_2D_TSE_EVIDENCE_COVERAGE_MANIFEST_V01.json`. The row-level matrix remains local-only.

## Measured state counts

| State | Cells |
| --- | ---: |
| `observed` | 7 |
| `no_match` | 3,692 |
| `unresolved_identity` | 3,715 |
| `not_integrated` | 11,121 |
| `unknown` | 0 |
| **Total** | **18,535** |

`no_match` means only that the fixed source snapshot contained no linked observation for that entity. It does **not** mean clean, safe, peaceful, PASS, or approved.

## Source/category result

### Ministry of Defense procurement — `jp-mod-procurement`

- Integration state: `integrated`
- Snapshot: `fy2026-04-buppin-competitive`
- Source SHA-256: `c1f37e838d66ffa7bc62c35c5d8830c75ed7b92b0befe0c380f0d79052c773e8`
- Fixed official snapshot contained **88** procurement observations.
- The existing adapter marked **86** observations `AUTO_LINK` and **2** unresolved before TSE-universe intersection.
- Exact 13-digit Japanese corporate-number intersection linked **10 procurement observations to 7 TSE entities**.
- Linked-observation multiplicity across those seven entities was `3, 2, 1, 1, 1, 1, 1`.
- Coverage cells: **7 observed / 3,692 no_match / 8 unresolved_identity**.

Company names, corporate numbers, and row-level contract-to-company links are intentionally not published by this result artifact.

### Political finance — `jp-political-finance`

- Integration state: `integrated`
- Identity linkage remains `unresolved` under the existing strong-ID-only rule.
- Therefore all **3,707** TSE entity/source cells remain `unresolved_identity`.
- No name-only rescue linking was introduced.

### Not-yet-integrated adopted sources

The existing source catalog currently marks these as not integrated/not run for this coverage pipeline:

- `sipri-arms-industry`
- `us-uflpa-entity-list`
- `oecd-ncp-cases`

Each therefore contributes **3,707 `not_integrated` cells**, for **11,121** total. These cells are not converted to `no_match` or any positive judgment.

## Determinism

The measured semantic coverage SHA-256 is:

`ccc77af755a6022031d5aca6bc8fbd1f53b7136eb460c0fd69d17e07263f0941`

Independent reruns with the same identity artifact, source configuration, MOD observations, and coverage rules reproduced the same semantic hash. A later public-output metadata cleanup changed only what provenance metadata is published; it did not change the row-level coverage matrix or this semantic hash.

## Public/private boundary

The full local artifact contains all **18,535** row-level coverage cells and is not committed to the public repository.

The public aggregate manifest was verified to contain:

- only top-level `manifest` and `source_catalog`;
- no `matrix`;
- no `entity_id`;
- no 13-digit corporate-number value;
- no fixed-100 pilot measurement counters or measurement notes.

Stable source provenance such as adapter version, snapshot version, source SHA-256, identity method, and Source Registry adoption status is retained.

## Focused behavior verified

The #54 implementation/tests cover:

- all 3,707 #53 entities remain represented;
- unresolved #53 identities remain unresolved rather than becoming `no_match`;
- source outage/unknown state cannot become `no_match`;
- not-integrated sources remain explicit;
- MOD observations link only by exact corporate number, not company name;
- input ordering does not change the semantic coverage hash;
- local row-level output and public aggregate output are separate paths;
- public output strips obsolete fixed-100 measurement metadata;
- the operator CLI accepts local input paths only and does not add a downloader.

At generator commit `e2268900aef5bfdfbaf7ac3723a4a967af9d7a4e`:

- `tests` workflow `34203002963`: **SUCCESS — 157 passed**
- `tse-evidence-coverage` workflow `34203002897`: **SUCCESS**
- `mod-procurement-pilot` workflow `34203002879`: **SUCCESS**

Final PR-head CI must still be green before merge.

## Acceptance against Issue #54

- Every #53 entity appears: **PASS — 3,707 / 3,707**.
- Every configured source/category has an explicit state per entity: **PASS — 18,535 / 18,535 cells**.
- Missing/unintegrated evidence cannot become clean/safe/PASS: **PASS**.
- Rerun reproduces semantic coverage payload: **PASS**.
- Targeted tests cover state propagation, unresolved identity, outage behavior, exact-ID linking, deterministic ordering, and publication boundary: **PASS**.
- Measured aggregate result is recorded without publishing row-level company data: **PASS**.

Subject to final PR-head CI and review-thread checks, Issue #54 meets its stated definition of done.
