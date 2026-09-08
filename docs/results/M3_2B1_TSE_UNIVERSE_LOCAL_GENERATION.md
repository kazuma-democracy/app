# M3.2b1 TSE company universe — local-generation contract

Status: **PR candidate / Issue #46**  
Rights decision: **`ADOPT_LOCAL_GENERATION_ONLY`** from Issue #61  
Public row-level JPX artifact: **NONE**

## Purpose

Issue #46 replaces the earlier 100-company engineering cohort with a deterministic TSE domestic-company universe for later identity enrichment. Under the rights boundary adopted in #61, the canonical row-level universe is generated only from a JPX snapshot supplied by the operator in an authorized local workspace. The free JPX source file and the derived company rows are not committed to this repository and are not uploaded by CI.

Canonical source locator:

`https://www.jpx.co.jp/markets/statistics-equities/misc/01.html`

The operator is responsible for obtaining and retaining the applicable JPX source under their own rights/terms and for supplying the effective snapshot date and retrieval timestamp used for the run.

## Scope

`build_universe()` accepts the existing JPX CSV/XLS/XLSX input formats and includes only the exact market/product labels:

- `プライム（内国株式）` → `Prime`
- `スタンダード（内国株式）` → `Standard`
- `グロース（内国株式）` → `Growth`

ETF/ETN, REIT, TOKYO PRO Market, foreign stocks and other out-of-scope market/product rows are excluded and counted separately. An in-scope row missing the required security code or listed name is not silently dropped: the run fails closed so the source row remains available for operator review. A source-row date that does not match the pinned snapshot also fails closed. Duplicate normalized security codes fail closed instead of being silently retained or deduplicated.

The local row-level output is canonically ordered by normalized JPX security code. Each row preserves the existing `EntityRecord` identity/provenance envelope produced by `from_jpx_row()`, including the `JPX_SECURITY_CODE` identifier and its `SourceRef` (`source_key`, snapshot, source URL, retrieval timestamp, and adapter version). It also exposes two deterministic convenience fields needed by the #53 handoff:

- normalized `security_code`;
- normalized `market_segment` (`Prime`, `Standard`, or `Growth`).

The existing envelope continues to carry the WA canonical `entity_id`, JPX listed `canonical_name`, jurisdiction/review fields, and identifier provenance. No EDINET/NTA/GLEIF enrichment, benchmark filtering, evidence screening, portfolio logic, or #53 work is included in #46.

## Public-safe manifest

Each successful local run also emits a separate manifest containing only non-row-level reproducibility metadata:

- publisher/source ID and official source locator;
- operator-supplied snapshot/effective date and retrieval timestamp;
- local source filename and SHA-256;
- adapter version and scope rule;
- `rights_mode = local_generation_only`;
- explicit row-publication boundary;
- Prime / Standard / Growth counts and total entity count;
- exclusion counts by category;
- SHA-256 of the canonical row-level **semantic projection**.

The public-safe manifest contains no company rows, listed company names, individual security codes, or per-row SourceRef data. The semantic projection contains only `entity_id`, normalized security code, listed canonical name, and normalized market segment; local transport/provenance details such as filename and retrieval timestamp are deliberately excluded from that semantic hash. This allows authorized local runs to compare the derived company universe without publishing the underlying rows or making the semantic identity depend on local path/timing metadata.

## Local reproduction

After obtaining the JPX snapshot locally, run:

```text
wa-commons build-jpx-universe <JPX_SNAPSHOT_FILE> <LOCAL_UNIVERSE_JSON> <PUBLIC_MANIFEST_JSON> \
  --snapshot <EFFECTIVE_DATE> \
  --source-url https://www.jpx.co.jp/markets/statistics-equities/misc/01.html \
  --retrieved-at <ISO8601_TIMESTAMP>
```

`LOCAL_UNIVERSE_JSON` contains JPX-derived row-level data and must remain within the operator's authorized local workspace under the adopted free-site route. `PUBLIC_MANIFEST_JSON` is the non-row-level verification surface designed for public evidence/handoff. The two output paths must be distinct; the writer fails before writing if the resolved paths are the same.

## Verification contract

CI uses only synthetic/minimal fixtures. It does not fetch JPX and does not publish JPX-derived rows. Fixture coverage proves:

- exact Prime / Standard / Growth inclusion;
- ETF/ETN, REIT, PRO Market and foreign/other exclusion accounting;
- pinned snapshot/source-row date consistency with fail-closed mismatch handling;
- fail-closed handling of in-scope rows missing required identity fields;
- canonical security-code ordering;
- preservation of the existing JPX identifier `SourceRef` in the local row-level envelope;
- input-order-independent semantic payload hash;
- semantic-hash independence from local filename/retrieval-time provenance;
- byte-level source SHA distinction;
- duplicate security-code fail-closed behavior;
- separation of local row output from the public-safe manifest, including same-path rejection;
- CLI production of both outputs from a local input path.

A real operator run supplies the real snapshot hash, market counts, exclusion counts and semantic payload hash. Those values are intentionally not fabricated or inferred when the JPX source bytes are not present in the authorized local workspace.

## Rights boundary

The free JPX listed-issues page/file is an authoritative acquisition source, not a blanket public-redistribution license. WA Commons therefore does not commit or upload the free-source raw file or normalized row-level universe. Commercial acquisition/secondary use or public row-level redistribution requires the operator's own applicable JPX permission/contract or a separately adopted licensed route.

`docs/SOURCE_REGISTRY.md` remains unchanged: `jp-jpx-listed` is adopted for identity while redistribution still requires review.

## Disposition

`M3_2B1_TSE_UNIVERSE_MODE = LOCAL_GENERATION_ONLY`

The fresh implementation starts from the current `main` and reuses the existing JPX reader, normalization, `from_jpx_row()` identity convention and source hashing. The historical VM checkpoint is not used. Issue #53 remains out of scope until #46 is durably completed.
