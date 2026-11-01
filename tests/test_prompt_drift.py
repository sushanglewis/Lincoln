"""Tests for prompt drift across Lincoln's agent/stage/workflow/skill layers."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIFT_SCRIPT = ROOT / "scripts" / "check-prompt-drift.py"
SPEC = importlib.util.spec_from_file_location("check_prompt_drift", DRIFT_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
drift = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drift)

PEN_ARTIFACT = "{process_slug}/designs/{design_id}/prototype.pen"
HTML_PROTOTYPE = "{process_slug}/pages/prototype/**/*.html"


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


def test_drift_script_pm_stage_is_clean():
    """Declared lightweight subsets must not produce repetitive PM-stage warnings."""
    rc, stdout, stderr = run_drift("--focus", "pm")
    combined = stdout + stderr
    assert rc == 0
    assert "0 error(s), 0 warning(s)" in combined, combined


def test_drift_script_strict_pm_stage_fails():
    """In strict mode, any PM-stage error must cause a non-zero exit."""
    rc, stdout, stderr = run_drift("--strict", "--focus", "pm")
    combined = stdout + stderr
    has_pm_error = "ERROR [PM]" in combined
    if has_pm_error:
        assert rc != 0, "Strict mode should fail when PM-stage errors exist"
    else:
        assert rc == 0, f"Strict mode failed unexpectedly:\n{combined}"


def test_drift_script_all_mode_reports_summary():
    """The full report should execute all rules and end with a findings summary."""
    rc, stdout, stderr = run_drift()
    combined = stdout + stderr
    assert rc == 0
    assert "error(s)," in combined and "warning(s)" in combined


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


def make_r3_case(
    profile: str,
    required: list[str],
    optional: list[str] | None = None,
) -> tuple[dict, dict]:
    workflows = {
        "contract-test": {
            "data": {
                "artifact_profile": profile,
                "steps": [{
                    "id": "clarify",
                    "artifacts": required,
                    "optional_artifacts": optional or [],
                }],
            },
        },
    }
    stages = {
        "clarify": {
            "data": {
                "id": "clarify",
                "artifacts": {
                    "required": ["requirements.html", "prd.html"],
                    "optional": ["prd-snapshot.html"],
                },
            },
        },
    }
    return workflows, stages


def test_r3_lightweight_intentional_subset_is_quiet():
    workflows, stages = make_r3_case("lightweight", ["requirements.html"])

    findings = drift.check_r3_workflow_artifacts_match_stage(workflows, stages)

    assert findings == []


def test_r3_full_prd_missing_artifact_is_an_error():
    workflows, stages = make_r3_case("full-prd", ["requirements.html"])

    findings = drift.check_r3_workflow_artifacts_match_stage(workflows, stages)

    missing_prd = [finding for finding in findings if "prd.html" in finding["message"]]
    assert len(missing_prd) == 1
    assert missing_prd[0]["severity"] == "error"
    assert missing_prd[0]["rule"] == "R3"


def test_r3_lightweight_undeclared_artifacts_still_warn():
    workflows, stages = make_r3_case(
        "lightweight",
        ["requirements.html", "unexpected-required.html"],
        ["unexpected-optional.html"],
    )

    findings = drift.check_r3_workflow_artifacts_match_stage(workflows, stages)

    assert len(findings) == 2
    assert all(finding["severity"] == "warning" for finding in findings)
    assert {finding["file"] for finding in findings} == {".claude/workflows/contract-test.yaml"}
    messages = "\n".join(finding["message"] for finding in findings)
    assert "unexpected-required.html" in messages
    assert "unexpected-optional.html" in messages


def test_pm_workflows_declare_artifact_profiles():
    workflows = drift.collect_workflows()
    pm_workflows = {
        name: info
        for name, info in workflows.items()
        if any(step.get("id") in drift.PM_STAGES for step in info["data"].get("steps", []))
    }

    assert pm_workflows
    for name, info in pm_workflows.items():
        assert info["data"].get("artifact_profile") in {"full-prd", "lightweight"}, name
    assert workflows["interview-to-knowledge"]["data"]["artifact_profile"] == "full-prd"
    assert workflows["pm-team"]["data"]["artifact_profile"] == "full-prd"


def test_prototype_workflows_require_html_and_make_pencil_optional():
    workflows = drift.collect_workflows()
    prototype_steps = {
        name: next(step for step in info["data"]["steps"] if step.get("id") == "product-prototype")
        for name, info in workflows.items()
        if any(step.get("id") == "product-prototype" for step in info["data"].get("steps", []))
    }

    assert {"design-spike", "existing-project-iteration", "oss-first-design"} <= prototype_steps.keys()
    for name, step in prototype_steps.items():
        required = step.get("artifacts", [])
        optional = step.get("optional_artifacts", [])
        assert HTML_PROTOTYPE in required, name
        assert PEN_ARTIFACT not in required, name
        assert PEN_ARTIFACT in optional, name


def test_tdd_prompt_treats_html_as_required_and_pencil_as_optional():
    prompt = (ROOT / ".claude/skills/plan-tdd-development/prompts/main.md").read_text(encoding="utf-8")

    assert "Confirm `{process_slug}/pages/prototype/**/*.html`" in prompt
    assert "prototype.pen` source file is optional" in prompt
    assert "If the optional `.pen` exists" in prompt
