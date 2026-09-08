from __future__ import annotations

from decimal import Decimal

import pytest

from wa_commons.portfolio.benchmark_snapshot import (
    build_topix_snapshot,
    read_topix_month_end_csv,
)


def _config() -> dict:
    return {
        "artifact_version": "m3.3b-topix-benchmark-v0.1",
        "benchmark_id": "JPX:TOPIX_TOTAL_RETURN:6000",
        "provider": "JPX Market Innovation & Research, Inc.",
        "constituent_product": "TOPIX End of month Master Of Index",
        "effective_date": "2026-08-31",
        "available_at": "2026-09-01T16:20:00+09:00",
        "index_code": "0000",
        "return_index_code": "6000",
        "currency": "JPY",
        "weight_basis": "CMV",
        "semantic_weight_decimals": 12,
        "rights_mode": "licensed_local_self_use_no_external_distribution",
        "raw_publication": False,
    }


def _row(code: str, cmv: str, *, name: str = "Example", isin: str = "JP0000000000") -> dict:
    return {
        "Date": "20260831",
        "Local Code": code,
        "Name": name,
        "ISIN": isin,
        "CMV": cmv,
        "Index Code": "0000",
        "Index Name": "TOPIX",
    }


def test_reconstructs_cmv_weights_and_is_order_independent():
    rows = [_row("72030", "60"), _row("130A0", "30"), _row("99990", "10")]
    first = build_topix_snapshot(rows, _config(), "a" * 64)
    second = build_topix_snapshot(list(reversed(rows)), _config(), "a" * 64)

    assert [row["security_id"] for row in first["rows"]] == ["TSE:130A", "TSE:7203", "TSE:9999"]
    assert sum(Decimal(row["benchmark_weight"]) for row in first["rows"]) == Decimal("1.000000000000")
    assert first["manifest"]["benchmark_weight_sum"] == "1.000000000000"
    assert first["manifest"]["constituent_count"] == 3
    assert first["manifest"]["source_sha256"] == "a" * 64
    assert first["manifest"]["semantic_snapshot_sha256"] == second["manifest"]["semantic_snapshot_sha256"]


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda rows: rows + [_row("72030", "5")], "duplicate Local Code"),
        (lambda rows: [{**rows[0], "Date": "20260731"}, *rows[1:]], "effective date"),
        (lambda rows: [{**rows[0], "Index Code": "5000"}, *rows[1:]], "Index Code"),
        (lambda rows: [{**rows[0], "CMV": "0"}, *rows[1:]], "CMV"),
    ],
)
def test_snapshot_validation_fails_closed(mutator, message):
    rows = [_row("72030", "60"), _row("130A0", "40")]
    with pytest.raises(ValueError, match=message):
        build_topix_snapshot(mutator(rows), _config(), "b" * 64)


def test_rejects_mixed_effective_dates():
    rows = [_row("72030", "60"), {**_row("130A0", "40"), "Date": "20260830"}]
    with pytest.raises(ValueError, match="effective date"):
        build_topix_snapshot(rows, _config(), "c" * 64)


def test_rejects_invalid_source_hash():
    with pytest.raises(ValueError, match="source SHA-256"):
        build_topix_snapshot([_row("72030", "100")], _config(), "not-a-hash")


def test_reads_documented_csv_headers(tmp_path):
    path = tmp_path / "topix.csv"
    path.write_text(
        "Date,Local Code,Name,ISIN,CMV,Index Code,Index Name\n"
        "20260831,72030,Example Co.,JP0000000000,100,0000,TOPIX\n",
        encoding="utf-8-sig",
    )

    rows = read_topix_month_end_csv(path)

    assert rows == [{
        "Date": "20260831",
        "Local Code": "72030",
        "Name": "Example Co.",
        "ISIN": "JP0000000000",
        "CMV": "100",
        "Index Code": "0000",
        "Index Name": "TOPIX",
    }]
