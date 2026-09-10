# Bundled Public Evidence Pack

The release/package builder injects `wa-public-evidence-pack.json` here only after the
pack passes the public-source rights, identity, evidence, and semantic-hash validators.

Do not commit a real generated pack in this common source directory. Tests use only the
synthetic fixture under `tests/fixtures/`.
