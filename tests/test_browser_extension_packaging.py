from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.build_browser_extension_packages import (
    build_all_packages,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_PACK = ROOT / "tests/fixtures/public-browser-pack.synthetic.json"
EXPECTED_BROWSERS = ["chrome", "edge", "firefox", "safari"]


def _zip_bytes(path: Path, member: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        return archive.read(member)


def test_four_packages_share_common_logic_and_minimal_permissions(tmp_path):
    results = build_all_packages(SYNTHETIC_PACK, tmp_path)
    assert [item.browser for item in results] == EXPECTED_BROWSERS

    logic_hashes = {}
    for result in results:
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["manifest_version"] == 3
        assert set(manifest.get("permissions", [])) <= {
            "storage", "activeTab", "scripting"
        }
        assert manifest.get("host_permissions", []) == []
        assert result.sha256 == sha256_file(result.zip_path)
        with zipfile.ZipFile(result.zip_path) as archive:
            assert "manifest.json" in archive.namelist()
            assert "manifest.base.json" not in archive.namelist()
            assert "data/wa-public-evidence-pack.json" in archive.namelist()
        logic_hashes[result.browser] = tuple(
            hashlib.sha256(_zip_bytes(result.zip_path, name)).hexdigest()
            for name in ("search.mjs", "popup.mjs", "page-hint.js")
        )
    assert len(set(logic_hashes.values())) == 1


def test_firefox_manifest_declares_id_and_no_data_collection(tmp_path):
    result = next(
        item for item in build_all_packages(SYNTHETIC_PACK, tmp_path)
        if item.browser == "firefox"
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    gecko = manifest["browser_specific_settings"]["gecko"]
    assert gecko["id"] == "wa-commons@kazuma-democracy.github.io"
    assert gecko["data_collection_permissions"]["required"] == ["none"]


def test_package_bytes_are_deterministic_across_output_roots(tmp_path):
    first = build_all_packages(SYNTHETIC_PACK, tmp_path / "first")
    second = build_all_packages(SYNTHETIC_PACK, tmp_path / "second")
    assert {
        item.browser: item.sha256 for item in first
    } == {
        item.browser: item.sha256 for item in second
    }


def test_packaging_rejects_non_ready_pack(tmp_path):
    payload = json.loads(SYNTHETIC_PACK.read_text(encoding="utf-8"))
    payload["manifest"]["release_state"] = "BLOCK_SOURCE_RIGHTS"
    blocked = tmp_path / "blocked.json"
    blocked.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not ready for packaging"):
        build_all_packages(blocked, tmp_path / "out")


def test_package_contains_no_secret_like_or_remote_script_paths(tmp_path):
    results = build_all_packages(SYNTHETIC_PACK, tmp_path)
    for result in results:
        with zipfile.ZipFile(result.zip_path) as archive:
            names = archive.namelist()
            assert not any(
                token in name.lower()
                for name in names
                for token in (".env", "secret", "private_key", "credentials")
            )
            manifest = json.loads(archive.read("manifest.json"))
            assert "http://" not in json.dumps(manifest)
            assert "https://" not in json.dumps(manifest)


def test_manifest_audit_rejects_persistent_host_access():
    from scripts.build_browser_extension_packages import _audit_manifest

    with pytest.raises(ValueError, match="persistent host permissions"):
        _audit_manifest({
            "manifest_version": 3,
            "permissions": ["storage"],
            "host_permissions": ["https://example.invalid/*"],
        })


def test_manifest_audit_rejects_remote_executable_script():
    from scripts.build_browser_extension_packages import _audit_manifest

    with pytest.raises(ValueError, match="remote executable script"):
        _audit_manifest({
            "manifest_version": 3,
            "permissions": ["storage"],
            "host_permissions": [],
            "background": {
                "service_worker": "https://example.invalid/worker.js"
            },
        })


def test_overlay_arrays_replace_instead_of_concatenate():
    from scripts.build_browser_extension_packages import _merge

    merged = _merge(
        {"permissions": ["storage", "activeTab"]},
        {"permissions": ["scripting"]},
    )
    assert merged["permissions"] == ["scripting"]
