"""Tests for the machine-readable output shape of on-session-start.sh (#67)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "on-session-start.sh"
SETUP_SCRIPT = ROOT / "scripts" / "lincoln-setup.py"


def _write_setup_state(root: Path, completed: bool) -> None:
    """Create a minimal lc-setup-state.yaml."""
    context_dir = root / ".context"
    context_dir.mkdir(parents=True, exist_ok=True)
    status = "completed" if completed else "pending"
    steps = {
        "skills": {"status": status},
        "clis": {"status": status},
        "repo_config": {"status": status},
        "init_project": {"status": status},
    }
    state = {"schema_version": "1.0.0", "steps": steps}
    (context_dir / "lc-setup-state.yaml").write_text(
        yaml.safe_dump(state), encoding="utf-8"
    )


def _write_workflow_state(root: Path, stage: str, process_slug: str = "") -> Path:
    """Create a minimal workflow-stage.yaml in the repo."""
    if process_slug:
        state_dir = root / process_slug
    else:
        state_dir = root / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "workflow-stage.yaml"
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge", "template": "interview-to-knowledge"},
        "current_run": {
            "current_stage": stage,
            "status": "in_progress",
            "variables": {"process_slug": process_slug},
        },
        "nodes": [],
        "recovery": {},
    }
    state_path.write_text(yaml.safe_dump(state), encoding="utf-8")
    return state_path


def _make_minimal_repo(tmp_path: Path, branch: str = "main") -> Path:
    """Create a minimal Lincoln-like repo and git-initialize it."""
    root = tmp_path / "repo"
    root.mkdir()
    # Copy only the files the hook actually needs
    shutil.copytree(ROOT / ".claude", root / ".claude")
    shutil.copytree(ROOT / "scripts", root / "scripts")
    (root / ".context").mkdir(exist_ok=True)
    # minimal dependencies.yaml is already in .claude
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-b", branch], cwd=root, check=True, capture_output=True)
    return root


def _run_hook(root: Path, env: dict | None = None) -> tuple[int, str, str]:
    """Run on-session-start.sh and return (exit_code, stdout, stderr)."""
    environment = {
        "HOME": str(Path.home()),
        "LINCOLN_SESSION_START_JSON": "1",
        "LINCOLN_SKIP_TRACE": "1",
        "LINCOLN_SKIP_DEP_CHECK": "1",
    }
    if env:
        environment.update(env)
    result = subprocess.run(
        ["bash", str(root / ".claude" / "hooks" / "on-session-start.sh")],
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, **environment},
    )
    return result.returncode, result.stdout, result.stderr


def _last_json_line(stdout: str) -> dict:
    """Extract the last line of stdout and parse it as JSON."""
    lines = [line for line in stdout.splitlines() if line.strip()]
    assert lines, "hook produced no output"
    return json.loads(lines[-1])


@pytest.mark.parametrize(
    "stage,has_state,expected_guidance",
    [
        ("not_started", True, True),
        ("clarify", True, False),
    ],
)
def test_session_start_json_shape_active_state(tmp_path, stage, has_state, expected_guidance):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="issue-42")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage=stage, process_slug="issue-42")

    # Act
    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    # Assert
    assert code == 0, stderr
    data = _last_json_line(stdout)
    assert data["schema_version"] == "1.0.0"
    assert data["has_state"] is has_state
    assert data["setup_complete"] is True
    assert data["guidance_injected"] is expected_guidance
    assert data["current_stage"] == stage
    assert data["workflow_template"] == "interview-to-knowledge"
    assert data["process_slug"] == "issue-42"


def test_session_start_json_no_state_shows_guidance(tmp_path):
    # Arrange: repo on a non-issue branch, no state file
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=True)

    # Act
    code, stdout, stderr = _run_hook(root)

    # Assert
    assert code == 0, stderr
    data = _last_json_line(stdout)
    assert data["has_state"] is False
    assert data["setup_complete"] is True
    assert data["guidance_injected"] is True
    assert data["current_stage"] == "not_started"


def test_session_start_json_setup_incomplete(tmp_path):
    # Arrange: setup not complete, no state file
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=False)

    # Act
    code, stdout, stderr = _run_hook(root)

    # Assert: hook exits early after dependency alert
    assert code == 0, stderr
    data = _last_json_line(stdout)
    assert data["setup_complete"] is False
    assert data["has_state"] is False
    assert data["current_stage"] == "not_started"


def test_session_start_json_skipped_when_env_not_set(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=True)

    # Act
    code, stdout, stderr = _run_hook(root, env={"LINCOLN_SESSION_START_JSON": "0"})

    # Assert
    assert code == 0, stderr
    lines = [line for line in stdout.splitlines() if line.strip()]
    # Last line should be the human-readable footer, not JSON
    assert lines[-1] == "=== End Lincoln Session Start ==="
    with pytest.raises(json.JSONDecodeError):
        json.loads(lines[-1])


def test_session_start_shape_includes_required_fields(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="issue-42")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage="clarify", process_slug="issue-42")

    # Act
    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    # Assert
    assert code == 0, stderr
    data = _last_json_line(stdout)
    required = {
        "schema_version",
        "has_state",
        "guidance_injected",
        "setup_complete",
        "current_stage",
        "status",
        "workflow_template",
        "process_slug",
    }
    assert required.issubset(data.keys())
