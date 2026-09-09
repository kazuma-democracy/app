from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
import hashlib
from io import StringIO
import json
import re
from typing import Any, Mapping

from wa_commons.identity.normalize import normalize_security_code


_WEIGHT_QUANTUM = Decimal("0.000000000001")
_TSE_CODE_RE = re.compile(r"[0-9A-Z]{4}")
_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}")


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_published_as_of(rows: list[list[str]]) -> str:
    for row in rows:
        if not row:
            continue
        if str(row[0]).strip().lower() != "fund holdings as of":
            continue
        if len(row) < 2 or not str(row[1]).strip():
            break
        text = str(row[1]).strip()
        try:
            return datetime.strptime(text, "%b %d, %Y").date().isoformat()
        except ValueError as exc:
            raise ValueError("invalid Fund Holdings as of date") from exc
    raise ValueError("Fund Holdings as of date not found")


def _header_index(rows: list[list[str]]) -> int:
    required = {"Ticker", "Name", "Asset Class", "Market Value"}
    for index, row in enumerate(rows):
        if required.issubset({str(value).strip() for value in row}):
            return index
    raise ValueError("1475 holdings header not found")


def _decimal_market_value(value: object) -> Decimal:
    text = str(value or "").replace(",", "").strip()
    try:
        amount = Decimal(text)
    except Exception as exc:
        raise ValueError("invalid equity market value") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("invalid equity market value")
    return amount


def _normalize_tse_code(value: object) -> str:
    code = normalize_security_code(value).strip().upper()
    if not _TSE_CODE_RE.fullmatch(code):
        raise ValueError(f"invalid TSE security code: {value!r}")
    return code


def _normalize_rows(parsed_rows: list[list[str]], header_index: int) -> list[dict[str, Any]]:
    header = [str(value).strip() for value in parsed_rows[header_index]]
    index = {name: header.index(name) for name in ("Ticker", "Name", "Asset Class", "Market Value")}
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in parsed_rows[header_index + 1 :]:
        if not raw or all(not str(value).strip() for value in raw):
            continue
        padded = list(raw) + [""] * max(0, len(header) - len(raw))
        asset_class = str(padded[index["Asset Class"]]).strip()
        if asset_class.casefold() != "equity":
            continue
        code = _normalize_tse_code(padded[index["Ticker"]])
        if code in seen:
            raise ValueError(f"duplicate TSE security code: {code}")
        seen.add(code)
        output.append(
            {
                "security_id": f"TSE:{code}",
                "security_code": code,
                "name": str(padded[index["Name"]]).strip(),
                "asset_class": "Equity",
                "equity_market_value_decimal": _decimal_market_value(
                    padded[index["Market Value"]]
                ),
            }
        )
    if not output:
        raise ValueError("1475 holdings contains no equity rows")
    output.sort(key=lambda row: row["security_id"])
    return output


