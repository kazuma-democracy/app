from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/public-browser-extension.yml"
REPORT = ROOT / "docs/results/M2_5_PUBLIC_BROWSER_EXTENSION_V01.md"
RUNBOOK = ROOT / "docs/PUBLIC_BROWSER_EXTENSION_RELEASE.md"


def test_ci_contains_no_store_publish_step_or_credentials():
    workflow = WORKFLOW.read_text(encoding="utf-8").lower()
    forbidden = (
        "chrome-webstore-upload",
        "chromewebstore.googleapis.com",
        "amo api key",
        "jwt issuer",
        "app store connect api key",
        "apple_api_key",
        "web-ext sign",
    )
    assert all(token not in workflow for token in forbidden)


def test_ci_runs_capability_tests_without_node_package_manager():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow.lower()
    assert 'python-version: "3.11"' in workflow
    assert 'node-version: "24"' in workflow
    assert "pytest" in workflow
    assert "node --test tests/browser_extension_search.test.mjs" in workflow
    assert "build_all_packages" in workflow
    assert "npm install" not in lowered
    assert "pnpm" not in lowered
    assert "yarn" not in lowered


def test_report_allows_military_first_store_submission_without_integrating_ohchr():
    report = REPORT.read_text(encoding="utf-8")
    assert "BLOCK_PUBLIC_REUSE_PERMISSION_REQUIRED" in report
    assert "ohchr-settlements-business" in report
    assert "Israel/OPT topic: NOT_INTEGRATED" in report
    assert "Release scope: STORE_SUBMISSION_READY" in report
    assert "OHCHR is optional for v0.1 release" in report
    assert "PUBLIC_RELEASE_COMPLETE" not in report


def test_runbook_requires_human_approval_for_all_store_paths():
    text = RUNBOOK.read_text(encoding="utf-8")
    for browser in ("Chrome", "Edge", "Firefox", "Safari"):
        assert f"## {browser}" in text
    assert text.count("HUMAN APPROVAL REQUIRED") >= 4
    assert "fresh official" in text.lower()
    assert "TestFlight" in text
    assert "addons.mozilla.org" in text
    assert "Chrome Web Store" in text
    assert "Microsoft Edge Add-ons" in text
    assert "OHCHR is optional for v0.1 release" in text
    assert "military_defence" in text
    assert "NOT_INTEGRATED" in text
