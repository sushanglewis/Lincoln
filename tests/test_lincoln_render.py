"""Tests for scripts/lincoln_render.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = ROOT / "scripts" / "lincoln_render.py"
PROCESS_SLUG = "issue-99-test"
TEST_ROOT = ROOT / PROCESS_SLUG


@pytest.fixture(scope="function", autouse=True)
def _clean_test_root():
    """Ensure a clean sandbox under the repo root for every test."""
    for path in list(ROOT.glob(f"{PROCESS_SLUG}*")):
        if path.is_dir():
            shutil.rmtree(path)
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    yield
    for path in list(ROOT.glob(f"{PROCESS_SLUG}*")):
        if path.is_dir():
            shutil.rmtree(path)


def run_render(*args: str, state_path: Path | None = None, cwd: Path = ROOT) -> tuple[int, str, str]:
    full_args = list(args)
    if state_path is not None:
        full_args.extend(["--state-file", str(state_path)])
    result = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), *full_args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def repo_relative(target: Path) -> str:
    """Return a repo-relative target path for lincoln_render --target."""
    return str(target.relative_to(ROOT))


def write_state(**variables: str) -> Path:
    """Write a minimal workflow-stage.yaml for the test process slug."""
    state_path = TEST_ROOT / "workflow-stage.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    merged = {"process_slug": PROCESS_SLUG}
    merged.update(variables)
    state_path.write_text(
        f"""schema_version: 2.0.0
workflow:
  template: interview-to-knowledge
current_run:
  variables:
{chr(10).join(f'    {k}: {v}' for k, v in merged.items())}
nodes: []
recovery: {{}}
""",
        encoding="utf-8",
    )
    return state_path


def test_render_prd_html() -> None:
    """Render a PRD page from the real clarify stage template."""
    state_path = write_state()
    target = TEST_ROOT / "pages" / "docs" / "prd.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "clarify",
        "--target",
        repo_relative(target),
        "--title",
        "产品需求文档",
        "--nav-label",
        "PRD",
        "--nav-group",
        "Docs",
        "--version",
        "v1.2",
        "--uid",
        "prd",
        "--stage-mark",
        "clarify",
        state_path=state_path,
    )
    assert rc == 0, stderr
    assert target.exists()
    html = target.read_text(encoding="utf-8")
    assert "产品需求文档" in html
    assert '<meta name="doc-title" content="产品需求文档">' in html
    assert '<meta name="nav-label" content="PRD">' in html
    assert '<meta name="nav-group" content="Docs">' in html
    assert '<meta name="doc-version" content="v1.2">' in html
    assert '<meta name="doc-uid" content="prd">' in html
    assert '<span class="doc-version">v1.2</span>' in html
    assert 'data-page-uid="prd"' in html


def test_render_prototype_glob_match() -> None:
    """Render a prototype page via the glob artifact_templates pattern."""
    state_path = write_state(design_id="d1")
    target = TEST_ROOT / "pages" / "prototype" / "web" / "dashboard" / "page.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "product-prototype",
        "--target",
        repo_relative(target),
        "--title",
        "仪表盘",
        "--nav-label",
        "仪表盘",
        "--nav-group",
        "Prototype",
        "--uid",
        "page-dashboard",
        state_path=state_path,
    )
    assert rc == 0, stderr
    assert target.exists()
    html = target.read_text(encoding="utf-8")
    assert "仪表盘" in html
    assert '<meta name="page-uid" content="page-dashboard">' in html
    assert 'data-page-uid="page-dashboard"' in html
    # page-prototype.html.tpl assumes depth-3 layout (pages/prototype/{group}/page.html).
    assert '<link rel="stylesheet" href="../../../assets/prototype.css">' in html


def test_render_injects_missing_meta_tags() -> None:
    """Missing nav-label / doc-uid meta tags are auto-filled for doc-like pages."""
    state_path = write_state()
    tpl = TEST_ROOT / "minimal.html.tpl"
    tpl.write_text(
        '<html><head><meta charset="UTF-8"></head>'
        '<body data-page-uid="{UID}">{TITLE}</body></html>',
        encoding="utf-8",
    )
    stage_id = "_test-render-meta"
    stage_path = ROOT / ".claude" / "stages" / f"{stage_id}.yaml"
    stage_path.write_text(
        f"""schema_version: 3.0.0
id: {stage_id}
name: Test Meta
workflows: []
artifact_templates:
  '{PROCESS_SLUG}/pages/test.html': '{tpl.as_posix()}'
context:
  goal: test
