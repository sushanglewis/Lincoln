"""Tests for sub-agent delegation validation in stage_loader."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def agents_dir(tmp_path):
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "architect.md").write_text("# architect", encoding="utf-8")
    (agents / "security-reviewer.md").write_text("# security", encoding="utf-8")
    return agents


@pytest.fixture
def stage_loader_module(tmp_path, agents_dir, monkeypatch):
    import scripts.stage_loader as sl

    monkeypatch.setattr(sl, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(sl, "STAGES_DIR", tmp_path / ".claude" / "stages")
    return sl


def test_delegation_passes_with_valid_agents_and_schema(stage_loader_module):
    schemas = stage_loader_module.PROJECT_ROOT / ".claude" / "schemas"
    schemas.mkdir(parents=True)
    (schemas / "design-review-feedback.json").write_text(
        json.dumps({"type": "object"}), encoding="utf-8"
    )
    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
  parallel_specialists:
    - lc-architect
    - lc-security-reviewer
  merge_strategy: priority
  output_schema: .claude/schemas/design-review-feedback.json
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is True


def test_delegation_fails_when_agent_file_missing(stage_loader_module):
    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
  parallel_specialists:
    - lc-architect
    - lc-missing-agent
  merge_strategy: priority
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is False


def test_delegation_fails_when_schema_missing(stage_loader_module):
    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
  parallel_specialists:
    - lc-architect
  output_schema: .claude/schemas/missing.json
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is False


def test_delegation_fails_when_schema_invalid_json(stage_loader_module):
    schemas = stage_loader_module.PROJECT_ROOT / ".claude" / "schemas"
    schemas.mkdir(parents=True)
    (schemas / "bad.json").write_text("not json", encoding="utf-8")

    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
  parallel_specialists:
    - lc-architect
  output_schema: .claude/schemas/bad.json
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is False


def test_delegation_fails_on_unsupported_merge_strategy(stage_loader_module):
    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
  parallel_specialists:
    - lc-architect
  merge_strategy: unknown_strategy
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is False


def test_delegation_passes_when_no_specialists_configured(stage_loader_module):
    stage_dir = stage_loader_module.PROJECT_ROOT / ".claude" / "stages"
    stage_dir.mkdir(parents=True)
    (stage_dir / "test-stage.yaml").write_text(
        """
schema_version: 2.0.0
id: test-stage
agent:
  primary: lc-architect
""",
        encoding="utf-8",
    )
    assert stage_loader_module._check_agent_delegation("test-stage") is True