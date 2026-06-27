import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STAGE_LOADER = ROOT / "scripts" / "stage_loader.py"


def run_loader(*args):
    return subprocess.run(
        [sys.executable, str(STAGE_LOADER), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_load_ingest_stage_returns_context():
    result = run_loader("--stage", "ingest", "--action", "load")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["stage_id"] == "ingest"
    assert data["stage_name"] == "摄入录音"
    assert "context" in data


def test_load_clarify_stage_returns_human_gate():
    result = run_loader("--stage", "clarify", "--action", "load")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["stage_id"] == "clarify"
    assert data["human_gate"] is True


def test_recover_action_outputs_json():
    result = run_loader("--action", "recover")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "can_resume_from" in data
    assert "last_completed" in data


def test_validate_entry_fails_when_requirements_missing():
    # clarify entry check requires summary.md which does not exist in this repo
    result = run_loader("--stage", "clarify", "--action", "validate-entry")
    assert result.returncode == 1
    assert "FAIL" in result.stderr or "FAIL" in result.stdout
