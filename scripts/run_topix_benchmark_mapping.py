from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.portfolio.benchmark_snapshot import (
    build_topix_snapshot,
    load_benchmark_config,
    map_topix_snapshot,
    read_topix_month_end_csv,
    sha256_file,
    write_topix_benchmark_mapping,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "m3-3b-topix-benchmark-v0.1.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map an operator-supplied licensed TOPIX month-end master onto the canonical TSE identity universe"
    )
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--local-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    config = load_benchmark_config(args.config)
    snapshot = build_topix_snapshot(
        read_topix_month_end_csv(args.master),
        config,
        sha256_file(args.master),
    )
    mapped = map_topix_snapshot(snapshot, load_json(args.identity))
    mapped["manifest"]["code_commit"] = args.code_commit
    write_topix_benchmark_mapping(mapped, args.local_output, args.public_output)

    print(json.dumps({
        "benchmark_id": mapped["manifest"]["benchmark_id"],
        "effective_date": mapped["manifest"]["effective_date"],
        "constituent_count": mapped["manifest"]["constituent_count"],
        "mapping_summary": mapped["manifest"]["mapping_summary"],
        "semantic_mapping_sha256": mapped["manifest"]["semantic_mapping_sha256"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
