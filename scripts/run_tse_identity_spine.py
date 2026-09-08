from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_real_identity_pilot import run_tse_identity_spine_local


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the #53 TSE identity spine from operator-supplied local snapshots. "
            "Row-level identity output remains local; the second output is manifest-only."
        )
    )
    parser.add_argument("universe", type=Path, help="#46 local row-level TSE universe JSON")
    parser.add_argument("edinet_zip", type=Path, help="local official EDINET code-list ZIP")
    parser.add_argument("nta_zip", type=Path, help="local official NTA nationwide Unicode CSV ZIP")
    parser.add_argument("gleif_zip", type=Path, help="local GLEIF Level 1 Golden Copy CSV ZIP")
    parser.add_argument("local_output", type=Path, help="local row-level enriched identity JSON")
    parser.add_argument("public_manifest", type=Path, help="public-safe manifest-only JSON")
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--edinet-snapshot", required=True)
    parser.add_argument("--nta-snapshot", required=True)
    parser.add_argument("--gleif-snapshot", required=True)
    parser.add_argument("--edinet-url", required=True)
    parser.add_argument("--nta-url", required=True)
    parser.add_argument("--gleif-url", required=True)
    args = parser.parse_args()

    payload = run_tse_identity_spine_local(
        args.universe,
        args.edinet_zip,
        args.nta_zip,
        args.gleif_zip,
        args.local_output,
        args.public_manifest,
        code_commit=args.code_commit,
        retrieved_at=args.retrieved_at,
        edinet_snapshot=args.edinet_snapshot,
        nta_snapshot=args.nta_snapshot,
        gleif_snapshot=args.gleif_snapshot,
        edinet_url=args.edinet_url,
        nta_url=args.nta_url,
        gleif_url=args.gleif_url,
    )
    print(json.dumps(payload["manifest"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
