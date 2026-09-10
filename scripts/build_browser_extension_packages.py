from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from wa_commons.public_client.browser_pack import (
    validate_public_browser_pack,
)

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "clients/browser-extension/common"
TARGET_ROOT = ROOT / "clients/browser-extension"
BROWSERS = ("chrome", "edge", "firefox", "safari")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ALLOWED_PERMISSIONS = {"storage", "activeTab", "scripting"}


@dataclass(frozen=True)
class PackageResult:
    browser: str
    manifest_path: Path
    zip_path: Path
    sha256: str
    permissions: tuple[str, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _merge(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _secret_like(path: Path) -> bool:
    lowered = path.as_posix().lower()
    tokens = (".env", "secret", "private_key", "credentials")
    return any(token in lowered for token in tokens) or path.suffix.lower() in {
        ".pem", ".key", ".p12", ".pfx"
    }


def _audit_manifest(manifest: dict) -> tuple[str, ...]:
    if manifest.get("manifest_version") != 3:
        raise ValueError("browser package must use Manifest V3")
    permissions = tuple(str(x) for x in manifest.get("permissions", []))
    unexpected = set(permissions) - ALLOWED_PERMISSIONS
    if unexpected:
        raise ValueError(f"unsupported extension permissions: {sorted(unexpected)}")
    if manifest.get("host_permissions", []) != []:
        raise ValueError("persistent host permissions are forbidden")
    raw = json.dumps(manifest, ensure_ascii=False)
    if "<all_urls>" in raw:
        raise ValueError("persistent all-urls access is forbidden")
    if re.search(r"https?://[^\s\"']+\.m?js(?:[?#][^\s\"']*)?", raw, re.I):
        raise ValueError("remote executable script is forbidden")
    return permissions


def _iter_common_files() -> list[Path]:
    files: list[Path] = []
    for path in COMMON.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink is forbidden in browser package: {path}")
        if not path.is_file():
            continue
        rel = path.relative_to(COMMON)
        if rel.as_posix() in {"manifest.base.json", "data/README.md"}:
            continue
        if _secret_like(rel):
            raise ValueError(f"secret-like file is forbidden: {rel}")
        files.append(rel)
    return sorted(files, key=lambda item: item.as_posix())


def _copy_common(staging: Path) -> None:
    for rel in _iter_common_files():
        source = COMMON / rel
        target = staging / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def _write_zip(source_root: Path, zip_path: Path) -> None:
    members = sorted(
        (path.relative_to(source_root) for path in source_root.rglob("*") if path.is_file()),
        key=lambda item: item.as_posix(),
    )
    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for rel in members:
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"unsafe archive path: {rel}")
            if _secret_like(rel):
                raise ValueError(f"secret-like file is forbidden: {rel}")
            info = zipfile.ZipInfo(rel.as_posix(), ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (source_root / rel).read_bytes())


def _load_valid_pack(pack_path: Path) -> dict:
    pack = _load_json(pack_path)
    state = pack.get("manifest", {}).get("release_state")
    if state != "READY_FOR_CAPABILITY_TEST":
        raise ValueError(f"public Evidence Pack is not ready for packaging: {state}")
    validate_public_browser_pack(pack)
    return pack


def build_browser_package(
    browser: str,
    pack_path: Path,
    output_root: Path,
) -> PackageResult:
    if browser not in BROWSERS:
        raise ValueError(f"unsupported browser: {browser}")
    pack = _load_valid_pack(Path(pack_path))

    output_root = Path(output_root)
    staging = output_root / browser / "extension"
    zip_path = output_root / f"wa-commons-{browser}.zip"
    if staging.exists():
        shutil.rmtree(staging)
    if zip_path.exists():
        zip_path.unlink()
    staging.mkdir(parents=True, exist_ok=True)

    base = _load_json(COMMON / "manifest.base.json")
    overlay = _load_json(TARGET_ROOT / browser / "manifest.overrides.json")
    manifest = _merge(base, overlay)
    permissions = _audit_manifest(manifest)

    _copy_common(staging)
    manifest_path = staging / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    data_path = staging / "data/wa-public-evidence-pack.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(pack, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    _write_zip(staging, zip_path)
    return PackageResult(
        browser=browser,
        manifest_path=manifest_path,
        zip_path=zip_path,
        sha256=sha256_file(zip_path),
        permissions=permissions,
    )


def build_all_packages(
    pack_path: Path,
    output_root: Path,
) -> list[PackageResult]:
    return [
        build_browser_package(browser, pack_path, output_root)
        for browser in BROWSERS
    ]
