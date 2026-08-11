"""Tests for prompt drift across Lincoln's agent/stage/workflow/skill layers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIFT_SCRIPT = ROOT / "scripts" / "check-prompt-drift.py"


def run_drift(*args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(DRIFT_SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_drift_script_runs():
    """The drift checker should execute without crashing."""
    rc, stdout, stderr = run_drift()
    combined = stdout + stderr
    assert rc == 0, f"check-prompt-drift.py exited {rc}:\n{combined}"


def test_drift_script_reports_pm_stage_errors():
    """PM-stage drift findings must be reported (strict mode only fails on errors)."""
    rc, stdout, stderr = run_drift("--focus", "pm")
    combined = stdout + stderr
    assert "[PM]" in combined, "Expected PM-stage drift findings to be reported"


def test_drift_script_strict_pm_stage_fails():
    """In strict mode, any PM-stage error must cause a non-zero exit."""
    rc, stdout, stderr = run_drift("--strict", "--focus", "pm")
    combined = stdout + stderr
    has_pm_error = "ERROR [PM]" in combined
    if has_pm_error:
        assert rc != 0, "Strict mode should fail when PM-stage errors exist"
    else:
        assert rc == 0, f"Strict mode failed unexpectedly:\n{combined}"


def test_drift_script_all_mode_reports_active_rules():
    """The full report should contain R3 findings; R2, R4-R6 are implemented and currently clean."""
    rc, stdout, stderr = run_drift()
    combined = stdout + stderr
    assert "R3" in combined, "Expected R3 findings in drift report"


def test_drift_script_implements_r6_check():
    """R6 rule logic is present in the drift checker source."""
    source = DRIFT_SCRIPT.read_text(encoding="utf-8")
    assert "R6" in source, "Expected R6 check in drift checker source"
    assert "check_r6_skill_dependencies_declared" in source


def test_drift_script_strict_all_fails_when_errors_exist():
    """Strict mode over all stages fails if any error exists."""
    rc, stdout, stderr = run_drift("--strict")
    combined = stdout + stderr
    has_error = "ERROR" in combined
    if has_error:
        assert rc != 0, "Strict mode should fail when any errors exist"
    else:
        assert rc == 0, f"Strict mode failed unexpectedly:\n{combined}"
