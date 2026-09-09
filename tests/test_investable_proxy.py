from decimal import Decimal

import pytest

from wa_commons.portfolio.investable_proxy import parse_ishares_1475_holdings_csv


HOLDINGS_FIXTURE = '''Fund Holdings as of,"Jan 30, 2026"
Ticker,Name,Asset Class,Market Value,Quantity,Price
7203,TOYOTA MOTOR CORP,Equity,"70,000",20,3500
130A,ALPHA CORP,Equity,"30,000",10,3000
JPY,CASH,Cash,"1,000",1000,1
TOPIX FUT,TOPIX FUTURE,Futures,"5,000",1,5000
'''


def test_1475_parser_keeps_equities_only_and_normalizes_market_value() -> None:
    payload = parse_ishares_1475_holdings_csv(
        HOLDINGS_FIXTURE,
        as_of_date="2026-01-30",
        source_sha256="a" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://1475/20260130",
    )
    assert payload["status"] == "INVESTABLE_CONTROL_SNAPSHOT_OK"
    assert [r["security_id"] for r in payload["rows"]] == ["TSE:130A", "TSE:7203"]
    assert sum(Decimal(r["control_weight"]) for r in payload["rows"]) == Decimal("1.000000000000")
    assert all(r["asset_class"] == "Equity" for r in payload["rows"])


def test_1475_parser_rejects_duplicate_security_code() -> None:
    fixture = HOLDINGS_FIXTURE.replace(
        '130A,ALPHA CORP,Equity,"30,000",10,3000',
        '7203,SECOND TOYOTA,Equity,"30,000",10,3000',
    )
    with pytest.raises(ValueError, match="duplicate"):
        parse_ishares_1475_holdings_csv(
            fixture,
            as_of_date="2026-01-30",
            source_sha256="b" * 64,
            retrieved_at="2026-09-09T20:00:00+09:00",
            source_locator="fixture://duplicate",
        )


def test_1475_parser_rejects_malformed_equity_market_value() -> None:
    fixture = HOLDINGS_FIXTURE.replace('"70,000"', 'NOT_A_NUMBER')
    with pytest.raises(ValueError, match="market value"):
        parse_ishares_1475_holdings_csv(
            fixture,
            as_of_date="2026-01-30",
            source_sha256="c" * 64,
            retrieved_at="2026-09-09T20:00:00+09:00",
            source_locator="fixture://bad-value",
        )


def test_1475_parser_rejects_mismatched_as_of_date() -> None:
    with pytest.raises(ValueError, match="as-of date"):
        parse_ishares_1475_holdings_csv(
            HOLDINGS_FIXTURE,
            as_of_date="2026-01-29",
            source_sha256="d" * 64,
            retrieved_at="2026-09-09T20:00:00+09:00",
            source_locator="fixture://wrong-date",
        )


def test_1475_parser_is_equity_input_order_independent() -> None:
    reversed_fixture = HOLDINGS_FIXTURE.replace(
        '7203,TOYOTA MOTOR CORP,Equity,"70,000",20,3500\n130A,ALPHA CORP,Equity,"30,000",10,3000',
        '130A,ALPHA CORP,Equity,"30,000",10,3000\n7203,TOYOTA MOTOR CORP,Equity,"70,000",20,3500',
    )
    first = parse_ishares_1475_holdings_csv(
        HOLDINGS_FIXTURE,
        as_of_date="2026-01-30",
        source_sha256="e" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://ordered",
    )
    second = parse_ishares_1475_holdings_csv(
        reversed_fixture,
        as_of_date="2026-01-30",
        source_sha256="e" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://ordered",
    )
    assert first["rows"] == second["rows"]
    assert first["manifest"]["semantic_snapshot_sha256"] == second["manifest"]["semantic_snapshot_sha256"]


def test_investable_control_mapping_reuses_exact_code_identity_without_claiming_topix() -> None:
    from wa_commons.portfolio.investable_proxy import map_investable_control_snapshot

    snapshot = parse_ishares_1475_holdings_csv(
        HOLDINGS_FIXTURE,
        as_of_date="2026-01-30",
        source_sha256="f" * 64,
        retrieved_at="2026-09-09T20:00:00+09:00",
        source_locator="fixture://mapping",
    )
    identity = {
        "manifest": {"semantic_identity_sha256": "1" * 64},
        "entities": [
            {"entity_id": "wa:org:jp:tse:130A", "review_state": "CONFIRMED", "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": "130A"}]},
            {"entity_id": "wa:org:jp:tse:7203", "review_state": "CONFIRMED", "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": "7203"}]},
        ],
    }
    mapped = map_investable_control_snapshot(snapshot, identity)
    assert mapped["manifest"]["allocation_role"] == "INVESTABLE_CONTROL"
    assert mapped["manifest"]["control_kind"] == "ISHARES_1475_POINT_IN_TIME"
    assert mapped["manifest"]["identity_semantic_sha256"] == "1" * 64
    assert all(row["mapping_state"] == "mapped" for row in mapped["rows"])
    assert all(row["benchmark_weight"] == row["control_weight"] for row in mapped["rows"])
