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
| `jp-political-finance` | political finance | integrated | 0 canonical linked claims; 100 `no_match` |
| `sipri-arms-industry` | arms industry | not integrated | 100 `not_integrated` |
| `us-uflpa-entity-list` | official listing | not integrated | 100 `not_integrated` |
| `oecd-ncp-cases` | responsible-business-conduct case | not integrated | 100 `not_integrated` |

For MOD procurement, the fixed M1 adapter snapshot is `fy2026-04-buppin-competitive`, source SHA-256 `c1f37e838d66ffa7bc62c35c5d8830c75ed7b92b0befe0c380f0d79052c773e8`. The fixed 100-company pilot was intersected by exact Japanese corporate number; no pilot entity matched the official April 2026 procurement publication.

For political finance, the existing M1 reproduction used snapshot `soumu-SS20241129-kokumin-seiji-kyokai-r5`, source SHA-256 `e8871ed2cb62729ec8a8c01028c3da2f797a6f65972abfb8dc4dcf757f11c8fe`. Its OCR/name-only donor observations remained review-required and unresolved, so the canonical linked-claim count is zero. No name-only association is converted into company evidence here.

## State semantics

- `observed` — at least one source observation is linked to the canonical entity. This is a factual coverage state, not a policy result.
- `no_match` — a completed integrated source snapshot supplied no linked observation for the entity. **This does not mean clean, safe, approved, peaceful, or PASS.**
- `unknown` — the integrated source/run cannot support a reliable coverage determination, for example because of source outage or equivalent uncertainty.
- `unresolved_identity` — candidate evidence cannot be consequentially linked to the canonical entity under the entity-resolution policy.
- `not_integrated` — the source is in the registry/coverage catalog but no adopted adapter is integrated in this snapshot.

The precedence implemented by the generator is: `not_integrated` → `unresolved_identity` → `unknown` → `observed` → `no_match`.

## Measured result

GitHub Actions `m2-coverage` run `34180397648` generated the machine-readable artifact and verified the pinned semantic result.

- focused tests: **8 passed**
- entities: **100**
- sources/categories: **5**
- matrix cells: **500**
- `observed`: **0**
- `no_match`: **200**
- `unknown`: **0**
- `unresolved_identity`: **0**
- `not_integrated`: **300**
- matrix semantic SHA-256: `ab41c898747c8a725ecaa240f1bb1d759c5e8233b2f9c25543647b9a7950ac68`
- generated Actions artifact: `m2-2a-coverage`, artifact ID `10038687908`

The zero `observed` count is a property of these fixed source snapshots and this fixed 100-company engineering cohort. It is not evidence that the companies lack peace-relevant activity in other sources or periods.

## Reproduction

```bash
python -m pytest -q tests/test_evidence_coverage.py tests/test_m2_2a_coverage_snapshot.py
python scripts/run_m2_2a_coverage.py --output artifacts/m2-coverage/coverage.json
```

Expected matrix SHA-256:

`ab41c898747c8a725ecaa240f1bb1d759c5e8233b2f9c25543647b9a7950ac68`

The dedicated `.github/workflows/m2-coverage.yml` performs the focused tests, generates `coverage.json`, verifies the pinned counts/hash, and uploads the machine-readable artifact.

## Scope boundary

This increment adds no new Evidence adapter, no new resolver, no user-policy screening, no UI, no benchmark selection, and no portfolio logic. Those remain outside Issue #42.
