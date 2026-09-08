from __future__ import annotations

import json

import pytest


def writer_api():
    try:
        from wa_commons.evidence.tse_coverage import write_tse_coverage
    except ImportError as exc:
        pytest.fail(f"TSE coverage writer missing: {exc}")
    return write_tse_coverage


def test_writer_keeps_row_level_matrix_local_and_public_output_aggregate_only(tmp_path):
    write = writer_api()
    payload = {
        "manifest": {
            "identity_entity_count": 3707,
            "coverage_semantic_sha256": "coverage-sha",
            "state_counts": {"observed": 1, "no_match": 3706},
        },
        "source_catalog": [
            {
                "source_id": "jp-mod-procurement",
                "category": "military_contract",
                "integration_state": "integrated",
                "provenance": {
                    "source_sha256": "source-sha",
                    "adapter_version": "0.1",
                    "pilot_matched_entity_count": 0,
                    "measurement_note": "stale fixed-100 pilot measurement",
                },
            }
        ],
        "matrix": {
            "rows": [
                {
                    "entity_id": "wa:org:jp:tse:1001",
                    "source_id": "jp-mod-procurement",
                    "state": "observed",
                    "observation_count": 1,
                }
            ]
        },
    }
    local_path = tmp_path / "local.json"
    public_path = tmp_path / "public.json"

    write(payload, local_path, public_path)

    local = json.loads(local_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    assert local == payload
    assert public["manifest"] == payload["manifest"]
    assert public["source_catalog"] == [
        {
            "source_id": "jp-mod-procurement",
            "category": "military_contract",
            "integration_state": "integrated",
            "provenance": {
                "source_sha256": "source-sha",
                "adapter_version": "0.1",
            },
        }
    ]
    assert "matrix" not in public
    public_text = public_path.read_text(encoding="utf-8")
    assert "wa:org:jp:tse:1001" not in public_text
    assert "pilot_matched_entity_count" not in public_text
    assert "measurement_note" not in public_text


def test_writer_rejects_same_local_and_public_path(tmp_path):
    write = writer_api()
    path = tmp_path / "same.json"
    with pytest.raises(ValueError, match="local and public outputs must differ"):
        write({"manifest": {}, "source_catalog": [], "matrix": {}}, path, path)
