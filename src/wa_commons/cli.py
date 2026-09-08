from __future__ import annotations

import argparse

from .identity.jpx_snapshot import build_pilot, build_universe, write_pilot, write_universe


def main() -> None:
    parser = argparse.ArgumentParser(prog="wa-commons")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build-jpx-pilot", help="Build a reproducible JPX identity pilot")
    p.add_argument("snapshot_file")
    p.add_argument("output")
    p.add_argument("--snapshot", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--retrieved-at", required=True)
    p.add_argument("--limit", type=int, default=100)

    u = sub.add_parser(
        "build-jpx-universe",
        help="Build a local TSE company universe plus public-safe manifest",
    )
    u.add_argument("snapshot_file")
    u.add_argument("local_output")
    u.add_argument("public_manifest")
    u.add_argument("--snapshot", required=True)
    u.add_argument("--source-url", required=True)
    u.add_argument("--retrieved-at", required=True)

    args = parser.parse_args()
    if args.command == "build-jpx-pilot":
        payload = build_pilot(
            args.snapshot_file,
            snapshot=args.snapshot,
            source_url=args.source_url,
            retrieved_at=args.retrieved_at,
            limit=args.limit,
        )
        write_pilot(payload, args.output)
        print(f"wrote {payload['manifest']['entity_count']} entities to {args.output}")
    elif args.command == "build-jpx-universe":
        payload = build_universe(
            args.snapshot_file,
            snapshot=args.snapshot,
            source_url=args.source_url,
            retrieved_at=args.retrieved_at,
        )
        write_universe(payload, args.local_output, args.public_manifest)
        count = payload["manifest"]["entity_count"]
        print(
            f"wrote {count} entities to local row output {args.local_output}; "
            f"public-safe manifest to {args.public_manifest}"
        )


if __name__ == "__main__":
    main()
