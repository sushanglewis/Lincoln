"""Tests for opening-guidance injection in .claude/hooks/on-session-start.sh."""

import os
import subprocess
from pathlib import Path

import yaml

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "on-session-start.sh"
GUIDANCE_MARKER = "=== Lincoln 开场引导 ==="


def _write_state(tmp_path, state):
    path = tmp_path / "lc-test" / "workflow-stage.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _state(current_stage, status="in_progress"):
    return {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge", "version": "1.0.0"},
        "current_run": {
            "run_id": "test",
            "branch": "issue-999",
            "started_at": "2026-07-15T00:00:00Z",
            "last_updated_at": "2026-07-15T00:00:00Z",
            "current_stage": current_stage,
            "status": status,
            "variables": {"process_slug": "lc-test", "session_id": "", "design_id": ""},
        },
        "nodes": [],
        "recovery": {},
    }


def run_session_start(state_file):
    env = os.environ.copy()
    env["LINCOLN_STATE_FILE"] = str(state_file)
    env["LINCOLN_SKIP_DEP_CHECK"] = "1"
    return subprocess.run(
        [str(HOOK)],
        cwd=state_file.parent,
        capture_output=True,
        text=True,
        env=env,
    )


def test_fresh_repo_injects_opening_guidance(tmp_path):
    missing = tmp_path / "no-such-state.yaml"
    result = run_session_start(missing)
    assert result.returncode == 0
    assert GUIDANCE_MARKER in result.stdout
    assert "intake-prompt.md" in result.stdout


def test_not_started_stage_injects_opening_guidance(tmp_path):
    state_file = _write_state(tmp_path, _state("not_started", status="not_started"))
    result = run_session_start(state_file)
    assert result.returncode == 0
    assert GUIDANCE_MARKER in result.stdout
    assert "validate-entry" in result.stdout


def test_active_stage_does_not_inject_guidance(tmp_path):
    state = _state("clarify")
    state["nodes"] = [
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "in_progress",
            "gate_passed": False,
            "approved_by": None,
            "artifacts": [],
            "handoff_file": None,
        }
    ]
    state_file = _write_state(tmp_path, state)
    result = run_session_start(state_file)
    assert result.returncode == 0
    assert GUIDANCE_MARKER not in result.stdout
    assert "=== Lincoln Stage Context ===" in result.stdout
