from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "clients/browser-extension/common"


def _read(name: str) -> str:
    return (COMMON / name).read_text(encoding="utf-8")


def test_manifest_is_mv3_local_first_and_minimal():
    manifest = json.loads(_read("manifest.base.json"))
    assert manifest["manifest_version"] == 3
    assert manifest["default_locale"] == "ja"
    assert manifest["action"]["default_popup"] == "popup.html"
    assert set(manifest.get("permissions", [])) <= {
        "storage", "activeTab", "scripting"
    }
    assert manifest.get("host_permissions", []) == []
    assert "<all_urls>" not in json.dumps(manifest)


def test_popup_uses_only_packaged_module_code():
    html = _read("popup.html")
    js = _read("popup.mjs")
    assert '<script type="module" src="popup.mjs"></script>' in html
    assert not re.search(r'<script[^>]+src=["\']https?://', html, re.I)
    assert "runtime.getURL" in js
    assert "data/wa-public-evidence-pack.json" in js
    assert "eval(" not in js
    assert "new Function(" not in js
    assert "google-analytics" not in (html + js).lower()
    assert "sentry" not in (html + js).lower()


def test_logic_has_no_hard_coded_japanese_ui_copy():
    logic = _read("search.mjs") + _read("popup.mjs")
    assert re.search(r"[ぁ-んァ-ヶ一-龠]", logic) is None
    messages = json.loads(
        (COMMON / "_locales/ja/messages.json").read_text(encoding="utf-8")
    )
    assert "noneWarning" in messages
    assert "安全" in messages["noneWarning"]["message"]


def test_ui_copy_has_no_universal_moral_or_boycott_score():
    corpus = (
        _read("popup.html")
        + _read("popup.mjs")
        + (COMMON / "_locales/ja/messages.json").read_text(encoding="utf-8")
    )
    forbidden = (
        "悪い会社",
        "平和スコア",
        "ボイコットスコア",
        "危険度",
        "war profiteer",
        "bad company",
    )
    lowered = corpus.lower()
    assert all(token.lower() not in lowered for token in forbidden)


def test_common_data_directory_does_not_commit_real_pack():
    data_dir = COMMON / "data"
    assert (data_dir / "README.md").exists()
    assert not (data_dir / "wa-public-evidence-pack.json").exists()
