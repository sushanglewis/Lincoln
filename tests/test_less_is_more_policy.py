"""Tests for the 少即是多 (Less is More) artifact-writing policy (#126).

Design decision: the policy is injected exactly once, by the session-start
hook, and only when an issue package is active (current_stage != not_started).
It must NOT live in default.md (which is injected into every stage, including
research/exploration) nor be duplicated across skill prompts/stage YAMLs, to
keep context pressure minimal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".claude" / "policies" / "less-is-more.md"
POLICY_REF = ".claude/policies/less-is-more.md"

import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

import yaml  # noqa: E402


# Minimal copies of the hook test harness (kept self-contained; the source
# helpers in test_hook_session_start.py are not importable without a package).
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


def test_policy_exists_with_core_principles():
    text = POLICY_PATH.read_text(encoding="utf-8")
    assert "少即是多" in text
    assert "结论先行" in text
    assert "删除测试" in text
    assert "三分钟可读" in text
    # Reader/purpose-driven generation
    assert "读者" in text and "用途" in text
    # Explicitly scoped: not for research/exploration stages
    assert "不适用" in text


def test_policy_not_in_universal_contract():
    default = (ROOT / ".claude" / "agents" / "default.md").read_text(encoding="utf-8")
    assert "少即是多" not in default, (
        "少即是多 must not live in default.md — it would be injected into "
        "research/exploration stages where it does not apply"
    )


def test_policy_not_duplicated_across_layers():
    """Single injection point: skill prompts, SKILL.md files, stage YAMLs and
    agent roles must not carry their own copies/references of the policy."""
    import yaml

    layers: list[Path] = []
    layers += sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    layers += sorted((ROOT / ".claude" / "skills").glob("*/prompts/*.md"))
    layers += sorted((ROOT / ".claude" / "agents").glob("*.md"))
    layers += sorted((ROOT / ".claude" / "stages").glob("*.yaml"))
    offenders = [
        str(p.relative_to(ROOT))
        for p in layers
        if p.name != "default.md" and POLICY_REF in p.read_text(encoding="utf-8")
    ]
    assert not offenders, f"policy must be hook-injected only, found references in: {offenders}"


def test_hook_injects_policy_when_issue_package_active(tmp_path):
    root = _make_minimal_repo(tmp_path, branch="issue-42")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage="clarify", process_slug="issue-42")

    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    assert code == 0, stderr
    assert "=== 制品生成纪律（少即是多） ===" in stdout
    assert "删除测试" in stdout  # full policy content, not just a pointer
    assert "三分钟可读" in stdout


def test_hook_skips_policy_without_active_issue_package(tmp_path):
    root = _make_minimal_repo(tmp_path, branch="main")
    _write_setup_state(root, completed=True)
    state_path = _write_workflow_state(root, stage="not_started")

    code, stdout, stderr = _run_hook(root, env={"LINCOLN_STATE_FILE": str(state_path)})

    assert code == 0, stderr
    assert "制品生成纪律" not in stdout