""",
        encoding="utf-8",
    )
    try:
        target = TEST_ROOT / "pages" / "test.html"
        rc, stdout, stderr = run_render(
            "--stage",
            stage_id,
            "--target",
            repo_relative(target),
            "--title",
            "Test Title",
            "--nav-label",
            "Test Label",
            "--nav-group",
            "TestGroup",
            "--version",
            "v2.0",
            "--uid",
            "test-uid",
            state_path=state_path,
        )
        assert rc == 0, stderr
        html = target.read_text(encoding="utf-8")
        assert '<meta name="doc-title" content="Test Title">' in html
        assert '<meta name="nav-label" content="Test Label">' in html
        assert '<meta name="nav-group" content="TestGroup">' in html
        assert '<meta name="doc-version" content="v2.0">' in html
        # Minimal templates with doc-title are treated as doc pages, so doc-uid is injected.
        assert '<meta name="doc-uid" content="test-uid">' in html
        assert "<!-- version: v2.0 -->" in html
    finally:
        stage_path.unlink(missing_ok=True)


def test_render_with_markdown_source() -> None:
    """Markdown source is injected into the doc page template."""
    state_path = write_state()
    md_path = TEST_ROOT / "source.md"
    md_path.write_text("# Hello\n\nThis is **bold**.", encoding="utf-8")
    target = TEST_ROOT / "pages" / "docs" / "requirements.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "clarify",
        "--target",
        repo_relative(target),
        "--title",
        "需求文档",
        "--nav-label",
        "需求",
        "--version",
        "v1.0",
        "--uid",
        "requirements",
        "--markdown",
        repo_relative(md_path),
        state_path=state_path,
    )
    assert rc == 0, stderr
    html = target.read_text(encoding="utf-8")
    assert "# Hello" in html
    assert "This is **bold**." in html


def test_render_with_runtime_variables_from_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Runtime variables are read from the canonical state file."""
    state_path = write_state(change_name="coupon-refactor")

    stage_id = "_test-render-vars"
    stage_path = ROOT / ".claude" / "stages" / f"{stage_id}.yaml"
    stage_path.write_text(
        """schema_version: 3.0.0
id: _test-render-vars
name: Test Vars
workflows: []
artifact_templates:
  '{process_slug}/docs/{change_name}.html': '.claude/templates/issue-package/page-doc.html.tpl'
context:
  goal: test
""",
        encoding="utf-8",
    )
    try:
        target = TEST_ROOT / "docs" / "coupon-refactor.html"
        rc, stdout, stderr = run_render(
            "--stage",
            stage_id,
            "--target",
            repo_relative(target),
            "--title",
            "Coupon Refactor",
            "--nav-label",
            "Coupon",
            "--version",
            "v1.0",
            "--uid",
            "coupon",
            state_path=state_path,
        )
        assert rc == 0, stderr
        html = target.read_text(encoding="utf-8")
        assert "Coupon Refactor" in html
        assert target.exists()
    finally:
        stage_path.unlink(missing_ok=True)


def test_render_dry_run_does_not_write() -> None:
    """--dry-run prints to stdout and does not create the target file."""
    state_path = write_state()
    target = TEST_ROOT / "pages" / "docs" / "requirements.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "clarify",
        "--target",
        repo_relative(target),
        "--title",
        "Dry Run",
        "--nav-label",
        "Dry",
        "--version",
        "v1.0",
        "--uid",
        "dry",
        "--dry-run",
        state_path=state_path,
    )
    assert rc == 0, stderr
    assert not target.exists()
    assert "Dry Run" in stdout


def test_render_set_extra_variables() -> None:
    """--set provides extra template variables."""
    state_path = write_state()
    stage_id = "_test-render-set"
    stage_path = ROOT / ".claude" / "stages" / f"{stage_id}.yaml"
    tpl = TEST_ROOT / "set.html.tpl"
    tpl.write_text(
        '<html><head></head><body>{CUSTOM_VAR} {TITLE}</body></html>',
        encoding="utf-8",
    )
    stage_path.write_text(
        f"""schema_version: 3.0.0
id: {stage_id}
name: Test Set
workflows: []
artifact_templates:
  '{PROCESS_SLUG}/set.html': '{tpl.as_posix()}'
context:
  goal: test
""",
        encoding="utf-8",
    )
    try:
        target = TEST_ROOT / "set.html"
        rc, stdout, stderr = run_render(
            "--stage",
            stage_id,
            "--target",
            repo_relative(target),
            "--title",
            "Title",
            "--set",
            "CUSTOM_VAR=hello",
            state_path=state_path,
        )
        assert rc == 0, stderr
        html = target.read_text(encoding="utf-8")
        assert "hello Title" in html
    finally:
        stage_path.unlink(missing_ok=True)


def test_render_missing_stage_fails() -> None:
    """An unknown stage causes a non-zero exit."""
    target = TEST_ROOT / "pages" / "docs" / "x.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "no-such-stage-xyz",
        "--target",
        repo_relative(target),
        "--title",
        "X",
    )
    assert rc != 0
    assert "Stage definition not found" in stderr


def test_render_no_matching_pattern_fails() -> None:
    """A target that does not match any artifact_templates pattern fails."""
    state_path = write_state()
    target = TEST_ROOT / "pages" / "docs" / "nope.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "tdd-development-plan",
        "--target",
        repo_relative(target),
        "--title",
        "Nope",
        state_path=state_path,
    )
    assert rc != 0
    assert "No artifact_templates pattern matches" in stderr


