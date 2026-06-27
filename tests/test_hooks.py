import subprocess
from pathlib import Path

import pytest
import yaml

HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"


@pytest.fixture
def paused_state(tmp_path):
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge", "version": "1.0.0"},
        "current_run": {
            "run_id": "test",
            "branch": "lincoln/test",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "current_stage": "clarify",
            "previous_stage": "ingest",
            "status": "in_progress",
        },
        "stages": {
            "clarify": {
                "status": "waiting_for_human",
                "started_at": "2026-06-27T00:00:00Z",
                "completed_at": None,
                "entry_checks_passed": True,
                "entry_checks_run_at": "2026-06-27T00:00:00Z",
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            }
        },
        "variables": {},
        "recovery": {},
    }
    path = tmp_path / "workflow-state.yaml"
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def entry_not_passed_state(tmp_path):
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge", "version": "1.0.0"},
        "current_run": {
            "run_id": "test",
            "branch": "lincoln/test",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "current_stage": "clarify",
            "previous_stage": "ingest",
            "status": "in_progress",
        },
        "stages": {
            "clarify": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            }
        },
        "variables": {},
        "recovery": {},
    }
    path = tmp_path / "workflow-state.yaml"
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def run_hook(hook_name, state_file, *extra_args):
    hook = HOOKS_DIR / hook_name
    env = {"LINCOLN_STATE_FILE": str(state_file)}
    return subprocess.run(
        [str(hook), *extra_args],
        cwd=state_file.parent,
        capture_output=True,
        text=True,
        env=env,
    )


def test_pre_tool_use_blocks_write_when_entry_not_passed(entry_not_passed_state):
    result = run_hook(
        "pre-tool-use.sh",
        entry_not_passed_state,
        "Write",
        '{"file_path": "requirements/test/requirements.md"}',
    )
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr


def test_pre_tool_use_allows_read_when_paused(paused_state):
    result = run_hook(
        "pre-tool-use.sh",
        paused_state,
        "Read",
        '{"file_path": "requirements/test/requirements.md"}',
    )
    assert result.returncode == 0


def test_pre_tool_use_blocks_write_when_paused(paused_state):
    result = run_hook(
        "pre-tool-use.sh",
        paused_state,
        "Write",
        '{"file_path": "requirements/test/requirements.md"}',
    )
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr


def test_on_stop_updates_last_updated_at(entry_not_passed_state):
    result = run_hook("on-stop.sh", entry_not_passed_state)
    assert result.returncode == 0
    state = yaml.safe_load(entry_not_passed_state.read_text(encoding="utf-8"))
    assert state["current_run"]["last_updated_at"] != "2026-06-27T00:00:00Z"
