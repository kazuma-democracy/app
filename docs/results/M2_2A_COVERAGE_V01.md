# M2.2a — 100-company Evidence Coverage Matrix v0.1

Status: **PR candidate — measured on Issue #42 branch; not canonical until merged**

Issue: #42  
Coverage version: `m2.2a-coverage-v0.1`

## Purpose

Make Evidence coverage explicit across the existing fixed 100-company M1.1 identity pilot without turning missing evidence into a moral or policy judgment.

This result is a coverage artifact only. It does not emit `PASS`, `EXCLUDE`, `WATCH`, `safe`, `clean`, or a moral score.

## Fixed identity input

The matrix reuses the already accepted M1.1 100-company identity pilot from the JPX `20260731` snapshot.

- entity count: **100**
- identity semantic payload SHA-256: `589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f`
- source GitHub Actions run: `32459258713`
- source artifact: `9438384412`
- source artifact digest: `sha256:fba1edd656b3b55b1c2d82dee1333e56779d75b93ee910d0d89abf281e4f375e`

The #42 config retains only WA canonical entity IDs and review state. It does not mirror company names, corporate-number rows, or raw JPX/NTA/EDINET/GLEIF source files.

## Coverage catalog

The v0.1 coverage axis follows the Evidence-source portion of the Source Registry first-integration order. Identity-only sources are not treated as Evidence categories in this matrix.

| Source | Category | Integration state | Result for fixed 100-company pilot |
| --- | --- | --- | --- |
| `jp-mod-procurement` | military contract | integrated | 0 linked entities; 100 `no_match` |
| `jp-political-finance` | political finance | integrated | 52 review-required observations, all identity-unresolved; 100 `unresolved_identity` |
| `sipri-arms-industry` | arms industry | not integrated | 100 `not_integrated` |
| `us-uflpa-entity-list` | official listing | not integrated | 100 `not_integrated` |
| `oecd-ncp-cases` | responsible-business-conduct case | not integrated | 100 `not_integrated` |

For MOD procurement, the fixed M1 adapter snapshot is `fy2026-04-buppin-competitive`, source SHA-256 `c1f37e838d66ffa7bc62c35c5d8830c75ed7b92b0befe0c380f0d79052c773e8`. The fixed 100-company pilot was intersected by exact Japanese corporate number; no pilot entity matched the official April 2026 procurement publication. That strong-ID comparison is sufficient to record `no_match` for this bounded snapshot only.

For political finance, the existing M1 measured pilot used snapshot `soumu-SS20241129-kokumin-seiji-kyokai-r5`, source SHA-256 `e8871ed2cb62729ec8a8c01028c3da2f797a6f65972abfb8dc4dcf757f11c8fe`. It produced **52 observations, 0 AUTO_LINK, 52 identity-unresolved, and 0 canonical claims**. Zero claims is therefore a safety result caused by the strong-ID/review gate, not evidence that the 100 companies had no matching filing records. The #42 matrix preserves this as `unresolved_identity` rather than collapsing it into `no_match`.

## State semantics

- `observed` — at least one source observation is linked to the canonical entity. This is a factual coverage state, not a policy result.
- `no_match` — a completed integrated source snapshot supplied no linked observation and the identity/coverage path was sufficient to establish that bounded absence. **This does not mean clean, safe, approved, peaceful, or PASS.**
- `unknown` — the integrated source/run cannot support a reliable coverage determination, for example because of source outage or equivalent uncertainty.
- `unresolved_identity` — the canonical entity is unresolved, or source observations cannot be consequentially linked to canonical entities under the entity-resolution policy. This state must not collapse into `no_match`.
- `not_integrated` — the source is in the registry/coverage catalog but no adopted adapter is integrated in this snapshot.

The generator applies the following decision order per entity/source cell:

1. source not integrated → `not_integrated`;
2. canonical entity identity not confirmed → `unresolved_identity`;
3. linked observation exists → `observed`;
4. source has unresolved identity linkage preventing entity-level absence determination → `unresolved_identity`;
5. source/run coverage is unreliable → `unknown`;
6. otherwise → `no_match`.

## Measured result

GitHub Actions `m2-coverage` run `34181221281` generated the corrected machine-readable artifact and verified the pinned semantic result.

- focused tests: **11 passed**
- entities: **100**
- sources/categories: **5**
- matrix cells: **500**
- `observed`: **0**
- `no_match`: **100**
- `unknown`: **0**
- `unresolved_identity`: **100**
- `not_integrated`: **300**
- matrix semantic SHA-256: `41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403`
- generated Actions artifact: `m2-2a-coverage`, artifact ID `10038968804`

The zero `observed` count is a property of these fixed source snapshots and this fixed 100-company engineering cohort. It is not evidence that the companies lack peace-relevant activity in other sources or periods. Likewise, `unresolved_identity` does not imply a positive or negative claim about any company; it records that the source evidence cannot safely be assigned at entity level.

## Reproduction

```bash
python -m pytest -q tests/test_evidence_coverage.py tests/test_m2_2a_coverage_snapshot.py
python scripts/run_m2_2a_coverage.py --output artifacts/m2-coverage/coverage.json
```

Expected matrix SHA-256:

`41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403`

The dedicated `.github/workflows/m2-coverage.yml` performs the focused tests, generates `coverage.json`, verifies the pinned counts/hash, and uploads the machine-readable artifact.

## Scope boundary

This increment adds no new Evidence adapter, no new resolver, no user-policy screening, no UI, no benchmark selection, and no portfolio logic. Those remain outside Issue #42.
