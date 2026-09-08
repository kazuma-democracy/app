from __future__ import annotations

import json

import pytest


def runner_api():
    try:
        from wa_commons.evidence.tse_coverage import run_tse_coverage_local
    except ImportError as exc:
        pytest.fail(f"TSE coverage local runner missing: {exc}")
    return run_tse_coverage_local


def test_local_runner_reuses_existing_catalog_and_mod_observations(tmp_path):
    run = runner_api()

    identity = {
        "manifest": {"entity_count": 2, "semantic_identity_sha256": "identity-sha"},
        "entities": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "review_state": "CONFIRMED",
                "identifiers": [
                    {"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111", "source": {}}
                ],
            },
            {
                "entity_id": "wa:org:jp:tse:1002",
                "review_state": "CONFIRMED",
                "identifiers": [],
            },
        ],
    }
    config = {
        "source_catalog": [
            {
                "source_id": "jp-mod-procurement",
                "category": "military_contract",
                "integration_state": "integrated",
                "run_state": "complete",
                "provenance": {"source_sha256": "mod-sha"},
            },
            {
                "source_id": "jp-political-finance",
                "category": "political_finance",
                "integration_state": "integrated",
                "run_state": "complete",
                "identity_linkage_state": "unresolved",
                "provenance": {"source_sha256": "political-sha"},
            },
            {
                "source_id": "sipri-arms-industry",
                "category": "arms_industry",
                "integration_state": "not_integrated",
                "run_state": "not_run",
            },
        ]
    }
    mod_observations = [
        {
            "corporate_number": "1111111111111",
            "identity_decision": "AUTO_LINK",
            "supplier_name": "Published supplier",
        }
    ]

    identity_path = tmp_path / "identity.json"
    config_path = tmp_path / "coverage-config.json"
    mod_path = tmp_path / "mod-observations.json"
    local_path = tmp_path / "coverage-local.json"
    public_path = tmp_path / "coverage-public.json"
    identity_path.write_text(json.dumps(identity), encoding="utf-8")
    config_path.write_text(json.dumps(config), encoding="utf-8")
    mod_path.write_text(json.dumps(mod_observations), encoding="utf-8")

    result = run(
        identity_path=identity_path,
        coverage_config_path=config_path,
        mod_observations_path=mod_path,
        local_output=local_path,
        public_output=public_path,
        code_commit="deadbeef",
    )

    assert result["manifest"]["identity_entity_count"] == 2
    assert result["manifest"]["state_counts"] == {
        "no_match": 0,
        "not_integrated": 2,
        "observed": 1,
        "unknown": 0,
        "unresolved_identity": 3,
    }
    assert result["manifest"]["source_state_counts"]["jp-mod-procurement"] == {
        "observed": 1,
        "unresolved_identity": 1,
    }
    assert json.loads(local_path.read_text(encoding="utf-8"))["matrix"]["cell_count"] == 6
    public = json.loads(public_path.read_text(encoding="utf-8"))
    assert "matrix" not in public
    assert public["source_catalog"] == result["source_catalog"]
