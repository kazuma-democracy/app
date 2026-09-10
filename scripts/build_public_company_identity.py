from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.public_client.identity_projection import build_public_company_identity
from wa_commons.public_client.source_rights import load_public_source_rights


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rights-cleared public company identity projection")
    parser.add_argument("--canonical-identity", type=Path, required=True)
    parser.add_argument("--edinet-code-list", type=Path, required=True)
    parser.add_argument("--nta", type=Path, required=True)
    parser.add_argument("--rights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    inputs = [args.canonical_identity, args.edinet_code_list, args.nta, args.rights]
    output_resolved = args.output.resolve()
    if any(output_resolved == path.resolve() for path in inputs):
        raise ValueError("output path must differ from all raw/local input paths")

    result = build_public_company_identity(
        canonical_identity=_load_json(args.canonical_identity),
        edinet_rows=_load_json(args.edinet_code_list),
        nta_rows=_load_json(args.nta),
        rights=load_public_source_rights(args.rights),
        code_commit=args.code_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = result["manifest"]
    print(json.dumps({
        "resolved_public_company_count": manifest["resolved_public_company_count"],
        "unresolved_count": manifest["unresolved_count"],
        "public_projection_semantic_sha256": manifest["public_projection_semantic_sha256"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
