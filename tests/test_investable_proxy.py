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


def test_binding_changes_only_snapshot_input_hashes() -> None:
    import json
    from pathlib import Path
    from wa_commons.portfolio.investable_proxy import bind_policy_compiler_inputs

    base = json.loads(Path("configs/m3-3b2-policy-compiler-v0.1.json").read_text(encoding="utf-8"))
    mapped_control = {"manifest": {"semantic_mapping_sha256": "a" * 64}}
    screening = {"tse_screening_sha256": "b" * 64}
    bound = bind_policy_compiler_inputs(base, mapped_control, screening)
    assert bound is not base
    assert bound["arms"] == base["arms"]
    assert bound["unknown_handling"] == base["unknown_handling"]
    assert bound["numerical"] == base["numerical"]
    assert bound["input_contract"]["policy_sha256"] == base["input_contract"]["policy_sha256"]
    assert bound["input_contract"]["benchmark_semantic_mapping_sha256"] == "a" * 64
    assert bound["input_contract"]["screening_sha256"] == "b" * 64
    assert base["input_contract"]["benchmark_semantic_mapping_sha256"] != "a" * 64


def test_direct_changed_ids_ignore_normalization_only_rows() -> None:
    from wa_commons.portfolio.investable_proxy import directly_changed_security_ids

    payload = {
        "arms": [
            {
                "arm_id": "P2",
                "target_weights": [
                    {"security_id": "TSE:1001", "instruction": "UNDERWEIGHT", "multiplier": "0.500000000000", "allocation_delta": "-0.010000000000"},
                    {"security_id": "TSE:1002", "instruction": "NEUTRAL", "multiplier": "1.000000000000", "allocation_delta": "0.010000000000"},
                ],
            }
        ]
    }
    assert directly_changed_security_ids(payload, "P2") == ["TSE:1001"]


def test_two_month_bindings_keep_frozen_policy_semantics() -> None:
    import json
    from pathlib import Path
    from copy import deepcopy
    from wa_commons.portfolio.investable_proxy import bind_policy_compiler_inputs
    from wa_commons.portfolio.policy_compiler import compile_policy_family

    base = json.loads(Path("configs/m3-3b2-policy-compiler-v0.1.json").read_text(encoding="utf-8"))
    policy_sha = base["input_contract"]["policy_sha256"]
    rows = [
        {"security_id": "TSE:1001", "benchmark_weight": "0.600000000000", "mapping_state": "mapped", "canonical_entity_id": "wa:1", "canonical_review_state": "CONFIRMED"},
        {"security_id": "TSE:1002", "benchmark_weight": "0.400000000000", "mapping_state": "mapped", "canonical_entity_id": "wa:2", "canonical_review_state": "CONFIRMED"},
    ]
    views = [
        {"entity_id": "wa:1", "profile_id": "example:strict-military-avoidance", "profile_version": "1", "policy_sha256": policy_sha, "decision": "NONE", "identity_state": "confirmed", "claim_results": [], "coverage_state_counts": {"observed": 1}},
        {"entity_id": "wa:2", "profile_id": "example:strict-military-avoidance", "profile_version": "1", "policy_sha256": policy_sha, "decision": "WATCH", "identity_state": "confirmed", "claim_results": [], "coverage_state_counts": {"observed": 1}},
    ]
    outputs = []
    for benchmark_sha, screening_sha in (("a" * 64, "b" * 64), ("c" * 64, "d" * 64)):
        mapped = {"manifest": {"semantic_mapping_sha256": benchmark_sha}, "rows": deepcopy(rows)}
        screening = {"tse_screening_sha256": screening_sha, "views": deepcopy(views)}
        bound = bind_policy_compiler_inputs(base, mapped, screening)
        outputs.append(compile_policy_family(mapped, screening, bound))
    assert [item["status"] for item in outputs] == ["FROZEN_POLICY_FAMILY", "FROZEN_POLICY_FAMILY"]
    assert outputs[0]["manifest"]["profile_id"] == outputs[1]["manifest"]["profile_id"]
    assert outputs[0]["manifest"]["policy_sha256"] == outputs[1]["manifest"]["policy_sha256"]
    assert [arm["arm_id"] for arm in outputs[0]["arms"]] == [arm["arm_id"] for arm in outputs[1]["arms"]]
    assert outputs[0]["manifest"]["config_semantic_sha256"] != outputs[1]["manifest"]["config_semantic_sha256"]
