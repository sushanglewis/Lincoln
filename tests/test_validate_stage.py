"""Tests for scripts/validate_stage.py structural validators."""
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


@pytest.fixture
def state_file(tmp_path):
    """Create a minimal node-based workflow-stage.yaml."""
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "test"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "test"},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [],
        "recovery": {},
    }
    path = tmp_path / "test" / "workflow-stage.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _call_and_expect(validator_mod, monkeypatch, tmp_path, state_file, fn_name, args, project_root=None):
    project_root = project_root or tmp_path
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    fn = getattr(validator_mod, fn_name)
    return fn(*args)


# ---------------------------------------------------------------------------
# file_exists
# ---------------------------------------------------------------------------


def test_check_file_exists_passes(validator_mod, tmp_path, monkeypatch):
    target = tmp_path / "exists.txt"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_file_exists("exists.txt")
    assert exc_info.value.code == 0


def test_check_file_exists_fails(validator_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_file_exists("missing.txt")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# artifact_exists
# ---------------------------------------------------------------------------


def test_check_artifact_exists_passes(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    slug_dir = tmp_path / "test"
    slug_dir.mkdir(exist_ok=True)
    target = slug_dir / "artifact.md"
    target.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifact_exists("artifact.md")
    assert exc_info.value.code == 0


def test_check_artifact_exists_fails_when_empty(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    slug_dir = tmp_path / "test"
    slug_dir.mkdir(exist_ok=True)
    target = slug_dir / "artifact.md"
    target.write_text("", encoding="utf-8")
    monkeypatch.setattr(validator_mod, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifact_exists("artifact.md")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# audio_format_supported
# ---------------------------------------------------------------------------


def test_check_audio_format_supported_passes(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_audio_format_supported("recording.m4a")
    assert exc_info.value.code == 0


def test_check_audio_format_supported_fails(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_audio_format_supported("recording.ogg")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# previous_stage_completed
# ---------------------------------------------------------------------------


def test_check_previous_stage_completed_passes(validator_mod, tmp_path, monkeypatch, state_file):
    state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    state["nodes"].append({
        "stage_id": "ingest",
        "status": "completed",
    })
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_previous_stage_completed("ingest")
    assert exc_info.value.code == 0


def test_check_previous_stage_completed_fails(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_previous_stage_completed("ingest")
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# human_approved
# ---------------------------------------------------------------------------


def test_check_human_approved_passes(validator_mod, tmp_path, monkeypatch, state_file):
    state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    state["nodes"].append({
        "stage_id": "clarify",
        "status": "waiting_for_human",
        "gate_passed": True,
        "approved_by": "pm",
    })
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_human_approved()
    assert exc_info.value.code == 0


def test_check_human_approved_fails(validator_mod, tmp_path, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_human_approved()
    assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# artifacts_present
# ---------------------------------------------------------------------------


def test_check_artifacts_present_is_delegated(validator_mod):
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.check_artifacts_present()
    assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# CLI registry
# ---------------------------------------------------------------------------


def test_main_rejects_unknown_check(validator_mod, monkeypatch, state_file):
    monkeypatch.setattr(validator_mod, "resolve_state_path", lambda _path=None, _root=None: state_file)
    monkeypatch.setattr(sys, "argv", [
        "validate_stage.py", "--phase", "entry", "--check", "not_a_check",
    ])
    with pytest.raises(SystemExit) as exc_info:
        validator_mod.main()
    assert exc_info.value.code == 1
