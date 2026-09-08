from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from test_tse_policy_screening import coverage_fixture, identity_fixture, mod_observation_fixture


def test_cli_writes_local_and_public_outputs_from_local_inputs(tmp_path):
    root = Path(__file__).parents[1]
    identity = tmp_path / "identity.json"
    coverage = tmp_path / "coverage.json"
    observations = tmp_path / "observations.json"
    local_output = tmp_path / "local-screening.json"
    public_output = tmp_path / "public-screening.json"
    identity.write_text(json.dumps(identity_fixture()), encoding="utf-8")
    coverage.write_text(json.dumps(coverage_fixture()), encoding="utf-8")
    observations.write_text(json.dumps([mod_observation_fixture()]), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "run_tse_policy_screening.py"),
            "--identity", str(identity),
            "--coverage", str(coverage),
            "--mod-observations", str(observations),
            "--policies", str(root / "schemas" / "examples" / "user-policy.examples.json"),
            "--local-output", str(local_output),
            "--public-output", str(public_output),
            "--code-commit", "test-commit",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    local = json.loads(local_output.read_text(encoding="utf-8"))
    public = json.loads(public_output.read_text(encoding="utf-8"))
    assert local["view_count"] == 6
    assert public["view_count"] == 6
    assert "views" not in public
    assert local["tse_screening_sha256"] == public["tse_screening_sha256"]
