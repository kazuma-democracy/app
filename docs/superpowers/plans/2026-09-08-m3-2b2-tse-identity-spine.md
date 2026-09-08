# M3.2b2 TSE Identity Spine — implementation checkpoint

Issue: #53

This branch extends the existing conservative JPX/EDINET/NTA/GLEIF identity spine across the local-only canonical TSE universe from #46.

Approved bounded design:

- reuse `enrich_entity_batch()` and existing strong-ID conflict rules;
- preserve every #46 universe entity, including unresolved/disputed rows;
- never introduce name-only AUTO_LINK;
- generate a deterministic local row-level identity artifact plus a public-safe non-row manifest;
- use local official snapshots for JPX/EDINET/NTA and GLEIF Golden Copy data;
- keep EDINET/NTA row-level derived identity output local-only while Source Registry rights remain review-required;
- record mapped/unresolved/disputed and per-identifier coverage counts, source hashes/snapshots, policy version and code commit;
- do not start benchmark mapping, evidence expansion, policy screening, returns, portfolio integration or UI.

TDD status at this commit: first RED contract added; production implementation intentionally absent.
