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
