"""Tests that on-session-start.sh avoids expensive full-text dumps (#63)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _write_setup_state(root: Path, completed: bool) -> None:
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
    root = tmp_path / "repo"
    root.mkdir()
    shutil.copytree(ROOT / ".claude", root / ".claude")
    shutil.copytree(ROOT / "scripts", root / "scripts")
    (root / ".context").mkdir(exist_ok=True)
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-b", branch], cwd=root, check=True, capture_output=True)
    return root


def _run_hook(root: Path, env: dict | None = None) -> tuple[int, str, str]:
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


def test_active_stage_does_not_cat_agent_contract(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="issue-42")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage="clarify", process_slug="issue-42")

    # Act
    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    # Assert
    assert code == 0, stderr
    assert "Agent file: .claude/agents/pm.md" in stdout
    assert "Behavioral contract: .claude/agents/_contract.md" in stdout
    # The full agent contract text should not be dumped
    assert "## Lincoln Agent Contract" not in stdout


def test_active_stage_stage_context_is_summary_not_full_text(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="issue-42")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage="clarify", process_slug="issue-42")

    # Act
    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    # Assert
    assert code == 0, stderr
    assert "Goal:" in stdout
    assert "Primary agent:" in stdout
    # The long context block should not be dumped verbatim
    assert "## Goal" not in stdout
    assert "Use Read to inspect the full stage YAML if needed." in stdout


def test_dependency_missing_message_is_single_line(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=False)

    # Act
    code, stdout, stderr = _run_hook(
        root, env={"LINCOLN_SKIP_DEP_CHECK": "0"}
    )

    # Assert
    assert code == 0, stderr
    assert "Lincoln 依赖未就绪" in stdout
    # The old 7-line Chinese block header should be gone
    assert "=== Lincoln 依赖缺失 ===" not in stdout


def test_no_state_guidance_points_to_intake_prompt(tmp_path):
    # Arrange
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=True)

    # Act
    code, stdout, stderr = _run_hook(root)

    # Assert
    assert code == 0, stderr
    assert "lc-workflow-router/prompts/intake-prompt.md" in stdout
