from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from wa_commons.policy.screener_report import REPORT_VERSION, render_screener_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCREENING = ROOT / "artifacts" / "m2-screening" / "screening.json"
DEFAULT_GRAPH = ROOT / "artifacts" / "m1-reproduction" / "canonical-graph.json"
DEFAULT_DISPLAY_IDENTITIES = ROOT / "configs" / "m2-2c-display-identities-v0.1.json"
DEFAULT_POLICIES = ROOT / "schemas" / "examples" / "user-policy.examples.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "m2-screener-report" / "report.md"
DEFAULT_MANIFEST = ROOT / "artifacts" / "m2-screener-report" / "manifest.json"
DEFAULT_PROFILE = "example:strict-military-avoidance"

EXPECTED_IDENTITY_SEMANTIC_SHA256 = "589bd90eb2bc4a090cc1d73ebabdabab06ae3b12282a3ec38062d78e3399d61f"
EXPECTED_DISPLAY_IDENTITY_SHA256 = "50a23df77b6b1fddb8d8634974105dcec0037fede6975273ddf647674d44af35"
EXPECTED_SCREENING_SHA256 = "7bdfec9c733aa84940e23a8d93153b27f604ee0efc799e6cd9edf628d073971a"
EXPECTED_GRAPH_SHA256 = "0a4f9ed031eaa534e116dca9c441e08054be49047b4404832a14a48094cf2e15"
EXPECTED_COVERAGE_SHA256 = "41361d47e118168c1f393838d3083861d9eed7adc13f6e66d997f3e320f0e403"
EXPECTED_COMPANY_COUNT = 100
EXPECTED_PROFILE_COUNT = 3


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_sha256(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def display_identity_inputs(bundle: dict) -> tuple[list[dict], dict]:
    """Validate and unpack the immutable M1.1 display projection used by Issue #44."""
    recorded = str(bundle.get("display_identity_sha256", ""))
    semantic = dict(bundle)
    semantic.pop("display_identity_sha256", None)
    computed = canonical_sha256(semantic)
    if recorded != EXPECTED_DISPLAY_IDENTITY_SHA256 or computed != EXPECTED_DISPLAY_IDENTITY_SHA256:
        raise ValueError(
            "Issue 44 display identity projection changed: "
            f"expected {EXPECTED_DISPLAY_IDENTITY_SHA256}, recorded {recorded}, computed {computed}"
        )
    provenance = bundle.get("provenance", {})
    identity_sha = provenance.get("m1_identity_semantic_payload_sha256")
    if identity_sha != EXPECTED_IDENTITY_SEMANTIC_SHA256:
        raise ValueError(
            "M1.1 identity semantic snapshot changed in display projection provenance: "
            f"expected {EXPECTED_IDENTITY_SEMANTIC_SHA256}, got {identity_sha}"
        )
    identities = bundle.get("entities")
    if not isinstance(identities, list) or len(identities) != EXPECTED_COMPANY_COUNT:
        raise ValueError("Issue 44 display identity projection must contain exactly 100 entities")
    return identities, {"semantic_payload_sha256": identity_sha}


def generate(
    *,
    screening: dict,
    evidence_graph: dict,
    identities: list[dict],
    identity_report: dict,
    policies: list[dict],
    selected_profile_id: str,
) -> tuple[str, dict]:
    if identity_report.get("semantic_payload_sha256") != EXPECTED_IDENTITY_SEMANTIC_SHA256:
        raise ValueError(
            "M1.1 identity semantic snapshot changed: "
            f"expected {EXPECTED_IDENTITY_SEMANTIC_SHA256}, got {identity_report.get('semantic_payload_sha256')}"
        )
    if screening.get("screening_sha256") != EXPECTED_SCREENING_SHA256:
        raise ValueError(
            f"#43 screening snapshot changed: expected {EXPECTED_SCREENING_SHA256}, got {screening.get('screening_sha256')}"
        )
    if screening.get("evidence_graph_sha256") != EXPECTED_GRAPH_SHA256:
        raise ValueError("#43 report input no longer references the accepted M1 Evidence Graph snapshot")
    if screening.get("coverage_matrix_sha256") != EXPECTED_COVERAGE_SHA256:
        raise ValueError("#43 report input no longer references the accepted #42 coverage snapshot")
    if int(screening.get("company_count", -1)) != EXPECTED_COMPANY_COUNT:
        raise ValueError("#43 company_count is no longer the fixed 100-company cohort")
    if int(screening.get("profile_count", -1)) != EXPECTED_PROFILE_COUNT:
        raise ValueError("#43 profile_count no longer matches the three current example profiles")
    if len(identities) != EXPECTED_COMPANY_COUNT:
        raise ValueError(f"M1.1 identity projection contains {len(identities)} entities, expected 100")

    identity_ids = {str(item["entity_id"]) for item in identities}
    screening_ids = {str(item["entity_id"]) for item in screening.get("views", [])}
    if identity_ids != screening_ids:
        raise ValueError("M1.1 identity entities and #43 screening entities differ")

    report = render_screener_report(
        screening_artifact=screening,
        evidence_graph=evidence_graph,
        identities=identities,
        policies=policies,
        selected_profile_id=selected_profile_id,
    )
    report_sha = sha256_text(report)
    manifest = {
        "issue": 44,
        "report_version": REPORT_VERSION,
        "selected_profile_id": selected_profile_id,
        "company_count": EXPECTED_COMPANY_COUNT,
        "profile_count": EXPECTED_PROFILE_COUNT,
        "identity_semantic_payload_sha256": EXPECTED_IDENTITY_SEMANTIC_SHA256,
        "display_identity_sha256": EXPECTED_DISPLAY_IDENTITY_SHA256,
        "evidence_graph_sha256": screening["evidence_graph_sha256"],
        "coverage_matrix_sha256": screening["coverage_matrix_sha256"],
        "identity_bridge_sha256": screening["identity_bridge_sha256"],
        "screening_sha256": screening["screening_sha256"],
        "report_sha256": report_sha,
        "research_only": True,
        "none_is_not_pass": True,
        "challenge_path": "https://github.com/kazuma-democracy/wa-commons/issues/new",
    }
    return report, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the static Issue #44 explainable 100-company screener report")
    parser.add_argument("--screening", type=Path, default=DEFAULT_SCREENING)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--display-identities", type=Path, default=DEFAULT_DISPLAY_IDENTITIES)
    parser.add_argument("--policies", type=Path, default=DEFAULT_POLICIES)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    identities, identity_report = display_identity_inputs(load_json(args.display_identities))
    report, manifest = generate(
        screening=load_json(args.screening),
        evidence_graph=load_json(args.graph),
        identities=identities,
        identity_report=identity_report,
        policies=load_json(args.policies),
        selected_profile_id=args.profile,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
