from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

from wa_commons.portfolio.historical_replay import run_frozen_replay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a previously frozen Historical Replay window."
    )
    parser.add_argument("--frozen-window", required=True, type=Path)
    parser.add_argument("--policy-payload-map", required=True, type=Path)
    parser.add_argument("--market-payload-map", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--local-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    return parser


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_output_paths(local_output: Path, public_output: Path) -> None:
    if local_output.resolve() == public_output.resolve():
        raise ValueError("local and public output paths must be distinct")


def build_public_payload(
    result: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    rights_cleared = bool(
        config.get("publication", {}).get("performance_rights_cleared", False)
    )
    public: dict[str, Any] = {
        "status": result.get("status"),
        "window": list(result.get("window", [])),
        "window_semantic_sha256": result.get("window_semantic_sha256"),
        "semantic_payload_sha256": result.get("semantic_payload_sha256"),
        "blocker_counts": dict(Counter(result.get("blockers", []))),
        "publication": {
            "performance_rights_cleared": rights_cleared,
            "financial_values_published": rights_cleared,
        },
    }
    public["months"] = [
        {
            "period": month.get("period"),
            "policy_transmission": month.get("policy_transmission", []),
        }
        for month in result.get("months", [])
    ]
    if rights_cleared:
        for public_month, source_month in zip(
            public["months"], result.get("months", [])
        ):
            public_month["financial"] = source_month.get("financial", {})
        public["arms"] = result.get("arms", [])
        public["benchmark"] = result.get("benchmark", {})
    return public


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_replay(
    *,
    frozen_window_path: str | Path,
    policy_payload_map_path: str | Path,
    market_payload_map_path: str | Path,
    config_path: str | Path,
    local_output_path: str | Path,
    public_output_path: str | Path,
) -> dict[str, Any]:
    local_output = Path(local_output_path)
    public_output = Path(public_output_path)
    validate_output_paths(local_output, public_output)

    window = _load_json(frozen_window_path)
    if window.get("status") != "HISTORICAL_REPLAY_WINDOW_FROZEN":
        raise ValueError("frozen window manifest is required before replay execution")

    config = _load_json(config_path)
    policy_map = _load_json(policy_payload_map_path)
    market_map = _load_json(market_payload_map_path)
    result = run_frozen_replay(window, policy_map, market_map, config)

    _write_json(local_output, result)
    _write_json(public_output, build_public_payload(result, config))
    return result


def main() -> int:
    args = build_parser().parse_args()
    run_replay(
        frozen_window_path=args.frozen_window,
        policy_payload_map_path=args.policy_payload_map,
        market_payload_map_path=args.market_payload_map,
        config_path=args.config,
        local_output_path=args.local_output,
        public_output_path=args.public_output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
