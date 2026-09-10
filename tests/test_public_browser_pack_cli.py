from __future__ import annotations

import json
import sys

from scripts.build_public_browser_pack import main

PROFILE = "public:strict-military-specific:v1"


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_cli_writes_valid_pack_and_prints_only_aggregates(tmp_path, monkeypatch, capsys):
    identity = {"manifest": {"public_projection_semantic_sha256": "a" * 64}, "companies": [{
        "entity_id": "jp:corporate-number:1111111111111", "corporate_number": "1111111111111",
        "canonical_name": "CLI合成株式会社", "security_code": "1001", "edinet_code": "E00001",
        "identity_state": "CONFIRMED",
    }]}
    coverage = {"matrix_sha256": "b" * 64, "matrix": {"entity_count": 1, "rows": [{
        "entity_id": "wa:org:jp:tse:1001", "source_id": "jp-mod-procurement",
        "state": "observed", "observation_count": 1,
    }]}}
    screening = {"screening_sha256": "d" * 64,
        "policies": [{"profile_id": PROFILE, "profile_version": "1", "policy_sha256": "c" * 64}],
        "views": [{"entity_id": "wa:org:jp:tse:1001", "profile_id": PROFILE,
                    "profile_version": "1", "policy_sha256": "c" * 64, "decision": "NONE",
                    "claim_results": [], "reasoning": "NONE is not PASS."}]}
    graph = {"claims": []}
    bridge = {"links": [{"entity_id": "wa:org:jp:tse:1001",
                          "corporate_number": "1111111111111", "review_state": "CONFIRMED"}]}
    rights = {"sources": [
        {"source_id": "jp-mod-procurement", "state": "PUBLIC_FIELDS_ALLOWED",
         "terms_url": "https://example.test/mod", "checked_at": "2026-09-11",
         "allowed_fields": ["source_id", "source_publisher", "source_url", "source_locator",
                            "claim_id", "narrow_claim", "category", "predicate",
                            "adjudication_status", "confidence", "evidence_date", "retrieved_at"],
         "attribution_required": True, "raw_rows_public": False, "note": "test"},
        {"source_id": "ohchr-settlements-business", "state": "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED",
         "terms_url": "https://example.test/un", "checked_at": "2026-09-11",
         "allowed_fields": [], "attribution_required": False, "raw_rows_public": False, "note": "blocked"},
    ]}

    paths = {}
    for name, value in {"identity": identity, "coverage": coverage, "screening": screening,
                        "graph": graph, "bridge": bridge, "rights": rights}.items():
        paths[name] = tmp_path / f"{name}.json"
        _write(paths[name], value)
    output = tmp_path / "pack.json"
    monkeypatch.setattr(sys, "argv", [
        "build_public_browser_pack.py",
        "--public-identity", str(paths["identity"]),
        "--coverage", str(paths["coverage"]),
        "--screening", str(paths["screening"]),
        "--evidence-graph", str(paths["graph"]),
        "--identity-bridge", str(paths["bridge"]),
        "--rights", str(paths["rights"]),
        "--profile-id", PROFILE,
        "--generated-at", "2026-09-11T00:00:00Z",
        "--code-commit", "abc123",
        "--output", str(output),
    ])
    assert main() == 0
    pack = json.loads(output.read_text(encoding="utf-8"))
    assert pack["manifest"]["release_state"] == "READY_FOR_CAPABILITY_TEST"
    assert pack["manifest"]["company_count"] == 1

    stdout = capsys.readouterr().out
    assert "release_state=READY_FOR_CAPABILITY_TEST" in stdout
    assert "company_count=1" in stdout
    assert "pack_semantic_sha256=" in stdout
    assert "CLI合成株式会社" not in stdout
    assert "wa:org:jp:tse:1001" not in stdout
