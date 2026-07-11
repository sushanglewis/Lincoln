"""Tests for skill routing derived from .claude/stages/*.yaml."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGES_DIR = ROOT / ".claude" / "stages"
WORKFLOW_PATH = ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"

VALID_NAMESPACES = {
    "superpowers",
    "gsd",
    "openspec",
    "oh-my-claudecode",
    "lincoln",
}


@pytest.fixture
def stage_files():
    return sorted(p for p in STAGES_DIR.glob("*.yaml") if p.stem != "stage-manifest")


@pytest.fixture
def routing(stage_files):
    """Build routing table from stage YAMLs."""
    data = {}
    for path in stage_files:
        stage = yaml.safe_load(path.read_text(encoding="utf-8"))
        skills = stage.get("skills", {})
        data[stage["id"]] = {
            "required": skills.get("required", []),
            "optional": skills.get("optional", []),
            "human_gate": stage.get("human_gate", False),
        }
    return data


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_routing_has_entries(routing):
    assert routing, f"No routing entries found under {STAGES_DIR}"


# ---------------------------------------------------------------------------
# Stage routing structure tests
# ---------------------------------------------------------------------------


def test_every_stage_has_required_optional_human_gate(routing):
    for stage_id, stage_def in routing.items():
        assert "required" in stage_def, f"Stage '{stage_id}' missing 'required'"
        assert isinstance(stage_def["required"], list), f"Stage '{stage_id}' required not a list"
        assert "optional" in stage_def, f"Stage '{stage_id}' missing 'optional'"
        assert isinstance(stage_def["optional"], list), f"Stage '{stage_id}' optional not a list"
        assert "human_gate" in stage_def, f"Stage '{stage_id}' missing 'human_gate'"
        assert isinstance(stage_def["human_gate"], bool), f"Stage '{stage_id}' human_gate not a bool"


# ---------------------------------------------------------------------------
# Workflow coverage tests
# ---------------------------------------------------------------------------


def test_every_interview_workflow_stage_has_routing_entry(routing):
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    workflow_steps = workflow.get("workflow", {}).get("steps", [])
    step_ids = {step["id"] for step in workflow_steps}

    missing = step_ids - set(routing.keys())
    assert not missing, f"Workflow stages missing from routing: {missing}"


# ---------------------------------------------------------------------------
# Namespace validation tests
# ---------------------------------------------------------------------------


def _extract_namespace(skill_str: str) -> str:
    if ":" in skill_str:
        return skill_str.split(":", 1)[0]
    return skill_str


def test_required_skills_use_recognized_namespaces(routing):
    for stage_id, stage_def in routing.items():
        for skill in stage_def.get("required", []):
            ns = _extract_namespace(skill)
            assert ns in VALID_NAMESPACES, (
                f"Stage '{stage_id}' required skill '{skill}' has unrecognized namespace '{ns}'"
            )


def test_optional_skills_use_recognized_namespaces(routing):
    for stage_id, stage_def in routing.items():
        for skill in stage_def.get("optional", []):
            ns = _extract_namespace(skill)
            assert ns in VALID_NAMESPACES, (
                f"Stage '{stage_id}' optional skill '{skill}' has unrecognized namespace '{ns}'"
            )


# ---------------------------------------------------------------------------
# Specific stage tests
# ---------------------------------------------------------------------------


def test_clarify_has_brainstorming_required(routing):
    assert "superpowers:brainstorming" in routing["clarify"]["required"]


def test_clarify_has_human_gate(routing):
    assert routing["clarify"]["human_gate"] is True


def test_implement_has_tdd_required(routing):
    assert "superpowers:test-driven-development" in routing["implement"]["required"]


def test_implement_has_human_gate(routing):
    assert routing["implement"]["human_gate"] is True


def test_sync_knowledge_has_docs_update_required(routing):
    assert "gsd:docs-update" in routing["sync-knowledge"]["required"]
