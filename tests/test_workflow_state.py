import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage_loader import (
    load_state,
    save_state,
    action_transition_next,
    action_recover,
    compute_next_stage,
    load_workflow,
)


def _legacy_state():
    """Return a minimal valid legacy state dict for unit tests."""
    return {
        "schema_version": "2.0.0",
        "workflow": {
            "name": "interview-to-knowledge",
            "version": "1.0.0",
            "template": "interview-to-knowledge",
        },
        "current_run": {
            "run_id": "test-001",
            "branch": "lincoln/test-branch",
            "current_stage": "ingest",
            "previous_stage": None,
            "status": "in_progress",
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
        },
        "stages": {
            "ingest": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "clarify": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "product-design-docs": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "product-prototype": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "tdd-development-plan": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "propose": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "split": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "implement": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "sync-knowledge": {
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "entry_checks_passed": None,
                "entry_checks_run_at": None,
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
        },
        "variables": {
            "session_id": "2026-06-27-test",
            "design_id": None,
            "change_name": None,
            "issue_number": None,
            "pr_number": None,
            "feature_slug": None,
        },
        "recovery": {
            "last_validated_checkpoint": None,
            "can_resume_from": None,
            "abort_reason": None,
            "abort_at": None,
        },
    }


@pytest.fixture
def fresh_state(tmp_path):
    """Return a copy of a minimal legacy state in a temp path."""
    state = _legacy_state()
    out = tmp_path / "workflow-state.yaml"
    out.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def test_load_state_requires_schema_version(fresh_state):
    state = yaml.safe_load(fresh_state.read_text(encoding="utf-8"))
    del state["schema_version"]
    fresh_state.write_text(yaml.dump(state), encoding="utf-8")
    with pytest.raises(ValueError, match="missing keys"):
        load_state(fresh_state)


def test_compute_next_stage_follows_workflow_order():
    workflow = load_workflow()
    assert compute_next_stage(workflow, "ingest") == "clarify"
    assert compute_next_stage(workflow, "clarify") == "product-design-docs"
    assert compute_next_stage(workflow, "sync-knowledge") is None


def test_action_transition_next_updates_current_run(fresh_state):
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    next_stage = action_transition_next("ingest", state, fresh_state)
    assert next_stage == "clarify"
    updated = load_state(fresh_state)
    assert updated["current_run"]["current_stage"] == "clarify"
    assert updated["current_run"]["previous_stage"] == "ingest"
    assert updated["stages"]["clarify"]["status"] == "not_started"


def test_action_recover_finds_last_completed(fresh_state):
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["clarify"]["status"] = "validation_failed"
    state["stages"]["clarify"]["retry_count"] = 1
    save_state(state, fresh_state)

    state = load_state(fresh_state)
    result = action_recover(state, fresh_state)
    assert result["last_completed"] == "ingest"
    assert result["can_resume_from"] == "clarify"


def test_state_file_in_project_has_all_stages():
    state = _legacy_state()
    workflow = load_workflow()
    expected = {s["id"] for s in workflow["steps"]}
    actual = set(state["stages"].keys())
    assert actual == expected


def test_action_validate_records_validator_history(fresh_state):
    from scripts.stage_loader import action_validate
    state = load_state(fresh_state)
    # Set up a stage with entry checks that will fail (so we get history)
    # First, set ingest to completed so we can validate clarify entry
    state["stages"]["ingest"]["status"] = "completed"
    save_state(state, fresh_state)

    state = load_state(fresh_state)
    result = action_validate("clarify", state, "entry", fresh_state)
    assert result == 1

    updated = load_state(fresh_state)
    clarify = updated["stages"]["clarify"]
    assert clarify["status"] == "validation_failed"
    assert clarify["retry_count"] == 1
    assert "validator_history" in clarify
    assert len(clarify["validator_history"]) >= 1


def test_action_validate_exit_records_validator_history(fresh_state):
    from scripts.stage_loader import action_validate
    state = load_state(fresh_state)
    # Set ingest to completed and clarify to in_progress so exit checks run
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["clarify"]["status"] = "in_progress"
    save_state(state, fresh_state)

    state = load_state(fresh_state)
    result = action_validate("clarify", state, "exit", fresh_state)
    assert result == 1

    updated = load_state(fresh_state)
    clarify = updated["stages"]["clarify"]
    assert clarify["retry_count"] == 1
    assert "validator_history" in clarify


def test_action_transition_next_records_duration_seconds(fresh_state):
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["ingest"]["started_at"] = "2026-06-27T00:00:00Z"
    save_state(state, fresh_state)

    state = load_state(fresh_state)
    action_transition_next("ingest", state, fresh_state)

    updated = load_state(fresh_state)
    assert updated["stages"]["ingest"]["duration_seconds"] is not None
    assert isinstance(updated["stages"]["ingest"]["duration_seconds"], int)
