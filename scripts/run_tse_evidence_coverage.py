from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.evidence.tse_coverage import run_tse_coverage_local


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Issue #54 TSE-wide evidence coverage from operator-supplied local artifacts only"
    )
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--coverage-config", type=Path, required=True)
    parser.add_argument("--mod-observations", type=Path, required=True)
    parser.add_argument("--local-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    result = run_tse_coverage_local(
        identity_path=args.identity,
        coverage_config_path=args.coverage_config,
        mod_observations_path=args.mod_observations,
        local_output=args.local_output,
        public_output=args.public_output,
        code_commit=args.code_commit,
    )
    print(json.dumps(result["manifest"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
