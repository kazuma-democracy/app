from __future__ import annotations

import argparse
import json
from pathlib import Path

from wa_commons.policy.tse_screening import build_tse_policy_screening, write_tse_policy_screening

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICIES = ROOT / "schemas" / "examples" / "user-policy.examples.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Issue #55 TSE-wide policy screening from operator-supplied local artifacts only"
    )
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--mod-observations", type=Path, required=True)
    parser.add_argument("--policies", type=Path, default=DEFAULT_POLICIES)
    parser.add_argument("--local-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()

    result = build_tse_policy_screening(
        identity=load_json(args.identity),
        coverage_artifact=load_json(args.coverage),
        mod_observations=load_json(args.mod_observations),
        policies=load_json(args.policies),
        code_commit=args.code_commit,
    )
    write_tse_policy_screening(result, args.local_output, args.public_output)
    print(json.dumps({
        "tse_screening_sha256": result["tse_screening_sha256"],
        "company_count": result["company_count"],
        "profile_count": result["profile_count"],
        "view_count": result["view_count"],
        "generated_claim_count": result["generated_claim_count"],
        "decision_counts_by_profile": result["decision_counts_by_profile"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
