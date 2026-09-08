from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from wa_commons.portfolio.benchmark_snapshot import write_topix_benchmark_mapping

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_topix_benchmark_mapping.py"


def _write_master(path: Path) -> None:
    path.write_text(
        "Date,Local Code,Name,ISIN,CMV,Index Code,Index Name\n"
        "20260831,10000,Alpha,JP0000000001,60,0000,TOPIX\n"
        "20260831,10010,Beta,JP0000000002,40,0000,TOPIX\n",
        encoding="utf-8-sig",
    )


def _write_identity(path: Path) -> None:
    payload = {
        "manifest": {"semantic_identity_sha256": "b" * 64},
        "entities": [
            {"entity_id": "wa:org:jp:tse:1000", "review_state": "CONFIRMED", "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": "1000"}]},
            {"entity_id": "wa:org:jp:tse:1001", "review_state": "UNRESOLVED", "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": "1001"}]},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_writer_rejects_same_local_and_public_path(tmp_path):
    payload = {"manifest": {"semantic_mapping_sha256": "a" * 64}, "rows": []}
    target = tmp_path / "same.json"
    with pytest.raises(ValueError, match="must differ"):
        write_topix_benchmark_mapping(payload, target, target)


def test_cli_writes_local_rows_and_aggregate_only_public_manifest(tmp_path):
    master = tmp_path / "topix.csv"
    identity = tmp_path / "identity.json"
    local_output = tmp_path / "local.json"
    public_output = tmp_path / "public.json"
    _write_master(master)
    _write_identity(identity)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--master", str(master),
            "--identity", str(identity),
            "--local-output", str(local_output),
            "--public-output", str(public_output),
            "--code-commit", "test-commit",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr

    local_payload = json.loads(local_output.read_text(encoding="utf-8"))
    public_payload = json.loads(public_output.read_text(encoding="utf-8"))
    public_text = public_output.read_text(encoding="utf-8")

    assert len(local_payload["rows"]) == 2
    assert public_payload["mapping_summary"]["mapped"]["count"] == 1
    assert public_payload["mapping_summary"]["unresolved_identity"]["count"] == 1
    assert public_payload["code_commit"] == "test-commit"
    assert "rows" not in public_payload
    assert "wa:org:jp:tse:1000" not in public_text
    assert "JP0000000001" not in public_text
    assert "10000" not in public_text


def test_cli_help_exposes_no_network_acquisition_option():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    help_text = result.stdout.lower()
    assert "--url" not in help_text
    assert "--download" not in help_text


def _write_public_weight(path: Path, date: str = "20260831") -> None:
    text = (
        "日付,銘柄名,コード,業種,TOPIXに占める個別銘柄のウエイト,ニューインデックス区分\n"
        f"{date},Alpha,1000,建設業,60.0000%,TOPIX Mid400\n"
        f"{date},Beta,1001,建設業,40.0000%,TOPIX Small 1\n"
    )
    path.write_bytes(text.encode("cp932"))


def _write_public_config(path: Path) -> None:
    payload = {
        "artifact_version": "m3.3b-topix-benchmark-v0.2",
        "benchmark_id": "JPX:TOPIX_TOTAL_RETURN:6000",
        "provider": "JPX Market Innovation & Research, Inc.",
        "constituent_product": "TOPIX Component Weight List",
        "effective_date": "2026-08-31",
        "available_at": "2026-09-30T16:20:00+09:00",
        "index_code": "0000",
        "return_index_code": "6000",
        "currency": "JPY",
        "weight_basis": "PROVIDER_PUBLISHED_WEIGHT",
        "semantic_weight_decimals": 12,
        "published_weight_percent_decimals": 4,
        "published_weight_sum_tolerance": "0.000100",
        "rights_mode": "official_public_web_terms_apply_no_raw_redistribution_assumed",
        "raw_publication": False,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cli_accepts_public_weight_snapshot_without_network(tmp_path):
    public_weight = tmp_path / "topixweight_j.csv"
    config = tmp_path / "config.json"
    identity = tmp_path / "identity.json"
    local_output = tmp_path / "local.json"
    public_output = tmp_path / "public.json"
    _write_public_weight(public_weight)
    _write_public_config(config)
    _write_identity(identity)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--public-weight", str(public_weight),
            "--config", str(config),
            "--identity", str(identity),
            "--local-output", str(local_output),
            "--public-output", str(public_output),
            "--code-commit", "test-commit",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(public_output.read_text(encoding="utf-8"))
    assert payload["weight_basis"] == "PROVIDER_PUBLISHED_WEIGHT"
    assert payload["mapping_summary"]["mapped"]["count"] == 1
    assert payload["mapping_summary"]["unresolved_identity"]["count"] == 1


def test_cli_public_weight_uses_versioned_default_config(tmp_path):
    public_weight = tmp_path / "topixweight_j.csv"
    identity = tmp_path / "identity.json"
    local_output = tmp_path / "local.json"
    public_output = tmp_path / "public.json"
    _write_public_weight(public_weight, date="20260731")
    _write_identity(identity)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--public-weight", str(public_weight),
            "--identity", str(identity),
            "--local-output", str(local_output),
            "--public-output", str(public_output),
            "--code-commit", "test-commit",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(public_output.read_text(encoding="utf-8"))
    assert payload["artifact_version"] == "m3.3b-topix-benchmark-v0.2"
    assert payload["effective_date"] == "2026-07-31"
    assert payload["available_at"] == "2026-08-31T16:20:00+09:00"


def test_cli_reports_not_yet_published_for_stale_public_weight(tmp_path):
    public_weight = tmp_path / "topixweight_j.csv"
    text = (
        "日付,銘柄名,コード,業種,TOPIXに占める個別銘柄のウエイト,ニューインデックス区分\n"
        "20260630,Alpha,1000,建設業,100.0000%,TOPIX Mid400\n"
    )
    public_weight.write_bytes(text.encode("cp932"))
    identity = tmp_path / "identity.json"
    _write_identity(identity)
    local_output = tmp_path / "local.json"
    public_output = tmp_path / "public.json"

    result = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--public-weight", str(public_weight),
            "--identity", str(identity),
            "--local-output", str(local_output),
            "--public-output", str(public_output),
            "--code-commit", "test-commit",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "NOT_YET_PUBLISHED" in result.stderr
    assert not local_output.exists()
    assert not public_output.exists()
