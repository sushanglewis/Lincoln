"""Tests for scripts/lincoln_workflow.py (lc-wf-* bundle CLI)."""

import pytest
import yaml

from scripts import lincoln_workflow as lw


def test_list_workflows_prints_all_with_modes(capsys):
    assert lw.list_workflows() == 0
    out = capsys.readouterr().out
    for name in (
        "interview-to-knowledge",
        "bug-fix",
        "design-spike",
        "existing-project-iteration",
        "oss-first-design",
    ):
        assert name in out
    assert "solo" in out and "team" in out


def test_load_workflow_definition_unknown_raises():
    with pytest.raises(SystemExit):
        lw.load_workflow_definition("does-not-exist")


def test_start_solo_creates_instance(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    wf = lw.load_workflow_definition("bug-fix")
    assert lw.start_solo("bug-fix", wf, force=False) == 0

    state_path = tmp_path / ".context" / "workflow" / "bug-fix.yaml"
    assert state_path.is_file()
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert state["schema_version"] == "2.0.0"
    assert state["workflow"]["template"] == "bug-fix"
    assert state["current_run"]["current_stage"] == wf["steps"][0]["id"]
    assert state["current_run"]["status"] == "in_progress"
    assert state["current_run"]["execution_mode"] == "solo"
    assert state["current_run"]["variables"]["process_slug"] == ".context"
    assert state["recovery"]["can_resume_from"] == wf["steps"][0]["id"]


def test_start_solo_refuses_overwrite_without_force(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    wf = lw.load_workflow_definition("bug-fix")
    lw.start_solo("bug-fix", wf, force=False)
    with pytest.raises(SystemExit):
        lw.start_solo("bug-fix", wf, force=False)
    assert lw.start_solo("bug-fix", wf, force=True) == 0


def test_start_team_requires_issue_number():
    with pytest.raises(SystemExit):
        lw.start_team("interview-to-knowledge", None)


def test_cmd_start_dispatches_team(monkeypatch):
    calls = {}

    def fake_start_team(workflow_name, issue_number):
        calls["workflow"] = workflow_name
        calls["issue_number"] = issue_number
        return 0

    monkeypatch.setattr(lw, "start_team", fake_start_team)
    args = type("Args", (), {"workflow": "interview-to-knowledge", "issue_number": "48", "force": False, "session_id": None})
    assert lw.cmd_start(args) == 0
    assert calls == {"workflow": "interview-to-knowledge", "issue_number": "48"}


def test_cmd_start_dispatches_solo(tmp_path, monkeypatch):
    import types
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    args = types.SimpleNamespace(workflow="design-spike", issue_number=None, force=False, session_id=None)
    assert lw.cmd_start(args) == 0
    assert (tmp_path / ".context" / "workflow" / "design-spike.yaml").is_file()


def test_start_solo_uses_provided_session_id(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    wf = lw.load_workflow_definition("bug-fix")
    assert lw.start_solo("bug-fix", wf, force=False, session_id="my-session") == 0
    state_path = tmp_path / ".context" / "workflow" / "bug-fix.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    assert state["current_run"]["variables"]["session_id"] == "my-session"


def test_start_solo_generates_default_session_id(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    wf = lw.load_workflow_definition("bug-fix")
    assert lw.start_solo("bug-fix", wf, force=False) == 0
    state_path = tmp_path / ".context" / "workflow" / "bug-fix.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    sid = state["current_run"]["variables"]["session_id"]
    assert sid.startswith("bug-fix-")


def test_load_workflow_definition_rejects_path_traversal():
    with pytest.raises(SystemExit):
        lw.load_workflow_definition("../../../etc/passwd")


def test_start_solo_rejects_invalid_workflow_name(tmp_path, monkeypatch):
    monkeypatch.setattr(lw, "SOLO_STATE_DIR", tmp_path / ".context" / "workflow")
    with pytest.raises(SystemExit):
        lw.start_solo("../../../x", {"steps": []}, force=False)
