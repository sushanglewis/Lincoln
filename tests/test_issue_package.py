"""Tests for issue-package template and issue-driven initialization."""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / ".claude" / "templates" / "issue-package"
SCHEMA_PATH = ROOT / ".claude" / "schemas" / "workflow-stage.schema.json"


REQUIRED_DIRS = [
    "designs",
    "docs",
    "docs/research",
    "interviews",
    "openspec",
    "openspec/changes",
    "openspec/specs",
    "recordings",
    "requirements",
]

REQUIRED_TEMPLATES = {
    "designs": ["design-review.md.tpl", "scenarios.md.tpl", "feature-catalog.md.tpl", "data-model.md.tpl", "flows.md.tpl", "feasibility.md.tpl", "ui-spec.md.tpl"],
    "docs": ["research-note.md.tpl", "decision-record.md.tpl"],
    "interviews": ["metadata.json.tpl", "transcript.md.tpl", "summary.md.tpl", "raw-insights.md.tpl"],
    "openspec": ["proposal.md.tpl", "design.md.tpl", "tasks.md.tpl"],
    "requirements": ["requirements.md.tpl", "user-stories.md.tpl"],
}

ROOT_TEMPLATES = ["prd.md.tpl"]


def test_issue_package_template_has_state_file():
    assert (TEMPLATE_ROOT / "workflow-stage.yaml").exists()


def test_issue_package_template_has_required_directories():
    for rel in REQUIRED_DIRS:
        assert (TEMPLATE_ROOT / rel).is_dir(), f"Missing directory: {rel}"


def test_issue_package_template_has_multiple_templates_per_directory():
    for directory, templates in REQUIRED_TEMPLATES.items():
        dir_path = TEMPLATE_ROOT / directory
        found = [p.name for p in dir_path.glob("*.tpl")]
        assert len(found) > 1, f"Expected >1 template in {directory}, found {found}"
        for tpl in templates:
            assert (dir_path / tpl).exists(), f"Missing template: {directory}/{tpl}"


def test_issue_package_workflow_stage_has_issue_number_and_guidance():
    state = yaml.safe_load((TEMPLATE_ROOT / "workflow-stage.yaml").read_text(encoding="utf-8"))
    assert state["current_run"]["issue_number"] == ""
    assert state["current_run"]["variables"]["issue_number"] == ""
    assert "artifact_guidance" in state
    assert "{issue_number}" in state["artifact_guidance"]


def test_issue_package_template_has_root_templates():
    for tpl in ROOT_TEMPLATES:
        assert (TEMPLATE_ROOT / tpl).exists(), f"Missing root template: {tpl}"


def test_schema_allows_issue_number_in_current_run():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    current_run_props = schema["properties"]["current_run"]["properties"]
    assert "issue_number" in current_run_props
    variables_props = current_run_props["variables"]["properties"]
    assert "issue_number" in variables_props
