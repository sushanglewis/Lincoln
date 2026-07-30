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


REQUIRED_PORTAL_TEMPLATES = [
    "index.html.tpl",
    "page-doc.html.tpl",
    "page-prototype.html.tpl",
]

REQUIRED_ASSETS = [
    "assets/style.css",
    "assets/app.js",
]

OBSOLETE_MD_TEMPLATES = [
    "prd.md.tpl",
    "requirements/requirements.md.tpl",
    "requirements/user-stories.md.tpl",
    "designs/design-review.md.tpl",
    "designs/scenarios.md.tpl",
    "designs/feature-catalog.md.tpl",
    "designs/data-model.md.tpl",
    "designs/flows.md.tpl",
    "designs/feasibility.md.tpl",
    "designs/ui-spec.md.tpl",
    "designs/page-map.md.tpl",
    "docs/decision-record.md.tpl",
    "docs/research-note.md.tpl",
]


def test_issue_package_template_has_state_file():
    assert (TEMPLATE_ROOT / "workflow-stage.yaml").exists()


def test_issue_package_template_has_portal_templates():
    for tpl in REQUIRED_PORTAL_TEMPLATES:
        assert (TEMPLATE_ROOT / tpl).exists(), f"Missing portal template: {tpl}"


def test_issue_package_template_has_shared_assets():
    for asset in REQUIRED_ASSETS:
        assert (TEMPLATE_ROOT / asset).exists(), f"Missing shared asset: {asset}"


def test_issue_package_workflow_stage_has_issue_number_and_guidance():
    state = yaml.safe_load((TEMPLATE_ROOT / "workflow-stage.yaml").read_text(encoding="utf-8"))
    assert state["current_run"]["issue_number"] == ""
    assert state["current_run"]["variables"]["issue_number"] == ""
    assert "artifact_guidance" in state
    assert "{issue_number}" in state["artifact_guidance"]


def test_issue_package_template_does_not_include_obsolete_markdown_templates():
    for rel in OBSOLETE_MD_TEMPLATES:
        assert not (TEMPLATE_ROOT / rel).exists(), f"Obsolete Markdown template should be removed: {rel}"


def test_schema_allows_issue_number_in_current_run():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    current_run_props = schema["properties"]["current_run"]["properties"]
    assert "issue_number" in current_run_props
    variables_props = current_run_props["variables"]["properties"]
    assert "issue_number" in variables_props
