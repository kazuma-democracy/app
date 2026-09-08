from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_tse_coverage_cli_exposes_only_local_input_arguments():
    script = Path("scripts/run_tse_evidence_coverage.py")
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    help_text = result.stdout
    for option in (
        "--identity",
        "--coverage-config",
        "--mod-observations",
        "--local-output",
        "--public-output",
        "--code-commit",
    ):
        assert option in help_text
    assert "--download" not in help_text
    assert "--url" not in help_text
