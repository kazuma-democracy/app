from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Iterable, Mapping

from wa_commons.identity.enrich import normalize_edinet_security_code

EXPECTED_BENCHMARK_ID = "JPX:TOPIX_TOTAL_RETURN:6000"
EXPECTED_INDEX_CODE = "0000"
EXPECTED_RETURN_INDEX_CODE = "6000"
REQUIRED_HEADERS = {
    "Date",
    "Local Code",
    "Name",
    "ISIN",
    "CMV",
    "Index Code",
    "Index Name",
}


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_benchmark_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_topix_month_end_csv(path: str | Path) -> list[dict[str, str]]:
    raw = Path(path).read_bytes()
    text: str | None = None
    for encoding in ("utf-8-sig", "cp932"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("TOPIX master CSV encoding is unsupported")
    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    missing = REQUIRED_HEADERS - headers
    if missing:
        raise ValueError(f"TOPIX master CSV missing required headers: {sorted(missing)}")
    return [dict(row) for row in reader]


def _validate_config(config: Mapping[str, Any]) -> None:
    if config.get("benchmark_id") != EXPECTED_BENCHMARK_ID:
        raise ValueError("unsupported benchmark_id")
    if str(config.get("index_code")) != EXPECTED_INDEX_CODE:
        raise ValueError("unsupported TOPIX Index Code")
    if str(config.get("return_index_code")) != EXPECTED_RETURN_INDEX_CODE:
        raise ValueError("unsupported TOPIX return index code")
    if config.get("weight_basis") != "CMV":
        raise ValueError("TOPIX benchmark weight basis must be CMV")
    if config.get("raw_publication") is not False:
        raise ValueError("licensed TOPIX raw rows must not be public")


def _expected_date(config: Mapping[str, Any]) -> str:
    text = str(config.get("effective_date", "")).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError("effective_date must be YYYY-MM-DD")
    return text.replace("-", "")


def _normalize_row(raw: Mapping[str, Any], expected_date: str) -> dict[str, Any]:
    date = str(raw.get("Date", "")).strip()
    if date != expected_date:
        raise ValueError("TOPIX row effective date does not match pinned effective date")
    if str(raw.get("Index Code", "")).strip() != EXPECTED_INDEX_CODE:
        raise ValueError("TOPIX row Index Code must be 0000")
    if str(raw.get("Index Name", "")).strip().upper() != "TOPIX":
        raise ValueError("TOPIX row Index Name must be TOPIX")

    provider_code = str(raw.get("Local Code", "")).strip().upper()
    code = normalize_edinet_security_code(provider_code)
    if len(code) != 4 or not code.isalnum():
        raise ValueError("TOPIX Local Code cannot be normalized to a four-character security code")
    try:
        cmv = Decimal(str(raw.get("CMV", "")).strip())
    except Exception as exc:
        raise ValueError("TOPIX CMV must be numeric") from exc
    if not cmv.is_finite() or cmv <= 0:
        raise ValueError("TOPIX CMV must be finite and positive")

    return {
        "security_id": f"TSE:{code}",
        "security_code": code,
        "provider_local_code": provider_code,
        "name": str(raw.get("Name", "")).strip(),
        "isin": str(raw.get("ISIN", "")).strip().upper(),
        "cmv_jpy": cmv,
    }


def _format_weights(rows: list[dict[str, Any]], decimals: int) -> list[dict[str, Any]]:
    quantum = Decimal(1).scaleb(-decimals)
    total_cmv = sum(row["cmv_jpy"] for row in rows)
    weights = [
        (row["cmv_jpy"] / total_cmv).quantize(quantum, rounding=ROUND_HALF_EVEN)
        for row in rows
    ]
    target = Decimal("1").quantize(quantum)
    residual = target - sum(weights)
    if residual:
        recipient = min(
            range(len(rows)),
            key=lambda index: (-rows[index]["cmv_jpy"], rows[index]["security_id"]),
        )
        weights[recipient] += residual
    if sum(weights) != target:
        raise ValueError("reconstructed TOPIX weights do not reconcile to 1.0")

    output: list[dict[str, Any]] = []
    for row, weight in zip(rows, weights, strict=True):
        output.append({
            "security_id": row["security_id"],
            "security_code": row["security_code"],
            "provider_local_code": row["provider_local_code"],
            "name": row["name"],
            "isin": row["isin"],
            "cmv_jpy": format(row["cmv_jpy"], "f"),
            "benchmark_weight": f"{weight:.{decimals}f}",
        })
    return output


def build_topix_snapshot(
    rows: Iterable[Mapping[str, Any]],
    config: Mapping[str, Any],
    source_sha256: str,
) -> dict[str, Any]:
    _validate_config(config)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(source_sha256)):
        raise ValueError("source SHA-256 must be 64 hexadecimal characters")
    normalized = [_normalize_row(row, _expected_date(config)) for row in rows]
    if not normalized:
        raise ValueError("TOPIX master contains no rows")
    normalized.sort(key=lambda row: row["security_id"])
    security_ids = [row["security_id"] for row in normalized]
    if len(security_ids) != len(set(security_ids)):
        raise ValueError("duplicate Local Code after normalization")

    decimals = int(config.get("semantic_weight_decimals", 12))
    if decimals != 12:
        raise ValueError("semantic_weight_decimals must be 12")
    output_rows = _format_weights(normalized, decimals)
    config_sha = _canonical_sha256(dict(config))
    total_cmv = sum(Decimal(row["cmv_jpy"]) for row in output_rows)
    manifest = {
        "artifact_version": config["artifact_version"],
        "benchmark_id": config["benchmark_id"],
        "provider": config["provider"],
        "constituent_product": config["constituent_product"],
        "effective_date": config["effective_date"],
        "available_at": config["available_at"],
        "index_code": config["index_code"],
        "return_index_code": config["return_index_code"],
        "currency": config["currency"],
        "weight_basis": config["weight_basis"],
        "rights_mode": config["rights_mode"],
        "raw_publication": config["raw_publication"],
        "source_sha256": str(source_sha256).lower(),
        "config_sha256": config_sha,
        "constituent_count": len(output_rows),
        "total_cmv_jpy": format(total_cmv, "f"),
        "benchmark_weight_sum": f"{sum(Decimal(row['benchmark_weight']) for row in output_rows):.{decimals}f}",
    }
    manifest["semantic_snapshot_sha256"] = _canonical_sha256({"manifest": manifest, "rows": output_rows})
    return {"manifest": manifest, "rows": output_rows}
