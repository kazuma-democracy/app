from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.public_client.browser_pack import (
    build_public_browser_pack,
    write_public_browser_pack,
)
from wa_commons.public_client.source_rights import load_public_source_rights


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the WA Commons public browser Evidence Pack")
    parser.add_argument("--public-identity", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--screening", type=Path, required=True)
    parser.add_argument("--evidence-graph", type=Path, required=True)
    parser.add_argument("--identity-bridge", type=Path, required=True)
    parser.add_argument("--rights", type=Path, required=True)
    parser.add_argument("--profile-id", action="append", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    input_paths = {
        args.public_identity.resolve(), args.coverage.resolve(), args.screening.resolve(),
        args.evidence_graph.resolve(), args.identity_bridge.resolve(), args.rights.resolve(),
    }
    if args.output.resolve() in input_paths:
        raise ValueError("output path must not overwrite an input artifact")

    pack = build_public_browser_pack(
        public_identity=_load(args.public_identity),
        coverage=_load(args.coverage),
        screening=_load(args.screening),
        evidence_graph=_load(args.evidence_graph),
        identity_bridge=_load(args.identity_bridge),
        source_rights=load_public_source_rights(args.rights),
        profile_ids=args.profile_id,
        generated_at=args.generated_at,
        code_commit=args.code_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_public_browser_pack(pack, args.output)
    manifest = pack["manifest"]
    print(f"release_state={manifest['release_state']}")
    print(f"company_count={manifest['company_count']}")
    print(f"evidence_count={manifest['evidence_count']}")
    print(f"pack_semantic_sha256={manifest['pack_semantic_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
