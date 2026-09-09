from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from wa_commons.portfolio.monthly_market import (
    build_monthly_return_payload,
    extract_pdf_text,
    load_monthly_market_config,
    parse_ex_rights_text,
    parse_listed_company_changes_text,
    parse_stock_price_table_text,
    parse_topix_monthly_roi_text,
    source_provenance,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build deterministic monthly JPX market primitives from explicit local files.")
    parser.add_argument("--period", required=True)
    parser.add_argument("--start-price-pdf", required=True, type=Path)
    parser.add_argument("--end-price-pdf", required=True, type=Path)
    parser.add_argument("--benchmark-pdf", required=True, type=Path)
    parser.add_argument("--ex-rights-pdf", required=True, type=Path)
    parser.add_argument("--listed-changes-pdf", required=True, type=Path)
    parser.add_argument("--held-securities", required=True, type=Path)
    parser.add_argument("--evidence-resolutions", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--local-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    parser.add_argument("--code-commit", required=True)
    return parser


def validate_output_paths(local_output: Path, public_output: Path) -> None:
    if local_output.resolve() == public_output.resolve():
        raise ValueError("local and public output paths must be distinct")


def validate_source_manifest_period(manifest: dict[str, Any], period: str) -> None:
    if manifest.get("period") != period:
        raise ValueError(f"source manifest period mismatch: expected {period!r}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _held_ids(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict) and isinstance(value.get("held_security_ids"), list):
        return [str(item) for item in value["held_security_ids"]]
    raise ValueError("held-securities must be a JSON list or contain held_security_ids")


def _source_meta(manifest: dict[str, Any], key: str) -> dict[str, str]:
    sources = manifest.get("sources")
    if not isinstance(sources, dict) or not isinstance(sources.get(key), dict):
        raise ValueError(f"source manifest missing source metadata for {key}")
    meta = sources[key]
    locator = meta.get("locator")
    retrieved_at = meta.get("retrieved_at")
    if not isinstance(locator, str) or not isinstance(retrieved_at, str):
        raise ValueError(f"source manifest source {key} requires locator and retrieved_at")
    return {"locator": locator, "retrieved_at": retrieved_at}


def build_public_artifact(
    local_payload: dict[str, Any],
    *,
    performance_publication_rights: str,
    artifact_version: str,
    code_commit: str,
    source_hashes: list[str],
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("state", "UNKNOWN")) for row in local_payload.get("rows", []))
    public: dict[str, Any] = {
        "artifact_version": artifact_version,
        "period": local_payload.get("period"),
        "status": local_payload.get("status"),
        "paper_only": True,
        "performance_publication_rights": performance_publication_rights,
        "code_commit": code_commit,
        "source_hashes": sorted(source_hashes),
        "semantic_payload_sha256": local_payload.get("semantic_payload_sha256"),
        "status_counts": dict(sorted(status_counts.items())),
    }
    if performance_publication_rights == "CLEARED":
        public["benchmark_decimal_return"] = local_payload.get("benchmark_decimal_return")
        public["rows"] = local_payload.get("rows", [])
    return public


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_output_paths(args.local_output, args.public_output)

    config = load_monthly_market_config(args.config)
    manifest = _read_json(args.source_manifest)
    validate_source_manifest_period(manifest, args.period)
    held_security_ids = _held_ids(_read_json(args.held_securities))
    evidence_resolutions = _read_json(args.evidence_resolutions)
    if not isinstance(evidence_resolutions, dict):
        raise ValueError("evidence-resolutions must be a JSON object keyed by security_id")

    start_valuation_date = manifest.get("start_valuation_date")
    end_valuation_date = manifest.get("end_valuation_date")
    if not isinstance(start_valuation_date, str) or not isinstance(end_valuation_date, str):
        raise ValueError("source manifest requires start_valuation_date and end_valuation_date")

    file_map = {
        "start_price": args.start_price_pdf,
        "end_price": args.end_price_pdf,
        "benchmark": args.benchmark_pdf,
        "ex_rights": args.ex_rights_pdf,
        "listed_changes": args.listed_changes_pdf,
    }
    provenance: dict[str, Any] = {"sources": {}}
    source_hashes: list[str] = []
    for key, path in file_map.items():
        meta = _source_meta(manifest, key)
        result = source_provenance(path, locator=meta["locator"], retrieved_at=meta["retrieved_at"])
        provenance["sources"][key] = result
        if result.get("status") != "SOURCE_OK":
            blocked = {
                "status": "BLOCK_SOURCE_UNAVAILABLE",
                "period": args.period,
                "rows": [],
                "provenance": provenance,
            }
            args.local_output.write_text(json.dumps(blocked, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            public = build_public_artifact(
                blocked,
                performance_publication_rights=str(manifest.get("performance_publication_rights", "NOT_CLEARED")),
                artifact_version=str(config.get("artifact_version", "UNKNOWN")),
                code_commit=args.code_commit,
                source_hashes=source_hashes,
            )
            args.public_output.write_text(json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            return 2
        source_hashes.append(str(result["source_sha256"]))

    start_text = extract_pdf_text(args.start_price_pdf)
    end_text = extract_pdf_text(args.end_price_pdf)
    benchmark_text = extract_pdf_text(args.benchmark_pdf)
    ex_rights_text = extract_pdf_text(args.ex_rights_pdf)
    listed_changes_text = extract_pdf_text(args.listed_changes_pdf)

    start_prices = parse_stock_price_table_text(
        start_text,
        period=start_valuation_date[:7],
        valuation_date=start_valuation_date,
        security_ids=held_security_ids,
        price_role="start",
    )
    end_prices = parse_stock_price_table_text(
        end_text,
        period=end_valuation_date[:7],
        valuation_date=end_valuation_date,
        security_ids=held_security_ids,
        price_role="end",
    )
    benchmark_roi = parse_topix_monthly_roi_text(benchmark_text, args.period)
    ex_rights = parse_ex_rights_text(ex_rights_text, args.period, held_security_ids)
    listed_changes = parse_listed_company_changes_text(listed_changes_text, args.period, held_security_ids)
    events = [*ex_rights.get("events", []), *listed_changes.get("events", [])]

    payload = build_monthly_return_payload(
        args.period,
        held_security_ids,
        start_prices,
        end_prices,
        benchmark_roi,
        events,
        evidence_resolutions,
        provenance,
        config,
    )
    payload["code_commit"] = args.code_commit
    payload["source_hashes"] = sorted(source_hashes)
    args.local_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.local_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    public = build_public_artifact(
        payload,
        performance_publication_rights=str(manifest.get("performance_publication_rights", "NOT_CLEARED")),
        artifact_version=str(config.get("artifact_version", "UNKNOWN")),
        code_commit=args.code_commit,
        source_hashes=source_hashes,
    )
    args.public_output.write_text(json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if payload.get("status") == "MONTHLY_RETURN_OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
