import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TRACK_SCRIPT = ROOT / "scripts" / "track-artifacts.py"


def run_tracker(state_file, tool, args, project_root=ROOT):
    return subprocess.run(
        [
            sys.executable,
            str(TRACK_SCRIPT),
            "--state-file", str(state_file),
            "--tool", tool,
            "--args", args,
            "--project-root", str(project_root),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_track_artifacts_appends_to_current_node(tmp_path):
    process_root = tmp_path / "feature-xyz"
    process_root.mkdir()
    state_file = process_root / "workflow-stage.yaml"
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "feature-xyz"},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [
            {
                "stage_id": "clarify",
                "node_id": "clarify-1",
                "status": "in_progress",
                "gate_passed": False,
                "approved_by": None,
                "artifacts": [],
                "handoff_file": None,
            }
        ],
        "recovery": {},
    }
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = run_tracker(
        state_file,
        "Write",
        '{"file_path": "feature-xyz/requirements/2026-07-06-test/requirements.md"}',
        project_root=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    updated = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    assert "feature-xyz/requirements/2026-07-06-test/requirements.md" in updated["nodes"][0]["artifacts"]


def test_track_artifacts_creates_node_when_missing(tmp_path):
    process_root = tmp_path / "feature-xyz"
    process_root.mkdir()
    state_file = process_root / "workflow-stage.yaml"
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "feature-xyz"},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [],
        "recovery": {},
    }
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = run_tracker(
        state_file,
        "Write",
        '{"file_path": "feature-xyz/requirements/2026-07-06-test/requirements.md"}',
        project_root=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    updated = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    assert len(updated["nodes"]) == 1
    assert updated["nodes"][0]["stage_id"] == "clarify"
    assert "feature-xyz/requirements/2026-07-06-test/requirements.md" in updated["nodes"][0]["artifacts"]


def test_track_artifacts_skips_non_artifact_paths(tmp_path):
    process_root = tmp_path / "feature-xyz"
    process_root.mkdir()
    state_file = process_root / "workflow-stage.yaml"
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "feature-xyz"},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [
            {
                "stage_id": "clarify",
                "node_id": "clarify-1",
                "status": "in_progress",
                "gate_passed": False,
                "approved_by": None,
                "artifacts": [],
                "handoff_file": None,
            }
        ],
        "recovery": {},
    }
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = run_tracker(
        state_file,
        "Write",
        '{"file_path": "scripts/helper.py"}',
        project_root=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    updated = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    assert updated["nodes"][0]["artifacts"] == []


def test_track_artifacts_updates_legacy_artifacts_produced(tmp_path):
    state_file = tmp_path / ".claude" / "workflow-state.yaml"
    state_file.parent.mkdir(parents=True)
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "stages": {"clarify": {"artifacts_produced": []}},
        "variables": {},
        "recovery": {},
    }
    state_file.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = run_tracker(
        state_file,
        "Write",
        '{"file_path": "requirements/2026-07-06-test/requirements.md"}',
        project_root=tmp_path,
    )
    assert result.returncode == 0, result.stderr

    updated = yaml.safe_load(state_file.read_text(encoding="utf-8"))
    assert "requirements/2026-07-06-test/requirements.md" in updated["stages"]["clarify"]["artifacts_produced"]