def _apply_control_weights(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    total = sum((row["equity_market_value_decimal"] for row in rows), Decimal(0))
    unrounded = {
        row["security_id"]: row["equity_market_value_decimal"] / total
        for row in rows
    }
    rounded = {
        security_id: weight.quantize(_WEIGHT_QUANTUM)
        for security_id, weight in unrounded.items()
    }
    residual = Decimal("1.000000000000") - sum(rounded.values(), Decimal(0))
    if residual:
        recipient = sorted(
            rows,
            key=lambda row: (-unrounded[row["security_id"]], row["security_id"]),
        )[0]["security_id"]
        rounded[recipient] += residual
    result: list[dict[str, str]] = []
    for row in rows:
        result.append(
            {
                "security_id": row["security_id"],
                "security_code": row["security_code"],
                "name": row["name"],
                "asset_class": row["asset_class"],
                "equity_market_value": format(row["equity_market_value_decimal"], "f"),
                "control_weight": format(rounded[row["security_id"]], ".12f"),
            }
        )
    return result


def parse_ishares_1475_holdings_csv(
    csv_text: str,
    *,
    as_of_date: str,
    source_sha256: str,
    retrieved_at: str,
    source_locator: str,
) -> dict[str, Any]:
    if not _SHA256_RE.fullmatch(str(source_sha256)):
        raise ValueError("source SHA-256 must be 64 hexadecimal characters")
    retrieved = datetime.fromisoformat(retrieved_at)
    if retrieved.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    parsed_rows = list(csv.reader(StringIO(csv_text)))
    published_as_of = _parse_published_as_of(parsed_rows)
    if published_as_of != as_of_date:
        raise ValueError("1475 holdings as-of date mismatch")
    rows = _apply_control_weights(_normalize_rows(parsed_rows, _header_index(parsed_rows)))
    equity_value_sum = sum(Decimal(row["equity_market_value"]) for row in rows)
    manifest = {
        "control_kind": "ISHARES_1475_POINT_IN_TIME",
        "as_of_date": as_of_date,
        "source_locator": source_locator,
        "source_sha256": source_sha256.lower(),
        "retrieved_at": retrieved_at,
        "equity_count": len(rows),
        "equity_market_value_sum": format(equity_value_sum, "f"),
        "control_weight_sum": format(
            sum(Decimal(row["control_weight"]) for row in rows), ".12f"
        ),
    }
    semantic = {
        "manifest": manifest,
        "rows": rows,
    }
    manifest["semantic_snapshot_sha256"] = _canonical_sha256(semantic)
    return {
        "status": "INVESTABLE_CONTROL_SNAPSHOT_OK",
        "manifest": manifest,
        "rows": rows,
    }



def map_investable_control_snapshot(
    snapshot: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    from wa_commons.portfolio.benchmark_snapshot import map_topix_snapshot

    compatible = {
        "manifest": dict(snapshot.get("manifest", {})),
        "rows": [
            {**dict(row), "benchmark_weight": str(row["control_weight"])}
            for row in snapshot.get("rows", [])
        ],
    }
    mapped = map_topix_snapshot(compatible, identity)
    mapped["manifest"]["allocation_role"] = "INVESTABLE_CONTROL"
    mapped["manifest"]["control_kind"] = "ISHARES_1475_POINT_IN_TIME"
    return mapped


from copy import deepcopy


def _policy_semantics_projection(config: Mapping[str, Any]) -> dict[str, Any]:
    contract = dict(config.get("input_contract", {}))
    return {
        "artifact_version": config.get("artifact_version"),
        "market_data_inputs_allowed": config.get("market_data_inputs_allowed"),
        "profile_id": contract.get("profile_id"),
        "profile_version": str(contract.get("profile_version")),
        "policy_sha256": contract.get("policy_sha256"),
        "unknown_handling": deepcopy(config.get("unknown_handling", {})),
        "numerical": deepcopy(config.get("numerical", {})),
        "arms": deepcopy(config.get("arms", [])),
    }


def bind_policy_compiler_inputs(
    base_config: Mapping[str, Any],
    mapped_control: Mapping[str, Any],
    screening: Mapping[str, Any],
) -> dict[str, Any]:
    before = _policy_semantics_projection(base_config)
    bound = deepcopy(dict(base_config))
    contract = dict(bound.get("input_contract", {}))
    benchmark_sha = str(mapped_control.get("manifest", {}).get("semantic_mapping_sha256", "")).strip()
    screening_sha = str(screening.get("tse_screening_sha256", "")).strip()
    if not _SHA256_RE.fullmatch(benchmark_sha):
        raise ValueError("mapped control semantic SHA-256 is missing or invalid")
    if not _SHA256_RE.fullmatch(screening_sha):
        raise ValueError("screening SHA-256 is missing or invalid")
    contract["benchmark_semantic_mapping_sha256"] = benchmark_sha.lower()
    contract["screening_sha256"] = screening_sha.lower()
    bound["input_contract"] = contract
    if _policy_semantics_projection(bound) != before:
        raise ValueError("policy semantics changed during input binding")
    return bound


def directly_changed_security_ids(
    policy_payload: Mapping[str, Any],
    arm_id: str,
) -> list[str]:
    arms = [arm for arm in policy_payload.get("arms", []) if str(arm.get("arm_id", "")) == arm_id]
    if len(arms) != 1:
        raise ValueError(f"policy arm not found or duplicated: {arm_id}")
    changed: set[str] = set()
    for row in arms[0].get("target_weights", []):
        instruction = str(row.get("instruction", ""))
        multiplier = Decimal(str(row.get("multiplier", "1")))
        if instruction in {"EXCLUDE", "UNDERWEIGHT"} and multiplier != Decimal("1"):
            security_id = str(row.get("security_id", "")).strip()
            if not security_id:
                raise ValueError("direct policy instruction missing security_id")
            changed.add(security_id)
    return sorted(changed)
