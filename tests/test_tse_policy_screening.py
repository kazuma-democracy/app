from __future__ import annotations

import pytest


def screening_api():
    try:
        from wa_commons.policy.tse_screening import build_tse_policy_screening
    except ModuleNotFoundError as exc:
        pytest.fail(f"TSE screening implementation missing: {exc}")
    return build_tse_policy_screening


def identity_fixture() -> dict:
    return {
        "manifest": {"entity_count": 2, "semantic_identity_sha256": "identity-hash"},
        "entities": [
            {
                "entity_id": "wa:org:jp:tse:1001",
                "review_state": "CONFIRMED",
                "identifiers": [{"scheme": "JP_CORPORATE_NUMBER", "value": "1111111111111"}],
            },
            {"entity_id": "wa:org:jp:tse:1002", "review_state": "UNRESOLVED", "identifiers": []},
        ],
    }


def coverage_fixture() -> dict:
    rows = []
    for source_id in (
        "jp-mod-procurement",
        "jp-political-finance",
        "sipri-arms-industry",
        "us-uflpa-entity-list",
        "oecd-ncp-cases",
    ):
        rows.append({
            "entity_id": "wa:org:jp:tse:1001",
            "source_id": source_id,
            "state": "observed" if source_id == "jp-mod-procurement" else (
                "unresolved_identity" if source_id == "jp-political-finance" else "not_integrated"
            ),
        })
        rows.append({
            "entity_id": "wa:org:jp:tse:1002",
            "source_id": source_id,
            "state": "unresolved_identity" if source_id in {"jp-mod-procurement", "jp-political-finance"} else "not_integrated",
        })
    return {
        "manifest": {"coverage_semantic_sha256": "coverage-hash"},
        "matrix": {"entity_count": 2, "source_count": 5, "cell_count": 10, "rows": rows},
    }


def mod_observation_fixture() -> dict:
    return {
        "observation_id": "wc:obs:mod-fy2026-04:test:1",
        "subject": "一般事務用品",
        "supplier_name": "Test Supplier",
        "supplier_address": "Tokyo",
        "corporate_number": "1111111111111",
        "contract_date": "2026-04-01",
        "contract_amount_jpy": 1000,
        "planned_price_jpy": 1200,
        "contracting_authority": "Japan Ministry of Defense",
        "source_url": "https://example.invalid/mod.xlsx",
        "source_page_url": "https://example.invalid/mod",
        "source_locator": "sheet=test;row=1",
        "retrieved_at": "2026-09-08T00:00:00Z",
        "source_sha256": "a" * 64,
        "snapshot_version": "fy2026-04-buppin-competitive",
        "adapter_version": "0.1",
        "identity_decision": "AUTO_LINK",
        "entity_id": "jp:corporate-number:1111111111111",
    }


def example_policies() -> list[dict]:
    import json
    from pathlib import Path

    path = Path(__file__).parents[1] / "schemas" / "examples" / "user-policy.examples.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_builds_every_tse_entity_profile_view_using_existing_mod_claims():
    build = screening_api()
    observation = mod_observation_fixture()
    observation["subject"] = "ＰＰＣ用紙"

    result = build(
        identity=identity_fixture(),
        coverage_artifact=coverage_fixture(),
        mod_observations=[observation],
        policies=example_policies(),
        code_commit="test-commit",
    )

    assert result["company_count"] == 2
    assert result["profile_count"] == 3
    assert result["view_count"] == 6
    assert result["mod_observation_count"] == 1
    assert result["generated_claim_count"] == 2


