from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "real-identity-pilot.yml"


def test_live_identity_acquisition_is_manual_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Diagnose JPX request client" not in text
    assert (
        "- name: Run official-data 100-company pilot\n"
        "        if: github.event_name == 'workflow_dispatch'"
    ) in text
    assert (
        "- name: Print report\n"
        "        if: github.event_name == 'workflow_dispatch'"
    ) in text
    assert (
        "- name: Publish live identity pilot artifact\n"
        "        if: github.event_name == 'workflow_dispatch'"
    ) in text
