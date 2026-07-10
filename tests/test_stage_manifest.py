"""Tests for .claude/stages/*.yaml stage definitions."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGES_DIR = ROOT / ".claude" / "stages"
WORKFLOW_PATH = ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"

REQUIRED_KEYS = {
    "schema_version",
    "id",
    "name",
    "description",
    "templates",
    "prerequisite_stage",
    "next_stage",
    "human_gate",
    "agent",
    "skills",
    "artifacts",
    "context",
    "gates",
}


@pytest.fixture
def stage_files():
    return sorted(p for p in STAGES_DIR.glob("*.yaml") if p.stem != "stage-manifest")


@pytest.fixture
def stages(stage_files):
    loaded = []
    for path in stage_files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path.name}: root is not a mapping"
        loaded.append((path, data))
    return loaded


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_stage_yaml_files_exist(stage_files):
    assert stage_files, f"No stage YAML files found under {STAGES_DIR}"


def test_every_stage_has_required_keys(stages):
    for path, data in stages:
        missing = REQUIRED_KEYS - set(data.keys())
        assert not missing, f"{path.name}: missing keys {missing}"


def test_every_stage_has_context_goal(stages):
    for path, data in stages:
        assert "goal" in data.get("context", {}), f"{path.name}: missing context.goal"


def test_human_gate_is_boolean(stages):
    for path, data in stages:
        assert isinstance(data["human_gate"], bool), f"{path.name}: human_gate is not a bool"


def test_agent_block_has_primary(stages):
    for path, data in stages:
        agent = data.get("agent", {})
        assert "primary" in agent, f"{path.name}: missing agent.primary"


def test_skills_are_lists(stages):
    for path, data in stages:
        skills = data.get("skills", {})
        assert isinstance(skills.get("required", []), list), f"{path.name}: required skills not a list"
        assert isinstance(skills.get("optional", []), list), f"{path.name}: optional skills not a list"


def test_artifacts_are_lists(stages):
    for path, data in stages:
        artifacts = data.get("artifacts", {})
        assert isinstance(artifacts.get("required", []), list), f"{path.name}: required artifacts not a list"
        assert isinstance(artifacts.get("optional", []), list), f"{path.name}: optional artifacts not a list"


# ---------------------------------------------------------------------------
# Id consistency tests
# ---------------------------------------------------------------------------


def test_stage_filename_matches_id(stages):
    for path, data in stages:
        assert path.stem == data["id"], (
            f"{path.name}: filename '{path.stem}' does not match id '{data['id']}'"
        )


# ---------------------------------------------------------------------------
# Workflow coverage tests
# ---------------------------------------------------------------------------


def test_every_workflow_stage_has_yaml(stages):
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    workflow_steps = workflow.get("workflow", {}).get("steps", [])
    workflow_stage_ids = {step["id"] for step in workflow_steps}

    yaml_stage_ids = {data["id"] for _, data in stages}

    missing = workflow_stage_ids - yaml_stage_ids
    assert not missing, f"Workflow stages missing from stage YAMLs: {missing}"


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------


def test_entry_and_exit_gates_are_lists(stages):
    for path, data in stages:
        gates = data.get("gates", {})
        assert isinstance(gates.get("entry", []), list), f"{path.name}: entry gates not a list"
        assert isinstance(gates.get("exit", []), list), f"{path.name}: exit gates not a list"
