"""Focused tests for HTML prototype and PRD bidirectional traceability."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lincoln_prototype_traceability import validate_prototype_traceability

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lincoln_prototype_traceability.py"
FIXTURES = ROOT / "tests" / "fixtures" / "prototype-traceability"
PROMPT = ROOT / ".claude" / "skills" / "build-product-prototype" / "prompts" / "main.md"


def fixture(name: str) -> Path:
    return FIXTURES / name


def run_cli(process_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--package", str(process_root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_complete_fixture_passes() -> None:
    assert validate_prototype_traceability(fixture("complete")) == []


def test_complete_fixture_keeps_top_level_trace_ids_and_hotspots() -> None:
    for page in fixture("complete").glob("pages/prototype/**/*.html"):
        source = page.read_text(encoding="utf-8")
        match = re.search(
            r'<script\b[^>]*\bid="pageData"[^>]*>(.*?)</script>', source, re.DOTALL
        )
        assert match is not None
        data = json.loads(match.group(1))
        assert data["requirement_ids"] == ["REQ-001"]
        assert data["story_ids"] == ["STORY-001"]
        assert data["flow_step_ids"]
        assert data["hotspots"]


@pytest.mark.parametrize(
    ("fixture_name", "expected_messages"),
    [
        ("missing-page", ["PAGE_FILE_MISSING", "CORE_FLOW_WITHOUT_PAGE"]),
        ("unregistered-page", ["ORPHAN_PAGE: actual HTML is not registered"]),
        ("core-flow-without-page", ["REQ-001/FLOW-002 has no matching prototype page"]),
        (
            "broken-links",
            [
                "unknown requirement REQ-999",
                "unknown flow step FLOW-999",
                "does not declare that ID",
            ],
        ),
        ("missing-metadata", ["INVALID_METADATA: requirement_ids", "ORPHAN_PAGE: flow_step_ids"]),
        ("invalid-json", ["INVALID_PAGE_DATA: invalid JSON"]),
    ],
)
def test_broken_fixtures_report_actionable_errors(
    fixture_name: str, expected_messages: list[str]
) -> None:
    errors = validate_prototype_traceability(fixture(fixture_name))
    assert errors
    report = "\n".join(errors)
    for message in expected_messages:
        assert message in report


def test_cli_reports_success() -> None:
    result = run_cli(fixture("complete"))
    assert result.returncode == 0
    assert "Prototype traceability OK" in result.stdout
    assert result.stderr == ""


def test_cli_reports_failure_and_nonzero_exit() -> None:
    result = run_cli(fixture("broken-links"))
    assert result.returncode == 1
    assert "BROKEN_REQUIREMENT_LINK" in result.stderr
    assert "BROKEN_FLOW_LINK" in result.stderr
    assert "Prototype traceability failed" in result.stderr


def test_prompt_preserves_prototype_quality_and_declares_metadata_contract() -> None:
    prompt = PROMPT.read_text(encoding="utf-8")
    for required in (
        "requirement_ids",
        "story_ids",
        "flow_step_ids",
        "requirements[].prototype_pages",
        "pages/docs/prd-traceability.yaml",
        "script#pageData",
        "hotspots",
        "角色×场景矩阵",
        "light and dark",
        "default, hover/focus where relevant, disabled, empty, loading, error, and success",
        "lincoln_prototype_traceability.py --package {process_slug}",
    ):
        assert required in prompt


def test_unknown_story_id_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "package"
    import shutil
    shutil.copytree(fixture("complete"), root)
    page = root / "pages" / "prototype" / "web" / "list" / "page.html"
    page.write_text(page.read_text(encoding="utf-8").replace("STORY-001", "US-999"), encoding="utf-8")

    errors = validate_prototype_traceability(root)

    assert any("BROKEN_STORY_LINK" in error and "US-999" in error for error in errors)


def test_page_cannot_declare_requirement_that_does_not_register_it(tmp_path: Path) -> None:
    root = tmp_path / "package"
    import shutil
    import yaml
    shutil.copytree(fixture("complete"), root)
    sidecar = root / "pages" / "docs" / "prd-traceability.yaml"
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    data["requirements"].append({
        "id": "REQ-002",
        "core": False,
        "story_ids": ["STORY-002"],
        "flow_step_ids": [],
        "prototype_pages": [],
    })
    sidecar.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    page = root / "pages" / "prototype" / "web" / "detail" / "page.html"
    source = page.read_text(encoding="utf-8")
    source = source.replace('"REQ-001"', '"REQ-001", "REQ-002"')
    source = source.replace('"STORY-001"', '"STORY-001", "STORY-002"')
    page.write_text(source, encoding="utf-8")

    errors = validate_prototype_traceability(root)

    assert any("REQ-002" in error and "does not register the page" in error for error in errors)


def test_backslash_path_cannot_bypass_package_relative_checks(tmp_path: Path) -> None:
    root = tmp_path / "package"
    import shutil
    import yaml
    shutil.copytree(fixture("complete"), root)
    sidecar = root / "pages" / "docs" / "prd-traceability.yaml"
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    data["requirements"][0]["prototype_pages"][0] = "pages/prototype/x\\..\\list/page.html"
    sidecar.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    errors = validate_prototype_traceability(root)

    assert any("POSIX separators" in error for error in errors)
