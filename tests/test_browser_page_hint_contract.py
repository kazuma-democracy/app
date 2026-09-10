from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "clients/browser-extension/common"


def test_page_hint_is_search_only_and_private():
    popup = (COMMON / "popup.mjs").read_text(encoding="utf-8")
    hint = (COMMON / "page-hint.js").read_text(encoding="utf-8")
    assert "executeScript" in popup
    assert "searchCompanies" in popup
    assert "renderCompany(pageHint" not in popup
    assert "storage.local.set" not in hint
    assert "fetch(" not in hint
    assert "document.cookie" not in hint
    assert "localStorage" not in hint
    assert "sessionStorage" not in hint


def test_page_hint_is_bounded_and_hostname_is_context_only():
    popup = (COMMON / "popup.mjs").read_text(encoding="utf-8")
    hint = (COMMON / "page-hint.js").read_text(encoding="utf-8")
    assert ".slice(0, 256)" in hint
    assert "hostname" in hint
    assert "searchCompanies(pack, pageHint.hostname)" not in popup
    assert "pageHint.selectedText || pageHint.title" in popup


def test_manifest_still_has_no_persistent_host_access():
    manifest = json.loads(
        (COMMON / "manifest.base.json").read_text(encoding="utf-8")
    )
    assert manifest.get("host_permissions", []) == []
    assert "<all_urls>" not in json.dumps(manifest)
