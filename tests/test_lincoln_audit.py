"""Tests for scripts/lincoln-audit.py."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "scripts" / "lincoln-audit.py"


STAGE_HUMAN_GATES = {
    "ingest": False,
    "clarify": True,
    "product-design-docs": True,
    "implement": True,
}


def fake_load_stage_yaml(stage_id: str) -> dict:
    """Minimal stage definition for unit tests; no required artifacts by default."""
    return {
        "human_gate": STAGE_HUMAN_GATES.get(stage_id, False),
        "artifacts": {"required": []},
    }


def _load_audit_module():
    """Load lincoln-audit.py as a module (filename has hyphen)."""
    spec = importlib.util.spec_from_file_location("lincoln_audit", AUDIT_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_audit(*args):
    return subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.fixture
def audit_mod():
    return _load_audit_module()


@pytest.fixture
def valid_workflow():
    return {
        "name": "test-workflow",
        "steps": [
            {"id": "ingest", "name": "Ingest", "human_gate": False, "artifacts": []},
            {"id": "clarify", "name": "Clarify", "human_gate": True, "artifacts": []},
            {"id": "product-design-docs", "name": "Design", "human_gate": True, "artifacts": []},
        ],
    }


@pytest.fixture
def completed_state(valid_workflow):
    """A fully valid/completed node-based state that should PASS all audits."""
    return {
        "schema_version": "2.0.0",
        "workflow": {"name": "test-workflow", "template": "test-workflow"},
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": None,
            "previous_stage": "product-design-docs",
            "status": "completed",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "variables": {"process_slug": "test"},
        },
        "nodes": [
            {
                "stage_id": "ingest",
                "node_id": "ingest-1",
                "status": "completed",
                "gate_passed": False,
                "approved_by": None,
                "started_at": "2026-06-27T00:00:00Z",
                "completed_at": "2026-06-27T01:00:00Z",
                "entry_checks_passed": True,
                "exit_checks_passed": True,
                "retry_count": 0,
                "artifacts": [],
                "handoff_file": None,
                "skills_invoked": [{"skill": "test", "invoked_at": "2026-06-27T00:00:00Z", "result": "ok"}],
            },
            {
                "stage_id": "clarify",
                "node_id": "clarify-1",
                "status": "completed",
                "gate_passed": True,
                "approved_by": "human-pm",
                "started_at": "2026-06-27T01:00:00Z",
                "completed_at": "2026-06-27T02:00:00Z",
                "entry_checks_passed": True,
                "exit_checks_passed": True,
                "retry_count": 0,
                "artifacts": [],
                "handoff_file": None,
                "skills_invoked": [{"skill": "test", "invoked_at": "2026-06-27T01:00:00Z", "result": "ok"}],
            },
            {
                "stage_id": "product-design-docs",
                "node_id": "product-design-docs-1",
                "status": "completed",
                "gate_passed": True,
                "approved_by": "human-pm",
                "started_at": "2026-06-27T02:00:00Z",
                "completed_at": "2026-06-27T03:00:00Z",
                "entry_checks_passed": True,
                "exit_checks_passed": True,
                "retry_count": 0,
                "artifacts": [],
                "handoff_file": None,
                "skills_invoked": [{"skill": "test", "invoked_at": "2026-06-27T02:00:00Z", "result": "ok"}],
            },
        ],
        "recovery": {},
    }


# ---------------------------------------------------------------------------
# PASS tests
# ---------------------------------------------------------------------------


def test_audit_state_consistency_pass(audit_mod, completed_state, valid_workflow):
    result = audit_mod.audit_state_consistency(completed_state, valid_workflow)
    assert result["status"] == "PASS"


def test_audit_artifact_completeness_pass(audit_mod, completed_state, valid_workflow, monkeypatch):
    monkeypatch.setattr(audit_mod, "load_stage_yaml", fake_load_stage_yaml)
    result = audit_mod.audit_artifact_completeness(completed_state, valid_workflow)
    assert result["status"] == "PASS"


def test_audit_human_gate_compliance_pass(audit_mod, completed_state, valid_workflow):
    result = audit_mod.audit_human_gate_compliance(completed_state, valid_workflow)
    assert result["status"] == "PASS"


def test_audit_entry_exit_compliance_pass(audit_mod, completed_state, valid_workflow):
    result = audit_mod.audit_entry_exit_compliance(completed_state, valid_workflow)
    assert result["status"] == "PASS"


def test_audit_skill_coverage_pass(audit_mod, completed_state):
    result = audit_mod.audit_skill_coverage(completed_state)
    assert result["status"] == "PASS"


def test_audit_anomaly_detection_pass(audit_mod, completed_state):
    result = audit_mod.audit_anomaly_detection(completed_state)
    assert result["status"] == "PASS"


def test_run_all_audits_no_failures(audit_mod, completed_state, valid_workflow, monkeypatch):
    """Run all audits on completed state - should not have any FAIL."""
    monkeypatch.setattr(audit_mod, "load_workflow", lambda _name=None: valid_workflow)
    monkeypatch.setattr(audit_mod, "load_stage_yaml", fake_load_stage_yaml)
    results = audit_mod.run_all_audits(completed_state)
    overall = audit_mod.compute_overall_status(results)
    assert overall in ("PASS", "WARN")
    for r in results:
        assert r["status"] in ("PASS", "WARN")


# ---------------------------------------------------------------------------
# FAIL/WARN tests
# ---------------------------------------------------------------------------


def test_human_gate_fail_when_completed_but_not_passed(audit_mod, completed_state, valid_workflow):
    """FAIL when human_gate stage completed but gate_passed false."""
    for node in completed_state["nodes"]:
        if node["stage_id"] == "clarify":
            node["gate_passed"] = False
            node["approved_by"] = None
    result = audit_mod.audit_human_gate_compliance(completed_state, valid_workflow)
    assert result["status"] == "FAIL"
    assert "clarify" in result["message"]


def test_artifact_completeness_warn_when_required_missing(audit_mod, valid_workflow, monkeypatch):
    """WARN when required artifacts missing."""
    def fake_load(stage_id: str) -> dict:
        return {
            "human_gate": False,
            "artifacts": {"required": ["missing/file.txt"]},
        }

    monkeypatch.setattr(audit_mod, "load_stage_yaml", fake_load)

    workflow = {
        "name": "test",
        "steps": [
            {"id": "ingest", "name": "Ingest", "human_gate": False, "artifacts": []},
        ],
    }
    state = {
        "schema_version": "2.0.0",
        "workflow": workflow,
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": "ingest",
            "previous_stage": None,
            "status": "in_progress",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "variables": {"process_slug": "test"},
        },
        "nodes": [
            {
                "stage_id": "ingest",
                "node_id": "ingest-1",
                "status": "in_progress",
                "gate_passed": False,
                "approved_by": None,
                "started_at": "2026-06-27T00:00:00Z",
                "completed_at": None,
                "entry_checks_passed": True,
                "exit_checks_passed": None,
                "retry_count": 0,
                "artifacts": [],
                "handoff_file": None,
            }
        ],
        "recovery": {},
    }
    result = audit_mod.audit_artifact_completeness(state, workflow)
    assert result["status"] == "WARN"
    assert "missing" in result["message"]


def test_anomaly_detection_warn_when_validation_failed(audit_mod, completed_state):
    """WARN when validation_failed nodes exist."""
    completed_state["nodes"][0]["status"] = "validation_failed"
    result = audit_mod.audit_anomaly_detection(completed_state)
    assert result["status"] == "WARN"
    assert "validation_failed" in result["message"]


def test_anomaly_detection_warn_when_retry_count_high(audit_mod, completed_state):
    """WARN when retry_count > 1."""
    completed_state["nodes"][1]["retry_count"] = 3
    result = audit_mod.audit_anomaly_detection(completed_state)
    assert result["status"] == "WARN"
    assert "retry_count=3" in result["message"]


def test_entry_exit_compliance_warn_when_checks_missing(audit_mod, completed_state, valid_workflow):
    """WARN when completed stage lacks entry/exit checks."""
    completed_state["nodes"][0]["entry_checks_passed"] = None
    result = audit_mod.audit_entry_exit_compliance(completed_state, valid_workflow)
    assert result["status"] == "WARN"
    assert "entry checks not passed" in result["message"]


# ---------------------------------------------------------------------------
# Per-process handoff test
# ---------------------------------------------------------------------------


def test_audit_finds_process_handoff(audit_mod, tmp_path, monkeypatch):
    handoff_dir = tmp_path / "feature-xyz" / "handoffs"
    handoff_dir.mkdir(parents=True)
    handoff_file = handoff_dir / "lc-handoff-clarify.md"
    handoff_file.write_text("# Handoff\n", encoding="utf-8")

    def fake_process_root(**kwargs):
        return tmp_path / "feature-xyz"

    monkeypatch.setattr(audit_mod, "process_package_root", fake_process_root)

    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge", "template": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "feature-xyz", "session_id": "", "design_id": ""},
            "started_at": "2026-07-06T00:00:00Z",
            "last_updated_at": "2026-07-06T00:00:00Z",
        },
        "nodes": [
            {
                "stage_id": "clarify",
                "node_id": "clarify-1",
                "status": "waiting_for_human",
                "gate_passed": False,
                "approved_by": None,
                "artifacts": [],
                "handoff_file": None,
            }
        ],
        "recovery": {},
    }
    result = audit_mod.audit_handoff_file(state)
    assert result["status"] == "PASS"
    assert "feature-xyz/handoffs" in result["message"]


# ---------------------------------------------------------------------------
# Overall status computation
# ---------------------------------------------------------------------------


def test_compute_overall_status_pass():
    mod = _load_audit_module()
    results = [
        {"status": "PASS"},
        {"status": "PASS"},
    ]
    assert mod.compute_overall_status(results) == "PASS"


def test_compute_overall_status_warn():
    mod = _load_audit_module()
    results = [
        {"status": "PASS"},
        {"status": "WARN"},
    ]
    assert mod.compute_overall_status(results) == "WARN"


def test_compute_overall_status_fail():
    mod = _load_audit_module()
    results = [
        {"status": "PASS"},
        {"status": "WARN"},
        {"status": "FAIL"},
    ]
    assert mod.compute_overall_status(results) == "FAIL"


# ---------------------------------------------------------------------------
# CLI output tests
# ---------------------------------------------------------------------------


def _cli_state(tmp_path):
    """Create a minimal node-based state file for CLI tests."""
    process_root = tmp_path / "audit-cli-test"
    process_root.mkdir()
    state_file = process_root / "workflow-stage.yaml"
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "interview-to-knowledge", "template": "interview-to-knowledge"},
        "current_run": {
            "run_id": "r1",
            "current_stage": "clarify",
            "status": "in_progress",
            "variables": {"process_slug": "audit-cli-test", "session_id": "", "design_id": ""},
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
    return state_file


def test_cli_markdown_contains_status(tmp_path):
    state_file = _cli_state(tmp_path)
    result = run_audit("--state-file", str(state_file), "--format", "markdown")
    assert result.returncode in (0, 1)
    output = result.stdout
    assert any(s in output for s in ("PASS", "WARN", "FAIL"))


def test_cli_json_contains_overall_status(tmp_path):
    state_file = _cli_state(tmp_path)
    result = run_audit("--state-file", str(state_file), "--format", "json")
    assert result.returncode in (0, 1)
    data = json.loads(result.stdout)
    assert "overall_status" in data
    assert "checks" in data


# ---------------------------------------------------------------------------
# State consistency edge cases
# ---------------------------------------------------------------------------


def test_state_consistency_warn_when_no_current_stage_and_not_completed(audit_mod, valid_workflow):
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "test-workflow", "template": "test-workflow"},
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": None,
            "previous_stage": None,
            "status": "in_progress",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "variables": {"process_slug": "test"},
        },
        "nodes": [],
        "recovery": {},
    }
    result = audit_mod.audit_state_consistency(state, valid_workflow)
    assert result["status"] == "WARN"


def test_state_consistency_fail_when_stage_not_found(audit_mod, valid_workflow):
    state = {
        "schema_version": "2.0.0",
        "workflow": {"name": "test-workflow", "template": "test-workflow"},
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": "nonexistent-stage",
            "previous_stage": None,
            "status": "in_progress",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
            "variables": {"process_slug": "test"},
        },
        "nodes": [],
        "recovery": {},
    }
    result = audit_mod.audit_state_consistency(state, valid_workflow)
    assert result["status"] == "FAIL"
