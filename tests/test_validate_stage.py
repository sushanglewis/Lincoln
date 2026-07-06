import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_stage.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_stage", VALIDATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def validator_mod():
    return load_validator_module()


def test_state_file_resolves_process_slug(validator_mod, tmp_path, monkeypatch):
    process_slug = "feature-xyz"
    process_root = tmp_path / process_slug
    process_root.mkdir()
    state_file = process_root / "workflow-stage.yaml"
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {
                "process_slug": process_slug,
                "session_id": "2026-07-06-test",
            },
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [],
        "recovery": {},
    }
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    req_dir = process_root / "requirements" / "2026-07-06-test"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "requirements.md"
    req_file.write_text("<!-- status: approved -->\n", encoding="utf-8")

    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    validator_mod.set_state_file(state_file)

    # Should not raise; process_slug should resolve from state file.
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_requirements_approved("2026-07-06-test")
    assert exc_info.value.code == 0
