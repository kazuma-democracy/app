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
