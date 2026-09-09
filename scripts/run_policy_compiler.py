from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wa_commons.portfolio.policy_compiler import (
    compile_policy_family,
    load_policy_compiler_config,
    write_policy_transmission,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile preregistered Peace Capital policy-family allocations without market data"
    )
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--screening", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--local-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    payload = compile_policy_family(
        _load_json(args.benchmark),
        _load_json(args.screening),
        load_policy_compiler_config(args.config),
    )
    payload.setdefault("manifest", {})["code_commit"] = args.code_commit
    write_policy_transmission(payload, args.local_output, args.public_output)

    print(json.dumps({
        "status": payload.get("status"),
        "artifact_version": payload.get("artifact_version"),
        "policy_family_sha256": payload.get("manifest", {}).get("policy_family_sha256"),
        "arms": [
            {
                "arm_id": arm.get("arm_id"),
                "status": arm.get("status"),
                "active_share": arm.get("metrics", {}).get("active_share"),
            }
            for arm in payload.get("arms", [])
        ],
    }, ensure_ascii=False, indent=2, sort_keys=True))

    if str(payload.get("status", "")).startswith("BLOCK_"):
        raise SystemExit(3)


if __name__ == "__main__":
    main()