def test_render_missing_markdown_source_fails() -> None:
    """--markdown pointing to a missing file fails gracefully."""
    state_path = write_state()
    target = TEST_ROOT / "pages" / "docs" / "md.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "clarify",
        "--target",
        repo_relative(target),
        "--title",
        "MD",
        "--markdown",
        repo_relative(TEST_ROOT / "missing.md"),
        state_path=state_path,
    )
    assert rc != 0
    assert "Markdown source not found" in stderr


def test_render_with_structured_data() -> None:
    """Structured YAML data is injected as pageData and pre-rendered as HTML."""
    state_path = write_state()
    data_path = TEST_ROOT / "feature-catalog.yaml"
    data_path.write_text(
        '''intro: "功能目录简介"
annotations:
  doc-purpose: "列出本次需求的所有功能点"
  doc-refs: "prd.html | requirements.html"
features:
  - id: "f-login"
    title: "微信登录"
    priority: "P0"
    acceptance: "扫码后 3 秒内完成登录"
    source: "story-guest-login"
''',
        encoding="utf-8",
    )
    target = TEST_ROOT / "pages" / "docs" / "feature-catalog.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "product-design-docs",
        "--target",
        repo_relative(target),
        "--title",
        "功能目录",
        "--nav-label",
        "功能目录",
        "--version",
        "v1.0",
        "--uid",
        "feature-catalog",
        "--data",
        repo_relative(data_path),
        state_path=state_path,
    )
    assert rc == 0, stderr
    html = target.read_text(encoding="utf-8")
    assert "功能目录简介" in html
    assert '"features"' in html
    assert "微信登录" in html
    assert "f-login" in html
    assert '<meta name="doc-purpose" content="列出本次需求的所有功能点">' in html
    assert '<meta name="doc-refs" content="prd.html | requirements.html">' in html


def test_render_data_file_missing_fails() -> None:
    """--data pointing to a missing file fails gracefully."""
    state_path = write_state()
    target = TEST_ROOT / "pages" / "docs" / "data.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "clarify",
        "--target",
        repo_relative(target),
        "--title",
        "Data",
        "--data",
        repo_relative(TEST_ROOT / "missing.yaml"),
        state_path=state_path,
    )
    assert rc != 0
    assert "Data file not found" in stderr


def test_render_prototype_with_structured_data() -> None:
    """A prototype page can be rendered from structured YAML data."""
    state_path = write_state(design_id="d1")
    data_path = TEST_ROOT / "dashboard.yaml"
    data_path.write_text(
        '''layout:
  type: web
  shell: dashboard
  title: "仪表盘"
  active: dashboard
  navItems:
    - {id: dashboard, label: 概览, href: ./dashboard/page.html}
annotations:
  doc-purpose: "展示核心指标"
components:
  - type: html
    uid: dashboard-metrics
    props:
      html: '<div class="metric">订单 100</div>'
''',
        encoding="utf-8",
    )
    target = TEST_ROOT / "pages" / "prototype" / "web" / "dashboard" / "page.html"
    rc, stdout, stderr = run_render(
        "--stage",
        "product-prototype",
        "--target",
        repo_relative(target),
        "--title",
        "仪表盘",
        "--nav-label",
        "仪表盘",
        "--nav-group",
        "Prototype",
        "--uid",
        "page-dashboard",
        "--data",
        repo_relative(data_path),
        state_path=state_path,
    )
    assert rc == 0, stderr
    html = target.read_text(encoding="utf-8")
    assert "仪表盘" in html
    assert '"type": "web"' in html
    assert "dashboard-metrics" in html
    assert '<meta name="doc-purpose" content="展示核心指标">' in html


def test_render_sections_html_placeholder() -> None:
    """{SECTIONS_HTML} is pre-rendered from pageData.sections."""
    state_path = write_state()
    tpl = TEST_ROOT / "sections.html.tpl"
    tpl.write_text(
        '<html><head></head><body>{SECTIONS_HTML} {TITLE}</body></html>',
        encoding="utf-8",
    )
    stage_id = "_test-render-sections"
    stage_path = ROOT / ".claude" / "stages" / f"{stage_id}.yaml"
    stage_path.write_text(
        f"""schema_version: 3.0.0
id: {stage_id}
name: Test Sections
workflows: []
artifact_templates:
  '{PROCESS_SLUG}/sections.html': '{tpl.as_posix()}'
context:
  goal: test
""",
        encoding="utf-8",
    )
    data_path = TEST_ROOT / "sections.yaml"
    data_path.write_text(
        '''sections:
  - title: "背景"
    content: "需求来源"
''',
        encoding="utf-8",
    )
    try:
        target = TEST_ROOT / "sections.html"
        rc, stdout, stderr = run_render(
            "--stage",
            stage_id,
            "--target",
            repo_relative(target),
            "--title",
            "Sections",
            "--data",
            repo_relative(data_path),
            state_path=state_path,
        )
        assert rc == 0, stderr
        html = target.read_text(encoding="utf-8")
        assert "lincoln-section" in html
        assert "背景" in html
        assert "需求来源" in html
    finally:
        stage_path.unlink(missing_ok=True)
