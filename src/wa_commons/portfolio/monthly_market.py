from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def load_monthly_market_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_provenance(
    path: str | Path,
    *,
    locator: str,
    retrieved_at: str,
) -> dict[str, Any]:
    source_path = Path(path)
    base = {
        "source_path": str(source_path),
        "source_locator": locator,
        "retrieved_at": retrieved_at,
    }
    if not source_path.is_file():
        return {"status": "BLOCK_SOURCE_UNAVAILABLE", **base}
    return {
        "status": "SOURCE_OK",
        **base,
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    }


def extract_pdf_text(path: str | Path) -> str:
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    reader = PdfReader(str(source_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


_PRICE_LINE_RE = re.compile(r"^(?P<year>\d{4})/(?P<month>\d{2})\s+(?P<code>\d{4})\s+(?P<body>.+)$")
_NUM_RE = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")


def _decimal_text(value: str) -> str:
    return f"{Decimal(value.replace(',', '')):.12f}"


def _parse_price_candidate(line: str, period: str) -> dict[str, Any] | None:
    match = _PRICE_LINE_RE.match(line.strip())
    if not match:
        return None
    line_period = f"{match.group('year')}-{match.group('month')}"
    if line_period != period:
        return None
    numeric = [token for token in match.group('body').split() if _NUM_RE.match(token)]
    if len(numeric) < 17:
        return None
    tail = numeric[-17:]
    return {
        "security_code": match.group("code"),
        "close_price": _decimal_text(tail[7]),
        "close_day": int(tail[8].replace(',', '')),
    }


def parse_stock_price_table_text(
    text: str,
    period: str,
    valuation_date: str,
    security_ids: list[str],
    price_role: str,
) -> dict[str, Any]:
    if price_role not in {"start", "end"}:
        raise ValueError("price_role must be 'start' or 'end'")
    if not all(re.fullmatch(r"TSE:\d{4}", security_id) for security_id in security_ids):
        return {"status": "BLOCK_IDENTITY", "rows": []}

    valuation = date.fromisoformat(valuation_date)
    if valuation.strftime("%Y-%m") != period:
        raise ValueError("valuation_date must fall within period")

    candidates: dict[str, list[dict[str, Any]]] = {}
    for line in text.splitlines():
        candidate = _parse_price_candidate(line, period)
        if candidate is not None:
            candidates.setdefault(candidate["security_code"], []).append(candidate)

    rows: list[dict[str, Any]] = []
    for security_id in sorted(set(security_ids)):
        code = security_id.removeprefix("TSE:")
        code_rows = candidates.get(code, [])
        if not code_rows:
            return {"status": "BLOCK_START_PRICE" if price_role == "start" else "BLOCK_END_PRICE", "rows": []}
        matched = [row for row in code_rows if row["close_day"] == valuation.day]
        if len(matched) != 1:
            return {"status": "BLOCK_CORPORATE_ACTION", "rows": []}
        selected = matched[0]
        rows.append({
            "security_id": security_id,
            "security_code": code,
            "close_price": selected["close_price"],
            "close_date": valuation.isoformat(),
            "source_row_count": len(code_rows),
            "selection_reason": "UNIQUE_CLOSE_DATE_MATCH",
        })

    semantic = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "status": "PRICE_SNAPSHOT_OK",
        "period": period,
        "valuation_date": valuation.isoformat(),
        "price_role": price_role,
        "rows": rows,
        "semantic_rows_sha256": hashlib.sha256(semantic.encode("utf-8")).hexdigest(),
    }


_MONTH_ABBR = {
    "01": "Jan.", "02": "Feb.", "03": "Mar.", "04": "Apr.",
    "05": "May", "06": "Jun.", "07": "Jul.", "08": "Aug.",
    "09": "Sep.", "10": "Oct.", "11": "Nov.", "12": "Dec.",
}


def _canonical_security_ids(security_ids: list[str]) -> tuple[bool, set[str]]:
    if not all(re.fullmatch(r"TSE:\d{4}", security_id) for security_id in security_ids):
        return False, set()
    return True, {security_id.removeprefix("TSE:") for security_id in security_ids}


def parse_topix_monthly_roi_text(text: str, period: str) -> dict[str, Any]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", period)
    if not match:
        return {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN"}
    year, month = match.groups()
    marker = f"As of the End of {_MONTH_ABBR.get(month, '')} {year}"
    if marker not in text:
        return {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN", "period": period}

    values: list[str] = []
    for line in text.splitlines():
        row = re.match(r"^TOPIX\s+(-?\d+(?:\.\d+)?)\b", line.strip())
        if row:
            values.append(row.group(1))
    if len(values) != 1:
        return {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN", "period": period}

    percent = Decimal(values[0])
    return {
        "status": "BENCHMARK_ROI_OK",
        "period": period,
        "one_month_percent": f"{percent:.12f}",
        "decimal_return": f"{(percent / Decimal('100')):.12f}",
    }


def parse_ex_rights_text(text: str, period: str, security_ids: list[str]) -> dict[str, Any]:
    valid, requested = _canonical_security_ids(security_ids)
    if not valid:
        return {"status": "BLOCK_IDENTITY", "period": period, "events": []}

    events: list[dict[str, Any]] = []
    pattern = re.compile(
        r"^(?P<ex>\d{4}/\d{2}/\d{2})\s+(?P<code>\d{4})\s+.*?"
        r"(?P<record>\d{4}/\d{2}/\d{2})\s+Stock Split\s+(?P<ratio>\d+:\d+)\s*$"
    )
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match or match.group("code") not in requested:
            continue
        ex_date = match.group("ex").replace("/", "-")
        if not ex_date.startswith(period):
            continue
        code = match.group("code")
        events.append({
            "security_id": f"TSE:{code}",
            "security_code": code,
            "event_type": "STOCK_SPLIT",
            "ex_rights_date": ex_date,
            "record_date": match.group("record").replace("/", "-"),
            "split_ratio": match.group("ratio"),
        })
    events.sort(key=lambda event: (event["security_id"], event["ex_rights_date"], event["split_ratio"]))
    return {"status": "EVENTS_OK", "period": period, "events": events}


def parse_listed_company_changes_text(text: str, period: str, security_ids: list[str]) -> dict[str, Any]:
    valid, requested = _canonical_security_ids(security_ids)
    if not valid:
        return {"status": "BLOCK_IDENTITY", "period": period, "events": []}

    events: list[dict[str, Any]] = []
    section: str | None = None
    row_pattern = re.compile(r"^(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<code>\d{4})\b")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "Delisting":
            section = "DELISTING"
            continue
        if line in {"Margin Trading", "Name Change", "New Listings", "Listing"}:
            section = None
            continue
        if section != "DELISTING":
            continue
        match = row_pattern.match(line)
        if not match or match.group("code") not in requested:
            continue
        effective_date = match.group("date").replace("/", "-")
        if not effective_date.startswith(period):
            continue
        code = match.group("code")
        events.append({
            "security_id": f"TSE:{code}",
            "security_code": code,
            "event_type": "DELISTING",
            "effective_date": effective_date,
        })
    events.sort(key=lambda event: (event["security_id"], event["effective_date"]))
    return {"status": "EVENTS_OK", "period": period, "events": events}



def _row_price_map(snapshot: dict[str, Any]) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    for row in snapshot.get("rows", []):
        security_id = row.get("security_id")
        price = row.get("close_price")
        if isinstance(security_id, str) and price is not None:
            result[security_id] = Decimal(str(price))
    return result


def _semantic_decimal(value: Decimal, decimals: int) -> str:
    quantum = Decimal(1).scaleb(-decimals)
    return f"{value.quantize(quantum):.{decimals}f}"


def build_monthly_return_payload(
    period: str,
    held_security_ids: list[str],
    start_prices: dict[str, Any],
    end_prices: dict[str, Any],
    benchmark_roi: dict[str, Any],
    events: list[dict[str, Any]],
    evidence_resolutions: dict[str, dict[str, Any]],
    provenance: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if benchmark_roi.get("status") != "BENCHMARK_ROI_OK" or "decimal_return" not in benchmark_roi:
        return {"status": "BLOCK_BENCHMARK_MONTHLY_RETURN", "period": period, "rows": []}

    decimals = int(config.get("semantic_decimals", 12))
    start_map = _row_price_map(start_prices)
    end_map = _row_price_map(end_prices)
    events_by_security: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        security_id = event.get("security_id")
        if isinstance(security_id, str):
            events_by_security.setdefault(security_id, []).append(event)

    rows: list[dict[str, Any]] = []
    for security_id in sorted(set(held_security_ids)):
        base = {"security_id": security_id}
        if not re.fullmatch(r"TSE:\d{4}", security_id):
            rows.append({**base, "state": "BLOCK_IDENTITY"})
            continue
        if security_id not in start_map:
            rows.append({**base, "state": "BLOCK_START_PRICE"})
            continue
        if security_id not in end_map:
            rows.append({**base, "state": "BLOCK_END_PRICE"})
            continue

        resolution = evidence_resolutions.get(security_id)
        if not resolution or resolution.get("identity_state") != "RESOLVED":
            rows.append({**base, "state": "BLOCK_IDENTITY"})
            continue
        dividend_status = resolution.get("dividend_status")
        if dividend_status not in {"CONFIRMED_NONE", "CONFIRMED_CASH"}:
            rows.append({**base, "state": "BLOCK_DIVIDEND_EVIDENCE"})
            continue

        security_events = events_by_security.get(security_id, [])
        action_resolution = resolution.get("action_resolution")
        if security_events:
            if not isinstance(action_resolution, dict) or action_resolution.get("status") != "RESOLVED":
                rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                continue
            if len(security_events) != 1:
                rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                continue
            event = security_events[0]
            units = Decimal(str(action_resolution.get("end_units_per_start_unit", "0")))
            cash_consideration = Decimal(str(action_resolution.get("cash_consideration_per_start_unit", "0")))
            terminal_id = action_resolution.get("terminal_security_id")
            if units <= 0 or terminal_id != security_id:
                rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                continue
            if event.get("event_type") == "STOCK_SPLIT":
                ratio = str(event.get("split_ratio", ""))
                ratio_match = re.fullmatch(r"(\d+):(\d+)", ratio)
                if not ratio_match:
                    rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                    continue
                expected_units = Decimal(ratio_match.group(2)) / Decimal(ratio_match.group(1))
                if units != expected_units:
                    rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                    continue
            state = "RETURN_OK_ACTION_EXPLAINED"
        else:
            if action_resolution is not None:
                rows.append({**base, "state": "BLOCK_CORPORATE_ACTION"})
                continue
            units = Decimal("1")
            cash_consideration = Decimal("0")
            state = "RETURN_OK_NO_ACTION"

        dividend_cash = Decimal(str(resolution.get("dividend_cash_per_start_unit", "0")))
        if dividend_status == "CONFIRMED_NONE" and dividend_cash != 0:
            rows.append({**base, "state": "BLOCK_DIVIDEND_EVIDENCE"})
            continue

        start = start_map[security_id]
        end = end_map[security_id]
        if start <= 0:
            rows.append({**base, "state": "BLOCK_START_PRICE"})
            continue
        ending_wealth = end * units + dividend_cash + cash_consideration
        total_return = ending_wealth / start - Decimal("1")
        rows.append({
            **base,
            "state": state,
            "start_price": _semantic_decimal(start, decimals),
            "end_price": _semantic_decimal(end, decimals),
            "end_units_per_start_unit": _semantic_decimal(units, decimals),
            "dividend_cash_per_start_unit": _semantic_decimal(dividend_cash, decimals),
            "cash_consideration_per_start_unit": _semantic_decimal(cash_consideration, decimals),
            "ending_wealth_per_start_unit": _semantic_decimal(ending_wealth, decimals),
            "total_wealth_return": _semantic_decimal(total_return, decimals),
            "evidence_refs": sorted(str(ref) for ref in resolution.get("evidence_refs", [])),
        })

    blocked = any(str(row.get("state", "")).startswith("BLOCK_") for row in rows)
    semantic_payload = {
        "period": period,
        "benchmark_decimal_return": _semantic_decimal(Decimal(str(benchmark_roi["decimal_return"])), decimals),
        "rows": rows,
    }
    semantic = json.dumps(semantic_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "status": "MONTHLY_RETURN_BLOCKED" if blocked else "MONTHLY_RETURN_OK",
        "period": period,
        "benchmark_decimal_return": semantic_payload["benchmark_decimal_return"],
        "rows": rows,
        "provenance": provenance,
        "semantic_payload_sha256": hashlib.sha256(semantic.encode("utf-8")).hexdigest(),
    }
