import csv
import io
import json
import subprocess
import sys
import zipfile

from scripts import run_real_identity_pilot


def test_gleif_golden_copy_parser_keeps_only_exact_japanese_registration_ids(tmp_path):
    zip_path = tmp_path / "gleif-golden-copy.csv.zip"
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "LEI",
            "Entity.RegistrationAuthority.RegistrationAuthorityID",
            "Entity.RegistrationAuthority.RegistrationAuthorityEntityID",
        ],
    )
    writer.writeheader()
    writer.writerows(
        [
            {
                "LEI": "549300JPVALID00000001",
                "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA001075",
                "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111",
            },
            {
                "LEI": "549300WRONGAUTH000001",
                "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA999999",
                "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111",
            },
            {
                "LEI": "549300OTHERJP0000001",
                "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA001075",
                "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "2222222222222",
            },
        ]
    )
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("golden-copy.csv", buffer.getvalue().encode("utf-8"))

    rows = run_real_identity_pilot.read_gleif_golden_copy_zip(
        zip_path,
        {"1111111111111"},
    )

    assert rows == [
        {
            "LEI": "549300JPVALID00000001",
            "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA001075",
            "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111",
        }
    ]


def test_local_tse_identity_runner_uses_local_snapshots_and_publishes_manifest_only(tmp_path):
    universe_path = tmp_path / "tse-universe-local.json"
    universe = {
        "manifest": {
            "snapshot": "20260831",
            "source_sha256": "jpx-source-sha",
            "semantic_payload_sha256": "jpx-semantic-sha",
            "entity_count": 1,
        },
        "entities": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "canonical_name": "Local Universe Co",
                "jurisdiction": "JP",
                "aliases": [],
                "identifiers": [
                    {
                        "scheme": "JPX_SECURITY_CODE",
                        "value": "1001",
                        "source": {
                            "source": "JPX",
                            "source_key": "local-jpx.xlsx",
                            "snapshot": "20260831",
                            "url": "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
                            "retrieved_at": "2026-09-08T00:00:00Z",
                            "adapter_version": "0.4",
                        },
                    }
                ],
                "addresses": [],
                "review_state": "CONFIRMED",
                "review_reason": None,
                "security_code": "1001",
                "market_segment": "Prime",
            }
        ],
    }
    universe_path.write_text(json.dumps(universe, ensure_ascii=False), encoding="utf-8")

    edinet_zip = tmp_path / "Edinetcode.zip"
    edinet_csv = io.StringIO()
    writer = csv.writer(edinet_csv)
    writer.writerow(["metadata"])
    writer.writerow(["証券コード", "ＥＤＩＮＥＴコード", "提出者法人番号"])
    writer.writerow(["10010", "E10001", "1111111111111"])
    with zipfile.ZipFile(edinet_zip, "w") as zf:
        zf.writestr("EdinetcodeDlInfo.csv", edinet_csv.getvalue().encode("cp932"))

    nta_zip = tmp_path / "nta-all.zip"
    nta_row = [""] * 12
    nta_row[1] = "1111111111111"
    nta_row[6] = "Local Universe Co株式会社"
    nta_row[9] = "東京都"
    nta_row[10] = "千代田区"
    nta_row[11] = "1-1"
    nta_csv = io.StringIO()
    csv.writer(nta_csv).writerow(nta_row)
    with zipfile.ZipFile(nta_zip, "w") as zf:
        zf.writestr("nta.csv", nta_csv.getvalue().encode("utf-8"))

    gleif_zip = tmp_path / "gleif-golden-copy.csv.zip"
    gleif_csv = io.StringIO()
    writer = csv.DictWriter(
        gleif_csv,
        fieldnames=[
            "LEI",
            "Entity.RegistrationAuthority.RegistrationAuthorityID",
            "Entity.RegistrationAuthority.RegistrationAuthorityEntityID",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "LEI": "549300JPVALID00000001",
            "Entity.RegistrationAuthority.RegistrationAuthorityID": "RA001075",
            "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": "1111111111111",
        }
    )
    with zipfile.ZipFile(gleif_zip, "w") as zf:
        zf.writestr("golden-copy.csv", gleif_csv.getvalue().encode("utf-8"))

    local_output = tmp_path / "tse-identity-local.json"
    public_manifest = tmp_path / "tse-identity-manifest.json"
    payload = run_real_identity_pilot.run_tse_identity_spine_local(
        universe_path,
        edinet_zip,
        nta_zip,
        gleif_zip,
        local_output,
        public_manifest,
        code_commit="abc123",
        retrieved_at="2026-09-08T01:02:03Z",
        edinet_snapshot="2026-09-01",
        nta_snapshot="2026-08-31",
        gleif_snapshot="2026-09-08T00:00:00Z",
        edinet_url="https://example.test/edinet",
        nta_url="https://example.test/nta",
        gleif_url="https://example.test/gleif",
    )

    assert payload["manifest"]["entity_count"] == 1
    assert payload["manifest"]["mapped_count"] == 1
    assert payload["manifest"]["nta_validated_count"] == 1
    assert payload["manifest"]["lei_count"] == 1
    assert payload["manifest"]["code_commit"] == "abc123"
    assert payload["manifest"]["sources"]["edinet"]["snapshot"] == "2026-09-01"
    assert payload["manifest"]["sources"]["nta"]["snapshot"] == "2026-08-31"
    assert payload["manifest"]["sources"]["gleif"]["registration_authority"] == "RA001075"
    assert payload["manifest"]["sources"]["edinet"]["sha256"] == run_real_identity_pilot.sha256(edinet_zip)
    assert payload["manifest"]["sources"]["nta"]["sha256"] == run_real_identity_pilot.sha256(nta_zip)
    assert payload["manifest"]["sources"]["gleif"]["sha256"] == run_real_identity_pilot.sha256(gleif_zip)

    local = json.loads(local_output.read_text(encoding="utf-8"))
    public = json.loads(public_manifest.read_text(encoding="utf-8"))
    schemes = {item["scheme"] for item in local["entities"][0]["identifiers"]}
    assert {"JPX_SECURITY_CODE", "EDINET_CODE", "JP_CORPORATE_NUMBER", "LEI"} <= schemes
    assert public == payload["manifest"]
    public_text = public_manifest.read_text(encoding="utf-8")
    assert "entities" not in public
    assert "Local Universe Co" not in public_text
    assert "1001" not in public_text


def test_operator_cli_requires_local_source_metadata_arguments():
    result = subprocess.run(
        [sys.executable, "scripts/run_tse_identity_spine.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    for token in (
        "--code-commit",
        "--retrieved-at",
        "--edinet-snapshot",
        "--nta-snapshot",
        "--gleif-snapshot",
        "--edinet-url",
        "--nta-url",
        "--gleif-url",
    ):
        assert token in result.stdout