def test_public_output_contains_aggregate_only(tmp_path):
    try:
        from wa_commons.policy.tse_screening import write_tse_policy_screening
    except ImportError as exc:
        pytest.fail(f"TSE screening writer missing: {exc}")
    result = screening_api()(
        identity=identity_fixture(),
        coverage_artifact=coverage_fixture(),
        mod_observations=[mod_observation_fixture()],
        policies=example_policies(),
        code_commit="test-commit",
    )
    local_path = tmp_path / "local.json"
    public_path = tmp_path / "public.json"

    write_tse_policy_screening(result, local_path, public_path)

    import json
    local = json.loads(local_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    assert len(local["views"]) == 6
    serialized = json.dumps(public, ensure_ascii=False, sort_keys=True)
    assert "views" not in public
    assert "entity_id" not in serialized
    assert "1111111111111" not in serialized
    assert public["view_count"] == 6


def test_weight_interface_reports_decision_and_coverage_weights_only():
    try:
        from wa_commons.policy.tse_screening import summarize_weighted_coverage
    except ImportError as exc:
        pytest.fail(f"weight coverage interface missing: {exc}")
    observation = mod_observation_fixture()
    observation["subject"] = "ＰＰＣ用紙"
    result = screening_api()(
        identity=identity_fixture(),
        coverage_artifact=coverage_fixture(),
        mod_observations=[observation],
        policies=example_policies(),
        code_commit="test-commit",
    )

    summary = summarize_weighted_coverage(
        result,
        {"wa:org:jp:tse:1001": 0.6, "wa:org:jp:tse:1002": 0.4},
    )

    assert summary["total_weight"] == pytest.approx(1.0)
    assert summary["represented_weight"] == pytest.approx(1.0)
    assert summary["unresolved_identity_weight"] == pytest.approx(0.4)
    transparency = summary["decision_weight_by_profile"]["example:transparency-first"]
    assert transparency == {"EXCLUDE": 0.0, "WATCH": pytest.approx(0.6), "NONE": pytest.approx(0.4)}
    assert not any("return" in key.lower() for key in summary)


def test_tse_screening_hash_is_input_order_independent():
    build = screening_api()
    identity = identity_fixture()
    coverage = coverage_fixture()
    policies = example_policies()
    first = build(
        identity=identity,
        coverage_artifact=coverage,
        mod_observations=[mod_observation_fixture()],
        policies=policies,
        code_commit="first-commit",
    )
    second = build(
        identity={**identity, "entities": list(reversed(identity["entities"]))},
        coverage_artifact={
            **coverage,
            "matrix": {**coverage["matrix"], "rows": list(reversed(coverage["matrix"]["rows"]))},
        },
        mod_observations=[mod_observation_fixture()],
        policies=list(reversed(policies)),
        code_commit="second-commit",
    )

    assert first["tse_screening_sha256"] == second["tse_screening_sha256"]


def test_pinned_scale_emits_3707_by_three_views_and_keeps_eight_unresolved():
    build = screening_api()
    entities = []
    rows = []
    sources = ["jp-mod-procurement", "jp-political-finance", "sipri-arms-industry", "us-uflpa-entity-list", "oecd-ncp-cases"]
    for index in range(3707):
        entity_id = f"wa:org:jp:tse:{10000 + index}"
        confirmed = index < 3699
        entities.append({
            "entity_id": entity_id,
            "review_state": "CONFIRMED" if confirmed else "UNRESOLVED",
            "identifiers": ([{"scheme": "JP_CORPORATE_NUMBER", "value": f"{index + 1:013d}"}] if confirmed else []),
        })
        for source_id in sources:
            state = "not_integrated" if source_id not in {"jp-mod-procurement", "jp-political-finance"} else (
                "no_match" if confirmed and source_id == "jp-mod-procurement" else "unresolved_identity"
            )
            rows.append({"entity_id": entity_id, "source_id": source_id, "state": state})
    identity = {"manifest": {"entity_count": 3707, "semantic_identity_sha256": "scale-identity"}, "entities": entities}
    coverage = {"manifest": {"coverage_semantic_sha256": "scale-coverage"}, "matrix": {"entity_count": 3707, "source_count": 5, "cell_count": len(rows), "rows": rows}}
    result = build(identity=identity, coverage_artifact=coverage, mod_observations=[], policies=example_policies(), code_commit="scale-test")
    assert result["company_count"] == 3707
    assert result["view_count"] == 11121
    assert result["unresolved_identity_entity_count"] == 8


def test_generated_non_none_results_keep_rule_claim_and_source_traceability():
    observation = mod_observation_fixture()
    observation["subject"] = "誘導弾の整備役務一式"
    result = screening_api()(
        identity=identity_fixture(),
        coverage_artifact=coverage_fixture(),
        mod_observations=[observation],
        policies=example_policies(),
        code_commit="trace-test",
    )
    view = next(
        item for item in result["views"]
        if item["entity_id"] == "wa:org:jp:tse:1001"
        and item["profile_id"] == "example:strict-military-avoidance"
    )
    assert view["decision"] == "EXCLUDE"
    decisive = [item for item in view["claim_results"] if item["decision"] == "EXCLUDE"]
    assert decisive
    assert decisive[0]["claim_id"]
    assert decisive[0]["rule_refs"] == ["exclude-confirmed-military-specific"]
    assert decisive[0]["source_ids"] == ["jp-mod-procurement"]
