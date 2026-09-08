import csv
import io
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
