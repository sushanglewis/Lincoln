"""Deterministic infrastructure layer tests (#67).

These tests exercise the scripts that guard Lincoln's packaging and harness
consistency. They must not depend on LLM calls, network access, or stochastic
behavior.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _harness_artifacts_exist(harness: str) -> bool:
    if harness == "opencode":
        return (ROOT / ".opencode").exists()
    if harness == "codex":
        return (ROOT / ".codex-plugin").exists() or (ROOT / "AGENTS.md").exists()
    return False


def test_version_lockstep_check_passes():
    # Arrange / Act
    result = _run(["python3", "scripts/bump_version.py", "--check"])

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("harness", ["codex", "opencode"])
def test_harness_adapter_drift_check_passes(harness: str):
    # Skip drift check when generated artifacts have not been materialized locally.
    if not _harness_artifacts_exist(harness):
        pytest.skip(f"{harness} harness artifacts not present; drift check not applicable")

    # Arrange / Act
    result = _run(
        ["python3", "scripts/lincoln_harness_adapter.py", "--harness", harness, "--check"]
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr


def test_harness_drift_script_passes():
    # Arrange / Act
    result = _run(["bash", "scripts/check-harness-drift.sh"])

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
