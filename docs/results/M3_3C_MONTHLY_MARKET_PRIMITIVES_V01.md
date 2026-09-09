# M3.3c Monthly Market Primitives v0.1

Issue: #56
Validation class: `ENGINEERING_VALIDATION_ONLY`
Validation month: `2026-07`
Code under validation: `653aa38bff16c895cfcd4d30268e3c83ee8aa722`

## Result

The reusable monthly JPX primitives are validated against official June/July 2026 JPX PDF files using explicit local inputs only.

The validation passed for:

- normal month-end price extraction by exact JPX security code;
- duplicate monthly price rows around a corporate action, selecting only the unique valuation-date close;
- official dividend-included TOPIX one-month ROI extraction;
- JPX ex-rights stock-split detection;
- TSE monthly listed-company delisting detection;
- fail-closed missing price, benchmark, identity, dividend and action states;
- deterministic semantic output for repeated inputs and reversed requested-security order;
- local-only raw-source and public-output boundaries.

July 2026 is not a Historical Replay result. Its schema was inspected during engineering, so it is permanently excluded from becoming the first #85 headline replay window.

## Real-source parser findings

The real JPX PDF text exposed three parser shapes that the first synthetic fixtures did not capture:

- the TOPIX ROI row is extracted as spaced `T O P I X`, with the index level before the one-month ROI;
- the ex-rights table uses dotted dates and includes market/sector text before the requested code;
- the delisting table may use Japanese market/sector text before the date and code.

These differences were converted into regression tests before the production parser was changed. The final parser scopes the benchmark row to the dividend-included ROI section, distinguishes TOPIX itself from TOPIX 100/500/1000 sub-index labels, accepts the observed dotted date format, and does not depend on English company or sector names for delisting identity.

## Determinism

The same official July stock-price input was parsed repeatedly and with the requested security order reversed. The normalized rows and semantic hash were identical.

Price semantic rows SHA-256:

`13241de3d6adda1a5677036add6786e730ed48774d2e0e2b62a7083a3bd0d64d`

Focused monthly-market tests: **34 passed**.

Final repository suite: **247 passed**.

## Publication boundary

The official PDF files and extracted market rows remain local-only. This repository result intentionally does **not** publish security-level price values, the numeric benchmark return, or any candidate portfolio return.

The repository-safe manifest records only source locator families, local file timestamps observed at validation, raw-file SHA-256 values, parser/config identity, pass/block facts and deterministic semantic hashes.

The source contract remains the completed #78 zero-purchase/monthly/fail-closed contract. Public availability of a JPX file is not treated as permission to republish its raw rows or performance values.

## Handoff to #85

#56 provides reusable month-parameterized primitives only. #85 must still:

- select the most recent reproducible three consecutive historical months using metadata/existence rules before loading returns;
- reconstruct point-in-time benchmark membership/weights and as-known evidence at each cutoff;
- BLOCK any month that cannot be reproduced without survivorship or evidence leakage;
- keep the October 2026 #78 interval reserved as the true future holdout.

No replay window, policy multiplier or methodology was selected from the July engineering-validation performance.
