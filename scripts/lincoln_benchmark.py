#!/usr/bin/env python3
"""Lincoln benchmark report generator.

Computes L1-L5 metrics from session trace and workflow state, evaluates them
against scenario-specific thresholds, and writes a Markdown + JSON report pair
to the issue package's `benchmark/` directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from scripts.lincoln_paths import (  # noqa: E402
    get_process_slug,
    load_yaml,
    process_package_root,
)

REPORT_SCHEMA_VERSION = "1.0.0"
SESSION_STOP_DEDUP_SECONDS = 5

SCENARIO_MAP = {
    "interview-to-knowledge": "S1",
    "existing-project-iteration": "S2",
    "bug-fix": "S3",
    "design-spike": "S4",
    "oss-first-design": "S5",
}

TEST_COMMAND_RE = re.compile(
    r"\b(pytest|npm test|yarn test|cargo test|go test|vitest|jest)\b",
    re.IGNORECASE,
)

STATIC_CHECK_RE = re.compile(r"\bstatic-check\.sh\b")

THRESHOLDS: dict[str, dict[str, dict[str, Any]]] = {
    "S1": {
        "time_to_merge_seconds": {"green": 3 * 24 * 3600, "yellow": 7 * 24 * 3600, "direction": "minimize"},
        "human_gate_wait_seconds": {"green": 4 * 3600, "yellow": 8 * 3600, "direction": "minimize"},
        "human_gate_pass_rate": {"green": 1.0, "yellow": 0.8, "direction": "maximize"},
        "requirements_clarity_score": {"green": 4, "yellow": 3, "direction": "maximize"},
        "static_check_pass": {"green": True, "yellow": None, "direction": "maximize"},
        "pr_size": {"green": 400, "yellow": 800, "direction": "minimize"},
    },
    "S2": {
        "build_codebase_knowledge_duration_seconds": {"green": 3600, "yellow": 2 * 3600, "direction": "minimize"},
        "unique_files_touched_ratio": {"green": 1.0, "yellow": 1.5, "direction": "minimize"},
        "pr_size": {"green": 300, "yellow": 600, "direction": "minimize"},
    },
    "S3": {
        "time_to_pr_seconds": {"green": 3600, "yellow": 4 * 3600, "direction": "minimize"},
        "retry_count": {"green": 1, "yellow": 3, "direction": "minimize"},
        "test_runs": {"green": 2, "yellow": 1, "direction": "maximize"},
        "pr_size": {"green": 100, "yellow": 300, "direction": "minimize"},
    },
    "S4": {
        "time_to_first_handoff": {"green": 30 * 60, "yellow": 2 * 3600, "direction": "minimize"},
        "explored_options_count": {"green": 2, "yellow": 1, "direction": "maximize"},
        "design_doc_completeness": {"green": 1.0, "yellow": 0.8, "direction": "maximize"},
    },
    "S5": {
        "time_to_first_handoff": {"green": 3600, "yellow": 4 * 3600, "direction": "minimize"},
        "oss_candidates_evaluated": {"green": 3, "yellow": 1, "direction": "maximize"},
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_stage_manifest(project_root: Path = _PROJECT_ROOT) -> dict[str, Any]:
    path = project_root / ".claude" / "stages" / "stage-manifest.yaml"
    if not path.exists():
        return {}
    return load_yaml(path) or {}


def _stage_primary_agents(manifest: dict[str, Any]) -> dict[str, str]:
    return {
        s.get("id"): s.get("primary_agent", "")
        for s in manifest.get("stages", [])
        if s.get("id")
    }


def detect_scenario(state: dict[str, Any]) -> str:
    template = (
        state.get("workflow", {}).get("template")
        or state.get("current_run", {}).get("workflow_template")
        or ""
    )
    return SCENARIO_MAP.get(template, "S1")


def load_trace(process_root: Path, process_slug: str) -> list[dict[str, Any]]:
    trace_dir = process_root / process_slug / ".trace"
    if not trace_dir.exists():
        return []

    entries: dict[tuple[str, str], dict[str, Any]] = {}
    for trace_file in sorted(trace_dir.glob("lincoln-trace*.jsonl")):
        try:
            text = trace_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            key = (str(entry.get("run_id", "")), str(entry.get("sequence_id", "")))
            if not key[1]:
                continue
            entries[key] = entry

    return sorted(entries.values(), key=lambda e: e.get("timestamp", ""))


def _stage_order_from_trace(trace: list[dict[str, Any]]) -> list[str]:
    order: list[str] = []
    for entry in trace:
        stage = entry.get("stage")
        if stage and (not order or order[-1] != stage):
            order.append(stage)
    return order


def _lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[len(b)]


def _workflow_steps(state: dict[str, Any]) -> list[dict[str, Any]]:
    template = (
        state.get("workflow", {}).get("template")
        or state.get("current_run", {}).get("workflow_template")
    )
    if not template:
        return []
    from scripts.stage_loader import load_workflow

    try:
        workflow = load_workflow(template)
    except Exception:
        return []
    return workflow.get("steps", [])


def _stage_durations(trace: list[dict[str, Any]]) -> dict[str, int]:
    durations: dict[str, list[datetime]] = {}
    for entry in trace:
        stage = entry.get("stage")
        ts = entry.get("timestamp")
        if not stage or not ts:
            continue
        try:
            dt = _parse_iso(ts)
        except Exception:
            continue
        durations.setdefault(stage, []).append(dt)
    return {
        stage: int((max(times) - min(times)).total_seconds())
        for stage, times in durations.items()
        if len(times) >= 2
    }


def _node_durations(state: dict[str, Any]) -> dict[str, int]:
    durations: dict[str, int] = {}
    for node in state.get("nodes", []):
        started = node.get("started_at")
        completed = node.get("completed_at")
        if started and completed:
            try:
                durations[str(node.get("stage_id"))] = int(
                    (_parse_iso(completed) - _parse_iso(started)).total_seconds()
                )
            except Exception:
                pass
    return durations


def _interpolate_placeholders(value: str, variables: dict[str, Any]) -> str:
    return re.sub(r"\{([a-zA-Z0-9_-]+)\}", lambda m: str(variables.get(m.group(1), m.group(0))), value)


def _artifact_paths_for_stage(
    workflow_steps: list[dict[str, Any]],
    stage_id: str,
    variables: dict[str, Any],
) -> list[str]:
    for step in workflow_steps:
        if step.get("id") == stage_id:
            artifacts = step.get("artifacts", [])
            return [_interpolate_placeholders(str(a), variables) for a in artifacts]
    return []


def _artifact_completion_rate(
    stage_id: str | None,
    workflow_steps: list[dict[str, Any]],
    variables: dict[str, Any],
    process_root: Path,
) -> float:
    if not stage_id:
        return 0.0
    paths = _artifact_paths_for_stage(workflow_steps, stage_id, variables)
    if not paths:
        return 1.0
    existing = sum(1 for p in paths if (process_root / p).exists())
    return round(existing / len(paths), 2)


def _requirements_clarity_score(process_root: Path, process_slug: str, variables: dict[str, Any]) -> int:
    session_id = variables.get("session_id", "")
    candidates = [
        process_root / process_slug / "requirements" / str(session_id) / "requirements.md",
        process_root / process_slug / "requirements" / "requirements.md",
    ]
    req_path = next((p for p in candidates if p.exists()), None)
    if not req_path:
        return 0
    text = req_path.read_text(encoding="utf-8").lower()
    checks = [
        "background" in text or "背景" in text,
        "problem" in text or "问题" in text,
        "solution" in text or "方案" in text,
        "acceptance" in text or "验收" in text,
    ]
    return sum(checks)


def _design_doc_completeness(
    state: dict[str, Any],
    workflow_steps: list[dict[str, Any]],
    variables: dict[str, Any],
    process_root: Path,
    process_slug: str,
) -> float:
    design_id = variables.get("design_id", "")
    if not design_id:
        return 0.0
    stage_id = "product-design-docs"
    artifacts = _artifact_paths_for_stage(workflow_steps, stage_id, variables)
    if not artifacts:
        # Fallback to known design docs if the template does not declare them.
        base = process_root / process_slug / "designs" / str(design_id)
        artifacts = [
            str(base / "design-review.md"),
            str(base / "scenarios.md"),
            str(base / "feature-catalog.md"),
            str(base / "data-model.md"),
            str(base / "flows.md"),
            str(base / "feasibility.md"),
        ]
    existing = sum(1 for p in artifacts if (process_root / p).exists())
    return round(existing / len(artifacts), 2) if artifacts else 0.0


def _tdd_plan_red_green_refactor(
    process_root: Path, process_slug: str, variables: dict[str, Any]
) -> dict[str, bool]:
    design_id = variables.get("design_id", "")
    path = process_root / process_slug / "designs" / str(design_id) / "tdd-plan.md"
    result = {"red": False, "green": False, "refactor": False}
    if not path.exists():
        return result
    text = path.read_text(encoding="utf-8").lower()
    result["red"] = bool(re.search(r"\bred\b|\bred phase\b|\bred-green", text))
    result["green"] = bool(re.search(r"\bgreen\b|\bgreen phase\b", text))
    result["refactor"] = bool(re.search(r"\brefactor\b|\brefactor phase\b", text))
    return result


def _openspec_task_count(
    process_root: Path, process_slug: str, variables: dict[str, Any]
) -> int:
    change_name = variables.get("change_name", "") or ""
    path = process_root / process_slug / "openspec" / "changes" / str(change_name) / "tasks.md"
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*-\s+\[.\]", text, re.MULTILINE))


def _static_check_pass(trace: list[dict[str, Any]]) -> bool | None:
    found = None
    for entry in trace:
        if entry.get("category") != "bash":
            continue
        command = str(entry.get("args_summary", {}).get("command", ""))
        if STATIC_CHECK_RE.search(command):
            if entry.get("exit_code") == 0:
                return True
            found = False
    return found


def _test_coverage(trace: list[dict[str, Any]]) -> float | None:
    # Future: parse pytest --cov output. For now we can only detect coverage runs.
    for entry in trace:
        if entry.get("category") != "bash":
            continue
        command = str(entry.get("args_summary", {}).get("command", ""))
        if "--cov" in command:
            return None  # pending: need structured output
    return None


def _git_diff_stat(process_root: Path, base: str = "main") -> int:
    try:
        output = subprocess.check_output(
            ["git", "diff", f"{base}...HEAD", "--stat"],
            cwd=process_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return 0
    match = re.search(r"(\d+)\s+files?\s+changed(?:,\s+(\d+)\s+insertions?\(\+\))?(?:,\s+(\d+)\s+deletions?\(-\))?", output)
    if not match:
        return 0
    return sum(int(g or 0) for g in match.groups()[1:])


def _run_audit(process_root: Path) -> dict[str, int] | None:
    audit_script = process_root / "scripts" / "lincoln-audit.py"
    if not audit_script.exists():
        return None
    try:
        output = subprocess.check_output(
            [sys.executable, str(audit_script), "--format", "json"],
            cwd=process_root,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
    except Exception:
        return None
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return None
    results = data.get("results", data) if isinstance(data, dict) else []
    counts = Counter()
    for item in results:
        status = str(item.get("status", "")).upper()
        if status in ("PASS", "WARN", "FAIL"):
            counts[status] += 1
    return dict(counts) if counts else None


def _pr_event_timestamps(state: dict[str, Any]) -> dict[str, str]:
    timestamps: dict[str, str] = {}
    for node in state.get("nodes", []):
        status = node.get("status")
        ts = node.get("started_at") or node.get("completed_at") or node.get("timestamp")
        if status in ("pr_submitted", "merged") and ts:
            timestamps[status] = ts
    return timestamps


def compute_metrics(
    trace: list[dict[str, Any]],
    state: dict[str, Any],
    scenario: str,
    process_root: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    confidence: dict[str, str] = {}
    variables = state.get("current_run", {}).get("variables", {})
    process_slug = get_process_slug(state, None)
    workflow_steps = _workflow_steps(state)
    trace = sorted(trace, key=lambda e: e.get("timestamp", ""))
    stage_order = _stage_order_from_trace(trace)
    manifest = _load_stage_manifest(process_root)
    primary_agents = _stage_primary_agents(manifest)

    # L1 Session activity
    if len(trace) >= 2:
        try:
            start = _parse_iso(trace[0]["timestamp"])
            end = _parse_iso(trace[-1]["timestamp"])
            session_duration_seconds = int((end - start).total_seconds())
        except Exception:
            session_duration_seconds = 0
    else:
        session_duration_seconds = 0
    confidence["session_duration_seconds"] = "exact" if len(trace) >= 2 else "estimated"

    tool_counts = Counter(e.get("category", "other") for e in trace)
    total_tool_calls = len(trace)

    unique_skills = sorted({
        e.get("target", "")
        for e in trace
        if e.get("category") == "skill" and e.get("target")
    })

    unique_files = set()
    for e in trace:
        if e.get("category") in ("read", "write", "edit"):
            target = e.get("target", "")
            if target:
                unique_files.add(target)

    error_count = sum(1 for e in trace if e.get("exit_code", 0) != 0)

    retry_count = 0
    prev: dict[str, Any] | None = None
    for e in trace:
        if (
            prev
            and prev.get("exit_code", 0) != 0
            and prev.get("tool") == e.get("tool")
            and prev.get("target") == e.get("target")
        ):
            retry_count += 1
        prev = e

    test_runs = sum(
        1
        for e in trace
        if e.get("category") == "bash"
        and TEST_COMMAND_RE.search(
            str(e.get("args_summary", {}).get("command", ""))
            or str(e.get("target", ""))
        )
    )

    session = {
        "session_duration_seconds": session_duration_seconds,
        "trace_line_count": len(trace),
        "total_tool_calls": total_tool_calls,
        "tool_calls_by_category": dict(tool_counts),
        "unique_skills": unique_skills,
        "unique_files_touched": len(unique_files),
        "test_runs": test_runs,
        "error_count": error_count,
        "retry_count": retry_count,
    }
    for key in session:
        if key not in confidence:
            confidence[key] = "exact"

    # L2 Workflow progress
    stage_transition_count = max(0, len(stage_order) - 1)
    durations_trace = _stage_durations(trace)
    durations_node = _node_durations(state)
    stage_durations = {k: durations_trace.get(k, durations_node.get(k, 0)) for k in set(durations_trace) | set(durations_node)}

    nodes = state.get("nodes", [])
    total_nodes = len(nodes)
    completed_nodes = sum(1 for n in nodes if n.get("status") == "completed")
    failed_nodes = sum(1 for n in nodes if n.get("status") == "validation_failed")
    stage_completion_rate = round(completed_nodes / total_nodes, 2) if total_nodes else 0.0

    stage_rework_count = 0
    seen: set[str] = set()
    for stage in stage_order:
        if stage in seen:
            stage_rework_count += 1
        seen.add(stage)

    current_stage = state.get("current_run", {}).get("current_stage")
    artifact_completion_rate = _artifact_completion_rate(
        current_stage, workflow_steps, variables, process_root
    )

    template_ids = [s.get("id") for s in workflow_steps if s.get("id")]
    lcs = _lcs_length(stage_order, template_ids)
    workflow_adherence_score = round(lcs / len(template_ids), 2) if template_ids else 1.0

    human_gate_stages = {
        s.get("id")
        for s in workflow_steps
        if s.get("human_gate") and s.get("id") in stage_order
    }
    human_gate_count = len(human_gate_stages)
    passed_human_gate = 0
    for stage_id in human_gate_stages:
        node = None
        if _is_legacy_state(state):
            node = state.get("stages", {}).get(stage_id, {})
        else:
            from scripts.stage_loader import get_latest_node_for_stage
            node = get_latest_node_for_stage(state, stage_id)
        if node and (
            node.get("status") == "completed"
            or node.get("gate_passed")
            or node.get("human_gate_passed")
        ):
            passed_human_gate += 1
    human_gate_pass_rate = round(passed_human_gate / human_gate_count, 2) if human_gate_count else 1.0
    human_gate_wait_seconds = sum(
        stage_durations.get(s, 0) for s in human_gate_stages
    )

    workflow = {
        "stage_transition_count": stage_transition_count,
        "stage_durations": stage_durations,
        "stage_completion_rate": stage_completion_rate,
        "stage_rework_count": stage_rework_count,
        "artifact_completion_rate": artifact_completion_rate,
        "validation_failure_count": failed_nodes,
        "workflow_adherence_score": workflow_adherence_score,
        "human_gate_count": human_gate_count,
        "human_gate_wait_seconds": human_gate_wait_seconds,
        "human_gate_pass_rate": human_gate_pass_rate,
    }
    confidence["stage_durations"] = "estimated"
    confidence["human_gate_wait_seconds"] = "estimated"
    confidence["artifact_completion_rate"] = "exact"
    confidence["workflow_adherence_score"] = "exact"

    # L3 Collaboration
    handoff_count = sum(
        1
        for e in trace
        if e.get("category") == "bash"
        and "--action handoff-report" in (
            str(e.get("args_summary", {}).get("command", ""))
            or str(e.get("target", ""))
        )
    )

    agent_switches = 0
    prev_stage: str | None = None
    for stage in stage_order:
        if prev_stage and primary_agents.get(prev_stage) and primary_agents.get(stage):
            if primary_agents[prev_stage] != primary_agents[stage]:
                agent_switches += 1
        prev_stage = stage

    pm_turns = human_gate_count

    time_to_first_handoff = 0
    if trace and handoff_count:
        first_handoff_ts = next(
            (
                e.get("timestamp")
                for e in trace
                if e.get("category") == "bash"
                and "--action handoff-report" in (
                    str(e.get("args_summary", {}).get("command", ""))
                    or str(e.get("target", ""))
                )
            ),
            None,
        )
        if first_handoff_ts:
            try:
                time_to_first_handoff = int(
                    (_parse_iso(first_handoff_ts) - _parse_iso(trace[0]["timestamp"])).total_seconds()
                )
            except Exception:
                time_to_first_handoff = 0

    collaboration = {
        "handoff_count": handoff_count,
        "agent_switches": agent_switches,
        "pm_turns": pm_turns,
        "time_to_first_handoff": time_to_first_handoff,
    }
    confidence["agent_switches"] = "exact" if primary_agents else "pending"
    confidence["pm_turns"] = "estimated"
    confidence["time_to_first_handoff"] = "exact" if handoff_count else "estimated"

    # L4 Quality
    requirements_score = _requirements_clarity_score(process_root, process_slug, variables)
    design_completeness = _design_doc_completeness(
        state, workflow_steps, variables, process_root, process_slug
    )
    tdd_phases = _tdd_plan_red_green_refactor(process_root, process_slug, variables)
    openspec_count = _openspec_task_count(process_root, process_slug, variables)
    static_pass = _static_check_pass(trace)
    coverage = _test_coverage(trace)
    pr_size = _git_diff_stat(process_root)
    audit_counts = _run_audit(process_root)
    code_review_calls = sum(
        1
        for e in trace
        if e.get("category") == "skill" and "code-review" in str(e.get("target", ""))
    )

    quality = {
        "requirements_clarity_score": requirements_score,
        "design_doc_completeness": design_completeness,
        "tdd_plan_red_green_refactor": tdd_phases,
        "openspec_task_count": openspec_count,
        "static_check_pass": static_pass,
        "test_coverage": coverage,
        "pr_size": pr_size,
        "audit_score": audit_counts,
        "code_review_calls": code_review_calls,
    }
    confidence["test_coverage"] = "pending"
    confidence["audit_score"] = "exact" if audit_counts is not None else "pending"
    confidence["pr_size"] = "exact" if pr_size > 0 else "estimated"

    # L5 Outcome
    pr_timestamps = _pr_event_timestamps(state)
    pr_submitted_ts = pr_timestamps.get("pr_submitted")
    merged_ts = pr_timestamps.get("merged")
    pr_merged = bool(merged_ts) or any(
        n.get("status") == "merged" for n in state.get("nodes", [])
    )
    pr_merge_latency_seconds = 0
    if pr_submitted_ts and merged_ts:
        try:
            pr_merge_latency_seconds = int(
                (_parse_iso(merged_ts) - _parse_iso(pr_submitted_ts)).total_seconds()
            )
        except Exception:
            pr_merge_latency_seconds = 0

    first_clarify_ts = next(
        (e.get("timestamp") for e in trace if e.get("stage") == "clarify"),
        trace[0].get("timestamp") if trace else None,
    )
    first_pr_ts = next(
        (
            e.get("timestamp")
            for e in trace
            if e.get("tool") == "mcp__plugin_ecc_github__create_pull_request"
        ),
        None,
    )
    time_to_pr_seconds = 0
    if first_clarify_ts and first_pr_ts:
        try:
            time_to_pr_seconds = int(
                (_parse_iso(first_pr_ts) - _parse_iso(first_clarify_ts)).total_seconds()
            )
        except Exception:
            time_to_pr_seconds = 0

    time_to_merge_seconds = 0
    if first_clarify_ts and merged_ts:
        try:
            time_to_merge_seconds = int(
                (_parse_iso(merged_ts) - _parse_iso(first_clarify_ts)).total_seconds()
            )
        except Exception:
            time_to_merge_seconds = 0

    outcome = {
        "issue_closed": None,
        "pr_merged": pr_merged,
        "pr_merge_latency_seconds": pr_merge_latency_seconds,
        "knowledge_synced": None,
        "time_to_pr_seconds": time_to_pr_seconds,
        "time_to_merge_seconds": time_to_merge_seconds,
    }
    confidence["issue_closed"] = "pending"
    confidence["knowledge_synced"] = "pending"
    confidence["pr_merge_latency_seconds"] = "exact" if merged_ts else "pending"

    metrics = {
        "session": session,
        "workflow": workflow,
        "collaboration": collaboration,
        "quality": quality,
        "outcome": outcome,
    }
    return metrics, confidence


def _is_legacy_state(state: dict[str, Any]) -> bool:
    return "stages" in state and "nodes" not in state


def evaluate_against_thresholds(metrics: dict[str, Any], scenario: str) -> dict[str, Any]:
    evaluation: dict[str, Any] = {}
    thresholds = THRESHOLDS.get(scenario, {})

    flat: dict[str, Any] = {}
    for group in metrics.values():
        if isinstance(group, dict):
            for key, value in group.items():
                flat[key] = value

    for metric, cfg in thresholds.items():
        value = flat.get(metric)
        if value is None:
            continue
        green = cfg.get("green")
        yellow = cfg.get("yellow")
        direction = cfg.get("direction", "minimize")
        status = "unknown"
        if isinstance(green, bool):
            status = "green" if value == green else "red"
        elif isinstance(green, (int, float)):
            if direction == "maximize":
                if value >= green:
                    status = "green"
                elif yellow is not None and value >= yellow:
                    status = "yellow"
                else:
                    status = "red"
            else:
                if yellow is None:
                    status = "green" if value <= green else "red"
                else:
                    if value <= green:
                        status = "green"
                    elif value <= yellow:
                        status = "yellow"
                    else:
                        status = "red"
        evaluation[metric] = {"value": value, "threshold": cfg, "status": status}

    # Boolean/structured metrics not in thresholds but worth surfacing
    if flat.get("tdd_plan_red_green_refactor"):
        phases = flat["tdd_plan_red_green_refactor"]
        passed = sum(1 for v in phases.values() if v)
        evaluation["tdd_plan_red_green_refactor"] = {
            "value": f"{passed}/3",
            "threshold": "3/3 phases",
            "status": "green" if passed == 3 else "yellow" if passed == 2 else "red",
        }

    return evaluation


def build_markdown_report(
    report_id: str,
    scenario: str,
    trigger: str,
    metrics: dict[str, Any],
    confidence: dict[str, str],
    evaluation: dict[str, Any],
    state: dict[str, Any],
    trace_files: list[str],
    generated_at: str,
) -> str:
    run = state.get("current_run", {})
    lines = [
        "# Lincoln Benchmark Report",
        "",
        f"- **Report ID:** `{report_id}`",
        f"- **Scenario:** `{scenario}`",
        f"- **Trigger:** `{trigger}`",
        f"- **Generated at:** {generated_at}",
        f"- **Process:** {run.get('variables', {}).get('process_slug', 'unknown')}",
        f"- **Current stage:** {run.get('current_stage', 'unknown')}",
        f"- **Workflow template:** {state.get('workflow', {}).get('template', 'unknown')}",
        "",
        "## Executive Summary",
        "",
    ]

    if evaluation:
        red = [m for m, v in evaluation.items() if v.get("status") == "red"]
        yellow = [m for m, v in evaluation.items() if v.get("status") == "yellow"]
        green = [m for m, v in evaluation.items() if v.get("status") == "green"]
        lines.append(f"- Green: {len(green)}, Yellow: {len(yellow)}, Red: {len(red)}")
        if red:
            lines.append(f"- Red flags: {', '.join(red)}")
        if yellow:
            lines.append(f"- Watch items: {', '.join(yellow)}")
    else:
        lines.append("- No threshold evaluation available for this scenario yet.")
    lines.append("")

    for title, group_key in [
        ("L1 Session Activity", "session"),
        ("L2 Workflow Progress", "workflow"),
        ("L3 Human-AI Collaboration", "collaboration"),
        ("L4 Output Quality", "quality"),
        ("L5 Business Outcome", "outcome"),
    ]:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Metric | Value | Confidence |")
        lines.append("|--------|-------|------------|")
        group = metrics.get(group_key, {})
        for key, value in group.items():
            conf = confidence.get(key, "exact")
            if isinstance(value, dict):
                value_str = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, list):
                value_str = ", ".join(str(v) for v in value) or "—"
            elif value is None:
                value_str = "—"
            else:
                value_str = str(value)
            lines.append(f"| `{key}` | {value_str} | {conf} |")
        lines.append("")

    if evaluation:
        lines.append("## Threshold Evaluation")
        lines.append("")
        lines.append("| Metric | Value | Status |")
        lines.append("|--------|-------|--------|")
        for metric, result in evaluation.items():
            status = result.get("status", "unknown")
            lines.append(f"| `{metric}` | {result.get('value')} | {status} |")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    recs = _generate_recommendations(metrics, evaluation)
    if recs:
        for rec in recs:
            lines.append(f"- {rec}")
    else:
        lines.append("- No automated recommendations.")
    lines.append("")

    lines.append("## Data Sources")
    lines.append("")
    for tf in trace_files:
        lines.append(f"- `{tf}`")
    lines.append("")

    return "\n".join(lines)


def _generate_recommendations(
    metrics: dict[str, Any], evaluation: dict[str, Any]
) -> list[str]:
    recs: list[str] = []
    session = metrics.get("session", {})
    workflow = metrics.get("workflow", {})
    quality = metrics.get("quality", {})

    if evaluation.get("retry_count", {}).get("status") == "red":
        recs.append("High retry count detected; investigate prompt stability or environment flakiness.")
    if evaluation.get("test_runs", {}).get("status") == "red":
        recs.append("Few test runs recorded; ensure TDD red/green/refactor loop is visible in trace.")
    if evaluation.get("pr_size", {}).get("status") == "red":
        recs.append("PR size is large; consider splitting the change into smaller reviewable units.")
    if workflow.get("stage_rework_count", 0) > 2:
        recs.append("Frequent stage rework detected; clarify exit criteria before progressing.")
    if quality.get("static_check_pass") is False:
        recs.append("Static checks failed; fix lint/type/test issues before handoff.")
    if session.get("error_count", 0) > 5:
        recs.append("Elevated tool error count; review recent failures for systemic issues.")
    return recs


def write_benchmark_report(
    state_file: Path,
    trigger: str,
    project_root: Path = _PROJECT_ROOT,
) -> dict[str, Path | None] | None:
    from scripts.stage_loader import load_state

    state = load_state(state_file)
    process_slug = get_process_slug(state, state_file)
    process_dir = project_root / process_slug
    benchmark_dir = process_dir / "benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    # Session-stop dedup: skip if a session_stop report was written very recently.
    if trigger == "session_stop":
        latest = 0.0
        for existing in benchmark_dir.glob("lincoln-benchmark-session_stop-*.json"):
            try:
                mtime = existing.stat().st_mtime
                if mtime > latest:
                    latest = mtime
            except Exception:
                pass
        if latest and (datetime.now(timezone.utc).timestamp() - latest) < SESSION_STOP_DEDUP_SECONDS:
            return None

    scenario = detect_scenario(state)
    trace = load_trace(project_root, process_slug)
    metrics, confidence = compute_metrics(trace, state, scenario, project_root)
    evaluation = evaluate_against_thresholds(metrics, scenario)
    report_id = uuid.uuid4().hex
    generated_at = _now()

    trace_files = sorted(
        str(p.relative_to(project_root))
        for p in (process_dir / ".trace").glob("lincoln-trace*.jsonl")
        if p.exists()
    )

    metadata = {
        "process_slug": process_slug,
        "run_id": state.get("current_run", {}).get("run_id", "unknown"),
        "branch": state.get("current_run", {}).get("branch", "unknown"),
        "issue_number": str(state.get("current_run", {}).get("issue_number", "")),
        "linear_id": "LEW-18",
        "current_stage": state.get("current_run", {}).get("current_stage", "unknown"),
        "trace_files": trace_files,
        "workflow_template": state.get("workflow", {}).get("template", "unknown"),
    }

    payload = {
        "report_id": report_id,
        "schema_version": REPORT_SCHEMA_VERSION,
        "scenario": scenario,
        "trigger": trigger,
        "generated_at": generated_at,
        "metadata": metadata,
        "metrics": metrics,
        "confidence": confidence,
        "evaluation": evaluation,
    }

    timestamp = generated_at.replace(":", "").replace("-", "").replace("T", "-")[:15]
    md_path = benchmark_dir / f"lincoln-benchmark-{trigger}-{timestamp}.md"
    json_path = benchmark_dir / f"lincoln-benchmark-{trigger}-{timestamp}.json"

    markdown = build_markdown_report(
        report_id, scenario, trigger, metrics, confidence, evaluation, state, trace_files, generated_at
    )

    _atomic_write(md_path, markdown.encode("utf-8"))
    _atomic_write(json_path, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))

    return {"markdown": md_path, "json": json_path}


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-lincoln-benchmark-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Lincoln benchmark report")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument(
        "--trigger",
        choices=["handoff", "pr_created", "pr_merged", "session_stop", "manual"],
        default="manual",
    )
    parser.add_argument("--project-root", type=Path, default=_PROJECT_ROOT)
    args = parser.parse_args(argv)

    result = write_benchmark_report(args.state_file, args.trigger, args.project_root)
    if result is None:
        print("Benchmark report skipped (recent session_stop report exists)")
        return 0
    print(f"Benchmark report written to:\n  {result['markdown']}\n  {result['json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
