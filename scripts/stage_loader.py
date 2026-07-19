#!/usr/bin/env python3
"""
Lincoln stage loader / dispatcher.

Loads stage-specific context from `.claude/stages/<stage>.yaml`, runs
entry/exit validators, and manages the per-process workflow state file at
`<process_slug>/workflow-stage.yaml`.

Usage:
    python scripts/stage_loader.py --stage clarify --action load
    python scripts/stage_loader.py --stage product-design-docs --action validate-entry
    python scripts/stage_loader.py --stage product-design-docs --action validate-exit
    python scripts/stage_loader.py --stage clarify --action transition-next
    python scripts/stage_loader.py --action recover
    python scripts/stage_loader.py --stage clarify --action approve-gate
    python scripts/stage_loader.py --stage clarify --action append-node --node-id clarify --status in_progress
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml

from scripts import lincoln_trace
from scripts.lincoln_documents import write_documents_index
from scripts.lincoln_paths import (
    LEGACY_STATE_PATH,
    ROOT_STATE_PATH,
    get_process_slug,
    interpolate_process_path,
    process_package_root,
    resolve_state_path as resolve_lincoln_state_path,
)

WORKFLOW_PATH = PROJECT_ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"
WORKFLOW_TEMPLATE_DIR = PROJECT_ROOT / ".claude" / "workflows"
DEFAULT_WORKFLOW_PATH = WORKFLOW_PATH

STATE_PATH = ROOT_STATE_PATH
STAGES_DIR = PROJECT_ROOT / ".claude" / "stages"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_stage.py"

REQUIRED_STATE_KEYS = {
    "schema_version",
    "workflow",
    "current_run",
    "nodes",
    "recovery",
}

LEGACY_REQUIRED_STATE_KEYS = {
    "schema_version",
    "workflow",
    "current_run",
    "stages",
    "variables",
    "recovery",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, data: Any) -> None:
    """Write YAML atomically to avoid corrupting the state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".yaml.tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=120)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def resolve_workflow_path(template_name: str | None = None) -> Path:
    if not template_name:
        return DEFAULT_WORKFLOW_PATH
    template_path = WORKFLOW_TEMPLATE_DIR / f"{template_name}.yaml"
    if template_path.exists():
        return template_path
    raise FileNotFoundError(f"Workflow template not found: {template_path}")


def load_workflow(template_name: str | None = None) -> dict[str, Any]:
    path = resolve_workflow_path(template_name)
    data = load_yaml(path)
    return data.get("workflow", data)


def list_workflow_templates() -> list[str]:
    if not WORKFLOW_TEMPLATE_DIR.exists():
        return []
    return sorted(p.stem for p in WORKFLOW_TEMPLATE_DIR.glob("*.yaml"))


def _is_legacy_state(state: dict[str, Any]) -> bool:
    """Detect whether a state file uses the legacy schema (has 'stages' key)."""
    return "stages" in state and "nodes" not in state


def load_state(path: Path | None = None) -> dict[str, Any]:
    path = resolve_state_path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    state = load_yaml(path)
    if not isinstance(state, dict):
        raise ValueError(f"State file {path} must contain a YAML mapping")

    if _is_legacy_state(state):
        missing = LEGACY_REQUIRED_STATE_KEYS - set(state.keys())
        if missing:
            raise ValueError(f"Legacy state file missing keys: {', '.join(missing)}")
    else:
        missing = REQUIRED_STATE_KEYS - set(state.keys())
        if missing:
            raise ValueError(f"State file missing keys: {', '.join(missing)}")
    return state


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = resolve_state_path(path)
    state["current_run"]["last_updated_at"] = now_iso()
    save_yaml(path, state)
    write_documents_index(state, path)


def resolve_state_path(path: Path | None = None) -> Path:
    """Return the actual state file path to use, preferring new over legacy."""
    return resolve_lincoln_state_path(path, PROJECT_ROOT)


