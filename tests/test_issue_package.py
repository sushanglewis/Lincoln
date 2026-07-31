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

REQUIRED_PROTOTYPE_ASSETS = [
    "assets/prototype.css",
    "assets/prototype.js",
]

REQUIRED_PROTOTYPE_EXAMPLES = [
    # App (desktop) shells
    "prototypes/app/main/page.html.tpl",
    "prototypes/app/onboarding/page.html.tpl",
    "prototypes/app/settings/page.html.tpl",
    "prototypes/app/overlays/page.html.tpl",
    "prototypes/app/tray/page.html.tpl",
    "prototypes/app/org/page.html.tpl",
    # Web shells
    "prototypes/web/dashboard/page.html.tpl",
    "prototypes/web/list/page.html.tpl",
    "prototypes/web/form/page.html.tpl",
    "prototypes/web/detail/page.html.tpl",
    # Mobile shells
    "prototypes/mobile/home/page.html.tpl",
    "prototypes/mobile/chat/page.html.tpl",
    "prototypes/mobile/settings/page.html.tpl",
    "prototypes/mobile/profile/page.html.tpl",
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


def test_issue_package_template_has_prototype_assets():
    for asset in REQUIRED_PROTOTYPE_ASSETS:
        assert (TEMPLATE_ROOT / asset).exists(), f"Missing prototype asset: {asset}"


def test_issue_package_template_has_prototype_example_templates():
    for tpl in REQUIRED_PROTOTYPE_EXAMPLES:
        assert (TEMPLATE_ROOT / tpl).exists(), f"Missing prototype example template: {tpl}"


def test_prototype_assets_do_not_contain_unrendered_placeholders():
    """Shared CSS/JS are static assets, not templates, so they must not contain {PLACEHOLDER} variables."""
    import re
    placeholder = re.compile(r"\{[A-Z_][A-Z0-9_]*\}")
    for asset in REQUIRED_PROTOTYPE_ASSETS:
        text = (TEMPLATE_ROOT / asset).read_text(encoding="utf-8")
        matches = placeholder.findall(text)
        assert not matches, f"Static asset contains unrendered placeholders: {asset} {matches}"


def test_page_prototype_template_uses_prototype_kit():
    text = (TEMPLATE_ROOT / "page-prototype.html.tpl").read_text(encoding="utf-8")
    assert "prototype.css" in text
    assert "prototype.js" in text
    assert 'name="prototype-base"' in text
    assert "data-uid" in text


def test_portal_and_prototype_templates_support_theme_sync():
    for tpl in ["index.html.tpl", "page-doc.html.tpl", "page-prototype.html.tpl"]:
        text = (TEMPLATE_ROOT / tpl).read_text(encoding="utf-8")
        assert "data-theme" in text or "lincoln-theme" in text, f"{tpl} should support theme sync"


def test_prototype_css_has_dark_mode_override():
    text = (TEMPLATE_ROOT / "assets" / "prototype.css").read_text(encoding="utf-8")
    assert '[data-theme="dark"]' in text, "prototype.css should define dark theme override"


def test_app_js_has_theme_helpers():
    text = (TEMPLATE_ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    assert "lincoln-theme" in text
    assert "toggleTheme" in text
    assert "artifactChecklist" in text


def test_prototype_js_has_frame_helpers():
    text = (TEMPLATE_ROOT / "assets" / "prototype.js").read_text(encoding="utf-8")
    for helper in ["frameApp", "frameWeb", "frameMobile"]:
        assert helper in text, f"prototype.js should export {helper}"


def test_prototype_js_is_syntactically_valid():
    js_path = TEMPLATE_ROOT / "assets" / "prototype.js"
    node = subprocess.run(["which", "node"], capture_output=True, text=True)
    if node.returncode != 0:
        pytest.skip("node not available")
    check = subprocess.run(["node", "--check", str(js_path)], capture_output=True, text=True)
    assert check.returncode == 0, f"prototype.js syntax error: {check.stderr}"


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
