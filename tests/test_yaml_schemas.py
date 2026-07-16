"""JSON Schema contract tests for stage and workflow YAML files (#67).

`.claude/schemas/` existing is not enough — every stage definition and every
workflow template must actually pass its schema in CI. Schemas are draft-07;
local `#/definitions/...` refs resolve inside each schema document.
"""

from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / ".claude" / "schemas"
STAGE_FILES = sorted((ROOT / ".claude" / "stages").glob("*.yaml"))
WORKFLOW_FILES = sorted((ROOT / ".claude" / "workflows").glob("*.yaml"))


def _validator(schema_name: str) -> jsonschema.Draft7Validator:
    schema = yaml.safe_load((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    jsonschema.Draft7Validator.check_schema(schema)
    return jsonschema.Draft7Validator(schema)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("stage_file", STAGE_FILES, ids=lambda p: p.name)
def test_stage_definition_matches_schema(stage_file: Path):
    # Arrange
    validator = _validator("stage-definition.schema.json")

    # Act
    errors = list(validator.iter_errors(_load_yaml(stage_file)))

    # Assert
    assert not errors, "\n".join(f"{e.json_path}: {e.message}" for e in errors)


@pytest.mark.parametrize("workflow_file", WORKFLOW_FILES, ids=lambda p: p.name)
def test_workflow_template_matches_schema(workflow_file: Path):
    # Arrange
    validator = _validator("workflow-template.schema.json")

    # Act
    errors = list(validator.iter_errors(_load_yaml(workflow_file)))

    # Assert
    assert not errors, "\n".join(f"{e.json_path}: {e.message}" for e in errors)


def test_stage_and_workflow_files_exist():
    # The parametrize guards above are vacuous if the glob silently finds nothing.
    assert STAGE_FILES, "no stage YAML files found under .claude/stages/"
    assert WORKFLOW_FILES, "no workflow YAML files found under .claude/workflows/"
