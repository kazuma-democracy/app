from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.portfolio.benchmark_snapshot import (
    PW_DATE,
    build_topix_public_weight_snapshot,
    build_topix_snapshot,
    load_benchmark_config,
    map_topix_snapshot,
    read_topix_month_end_csv,
    read_topix_public_weight_csv,
    sha256_file,
    write_topix_benchmark_mapping,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MASTER_CONFIG = ROOT / "configs" / "m3-3b-topix-benchmark-v0.1.json"
DEFAULT_PUBLIC_WEIGHT_CONFIG = ROOT / "configs" / "m3-3b-topix-benchmark-v0.2.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map a provider-native TOPIX constituent/weight snapshot onto the canonical TSE identity universe"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--master", type=Path)
    source.add_argument("--public-weight", type=Path)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--local-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    if args.public_weight is not None:
        source_path = args.public_weight
        config_path = args.config or DEFAULT_PUBLIC_WEIGHT_CONFIG
        config = load_benchmark_config(config_path)
        rows = read_topix_public_weight_csv(source_path)
        expected_date = str(config.get("effective_date", "")).replace("-", "")
        observed_dates = sorted({str(row.get(PW_DATE, "")).strip() for row in rows})
        if observed_dates != [expected_date]:
            status = (
                "NOT_YET_PUBLISHED"
                if observed_dates and max(observed_dates) < expected_date
                else "SOURCE_DATE_MISMATCH"
            )
            parser.exit(3, f"{status}: expected={expected_date} observed={observed_dates}\n")
        snapshot = build_topix_public_weight_snapshot(
            rows,
            config,
            sha256_file(source_path),
        )
    else:
        source_path = args.master
        config_path = args.config or DEFAULT_MASTER_CONFIG
        config = load_benchmark_config(config_path)
        snapshot = build_topix_snapshot(
            read_topix_month_end_csv(source_path),
            config,
            sha256_file(source_path),
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
