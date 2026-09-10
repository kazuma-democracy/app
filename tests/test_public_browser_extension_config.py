import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_m25_extension_config_freezes_scope():
    cfg = json.loads((ROOT / "configs/m2-5-public-browser-extension-v0.1.json").read_text(encoding="utf-8"))
    assert cfg["issue"] == 91
    assert cfg["artifact_version"] == "m2-5-public-browser-extension-v0.1"
    assert cfg["browsers"] == ["chrome", "edge", "firefox", "safari"]
    assert cfg["public_topics"] == ["military_defence", "ohchr_settlement_related"]
    assert cfg["required_public_topics"] == ["military_defence"]
    assert cfg["optional_public_topics"] == ["ohchr_settlement_related"]
    assert cfg["release_requires_all_required_topics_ready"] is True
    assert cfg["optional_topic_states_allowed_at_release"] == ["NOT_INTEGRATED"]
    assert "release_requires_all_public_topics_ready" not in cfg
    assert cfg["permissions"]["forbidden"] == [
        "<all_urls>", "history", "cookies", "webRequest", "nativeMessaging"
    ]
    assert cfg["manual_search_required"] is True
    assert cfg["page_hint_identity_authority"] is False
    assert cfg["policy_evaluator_location"] == "python_release_time_only"
    assert cfg["telemetry"] is False
    assert cfg["account_required"] is False
    assert cfg["remote_executable_code"] is False
    assert cfg["store_submission_requires_human_approval"] is True
    assert cfg["source_rights_contract"] == "configs/public-client-sources-v0.1.json"
    assert cfg["preserved_issue"] == 85


def test_roadmap_keeps_issue_85_open_while_issue_91_is_current():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    assert "#91" in roadmap and "CURRENT PUBLIC-PRODUCT PRIORITY" in roadmap
    assert "#85" in roadmap and "OPEN / PRESERVED / PAUSED FOR PRODUCT SEQUENCING" in roadmap
