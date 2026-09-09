from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from wa_commons.portfolio.historical_replay import (
    freeze_replay_window,
    load_historical_replay_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Qualify and freeze a Historical Replay window from metadata only."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--candidate-metadata", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--code-commit", required=True)
    return parser


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_qualification(
    *,
    config_path: str | Path,
    candidate_metadata_path: str | Path,
    output_path: str | Path,
    code_commit: str,
) -> dict[str, Any]:
    config = load_historical_replay_config(config_path)
    inventory = _load_json(candidate_metadata_path)
    candidates = list(inventory.get("candidates", []))
    result = freeze_replay_window(candidates, config)
    result["code_commit"] = code_commit
    result["candidate_inventory_version"] = inventory.get("artifact_version")
    result["selection_input_semantics"] = "METADATA_ONLY_NO_RETURNS"

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    args = build_parser().parse_args()
    run_qualification(
        config_path=args.config,
        candidate_metadata_path=args.candidate_metadata,
        output_path=args.output,
        code_commit=args.code_commit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
