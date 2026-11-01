"""Contract and semantic tests for the PRD traceability sidecar (#144)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

from scripts.lincoln_traceability import SCHEMA_PATH, validate_traceability

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lincoln_traceability.py"
FIXTURES = ROOT / "tests" / "fixtures" / "traceability"
VALID_PACKAGE = FIXTURES / "valid" / "issue-144"


@pytest.fixture
def valid_package(tmp_path: Path) -> Path:
    package = tmp_path / "issue-144"
    shutil.copytree(VALID_PACKAGE, package)
    return package


def _apply_sidecar(package: Path, fixture_name: str) -> None:
    shutil.copyfile(
        FIXTURES / fixture_name / "pages" / "docs" / "prd-traceability.yaml",
        package / "pages" / "docs" / "prd-traceability.yaml",
    )


def _load_sidecar(package: Path) -> dict:
    return yaml.safe_load((package / "pages" / "docs" / "prd-traceability.yaml").read_text(encoding="utf-8"))


def _write_sidecar(package: Path, data: dict) -> None:
    (package / "pages" / "docs" / "prd-traceability.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


def test_schema_is_valid_draft_07() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator.check_schema(schema)


@pytest.mark.parametrize("stage", ["clarify", "prototype", "tdd"])
def test_valid_fixture_passes_every_stage(stage: str) -> None:
    assert validate_traceability(VALID_PACKAGE, stage) == []


def test_non_core_requirement_does_not_need_stage_links(valid_package: Path) -> None:
    data = _load_sidecar(valid_package)
    assert data["requirements"][1]["core"] is False
    assert all(not data["requirements"][1][field] for field in (
        "sources", "story_ids", "acceptance_criterion_ids", "flow_step_ids",
        "prototype_pages", "test_scenario_ids",
    ))
    assert validate_traceability(valid_package, "tdd") == []


def test_stage_incomplete_passes_clarify_but_fails_progressive_gates(valid_package: Path) -> None:
    _apply_sidecar(valid_package, "stage-incomplete")

    assert validate_traceability(valid_package, "clarify") == []
    prototype_errors = validate_traceability(valid_package, "prototype")
    assert any("flow_step_ids" in error and "at least one flow step" in error for error in prototype_errors)
    assert any("prototype_pages" in error and "at least one prototype page" in error for error in prototype_errors)
    tdd_errors = validate_traceability(valid_package, "tdd")
    assert any("test_scenario_ids" in error and "at least one test scenario" in error for error in tdd_errors)
    assert any("flow_step_ids" in error for error in tdd_errors)
    assert any("prototype_pages" in error for error in tdd_errors)


def test_broken_reference_names_requirement_and_repair(valid_package: Path) -> None:
    _apply_sidecar(valid_package, "broken-reference")
    errors = validate_traceability(valid_package, "clarify")
    assert any(
        "requirements[0].story_ids[0]" in error
        and "US-999" in error
        and "define the user story or remove the stale reference" in error
        for error in errors
    )


def test_duplicate_ids_and_references_are_rejected(valid_package: Path) -> None:
    _apply_sidecar(valid_package, "duplicate-id")
    errors = validate_traceability(valid_package, "clarify")
    assert any("duplicate requirement ID 'REQ-001'" in error for error in errors)
    assert any("duplicate source ID 'SRC-INTERVIEW-001'" in error for error in errors)
    assert any("duplicate user story ID 'US-001'" in error for error in errors)


def test_version_drift_is_rejected_with_current_version(valid_package: Path) -> None:
    _apply_sidecar(valid_package, "version-drift")
    errors = validate_traceability(valid_package, "clarify")
    assert any("sidecar declares v1.1" in error and "declares v1.0" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "REQUIREMENT-001"),
        ("story_ids", ["STORY-001"]),
        ("acceptance_criterion_ids", ["ACCEPT-001"]),
        ("flow_step_ids", ["STEP-001"]),
        ("test_scenario_ids", ["SCENARIO-001"]),
    ],
)
def test_reference_fields_enforce_allowed_prefixes(valid_package: Path, field: str, value) -> None:
    data = _load_sidecar(valid_package)
    data["requirements"][0][field] = value
    _write_sidecar(valid_package, data)
    errors = validate_traceability(valid_package, "clarify")
    assert any(field in error and "match" in error for error in errors)


def test_source_id_and_uri_are_validated(valid_package: Path) -> None:
    data = _load_sidecar(valid_package)
    data["requirements"][0]["sources"][0] = {
        "id": "SOURCE-001",
        "uri": "research/missing.md",
    }
    _write_sidecar(valid_package, data)
    errors = validate_traceability(valid_package, "clarify")
    assert any("sources[0].id" in error and "match" in error for error in errors)
    assert any("research/missing.md" in error and "does not exist" in error for error in errors)


def test_missing_prototype_page_is_rejected(valid_package: Path) -> None:
    data = _load_sidecar(valid_package)
    data["requirements"][0]["prototype_pages"] = ["pages/prototype/missing.html"]
    _write_sidecar(valid_package, data)
    errors = validate_traceability(valid_package, "prototype")
    assert any("pages/prototype/missing.html" in error and "does not exist" in error for error in errors)


def test_prototype_page_cannot_escape_package(valid_package: Path) -> None:
    data = _load_sidecar(valid_package)
    data["requirements"][0]["prototype_pages"] = ["pages/prototype/../../secret.html"]
    _write_sidecar(valid_package, data)
    errors = validate_traceability(valid_package, "prototype")
    assert any("safe package-relative" in error for error in errors)


def test_prd_version_marker_is_required(valid_package: Path) -> None:
    prd = valid_package / "pages" / "docs" / "prd.html"
    prd.write_text(prd.read_text(encoding="utf-8").replace("<!-- version: v1.0 -->", ""), encoding="utf-8")
    errors = validate_traceability(valid_package, "clarify")
    assert any("no version marker" in error and "<!-- version: vX.Y -->" in error for error in errors)


def test_missing_sidecar_is_actionable(tmp_path: Path) -> None:
    errors = validate_traceability(tmp_path, "clarify")
    assert len(errors) == 1
    assert "sidecar not found" in errors[0]
    assert "create pages/docs/prd-traceability.yaml" in errors[0]


def test_invalid_yaml_is_actionable(valid_package: Path) -> None:
    (valid_package / "pages" / "docs" / "prd-traceability.yaml").write_text("requirements: [\n", encoding="utf-8")
    errors = validate_traceability(valid_package, "clarify")
    assert len(errors) == 1
    assert "invalid YAML" in errors[0]


def test_unknown_stage_is_rejected() -> None:
    with pytest.raises(ValueError, match="choose one of: clarify, prototype, tdd"):
        validate_traceability(VALID_PACKAGE, "implement")


def test_cli_passes_and_returns_nonzero_with_actionable_errors(valid_package: Path) -> None:
    passing = subprocess.run(
        [sys.executable, str(SCRIPT), "--package", str(VALID_PACKAGE), "--stage", "tdd"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert passing.returncode == 0, passing.stdout + passing.stderr
    assert "PASS:" in passing.stdout

    _apply_sidecar(valid_package, "stage-incomplete")
    failing = subprocess.run(
        [sys.executable, str(SCRIPT), "--package", str(valid_package), "--stage", "prototype"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failing.returncode == 1
    assert "FAIL:" in failing.stdout
    assert "flow_step_ids" in failing.stdout
    assert "add the missing relationship" in failing.stdout
