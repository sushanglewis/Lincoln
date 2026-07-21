"""Tests for scripts/lincoln_command_map.py."""

import json
from pathlib import Path

import pytest
import yaml

from scripts.lincoln_command_map import build_commands


def _write_command_map(root: Path, commands: dict) -> None:
    path = root / ".claude" / "harnesses" / "command-map.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"commands": commands}), encoding="utf-8")


def _write_plugin(root: Path, skills: list[str] | None = None) -> None:
    path = root / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    plugin = {
        "name": "lincoln",
        "version": "1.0.0",
        "description": "test",
        "author": {"name": "test"},
        "skills": skills or [],
        "agents": ["./.claude/agents/"],
    }
    path.write_text(json.dumps(plugin, indent=2), encoding="utf-8")


def _write_workflow(root: Path, name: str, mode: str = "solo") -> None:
    path = root / ".claude" / "workflows" / f"{name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "workflow": {
                    "name": name,
                    "version": "1.0.0",
                    "description": f"workflow {name}",
                    "execution_mode": mode,
                    "steps": [{"id": "step1", "name": "Step 1", "description": "d"}],
                }
            }
        ),
        encoding="utf-8",
    )


def _write_agent(root: Path, name: str) -> None:
    path = root / ".claude" / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nname: {name}\ndescription: agent {name}\n---\n\ncontent\n",
        encoding="utf-8",
    )


def _write_skill(root: Path, name: str) -> None:
    path = root / ".claude" / "skills" / name
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: skill {name}\n---\n\ncontent\n",
        encoding="utf-8",
    )


def _write_scenarios(root: Path, scenarios: dict) -> None:
    path = root / ".claude" / "harnesses" / "scenarios.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"scenarios": scenarios}), encoding="utf-8")


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "default.md").write_text(
        "---\nname: default\n---\n\nDefault.\n", encoding="utf-8"
    )
    _write_command_map(
        root,
        {
            "lc-status": {
                "description": "status",
                "action": "python3 scripts/lincoln-status.py",
            }
        },
    )
    _write_plugin(root, ["./.claude/skills/old/"])
    _write_workflow(root, "alpha", "solo")
    _write_workflow(root, "beta", "team")
    _write_agent(root, "pm")
    _write_agent(root, "engineer")
    _write_skill(root, "clarify-requirements")
    _write_skill(root, "lc-first-principles")
    _write_scenarios(
        root,
        {
            "make-prd": {
                "description": "make PRD",
                "role": "pm",
                "skills": ["clarify-requirements"],
                "goal": "PRD",
            }
        },
    )
    import scripts.lincoln_command_map as cm
    cm.PROJECT_ROOT = root
    cm.COMMAND_MAP_PATH = root / ".claude" / "harnesses" / "command-map.yaml"
    cm.SCENARIOS_PATH = root / ".claude" / "harnesses" / "scenarios.yaml"
    cm.PLUGIN_PATH = root / ".claude-plugin" / "plugin.json"
    cm.WORKFLOWS_DIR = root / ".claude" / "workflows"
    cm.AGENTS_DIR = root / ".claude" / "agents"
    cm.SKILLS_DIR = root / ".claude" / "skills"
    monkeypatch.chdir(root)
    return root


def test_build_commands_preserves_static_command(fake_repo):
    commands = build_commands()
    assert "lc-status" in commands
    assert commands["lc-status"]["action"] == "python3 scripts/lincoln-status.py"


def test_build_commands_generates_workflow_commands(fake_repo):
    commands = build_commands()
    assert "lc-wf-alpha" in commands
    assert commands["lc-wf-alpha"]["action"] == "python3 scripts/lincoln_workflow.py"
    assert "start --workflow alpha" in commands["lc-wf-alpha"].get("args_hint", "")
    assert "lc-wf-beta" in commands
    assert "--issue-number" in commands["lc-wf-beta"].get("args_hint", "")


def test_build_commands_generates_agent_commands(fake_repo):
    commands = build_commands()
    assert "lc-agent-pm" in commands
    assert commands["lc-agent-pm"]["action"] == "python3 scripts/lincoln_role.py --role pm"
    assert "lc-agent-engineer" in commands


def test_build_commands_generates_skill_commands(fake_repo):
    commands = build_commands()
    assert "lc-skill-clarify-requirements" in commands
    assert (
        commands["lc-skill-clarify-requirements"]["action"]
        == "python3 scripts/lincoln_skill_prompt.py --skill clarify-requirements"
    )
    assert "lc-skill-lc-first-principles" in commands


def test_build_commands_generates_scenario_commands(fake_repo):
    commands = build_commands()
    assert "lc-scenario-make-prd" in commands
    assert (
        commands["lc-scenario-make-prd"]["action"]
        == "python3 scripts/lincoln_scenario.py --scenario make-prd"
    )


def test_all_commands_start_with_lc(fake_repo):
    commands = build_commands()
    assert all(k.startswith("lc-") for k in commands)


def test_refresh_updates_command_map_and_plugin(fake_repo, monkeypatch):
    import scripts.lincoln_command_map as cm

    monkeypatch.setattr(cm, "PROJECT_ROOT", fake_repo)
    cm.COMMAND_MAP_PATH = fake_repo / ".claude" / "harnesses" / "command-map.yaml"
    cm.SCENARIOS_PATH = fake_repo / ".claude" / "harnesses" / "scenarios.yaml"
    cm.PLUGIN_PATH = fake_repo / ".claude-plugin" / "plugin.json"
    cm.WORKFLOWS_DIR = fake_repo / ".claude" / "workflows"
    cm.AGENTS_DIR = fake_repo / ".claude" / "agents"
    cm.SKILLS_DIR = fake_repo / ".claude" / "skills"

    cm.refresh_command_map()
    cm.refresh_plugin_json()

    data = yaml.safe_load(cm.COMMAND_MAP_PATH.read_text(encoding="utf-8"))
    commands = data["commands"]
    assert "lc-wf-alpha" in commands
    assert "lc-agent-pm" in commands
    assert "lc-skill-clarify-requirements" in commands
    assert "lc-scenario-make-prd" in commands
    assert "lc-status" in commands

    plugin = json.loads(cm.PLUGIN_PATH.read_text(encoding="utf-8"))
    skill_names = {Path(s).parts[-1] for s in plugin["skills"]}
    assert "clarify-requirements" in skill_names
    assert "lc-first-principles" in skill_names
    assert "old" not in skill_names
