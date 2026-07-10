#!/usr/bin/env python3
"""
Lincoln branch status reporter.

Reports the current Lincoln branch state including stage, status, waiting_for,
loaded context files, required skills, artifacts, and next action.

Usage:
    python scripts/lincoln-status.py [--format json|table|markdown] [--branch <branch>]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Re-use stage_loader helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.stage_loader import (  # noqa: E402
    PROJECT_ROOT,
    STATE_PATH,
    LEGACY_STATE_PATH,
    STAGES_DIR,
    compute_next_stage,
    load_state,
    load_stage_yaml,
    load_workflow,
    load_skill_routing,
    get_stage_skills,
    get_latest_node_for_stage,
    get_variables,
    interpolate_artifact,
    _is_legacy_state,
    now_iso,
    resolve_state_path,
)
from scripts.lincoln_paths import get_process_slug


def get_waiting_for(stage_status: str | None, stage_def: dict[str, Any]) -> str:
    """Determine who/what is being waited for based on stage status."""
    if stage_status == "waiting_for_human":
        return "pm"
    if stage_status == "validation_failed":
        return "agent-fix"
    if stage_status == "in_progress":
        return "agent"
    if stage_status == "completed":
        return "next-role"
    if stage_status == "entry_validating":
        return "agent"
    if stage_status == "not_started":
        # If stage has human_gate and hasn't started, waiting for human to kick it off
        if stage_def.get("human_gate", False):
            return "pm"
        return "agent"
    return "none"


def get_loaded_context(stage_id: str) -> list[str]:
    """Return the path to the stage YAML context file."""
    stage_yaml = STAGES_DIR / f"{stage_id}.yaml"
    if stage_yaml.exists():
        return [str(stage_yaml.relative_to(PROJECT_ROOT))]
    return []


def get_required_skills(stage_id: str) -> dict[str, list[str]]:
    """Read skill routing for required/optional skills for the stage."""
    routing_data = load_skill_routing()
    return get_stage_skills(routing_data, stage_id)


def get_required_artifacts(stage_id: str, state: dict[str, Any] | None = None, state_file: Path | None = None) -> list[str]:
    """Return artifact paths declared in the stage YAML, with variables resolved."""
    try:
        stage = load_stage_yaml(stage_id)
    except Exception:
        return []
    artifacts = stage.get("artifacts", {})
    paths = artifacts.get("required", [])
    return [interpolate_artifact(str(art), state, state_file or resolve_state_path(None)) for art in paths]


def get_next_action(state: dict[str, Any], stage_id: str | None, workflow: dict[str, Any]) -> str:
    """Generate a human-readable one-liner describing the next action."""
    if not stage_id:
        run_status = state.get("current_run", {}).get("status", "unknown")
        if run_status == "completed":
            return "Workflow complete. No further action required."
        return "No active stage. Run recovery to determine resume point."

    if _is_legacy_state(state):
        stage_state = state.get("stages", {}).get(stage_id, {})
        stage_status = stage_state.get("status", "unknown")
    else:
        latest_node = get_latest_node_for_stage(state, stage_id)
        stage_state = latest_node or {}
        stage_status = stage_state.get("status", state.get("current_run", {}).get("status", "unknown"))

    try:
        stage_yaml = load_stage_yaml(stage_id)
    except Exception:
        stage_yaml = {}
    human_gate = stage_yaml.get("human_gate", False)
    waiting_for = get_waiting_for(stage_status, stage_yaml)

    if stage_status == "not_started":
        if human_gate:
            return f"Stage '{stage_id}' not started. Human confirmation required to begin."
        return f"Stage '{stage_id}' ready to start. Run entry validation and begin work."

    if stage_status == "entry_validating":
        return f"Entry validation in progress for stage '{stage_id}'."

    if stage_status == "in_progress":
        if human_gate and not stage_state.get("gate_passed") and not stage_state.get("human_gate_passed"):
            return f"Stage '{stage_id}' in progress. Complete work and await human gate approval."
        return f"Stage '{stage_id}' in progress. Complete work and run exit validation."

    if stage_status == "waiting_for_human":
        return f"Stage '{stage_id}' paused for human review/approval."

    if stage_status == "validation_failed":
        retry = stage_state.get("retry_count", 0)
        return f"Stage '{stage_id}' validation failed (retry {retry}). Fix issues and re-run validation."

    if stage_status == "completed":
        next_stage = compute_next_stage(workflow, stage_id)
        if next_stage:
            return f"Stage '{stage_id}' completed. Proceed to next stage: '{next_stage}'."
        return f"Stage '{stage_id}' completed. This is the final stage."

    return f"Stage '{stage_id}' status: {stage_status}. Waiting for: {waiting_for}."


def compute_metrics(state: dict[str, Any]) -> dict[str, Any]:
    """Compute workflow metrics summary."""
    if _is_legacy_state(state):
        stages = state.get("stages", {})
        total = len(stages)
        completed = sum(1 for s in stages.values() if s.get("status") == "completed")
        failed = sum(1 for s in stages.values() if s.get("status") == "validation_failed")
        waiting_for_human = sum(
            1 for sid, s in stages.items()
            if s.get("status") in ("waiting_for_human", "not_started")
            and _stage_has_human_gate(sid)
        )
        return {
            "total_stages": total,
            "completed": completed,
            "failed": failed,
            "waiting_for_human": waiting_for_human,
        }

    # New schema: metrics based on nodes array
    nodes = state.get("nodes", [])
    total_nodes = len(nodes)
    completed = sum(1 for n in nodes if n.get("status") == "completed")
    failed = sum(1 for n in nodes if n.get("status") == "validation_failed")

    # Count unique stages that have been touched
    touched_stages = set(n.get("stage_id") for n in nodes if n.get("stage_id"))
    total_stages = len(touched_stages)

    # Waiting for human: stages with human_gate where latest node is not completed/gate_passed
    template_name = state.get("workflow", {}).get("template")
    try:
        workflow = load_workflow(template_name)
    except Exception:
        workflow = {"steps": []}

    waiting_for_human = 0
    for stage_id in touched_stages:
        latest = get_latest_node_for_stage(state, stage_id)
        if latest and latest.get("status") in ("not_started", "waiting_for_human"):
            if _stage_has_human_gate(stage_id):
                waiting_for_human += 1
        elif latest and latest.get("status") == "in_progress":
            if _stage_has_human_gate(stage_id) and not latest.get("gate_passed"):
                waiting_for_human += 1

    return {
        "total_stages": total_stages,
        "completed": completed,
        "failed": failed,
        "waiting_for_human": waiting_for_human,
        "total_nodes": total_nodes,
    }


def _stage_has_human_gate(stage_id: str) -> bool:
    """Check if a stage has human_gate enabled by reading stage YAML."""
    try:
        stage = load_stage_yaml(stage_id)
        return stage.get("human_gate", False)
    except Exception:
        return False


def build_status_report(state: dict[str, Any], state_file: Path | None = None) -> dict[str, Any]:
    """Build the full status report dictionary."""
    current_run = state.get("current_run", {})
    stage_id = current_run.get("current_stage")
    template_name = state.get("workflow", {}).get("template") or current_run.get("workflow_template")

    workflow = load_workflow(template_name)

    # Handle sentinel status values that are not real stage IDs
    _stage_id = stage_id
    if stage_id in ("not_started", "completed", "in_progress", "validation_failed", "waiting_for_human", "entry_validating"):
        _stage_id = None

    if _is_legacy_state(state):
        stage_state = state.get("stages", {}).get(stage_id, {}) if stage_id else {}
        stage_status = stage_state.get("status", "unknown")
        entry_checks_passed = stage_state.get("entry_checks_passed")
        exit_checks_passed = stage_state.get("exit_checks_passed")
        human_gate_passed = stage_state.get("human_gate_passed")
        retry_count = stage_state.get("retry_count", 0)
        stage_yaml = {}
    else:
        latest_node = get_latest_node_for_stage(state, _stage_id) if _stage_id else None
        stage_state = latest_node or {}
        stage_status = stage_state.get("status", current_run.get("status", "unknown")) if _stage_id else current_run.get("status", "unknown")
        entry_checks_passed = None
        exit_checks_passed = None
        human_gate_passed = stage_state.get("gate_passed")
        retry_count = 0
        try:
            stage_yaml = load_stage_yaml(_stage_id) if _stage_id else {}
        except Exception:
            stage_yaml = {}

    agent = stage_yaml.get("agent", {}) if stage_yaml else {}
    skills = get_required_skills(_stage_id) if _stage_id else {"required": [], "optional": []}
    artifacts = get_required_artifacts(_stage_id, state, state_file) if _stage_id else []

    resolved_state_file = state_file or resolve_state_path(None)

    return {
        "process_slug": get_process_slug(state, resolved_state_file),
        "state_file": str(resolved_state_file.relative_to(PROJECT_ROOT) if resolved_state_file.is_relative_to(PROJECT_ROOT) else resolved_state_file),
        "branch": current_run.get("branch", "unknown"),
        "run_id": current_run.get("run_id", "unknown"),
        "workflow_template": template_name or "unknown",
        "current_stage": stage_id,
        "previous_stage": current_run.get("previous_stage"),
        "run_status": current_run.get("status", "unknown"),
        "stage_status": stage_status,
        "entry_checks_passed": entry_checks_passed,
        "exit_checks_passed": exit_checks_passed,
        "human_gate_passed": human_gate_passed,
        "retry_count": retry_count,
        "waiting_for": get_waiting_for(stage_status, stage_yaml) if _stage_id else "none",
        "loaded_context": get_loaded_context(_stage_id) if _stage_id else [],
        "required_skills": skills.get("required", []),
        "optional_skills": skills.get("optional", []),
        "required_artifacts": artifacts,
        "primary_agent": agent.get("primary") if _stage_id else None,
        "review_agents": agent.get("reviewers", []) if _stage_id else None,
        "handoff_to": agent.get("handoff_to") if _stage_id else None,
        "next_action": get_next_action(state, _stage_id, workflow),
        "metrics": compute_metrics(state),
    }


def format_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def format_table(report: dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("LINCOLN BRANCH STATUS")
    lines.append("=" * 70)
    lines.append(f"{'Branch:':<25} {report['branch']}")
    lines.append(f"{'Process Package:':<25} {report.get('process_slug', 'unknown')}")
    lines.append(f"{'Run ID:':<25} {report['run_id']}")
    lines.append(f"{'Workflow Template:':<25} {report['workflow_template']}")
    lines.append(f"{'Current Stage:':<25} {report['current_stage'] or '(none)'}")
    lines.append(f"{'Previous Stage:':<25} {report['previous_stage'] or '(none)'}")
    lines.append(f"{'Run Status:':<25} {report['run_status']}")
    lines.append(f"{'Stage Status:':<25} {report['stage_status']}")
    lines.append(f"{'Entry Checks:':<25} {report['entry_checks_passed']}")
    lines.append(f"{'Exit Checks:':<25} {report['exit_checks_passed']}")
    lines.append(f"{'Human Gate:':<25} {report['human_gate_passed']}")
    lines.append(f"{'Retry Count:':<25} {report['retry_count']}")
    lines.append(f"{'Waiting For:':<25} {report['waiting_for']}")
    lines.append(f"{'Primary Agent:':<25} {report.get('primary_agent') or '(none)'}")
    lines.append(f"{'Review Agents:':<25} {', '.join(report.get('review_agents') or []) or '(none)'}")
    lines.append(f"{'Handoff To:':<25} {report.get('handoff_to') or '(none)'}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("LOADED CONTEXT")
    lines.append("-" * 70)
    for ctx in report["loaded_context"]:
        lines.append(f"  - {ctx}")
    if not report["loaded_context"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("REQUIRED SKILLS")
    lines.append("-" * 70)
    for skill in report["required_skills"]:
        lines.append(f"  [R] {skill}")
    for skill in report.get("optional_skills", []):
        lines.append(f"  [O] {skill}")
    if not report["required_skills"] and not report.get("optional_skills"):
        lines.append("  (none configured)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("REQUIRED ARTIFACTS")
    lines.append("-" * 70)
    for art in report["required_artifacts"]:
        lines.append(f"  - {art}")
    if not report["required_artifacts"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("NEXT ACTION")
    lines.append("-" * 70)
    lines.append(f"  {report['next_action']}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("METRICS")
    lines.append("-" * 70)
    m = report["metrics"]
    lines.append(f"  Total stages:        {m['total_stages']}")
    lines.append(f"  Completed:           {m['completed']}")
    lines.append(f"  Failed:              {m['failed']}")
    lines.append(f"  Waiting for human:   {m['waiting_for_human']}")
    if "total_nodes" in m:
        lines.append(f"  Total nodes:         {m['total_nodes']}")
    lines.append("=" * 70)
    return "\n".join(lines)


def format_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append("# Lincoln Branch Status")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Branch | `{report['branch']}` |")
    lines.append(f"| Process Package | `{report.get('process_slug', 'unknown')}` |")
    lines.append(f"| Run ID | `{report['run_id']}` |")
    lines.append(f"| Workflow Template | `{report['workflow_template']}` |")
    lines.append(f"| Current Stage | `{report['current_stage'] or 'none'}` |")
    lines.append(f"| Previous Stage | `{report['previous_stage'] or 'none'}` |")
    lines.append(f"| Run Status | `{report['run_status']}` |")
    lines.append(f"| Stage Status | `{report['stage_status']}` |")
    lines.append(f"| Entry Checks Passed | `{report['entry_checks_passed']}` |")
    lines.append(f"| Exit Checks Passed | `{report['exit_checks_passed']}` |")
    lines.append(f"| Human Gate Passed | `{report['human_gate_passed']}` |")
    lines.append(f"| Retry Count | `{report['retry_count']}` |")
    lines.append(f"| Waiting For | `{report['waiting_for']}` |")
    lines.append(f"| Primary Agent | `{report.get('primary_agent') or 'none'}` |")
    lines.append(f"| Review Agents | `{', '.join(report.get('review_agents') or []) or 'none'}` |")
    lines.append(f"| Handoff To | `{report.get('handoff_to') or 'none'}` |")
    lines.append("")
    lines.append("## Loaded Context")
    if report["loaded_context"]:
        for ctx in report["loaded_context"]:
            lines.append(f"- `{ctx}`")
    else:
        lines.append("_No context files found._")
    lines.append("")
    lines.append("## Required Skills")
    if report["required_skills"]:
        lines.append("**Required:**")
        for skill in report["required_skills"]:
            lines.append(f"- `{skill}`")
    if report.get("optional_skills"):
        lines.append("**Optional:**")
        for skill in report["optional_skills"]:
            lines.append(f"- `{skill}`")
    if not report["required_skills"] and not report.get("optional_skills"):
        lines.append("_No skills configured._")
    lines.append("")
    lines.append("## Required Artifacts")
    if report["required_artifacts"]:
        for art in report["required_artifacts"]:
            lines.append(f"- `{art}`")
    else:
        lines.append("_No artifacts required._")
    lines.append("")
    lines.append("## Next Action")
    lines.append(f"> {report['next_action']}")
    lines.append("")
    lines.append("## Metrics")
    m = report["metrics"]
    lines.append(f"- **Total stages:** {m['total_stages']}")
    lines.append(f"- **Completed:** {m['completed']}")
    lines.append(f"- **Failed:** {m['failed']}")
    lines.append(f"- **Waiting for human:** {m['waiting_for_human']}")
    if "total_nodes" in m:
        lines.append(f"- **Total nodes:** {m['total_nodes']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln branch status reporter")
    parser.add_argument(
        "--format",
        choices=["json", "table", "markdown"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--branch",
        help="Branch name (default: read from workflow-stage.yaml)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to workflow-stage.yaml",
    )
    args = parser.parse_args()

    state_file = resolve_state_path(args.state_file)
    state = load_state(state_file)

    # If --branch is specified but differs from state, note it but still report state
    report = build_status_report(state, state_file)
    report["state_file"] = str(state_file.relative_to(PROJECT_ROOT) if state_file.is_relative_to(PROJECT_ROOT) else state_file)
    if args.branch and report["branch"] != args.branch:
        report["_note"] = f"Requested branch '{args.branch}' but state shows '{report['branch']}'"

    if args.format == "json":
        print(format_json(report))
    elif args.format == "table":
        print(format_table(report))
    elif args.format == "markdown":
        print(format_markdown(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
