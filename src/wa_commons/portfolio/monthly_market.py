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