def find_stage(workflow: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for step in workflow.get("steps", []):
        if step.get("id") == stage_id:
            return step
    raise ValueError(f"Stage '{stage_id}' not found in workflow")


def compute_next_stage(workflow: dict[str, Any], stage_id: str) -> str | None:
    steps = workflow.get("steps", [])
    ids = [s["id"] for s in steps]
    try:
        idx = ids.index(stage_id)
    except ValueError:
        raise ValueError(f"Stage '{stage_id}' not found in workflow")
    if idx + 1 < len(ids):
        return ids[idx + 1]
    return None


def interpolate(value: str, variables: dict[str, Any]) -> str:
    """Replace {var} placeholders with variable values."""

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in variables and variables[key] is not None:
            return str(variables[key])
        return match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, value)


def interpolate_artifact(value: str, state: dict[str, Any], state_file: Path | None = None) -> str:
    value = interpolate(value, get_variables(state))
    return interpolate_process_path(value, state, resolve_state_path(state_file))


def get_variables(state: dict[str, Any]) -> dict[str, Any]:
    """Extract variables from state, handling both new and legacy schemas."""
    if _is_legacy_state(state):
        return state.get("variables", {})
    return state.get("current_run", {}).get("variables", {})


def get_stage_state(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    """Get stage state from legacy schema."""
    return state.get("stages", {}).get(stage_id, {})


def get_nodes(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Get nodes array from new schema."""
    return state.get("nodes", [])


def get_latest_node_for_stage(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    """Return the latest node for a given stage, or None."""
    nodes = get_nodes(state)
    matching = [n for n in nodes if n.get("stage_id") == stage_id]
    if not matching:
        return None
    return matching[-1]


def load_stage_yaml(stage_id: str) -> dict[str, Any]:
    """Load the single-YAML stage definition."""
    path = STAGES_DIR / f"{stage_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Stage YAML not found: {path}")
    return load_yaml(path)


def list_stage_ids() -> list[str]:
    """Return all stage IDs discovered from .claude/stages/*.yaml."""
    if not STAGES_DIR.exists():
        return []
    return sorted(p.stem for p in STAGES_DIR.glob("*.yaml") if p.stem != "stage-manifest")


def load_skill_routing() -> dict[str, Any]:
    """Build skill routing from stage YAMLs for backward compatibility."""
    routing: dict[str, Any] = {"routing": {}}
    for stage_id in list_stage_ids():
        try:
            stage = load_stage_yaml(stage_id)
            skills = stage.get("skills", {})
            routing["routing"][stage_id] = {
                "required": skills.get("required", []),
                "optional": skills.get("optional", []),
                "human_gate": stage.get("human_gate", False),
            }
        except Exception:
            continue
    return routing


def get_stage_skills(_routing_data: dict[str, Any] | None, stage_id: str) -> dict[str, list[str]]:
    """Extract required/optional skills for a stage from stage YAML."""
    try:
        stage = load_stage_yaml(stage_id)
        skills = stage.get("skills", {})
        return {
            "required": skills.get("required", []),
            "optional": skills.get("optional", []),
        }
    except Exception:
        return {"required": [], "optional": []}


def run_validator(
    phase: str,
    check_name: str,
    args: list[str],
    state_file: Path | None = None,
    project_root: Path | None = None,
) -> tuple[int, str, str]:
    """Run a validator check via validate_stage.py subprocess."""
    if not VALIDATOR_PATH.exists():
        raise FileNotFoundError(f"Validator not found: {VALIDATOR_PATH}")

    args_str = ",".join(args)
    cmd = [
        sys.executable,
        str(VALIDATOR_PATH),
        "--phase",
        phase,
        "--check",
        check_name,
    ]
    if args_str:
        cmd.extend(["--args", args_str])
    if state_file is not None:
        cmd.extend(["--state-file", str(state_file)])

    env = os.environ.copy()
    if project_root is not None:
        env["LINCOLN_PROJECT_ROOT"] = str(project_root)

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Context resolution
# ---------------------------------------------------------------------------


def resolve_stage_context(
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
) -> dict[str, Any]:
    """Return a deterministic context dict for the current stage.

    Merges:
      1. stage YAML (identity, agents, skills, artifacts, context, gates)
      2. workflow template step (for ordering and name override)
      3. interpolated variables from workflow-stage.yaml
    """
    stage = load_stage_yaml(stage_id)
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    workflow_step = find_stage(workflow, stage_id)

    variables = get_variables(state)
    variables.setdefault("process_slug", get_process_slug(state, resolve_state_path(state_file)))

    context = stage.get("context", {})
    interpolated_context = {
        key: interpolate(value, variables)
        for key, value in context.items()
        if isinstance(value, str)
    }

    artifacts = stage.get("artifacts", {})
    required_artifacts = [
        interpolate_artifact(str(art), state, state_file)
        for art in artifacts.get("required", [])
    ]
    optional_artifacts = [
        interpolate_artifact(str(art), state, state_file)
        for art in artifacts.get("optional", [])
    ]

    agent = stage.get("agent", {})
    skills = stage.get("skills", {})

    return {
        "stage_id": stage_id,
        "stage_name": workflow_step.get("name", stage.get("name", stage_id)),
        "description": stage.get("description", ""),
        "human_gate": stage.get("human_gate", False),
        "next_stage": compute_next_stage(workflow, stage_id),
        "primary_agent": agent.get("primary"),
        "review_agents": agent.get("reviewers", []),
        "handoff_to": agent.get("handoff_to"),
        "required_skills": skills.get("required", []),
        "optional_skills": skills.get("optional", []),
        "required_artifacts": required_artifacts,
        "optional_artifacts": optional_artifacts,
        "context": interpolated_context,
        "context_path": str((STAGES_DIR / f"{stage_id}.yaml").relative_to(PROJECT_ROOT)),
        "workflow_template": template_name,
    }


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_load(stage_id: str, state: dict[str, Any], state_file: Path | None = None) -> dict[str, Any]:
    context = resolve_stage_context(stage_id, state, state_file)

    if _is_legacy_state(state):
        stage_status = state.get("stages", {}).get(stage_id, {}).get("status")
    else:
        latest_node = get_latest_node_for_stage(state, stage_id)
        stage_status = latest_node.get("status") if latest_node else state.get("current_run", {}).get("status")

    return {
        "stage_id": context["stage_id"],
        "stage_name": context["stage_name"],
        "stage_status": stage_status,
        "human_gate": context["human_gate"],
        "next_stage": context["next_stage"],
        "context": json.dumps(context["context"], ensure_ascii=False),
        "context_paths": [context["context_path"]],
        "required_skills": context["required_skills"],
        "optional_skills": context["optional_skills"],
    }


def _check_artifacts_present(stage_id: str, state: dict[str, Any], state_file: Path | None = None) -> bool:
    """Check that all required artifacts for the stage exist and are non-empty."""
    stage = load_stage_yaml(stage_id)
    artifacts = stage.get("artifacts", {})
    required = artifacts.get("required", [])
    if not required:
        return True

    all_present = True
    for art in required:
        path = interpolate_artifact(str(art), state, state_file)
        target = PROJECT_ROOT / path
        if not target.exists() or target.stat().st_size == 0:
            print(f"FAIL: artifact missing or empty: {path}", file=sys.stderr)
            all_present = False
        else:
            print(f"PASS: artifact present: {path}")
    return all_present


def _check_human_approved(stage_id: str, state: dict[str, Any]) -> bool:
    """Check that the latest node for the stage is marked as approved."""
    latest_node = get_latest_node_for_stage(state, stage_id)
    if latest_node is None:
        print(f"FAIL: no node found for stage '{stage_id}'", file=sys.stderr)
        return False
    if bool(latest_node.get("gate_passed")) and latest_node.get("approved_by"):
        print(f"PASS: human approved for stage '{stage_id}'")
        return True
    print(f"FAIL: stage '{stage_id}' not approved", file=sys.stderr)
    return False


def _check_previous_stage_completed(stage_id: str, prev_stage_id: str, state: dict[str, Any]) -> bool:
    """Check that the prerequisite stage has a completed node."""
    prev_node = get_latest_node_for_stage(state, prev_stage_id)
    if prev_node and prev_node.get("status") == "completed":
        print(f"PASS: previous stage '{prev_stage_id}' completed")
        return True
    print(f"FAIL: previous stage '{prev_stage_id}' not completed", file=sys.stderr)
    return False


def _run_gate_check(
    phase: str,
    check: dict[str, Any],
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
) -> bool:
    """Run a single gate check. Returns True if passed."""
    check_name = check.get("check")
    raw_args = check.get("args", [])
    variables = get_variables(state)
    variables.setdefault("process_slug", get_process_slug(state, resolve_state_path(state_file)))
    args = [
        interpolate_process_path(interpolate(str(a), variables), state, resolve_state_path(state_file))
        for a in raw_args
    ]

    if check_name == "artifacts_present":
        return _check_artifacts_present(stage_id, state, state_file)

    if check_name in ("human_approved", "gate_review_passed"):
        return _check_human_approved(stage_id, state)

    if check_name == "previous_stage_completed":
        if not args:
            print(f"FAIL: previous_stage_completed requires an argument", file=sys.stderr)
            return False
        return _check_previous_stage_completed(stage_id, args[0], state)

    # Structural checks delegated to validate_stage.py
    exit_code, stdout, stderr = run_validator(phase, check_name, args, state_file)
    if exit_code == 0:
        print(f"PASS: {phase} check '{check_name}'")
        return True
    print(f"FAIL: {phase} check '{check_name}'", file=sys.stderr)
    if stdout:
        print(stdout, file=sys.stderr)
    if stderr:
        print(stderr, file=sys.stderr)
    return False


def action_validate(
    stage_id: str,
    state: dict[str, Any],
    phase: str,
    state_file: Path | None = None,
) -> int:
    """Run entry/exit checks from the stage YAML gates."""
    stage = load_stage_yaml(stage_id)
    checks = stage.get("gates", {}).get(phase, [])

    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["started_at"] = stage_state.get("started_at") or now_iso()
        if phase == "entry":
            stage_state["status"] = "entry_validating"
        save_state(state, state_file)

        if "validator_history" not in stage_state:
            stage_state["validator_history"] = []
    else:
        if phase == "entry":
            state["current_run"]["status"] = "entry_validating"
        save_state(state, state_file)

    all_passed = True
    for check in checks:
        passed = _run_gate_check(phase, check, stage_id, state, state_file)
        if _is_legacy_state(state):
            stage_state["validator_history"].append(
                {
                    "phase": phase,
                    "check": check.get("check"),
                    "exit_code": 0 if passed else 1,
                    "run_at": now_iso(),
                }
            )
        if not passed:
            all_passed = False

    if not all_passed:
        if _is_legacy_state(state):
            stage_state["status"] = "validation_failed"
            stage_state["retry_count"] = stage_state.get("retry_count", 0) + 1
        else:
            state["current_run"]["status"] = "validation_failed"
        save_state(state, state_file)
        return 1

    now = now_iso()
    if _is_legacy_state(state):
        if phase == "entry":
            stage_state["status"] = "in_progress"
            stage_state["entry_checks_passed"] = True
            stage_state["entry_checks_run_at"] = now
        else:
            stage_state["exit_checks_passed"] = True
            stage_state["exit_checks_run_at"] = now
        stage_state["error_message"] = None
    else:
        if phase == "entry":
            state["current_run"]["status"] = "in_progress"
        save_state(state, state_file)

    print(f"PASS: all {phase} checks for '{stage_id}'")
    return 0


def action_record_artifacts(
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
) -> list[str]:
    """Discover existing artifact paths declared by the stage YAML and record them."""
    stage = load_stage_yaml(stage_id)
    variables = get_variables(state)
    variables.setdefault("process_slug", get_process_slug(state, resolve_state_path(state_file)))

    recorded: list[str] = []
    artifacts = stage.get("artifacts", {})
    for art in artifacts.get("required", []) + artifacts.get("optional", []):
        path = interpolate_artifact(str(art), state, state_file)
        target = PROJECT_ROOT / path
        if target.exists():
            recorded.append(str(path))

    latest_node = get_latest_node_for_stage(state, stage_id)
    if latest_node is None:
        latest_node = {
            "stage_id": stage_id,
            "node_id": f"{stage_id}-{now_iso()}",
            "status": "in_progress",
            "started_at": now_iso(),
            "completed_at": None,
            "gate_passed": False,
            "approved_by": None,
            "artifacts": [],
            "handoff_file": None,
        }
        state.setdefault("nodes", []).append(latest_node)

    existing = set(latest_node.get("artifacts", []))
    existing.update(recorded)
    latest_node["artifacts"] = sorted(existing)

    save_state(state, state_file)
    print(f"Recorded {len(recorded)} artifacts for stage '{stage_id}'")
    for art in recorded:
        print(f"  - {art}")
    return recorded


def action_approve_gate(
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
    approved_by: str = "human-pm",
) -> int:
    """Mark the current/latest node for the stage as gate_passed: true."""
    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["human_gate_passed"] = True
        stage_state["human_gate_passed_at"] = now_iso()
        save_state(state, state_file)
        print(f"PASS: gate approved for stage '{stage_id}' (legacy mode)")
        return 0

    latest_node = get_latest_node_for_stage(state, stage_id)
    if latest_node is None:
        new_node = {
            "stage_id": stage_id,
            "node_id": f"{stage_id}-{now_iso()}",
            "status": "completed",
            "gate_passed": True,
            "approved_by": approved_by,
            "started_at": now_iso(),
            "completed_at": now_iso(),
            "artifacts": [],
            "handoff_file": None,
        }
        state.setdefault("nodes", []).append(new_node)
    else:
        latest_node["gate_passed"] = True
        latest_node["approved_by"] = approved_by
        latest_node["completed_at"] = now_iso()

    save_state(state, state_file)
    print(f"PASS: gate approved for stage '{stage_id}' by '{approved_by}'")
    return 0


def action_append_node(
    stage_id: str,
    state: dict[str, Any],
    node_id: str,
    status: str,
    state_file: Path | None = None,
    handoff_file: str | None = None,
    artifacts: list[str] | None = None,
) -> int:
    """Append a node record to the nodes array."""
    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["status"] = status
        if status == "completed":
            stage_state["completed_at"] = now_iso()
        if "started_at" not in stage_state or stage_state["started_at"] is None:
            stage_state["started_at"] = now_iso()
        if artifacts:
            existing = set(stage_state.get("artifacts_produced", []))
            existing.update(artifacts)
            stage_state["artifacts_produced"] = list(existing)
        save_state(state, state_file)
        print(f"Legacy node appended: stage '{stage_id}' -> status '{status}'")
        return 0

    node = {
        "stage_id": stage_id,
        "node_id": node_id,
        "status": status,
        "started_at": now_iso(),
        "completed_at": None,
        "gate_passed": False,
        "approved_by": None,
        "artifacts": artifacts or [],
        "handoff_file": handoff_file,
    }
    state.setdefault("nodes", []).append(node)

    state["current_run"]["current_stage"] = stage_id
    state["current_run"]["status"] = status

    save_state(state, state_file)
    print(f"Node appended: '{node_id}' for stage '{stage_id}' with status '{status}'")
    return 0


def action_transition_next(stage_id: str, state: dict[str, Any], state_file: Path | None = None) -> str | None:
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    next_stage_id = compute_next_stage(workflow, stage_id)

    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["status"] = "completed"
        stage_state["completed_at"] = now_iso()

        started_at = stage_state.get("started_at")
        completed_at = stage_state.get("completed_at")
        if started_at and completed_at:
            try:
                start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                stage_state["duration_seconds"] = int((end_dt - start_dt).total_seconds())
            except (ValueError, TypeError):
                stage_state["duration_seconds"] = None
        else:
            stage_state["duration_seconds"] = None

        if next_stage_id:
            next_state = state.setdefault("stages", {}).setdefault(next_stage_id, {})
            next_state.update(
                {
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
                }
            )
            state["current_run"]["current_stage"] = next_stage_id
            state["current_run"]["previous_stage"] = stage_id
        else:
            state["current_run"]["current_stage"] = None
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "completed"
    else:
        now = now_iso()
        recorded_artifacts = action_record_artifacts(stage_id, state, state_file)
        completed_node = {
            "stage_id": stage_id,
            "node_id": f"{stage_id}-completed",
            "status": "completed",
            "started_at": now,
            "completed_at": now,
            "gate_passed": True,
            "approved_by": "system",
            "artifacts": recorded_artifacts,
            "handoff_file": None,
        }
        state.setdefault("nodes", []).append(completed_node)

        if next_stage_id:
            state["current_run"]["current_stage"] = next_stage_id
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "not_started"
        else:
            state["current_run"]["current_stage"] = None
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "completed"

    save_state(state, state_file)
    print(f"Transitioned from '{stage_id}' to '{next_stage_id}'")
    return next_stage_id


def action_recover(state: dict[str, Any], state_file: Path | None = None) -> dict[str, Any]:
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    step_ids = [s["id"] for s in workflow.get("steps", [])]

    if _is_legacy_state(state):
        stages = state.get("stages", {})
        last_completed = None
        for sid in step_ids:
            if stages.get(sid, {}).get("status") == "completed":
                last_completed = sid

        resume_point = state["current_run"].get("current_stage") or last_completed
        if resume_point and stages.get(resume_point, {}).get("status") == "completed":
            resume_point = compute_next_stage(workflow, resume_point)

        state["recovery"]["last_validated_checkpoint"] = last_completed
        state["recovery"]["can_resume_from"] = resume_point
        save_state(state, state_file)

        return {
            "last_completed": last_completed,
            "can_resume_from": resume_point,
            "current_stage": state["current_run"].get("current_stage"),
            "current_status": state["current_run"].get("status"),
        }

    nodes = get_nodes(state)
    last_completed = None
    for node in reversed(nodes):
        if node.get("status") == "completed" and node.get("stage_id") in step_ids:
            last_completed = node.get("stage_id")
            break

    current_stage = state["current_run"].get("current_stage")
    resume_point = current_stage or last_completed
    if resume_point:
        latest = get_latest_node_for_stage(state, resume_point)
        if latest and latest.get("status") == "completed":
            resume_point = compute_next_stage(workflow, resume_point)

    state["recovery"]["last_validated_checkpoint"] = last_completed
    state["recovery"]["can_resume_from"] = resume_point
    save_state(state, state_file)

    return {
        "last_completed": last_completed,
        "can_resume_from": resume_point,
        "current_stage": current_stage,
        "current_status": state["current_run"].get("status"),
    }


def action_status(state: dict[str, Any]) -> dict[str, Any]:
    """Return status report by delegating to lc-status logic."""
    import importlib.util
    status_path = PROJECT_ROOT / "scripts" / "lincoln-status.py"
    spec = importlib.util.spec_from_file_location("lincoln_status", status_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_status_report(state)
    try:
        from lincoln_status import build_status_report
        return build_status_report(state)
    except ImportError:
        raise RuntimeError("Could not import lc-status module")


def action_handoff_report(stage_id: str, state: dict[str, Any], state_file: Path) -> str:
    """Generate <process_slug>/handoffs/lc-handoff-{stage}.md and trigger a handoff benchmark report."""
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)

    if _is_legacy_state(state):
        stage_state = state.get("stages", {}).get(stage_id, {})
        artifacts_produced = stage_state.get("artifacts_produced", [])
    else:
        latest_node = get_latest_node_for_stage(state, stage_id)
        stage_state = latest_node or {}
        artifacts_produced = stage_state.get("artifacts", [])

    lines = []
    lines.append("# Lincoln Handoff Report")
    lines.append("")
    lines.append(f"**Generated:** {now_iso()}")
    lines.append(f"**Branch:** {state.get('current_run', {}).get('branch', 'unknown')}")
    lines.append(f"**Run ID:** {state.get('current_run', {}).get('run_id', 'unknown')}")
    lines.append("")
    lines.append("## Current Stage")
    lines.append(f"- **Stage:** {stage_id}")
    lines.append(f"- **Name:** {stage_def.get('name', stage_id)}")
    if _is_legacy_state(state):
        lines.append(f"- **Status:** {stage_state.get('status', 'unknown')}")
    else:
        lines.append(f"- **Status:** {stage_state.get('status', state.get('current_run', {}).get('status', 'unknown'))}")
    lines.append("")
    lines.append("## Waiting For")
    lines.append(f"- **Waiting for:** {'human' if stage_def.get('human_gate') and not stage_state.get('gate_passed') else 'agent'}")
    lines.append("")
    lines.append("## Artifacts")
    if artifacts_produced:
        lines.append("### Produced")
        for art in artifacts_produced:
            lines.append(f"- [x] {art}")

    required = [
        interpolate_artifact(str(art), state, resolve_state_path(None))
        for art in stage_def.get("artifacts", [])
    ]
    if required:
        lines.append("### Required")
        for art in required:
            checked = "x" if art in artifacts_produced else " "
            lines.append(f"- [{checked}] {art}")
    lines.append("")
    lines.append("## Next Action")
    lines.append(f"{stage_state.get('status', 'unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("*This file is auto-generated by `scripts/stage_loader.py --action handoff-report`*")

    content = "\n".join(lines)
    project_root = state_file.parents[1]
    handoff_dir = process_package_root(state=state, state_path=state_file, project_root=project_root) / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"lc-handoff-{stage_id}.md"
    handoff_path.write_text(content, encoding="utf-8")

    # Record a structured handoff event in the session trace so benchmark metrics
    # can detect handoffs without regex-parsing the original Bash command.
    lincoln_trace.append_trace_entry(
        state_file,
        "LincolnHandoff",
        {"stage": stage_id},
        0,
        stage=stage_id,
        run_id=state.get("current_run", {}).get("run_id"),
    )

    return str(handoff_path.relative_to(project_root))


def action_update_last_updated(state_file: Path) -> None:
    """Update current_run.last_updated_at and persist state."""
    state = load_state(state_file)
    state["current_run"]["last_updated_at"] = now_iso()
    save_state(state, state_file)


def action_benchmark_report(state_file: Path, trigger: str) -> dict[str, str] | None:
    """Generate a benchmark report for the current process state."""
    from scripts import lincoln_benchmark

    result = lincoln_benchmark.write_benchmark_report(state_file, trigger, PROJECT_ROOT)
    if result is None:
        return None

    def _rel(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)

    return {
        "markdown": _rel(result["markdown"]),
        "json": _rel(result["json"]),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln stage loader")
    parser.add_argument("--stage", help="Stage ID")
    parser.add_argument("--action",
        required=True,
        choices=[
            "load",
            "validate-entry",
            "validate-exit",
            "record-artifacts",
            "approve-gate",
            "append-node",
            "transition-next",
            "recover",
            "status",
            "handoff-report",
            "benchmark-report",
            "update-last-updated",
        ],
    )
    parser.add_argument("--state-file", type=Path, default=None)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--approved-by", default="human-pm", help="Approver name for approve-gate")
    parser.add_argument("--node-id", help="Node ID for append-node")
    parser.add_argument("--status", help="Node status for append-node")
    parser.add_argument("--handoff-file", help="Handoff file path for append-node")
    parser.add_argument("--artifacts", help="Comma-separated artifact paths for append-node")
    parser.add_argument("--trigger", default="manual", help="Trigger type for benchmark-report")
    args = parser.parse_args()

    state_file = resolve_state_path(args.state_file)
    state = load_state(state_file)

    if args.action == "load":
        if not args.stage:
            parser.error("--stage is required for load")
        result = action_load(args.stage, state, state_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action in ("validate-entry", "validate-exit"):
        if not args.stage:
            parser.error("--stage is required for validate-*")
        phase = args.action.split("-")[1]
        return action_validate(args.stage, state, phase, state_file)

    if args.action == "record-artifacts":
        if not args.stage:
            parser.error("--stage is required for record-artifacts")
        action_record_artifacts(args.stage, state, state_file)
        return 0

    if args.action == "approve-gate":
        if not args.stage:
            parser.error("--stage is required for approve-gate")
        return action_approve_gate(args.stage, state, state_file, args.approved_by)

    if args.action == "append-node":
        if not args.node_id:
            parser.error("--node-id is required for append-node")
        if not args.status:
            parser.error("--status is required for append-node")
        stage_id = args.stage or args.node_id
        artifacts = [a.strip() for a in args.artifacts.split(",")] if args.artifacts else None
        return action_append_node(
            stage_id, state, args.node_id, args.status,
            state_file, args.handoff_file, artifacts,
        )

    if args.action == "transition-next":
        if not args.stage:
            parser.error("--stage is required for transition-next")
        action_transition_next(args.stage, state, state_file)
        return 0

    if args.action == "recover":
        result = action_recover(state, state_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action == "status":
        result = action_status(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action == "handoff-report":
        if not args.stage:
            parser.error("--stage is required for handoff-report")
        path = action_handoff_report(args.stage, state, state_file)
        print(f"Handoff report written to: {path}")
        return 0

    if args.action == "update-last-updated":
        action_update_last_updated(state_file)
        return 0

    if args.action == "benchmark-report":
        result = action_benchmark_report(state_file, args.trigger)
        if result is None:
            print("Benchmark report skipped")
        else:
            print(f"Benchmark report written to:\n  {result['markdown']}\n  {result['json']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
