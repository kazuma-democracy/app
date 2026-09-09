from __future__ import annotations

import hashlib
import json
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
