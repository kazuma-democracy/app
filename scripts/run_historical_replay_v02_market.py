from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from wa_commons.portfolio.monthly_market import (
    build_security_total_wealth_payload,
    extract_pdf_text,
    load_monthly_market_config,
    parse_ex_rights_text,
    parse_listed_company_changes_text,
    parse_stock_price_table_text,
    parse_topix_monthly_roi_text,
    source_provenance,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build post-freeze v0.2 market inputs from explicit local files."
    )
    parser.add_argument("--frozen-targets", required=True, type=Path)
    parser.add_argument("--period", required=True)
    parser.add_argument("--start-price-pdf", required=True, type=Path)
    parser.add_argument("--end-price-pdf", required=True, type=Path)
    parser.add_argument("--benchmark-pdf", required=True, type=Path)
    parser.add_argument("--ex-rights-pdf", required=True, type=Path)
    parser.add_argument("--listed-changes-pdf", required=True, type=Path)
    parser.add_argument("--evidence-resolutions", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def derive_held_security_ids(targets: dict[str, Any], period: str) -> list[str]:
    if targets.get("status") != "HISTORICAL_REPLAY_TARGETS_FROZEN":
        raise ValueError("frozen targets are required before market access")
    window = targets.get("window")
    if not isinstance(window, list) or period not in window:
        raise ValueError(f"period {period} is not in frozen targets")
    months = [
        month for month in targets.get("months", [])
        if isinstance(month, dict) and month.get("period") == period
    ]
    if len(months) != 1:
        raise ValueError(f"frozen targets require exactly one month entry for {period}")
    changed = months[0].get("direct_changed_security_ids")
    if not isinstance(changed, dict):
        raise ValueError("frozen targets missing direct_changed_security_ids")
    held = {"TSE:1475"}
    for arm_id in ("P1", "P2"):
        values = changed.get(arm_id, [])
        if not isinstance(values, list):
            raise ValueError(f"direct_changed_security_ids.{arm_id} must be a list")
        held.update(str(value) for value in values)
    return sorted(held)


def run_market_bundle(
    *,
    frozen_targets_path: str | Path,
    period: str,
    start_price_pdf: str | Path,
    end_price_pdf: str | Path,
    benchmark_pdf: str | Path,
    ex_rights_pdf: str | Path,
    listed_changes_pdf: str | Path,
    evidence_resolutions_path: str | Path,
    source_manifest_path: str | Path,
    config_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    targets = _read_json(frozen_targets_path)
    if not isinstance(targets, dict):
        raise ValueError("frozen targets must be a JSON object")
    held_security_ids = derive_held_security_ids(targets, period)

    config = load_monthly_market_config(config_path)
    manifest = _read_json(source_manifest_path)
    if not isinstance(manifest, dict) or manifest.get("period") != period:
        raise ValueError("source manifest period mismatch")
    evidence_resolutions = _read_json(evidence_resolutions_path)
    if not isinstance(evidence_resolutions, dict):
        raise ValueError("evidence-resolutions must be a JSON object keyed by security_id")
    start_date = manifest.get("start_valuation_date")
    end_date = manifest.get("end_valuation_date")
    if not isinstance(start_date, str) or not isinstance(end_date, str):
        raise ValueError("source manifest requires start_valuation_date and end_valuation_date")

    file_map = {
        "start_price": Path(start_price_pdf),
        "end_price": Path(end_price_pdf),
        "benchmark": Path(benchmark_pdf),
        "ex_rights": Path(ex_rights_pdf),
        "listed_changes": Path(listed_changes_pdf),
    }
    provenance: dict[str, Any] = {"sources": {}}
    source_hashes: list[str] = []
    for key, path in file_map.items():
        meta = _source_meta(manifest, key)
        source = source_provenance(
            path, locator=meta["locator"], retrieved_at=meta["retrieved_at"]
        )
        provenance["sources"][key] = source
        if source.get("status") != "SOURCE_OK":
            result = {"status": "BLOCK_SOURCE_UNAVAILABLE", "period": period}
            Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result
        source_hashes.append(str(source["source_sha256"]))

    start_text = extract_pdf_text(start_price_pdf)
    end_text = extract_pdf_text(end_price_pdf)
    benchmark_text = extract_pdf_text(benchmark_pdf)
    ex_rights_text = extract_pdf_text(ex_rights_pdf)
    listed_changes_text = extract_pdf_text(listed_changes_pdf)

    start_prices = parse_stock_price_table_text(
        start_text, start_date[:7], start_date, held_security_ids, "start"
    )
    end_prices = parse_stock_price_table_text(
        end_text, end_date[:7], end_date, held_security_ids, "end"
    )
    ex_rights = parse_ex_rights_text(ex_rights_text, period, held_security_ids)
    listed_changes = parse_listed_company_changes_text(
        listed_changes_text, period, held_security_ids
    )
    events = [*ex_rights.get("events", []), *listed_changes.get("events", [])]
    security_returns = build_security_total_wealth_payload(
        period, held_security_ids, start_prices, end_prices, events,
        evidence_resolutions, provenance, config,
    )
    topix_roi = parse_topix_monthly_roi_text(benchmark_text, period)

    if security_returns.get("status") != "SECURITY_RETURNS_OK":
        status = "BLOCK_MARKET_DATA"
    elif topix_roi.get("status") != "BENCHMARK_ROI_OK":
        status = "BLOCK_BENCHMARK_MONTHLY_RETURN"
    else:
        status = "PROXY_MARKET_BUNDLE_OK"
    result = {
        "status": status,
        "period": period,
        "security_returns": security_returns,
        "topix_roi": topix_roi,
        "source_hashes": sorted(source_hashes),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_market_bundle(
        frozen_targets_path=args.frozen_targets,
        period=args.period,
        start_price_pdf=args.start_price_pdf,
        end_price_pdf=args.end_price_pdf,
        benchmark_pdf=args.benchmark_pdf,
        ex_rights_pdf=args.ex_rights_pdf,
        listed_changes_pdf=args.listed_changes_pdf,
        evidence_resolutions_path=args.evidence_resolutions,
        source_manifest_path=args.source_manifest,
        config_path=args.config,
        output_path=args.output,
    )
    return 0 if result.get("status") == "PROXY_MARKET_BUNDLE_OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
