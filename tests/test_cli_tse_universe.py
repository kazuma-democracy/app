import json
import sys
from pathlib import Path

from wa_commons.cli import main


HEADER = "日付,コード,銘柄名,市場・商品区分,33業種コード,33業種区分,17業種コード,17業種区分,規模コード,規模区分"


def _write_fixture(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                HEADER,
                "20260831,1003,成長テスト,グロース（内国株式）,5250,情報・通信業,10,情報通信・サービスその他,-,-",
                "20260831,1001,主要テスト,プライム（内国株式）,2050,建設業,3,建設・資材,-,-",
                "20260831,1002,標準テスト,スタンダード（内国株式）,3050,卸売業,9,商社・卸売,-,-",
                "20260831,1305,ETF TEST,ETF・ETN,-,-,-,-,-,-",
            ]
        )
        + "\n",
        encoding="utf-8-sig",
    )


def test_build_jpx_universe_cli_writes_local_rows_and_public_manifest(
    tmp_path, monkeypatch, capsys
):
    fixture = tmp_path / "listed.csv"
    local_output = tmp_path / "universe.local.json"
    public_manifest = tmp_path / "universe.manifest.json"
    _write_fixture(fixture)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wa-commons",
            "build-jpx-universe",
            str(fixture),
            str(local_output),
            str(public_manifest),
            "--snapshot",
            "2026-08-31",
            "--source-url",
            "https://www.jpx.co.jp/markets/statistics-equities/misc/01.html",
            "--retrieved-at",
            "2026-09-08T00:00:00Z",
        ],
    )

    main()

    local_payload = json.loads(local_output.read_text(encoding="utf-8"))
    manifest = json.loads(public_manifest.read_text(encoding="utf-8"))
    assert [row["security_code"] for row in local_payload["entities"]] == [
        "1001",
        "1002",
        "1003",
    ]
    assert manifest == local_payload["manifest"]
    assert manifest["rights_mode"] == "local_generation_only"
    output = capsys.readouterr().out
    assert "3 entities" in output
    assert "local row output" in output
    assert "public-safe manifest" in output
