from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

import pytest

from wa_commons.portfolio.benchmark_snapshot import map_topix_snapshot


def _snapshot() -> dict:
    rows = []
    for code, weight in (("1000", "0.400000000000"), ("1001", "0.300000000000"), ("1002", "0.200000000000"), ("1003", "0.100000000000")):
        rows.append({
            "security_id": f"TSE:{code}",
            "security_code": code,
            "provider_local_code": f"{code}0",
            "name": "Same Name",
            "isin": f"JP{code}000000",
            "cmv_jpy": "1",
            "benchmark_weight": weight,
        })
    return {
        "manifest": {
            "semantic_snapshot_sha256": "a" * 64,
            "benchmark_weight_sum": "1.000000000000",
            "semantic_weight_decimals": 12,
        },
        "rows": rows,
    }


def _entity(code: str, state: str, entity_id: str | None = None) -> dict:
    return {
        "entity_id": entity_id or f"wa:org:jp:tse:{code}",
        "canonical_name": "Same Name",
        "review_state": state,
        "identifiers": [{"scheme": "JPX_SECURITY_CODE", "value": code}],
    }


def _identity() -> dict:
    return {
        "manifest": {"semantic_identity_sha256": "b" * 64},
        "entities": [
            _entity("1000", "CONFIRMED"),
            _entity("1001", "UNRESOLVED"),
            _entity("1002", "DISPUTED"),
        ],
    }


def test_maps_only_exact_confirmed_strong_identifiers():
    result = map_topix_snapshot(_snapshot(), _identity())
    by_id = {row["security_id"]: row for row in result["rows"]}

    assert by_id["TSE:1000"]["mapping_state"] == "mapped"
    assert by_id["TSE:1000"]["mapping_reason"] == "exact_jpx_security_code"
    assert by_id["TSE:1001"]["mapping_state"] == "unmapped"
    assert by_id["TSE:1001"]["mapping_reason"] == "canonical_identity_unresolved"
    assert by_id["TSE:1002"]["mapping_state"] == "disputed"
    assert by_id["TSE:1002"]["mapping_reason"] == "canonical_identity_disputed"
    assert by_id["TSE:1003"]["mapping_state"] == "unmapped"
    assert by_id["TSE:1003"]["mapping_reason"] == "out_of_canonical_universe"
    assert by_id["TSE:1003"]["canonical_entity_id"] is None

    summary = result["manifest"]["mapping_summary"]
    assert summary["mapped"] == {"count": 1, "benchmark_weight": "0.400000000000"}
    assert summary["unresolved_identity"] == {"count": 1, "benchmark_weight": "0.300000000000"}
    assert summary["disputed"] == {"count": 1, "benchmark_weight": "0.200000000000"}
    assert summary["out_of_canonical_universe"] == {"count": 1, "benchmark_weight": "0.100000000000"}
    assert sum(Decimal(bucket["benchmark_weight"]) for bucket in summary.values()) == Decimal("1.000000000000")


def test_name_match_never_creates_mapping():
    identity = {
        "manifest": {"semantic_identity_sha256": "b" * 64},
        "entities": [_entity("9999", "CONFIRMED", "wa:org:jp:tse:other")],
    }
    result = map_topix_snapshot(_snapshot(), identity)
    row = next(row for row in result["rows"] if row["security_id"] == "TSE:1000")
    assert row["mapping_state"] == "unmapped"
    assert row["mapping_reason"] == "out_of_canonical_universe"


def test_duplicate_canonical_security_identifier_fails_closed():
    identity = _identity()
    identity["entities"].append(_entity("1000", "CONFIRMED", "wa:org:jp:tse:duplicate"))
    with pytest.raises(ValueError, match="duplicate canonical JPX_SECURITY_CODE"):
        map_topix_snapshot(_snapshot(), identity)


def test_mapping_is_order_independent():
    first = map_topix_snapshot(_snapshot(), _identity())
    reversed_identity = deepcopy(_identity())
    reversed_identity["entities"].reverse()
    second = map_topix_snapshot(_snapshot(), reversed_identity)
    assert first["manifest"]["semantic_mapping_sha256"] == second["manifest"]["semantic_mapping_sha256"]
