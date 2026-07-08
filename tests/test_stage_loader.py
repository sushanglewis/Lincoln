import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGE_LOADER = ROOT / "scripts" / "stage_loader.py"


def run_loader(*args, state_file=None):
    cmd = [sys.executable, str(STAGE_LOADER), *args]
    if state_file is not None:
        cmd.extend(["--state-file", str(state_file)])
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


@pytest.fixture
def minimal_state_file(tmp_path):
    """Create a minimal valid workflow-state.yaml in a temporary issue process package."""
    state = {
        "schema_version": "2.0.0",
        "workflow": {
            "name": "interview-to-knowledge",
            "version": "1.0.0",
            "template": "interview-to-knowledge",
        },
        "current_run": {
            "run_id": "test-run",
            "branch": "issue-test",
            "current_stage": "ingest",
            "status": "in_progress",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "issue_number": "999",
            "variables": {
                "process_slug": "issue-test",
                "session_id": "2026-06-27-stakeholder",
                "design_id": "checkout-redesign",
                "issue_number": "999",
            },
        },
        "nodes": [],
        "recovery": {
            "last_validated_checkpoint": "",
            "can_resume_from": "ingest",
        },
    }
    pkg = tmp_path / "issue-test"
    pkg.mkdir()
    state_file = pkg / "workflow-stage.yaml"
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return state_file


def test_load_ingest_stage_returns_context(minimal_state_file):
    result = run_loader("--stage", "ingest", "--action", "load", state_file=minimal_state_file)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["stage_id"] == "ingest"
    assert data["stage_name"] == "摄入录音"
    assert "context" in data


def test_load_clarify_stage_returns_human_gate(minimal_state_file):
    result = run_loader("--stage", "clarify", "--action", "load", state_file=minimal_state_file)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["stage_id"] == "clarify"
    assert data["human_gate"] is True


def test_recover_action_outputs_json(minimal_state_file):
    result = run_loader("--action", "recover", state_file=minimal_state_file)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert "can_resume_from" in data
    assert "last_completed" in data


def test_validate_entry_fails_when_requirements_missing(minimal_state_file):
    # clarify entry check requires summary.md which does not exist in this repo
    result = run_loader("--stage", "clarify", "--action", "validate-entry", state_file=minimal_state_file)
    assert result.returncode == 1
    assert "FAIL" in result.stderr or "FAIL" in result.stdout


def test_record_artifacts_action_discovers_existing_files(minimal_state_file):
    """record-artifacts should discover existing workflow artifacts and update the node."""
    import importlib.util

    loader_spec = importlib.util.spec_from_file_location("stage_loader", STAGE_LOADER)
    loader_mod = importlib.util.module_from_spec(loader_spec)
    loader_spec.loader.exec_module(loader_mod)

    state = yaml.safe_load(minimal_state_file.read_text(encoding="utf-8"))
    process_slug = state["current_run"]["variables"]["process_slug"]
    session_id = state["current_run"]["variables"]["session_id"]

    created_paths = []
    try:
        for art in [
            f"{process_slug}/interviews/{session_id}/metadata.json",
            f"{process_slug}/interviews/{session_id}/summary.md",
        ]:
            path = ROOT / art
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")
            created_paths.append(path)

        state = loader_mod.load_state(minimal_state_file)
        recorded = loader_mod.action_record_artifacts("ingest", state, minimal_state_file)
        assert len(recorded) == 2
        assert any("metadata.json" in a for a in recorded)
        assert any("summary.md" in a for a in recorded)

        updated = yaml.safe_load(minimal_state_file.read_text(encoding="utf-8"))
        artifacts = updated["nodes"][0]["artifacts"]
        assert any("metadata.json" in a for a in artifacts)
        assert any("summary.md" in a for a in artifacts)
    finally:
        for path in created_paths:
            path.unlink(missing_ok=True)
        # Remove empty dirs up to process slug
        process_dir = ROOT / process_slug
        if process_dir.exists():
            import shutil
            shutil.rmtree(process_dir, ignore_errors=True)
