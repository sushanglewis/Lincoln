"""Tests for the everything-claude-code hook scripts in .claude/hooks/."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
GUARD_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "task_tool_guard.py"


def _write_state(tmp_path, state):
    # Place the state file at <tmp-project-root>/.claude/workflow-state.yaml so
    # resolve_project_root() returns tmp_path and the burst counter is isolated.
    path = tmp_path / ".claude" / "workflow-state.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _write_process_state(tmp_path, state):
    """Place the state file inside a process package, e.g. <slug>/workflow-stage.yaml."""
    slug = state.get("current_run", {}).get("variables", {}).get("process_slug", "lincoln-test")
    path = tmp_path / slug / "workflow-stage.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


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
    return _write_state(tmp_path, state)


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
    return _write_state(tmp_path, state)


@pytest.fixture
def process_package_state(tmp_path):
    """A node-based state file living inside a process package."""
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge", "version": "1.0.0"},
        "current_run": {
            "run_id": "test",
            "branch": "lincoln/test",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "current_stage": "clarify",
            "previous_stage": "ingest",
            "status": "in_progress",
            "variables": {"process_slug": "lincoln-test", "session_id": "", "design_id": ""},
        },
        "nodes": [
            {
                "stage_id": "clarify",
                "node_id": "clarify-1",
                "status": "in_progress",
                "gate_passed": False,
                "approved_by": None,
                "artifacts": [],
                "handoff_file": None,
            }
        ],
        "recovery": {},
    }
    return _write_process_state(tmp_path, state)


def run_hook(hook_name, state_file, *extra_args):
    hook = HOOKS_DIR / hook_name
    env = os.environ.copy()
    env["LINCOLN_STATE_FILE"] = str(state_file)
    return subprocess.run(
        [str(hook), *extra_args],
        cwd=state_file.parent,
        capture_output=True,
        text=True,
        env=env,
    )


def run_guard(state_file, tool_name, tool_args="{}", **kwargs):
    cmd = [
        str(GUARD_SCRIPT),
        "--state-file",
        str(state_file),
        "--tool-name",
        tool_name,
        "--tool-args",
        tool_args,
    ]
    for key, value in kwargs.items():
        cmd.append(f"--{key.replace('_', '-')}")
        cmd.append(str(value))
    return subprocess.run(
        cmd,
        cwd=state_file.parent,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


def burst_counter_file(state_file):
    # state_file is at <root>/.claude/workflow-state.yaml in these fixtures.
    return state_file.resolve().parents[1] / ".context" / "task-tool-burst.json"


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


def test_pre_tool_use_blocks_root_process_artifact_write(dialogue_in_progress_state):
    result = run_hook(
        "pre-tool-use.sh",
        dialogue_in_progress_state,
        "Write",
        '{"file_path": "requirements/test/requirements.md"}',
    )
    assert result.returncode == 1
    assert "process artifacts must be written under" in result.stderr


def test_pre_tool_use_blocks_state_file_write(process_package_state):
    result = run_hook(
        "pre-tool-use.sh",
        process_package_state,
        "Write",
        '{"file_path": "lincoln-test/workflow-stage.yaml"}',
    )
    assert result.returncode == 1
    assert "workflow state must be updated through stage_loader" in result.stderr


def test_pre_tool_use_allows_process_package_artifact(process_package_state):
    result = run_hook(
        "pre-tool-use.sh",
        process_package_state,
        "Write",
        '{"file_path": "lincoln-test/requirements/test/requirements.md"}',
    )
    assert result.returncode == 0


def test_pre_tool_use_blocks_plain_pen_access(dialogue_in_progress_state):
    result = run_hook(
        "pre-tool-use.sh",
        dialogue_in_progress_state,
        "Read",
        '{"file_path": "lincoln-test/designs/test/prototype.pen"}',
    )
    assert result.returncode == 1
    assert ".pen files must be handled through Pencil tools" in result.stderr


def test_on_stop_updates_last_updated_at(entry_not_passed_state):
    result = run_hook("on-stop.sh", entry_not_passed_state)
    assert result.returncode == 0
    state = yaml.safe_load(entry_not_passed_state.read_text(encoding="utf-8"))
    assert state["current_run"]["last_updated_at"] != "2026-06-27T00:00:00Z"


@pytest.fixture
def dialogue_in_progress_state(tmp_path):
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
                "status": "in_progress",
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
    return _write_state(tmp_path, state)


@pytest.fixture
def implementation_stage_state(tmp_path):
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge", "version": "1.0.0"},
        "current_run": {
            "run_id": "test",
            "branch": "lincoln/test",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "current_stage": "tdd-development-plan",
            "previous_stage": "product-prototype",
            "status": "in_progress",
        },
        "stages": {
            "tdd-development-plan": {
                "status": "in_progress",
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
    return _write_state(tmp_path, state)


def test_task_create_blocked_in_dialogue_stage(dialogue_in_progress_state):
    result = run_hook(
        "pre-tool-use.sh",
        dialogue_in_progress_state,
        "TaskCreate",
        '{"subject": "Output message now", "description": "placeholder"}',
    )
    assert result.returncode == 1
    assert "TaskCreate/TaskUpdate are not allowed" in result.stderr


def test_task_update_blocked_in_dialogue_stage(dialogue_in_progress_state):
    result = run_hook(
        "pre-tool-use.sh",
        dialogue_in_progress_state,
        "TaskUpdate",
        '{"taskId": "1", "status": "completed"}',
    )
    assert result.returncode == 1
    assert "TaskCreate/TaskUpdate are not allowed" in result.stderr


def test_consecutive_task_tools_blocked_after_threshold(implementation_stage_state):
    for i in range(3):
        result = run_hook(
            "pre-tool-use.sh",
            implementation_stage_state,
            "TaskCreate",
            f'{{"subject": "task {i}"}}',
        )
        assert result.returncode == 0, f"call {i + 1} should be allowed"

    counter_file = burst_counter_file(implementation_stage_state)
    assert counter_file.exists()
    assert json.loads(counter_file.read_text(encoding="utf-8"))["count"] == 3

    blocked = run_hook(
        "pre-tool-use.sh",
        implementation_stage_state,
        "TaskCreate",
        '{"subject": "task 4"}',
    )
    assert blocked.returncode == 1
    assert "Too many consecutive task-tool calls" in blocked.stderr
    assert json.loads(counter_file.read_text(encoding="utf-8"))["count"] == 4

    # A non-task tool resets the burst counter.
    read_result = run_hook(
        "pre-tool-use.sh",
        implementation_stage_state,
        "Read",
        '{"file_path": "designs/test/tdd-plan.md"}',
    )
    assert read_result.returncode == 0
    assert json.loads(counter_file.read_text(encoding="utf-8"))["count"] == 0

    after_read = run_hook(
        "pre-tool-use.sh",
        implementation_stage_state,
        "TaskCreate",
        '{"subject": "task after reset"}',
    )
    assert after_read.returncode == 0
    assert json.loads(counter_file.read_text(encoding="utf-8"))["count"] == 1


def test_mixed_task_tools_count_toward_threshold(implementation_stage_state):
    for tool in ("TaskCreate", "TaskUpdate", "TaskCreate"):
        result = run_hook(
            "pre-tool-use.sh",
            implementation_stage_state,
            tool,
            '{"subject": "x"}',
        )
        assert result.returncode == 0

    blocked = run_hook(
        "pre-tool-use.sh",
        implementation_stage_state,
        "TaskUpdate",
        '{"taskId": "1"}',
    )
    assert blocked.returncode == 1
    assert "Too many consecutive task-tool calls" in blocked.stderr


def test_guard_allows_task_tools_when_dialogue_override_empty(dialogue_in_progress_state):
    result = run_guard(
        dialogue_in_progress_state,
        "TaskCreate",
        '{"subject": "x"}',
        dialogue_stages="",
    )
    assert result.returncode == 0


def test_guard_blocks_when_dialogue_override_contains_stage(dialogue_in_progress_state):
    result = run_guard(
        dialogue_in_progress_state,
        "TaskCreate",
        '{"subject": "x"}',
        dialogue_stages="clarify",
    )
    assert result.returncode == 1
    assert "TaskCreate/TaskUpdate are not allowed" in result.stderr
