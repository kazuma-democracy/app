import json
import sys

import pytest

from scripts.build_public_company_identity import main


def _write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _rights_payload():
    return {
        "sources": [
            {
                "source_id": "jp-nta-corporate-number",
                "state": "PUBLIC_FIELDS_ALLOWED",
                "terms_url": "https://example.invalid/nta",
                "checked_at": "2026-09-11",
                "allowed_fields": ["corporate_number", "legal_name", "source_url", "source_snapshot"],
                "attribution_required": True,
                "raw_rows_public": False,
                "note": "synthetic",
            },
            {
                "source_id": "jp-edinet",
                "state": "PUBLIC_FIELDS_ALLOWED",
                "terms_url": "https://example.invalid/edinet",
                "checked_at": "2026-09-11",
                "allowed_fields": ["edinet_code", "security_code", "filer_name", "corporate_number", "source_url", "source_snapshot"],
                "attribution_required": True,
                "raw_rows_public": False,
                "note": "synthetic",
            },
        ]
    }


def test_cli_writes_only_public_projection_and_aggregate_stdout(tmp_path, monkeypatch, capsys):
    canonical = tmp_path / "canonical.json"
    edinet = tmp_path / "edinet.json"
    nta = tmp_path / "nta.json"
    rights = tmp_path / "rights.json"
    output = tmp_path / "public.json"
    _write_json(canonical, {
        "manifest": {"semantic_identity_sha256": "a" * 64},
        "entities": [{
            "entity_id": "tse:synthetic:1001",
            "review_state": "CONFIRMED",
            "identifiers": [{"scheme": "JP_CORPORATE_NUMBER", "value": "1234567890123"}],
        }],
    })
    _write_json(edinet, [{"EDINETコード": "E00001", "証券コード": "10010", "提出者法人番号": "1234567890123", "提出者名": "合成株式会社"}])
    _write_json(nta, [{"法人番号": "1234567890123", "商号又は名称": "合成株式会社"}])
    _write_json(rights, _rights_payload())
    monkeypatch.setattr(sys, "argv", [
        "build_public_company_identity.py",
        "--canonical-identity", str(canonical),
        "--edinet-code-list", str(edinet),
        "--nta", str(nta),
        "--rights", str(rights),
        "--output", str(output),
        "--code-commit", "abc123",
    ])
    main()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["manifest"]["resolved_public_company_count"] == 1
    stdout = capsys.readouterr().out
    assert "合成株式会社" not in stdout
    assert "resolved_public_company_count" in stdout
    assert "public_projection_semantic_sha256" in stdout


def test_cli_refuses_output_equal_to_raw_input(tmp_path, monkeypatch):
    path = tmp_path / "same.json"
    _write_json(path, {})
    monkeypatch.setattr(sys, "argv", [
        "build_public_company_identity.py",
        "--canonical-identity", str(path),
        "--edinet-code-list", str(path),
        "--nta", str(path),
        "--rights", str(path),
        "--output", str(path),
        "--code-commit", "abc123",
    ])
    with pytest.raises(ValueError, match="output path must differ"):
        main()
