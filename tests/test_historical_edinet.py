import pytest

from wa_commons.identity.historical_edinet import (
    build_historical_proxy_identity,
    normalize_edinet_document_rows,
)
from wa_commons.identity.models import SourceRef
from wa_commons.portfolio.investable_proxy import parse_ishares_1475_holdings_csv


CONTROL_CSV = '''Fund Holdings as of,"Jan 30, 2026"
Ticker,Name,Asset Class,Market Value
7203,TOYOTA MOTOR CORP,Equity,"70,000"
130A,ALPHA CORP,Equity,"30,000"
'''


def test_edinet_rows_after_cutoff_are_excluded() -> None:
    rows = normalize_edinet_document_rows(
        [
            {"submitDateTime": "2026-01-20 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
            {"submitDateTime": "2026-02-02 09:00", "secCode": "67580", "JCN": "2222222222222", "edinetCode": "E00002"},
        ],
        decision_cutoff="2026-01-30T15:30:00+09:00",
    )
    assert rows == [
        {"security_code": "72030", "corporate_number": "1111111111111", "edinet_code": "E00001"}
    ]


def test_conflicting_cutoff_eligible_corporate_numbers_fail_closed() -> None:
    with pytest.raises(ValueError, match="conflicting historical corporate number"):
        normalize_edinet_document_rows(
            [
                {"submitDateTime": "2026-01-10 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
                {"submitDateTime": "2026-01-20 09:00", "secCode": "72030", "JCN": "2222222222222", "edinetCode": "E00001"},
            ],
            decision_cutoff="2026-01-30T15:30:00+09:00",
        )


def _control_snapshot() -> dict:
    return parse_ishares_1475_holdings_csv(
        CONTROL_CSV,
        as_of_date="2026-01-30",
        source_sha256="a" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://1475/20260130",
    )


def _edinet_source() -> SourceRef:
    return SourceRef(
        source="jp-edinet",
        source_key="documents-2026-01-30",
        snapshot="cutoff-2026-01-30",
        url="fixture://edinet/20260130",
        retrieved_at="2026-09-09T20:00:00+09:00",
    )


def test_proxy_identity_keeps_unmapped_security_without_guessing_corporate_number() -> None:
    identity = build_historical_proxy_identity(
        _control_snapshot(),
        [
            {"submitDateTime": "2026-01-20 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
        ],
        decision_cutoff="2026-01-30T15:30:00+09:00",
        edinet_source=_edinet_source(),
        code_commit="a" * 40,
    )
    by_id = {row["entity_id"]: row for row in identity["entities"]}
    assert set(by_id) == {"wa:org:jp:tse:130A", "wa:org:jp:tse:7203"}
    toyota_ids = {(item["scheme"], item["value"]) for item in by_id["wa:org:jp:tse:7203"]["identifiers"]}
    alpha_ids = {(item["scheme"], item["value"]) for item in by_id["wa:org:jp:tse:130A"]["identifiers"]}
    assert ("JP_CORPORATE_NUMBER", "1111111111111") in toyota_ids
    assert not any(scheme == "JP_CORPORATE_NUMBER" for scheme, _ in alpha_ids)


def test_historical_identity_is_edinet_input_order_independent() -> None:
    records = [
        {"submitDateTime": "2026-01-10 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
        {"submitDateTime": "2026-01-20 09:00", "secCode": "72030", "JCN": "1111111111111", "edinetCode": "E00001"},
    ]
    first = build_historical_proxy_identity(
        _control_snapshot(), records,
        decision_cutoff="2026-01-30T15:30:00+09:00", edinet_source=_edinet_source(), code_commit="first"
    )
    second = build_historical_proxy_identity(
        _control_snapshot(), list(reversed(records)),
        decision_cutoff="2026-01-30T15:30:00+09:00", edinet_source=_edinet_source(), code_commit="second"
    )
    assert first["manifest"]["semantic_identity_sha256"] == second["manifest"]["semantic_identity_sha256"]
