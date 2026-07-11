#!/usr/bin/env python3
"""Metric computation for Lincoln benchmark reports."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.lincoln_paths import (  # noqa: E402
    get_process_slug,
    load_yaml,
)

TEST_COMMAND_RE = re.compile(
    r"\b(pytest|npm test|yarn test|cargo test|go test|vitest|jest)\b",
    re.IGNORECASE,
)

STATIC_CHECK_RE = re.compile(r"\bstatic-check\.sh\b")


def _safe_path_component(value: Any) -> str:
    """Sanitize a variable used as a path component to prevent traversal."""
    text = re.sub(r"[\\/]", "-", str(value))
    parts = [part for part in text.split("-") if part and part != "." and part != ".."]
    return "-".join(parts)


def _safe_variables(variables: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of variables with every value sanitized for path interpolation."""
    return {key: _safe_path_component(value) for key, value in variables.items()}


def _is_legacy_state(state: dict[str, Any]) -> bool:
    return "stages" in state and "nodes" not in state


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_stage_manifest(project_root: Path) -> dict[str, Any]:
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


def load_trace(process_root: Path, process_slug: str) -> list[dict[str, Any]]:
    trace_dir = process_root / process_slug / ".trace"
    if not trace_dir.exists():
        return []

    entries: dict[tuple[str, str], dict[str, Any]] = {}
    for trace_file in sorted(trace_dir.glob("lincoln-trace*.jsonl")):
        try:
            text = trace_file.read_text(encoding="utf-8")
        except Exception as exc:
            logging.warning("Cannot read trace file %s: %s", trace_file, exc)
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                logging.warning("Skipping malformed trace line in %s: %s", trace_file, exc)
                continue
            if not isinstance(entry, dict):
                continue
            key = (str(entry.get("run_id", "")), str(entry.get("sequence_id", "")))
            if not key[1]:
                continue
            entries[key] = entry

    return sorted(entries.values(), key=lambda e: e.get("timestamp", ""))


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
    safe_variables = _safe_variables(variables)
    for step in workflow_steps:
        if step.get("id") == stage_id:
            artifacts = step.get("artifacts", [])
            return [_interpolate_placeholders(str(a), safe_variables) for a in artifacts]
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
    session_id = _safe_path_component(variables.get("session_id", ""))
    candidates = [
        process_root / process_slug / "requirements" / session_id / "requirements.md",
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
    workflow_steps: list[dict[str, Any]],
    variables: dict[str, Any],
    process_root: Path,
    process_slug: str,
) -> float:
    design_id = _safe_path_component(variables.get("design_id", ""))
    if not design_id:
        return 0.0
    stage_id = "product-design-docs"
    artifacts = _artifact_paths_for_stage(workflow_steps, stage_id, variables)
    if not artifacts:
        base = process_root / process_slug / "designs" / design_id
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
    design_id = _safe_path_component(variables.get("design_id", ""))
    path = process_root / process_slug / "designs" / design_id / "tdd-plan.md"
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
    change_name = _safe_path_component(variables.get("change_name", "") or "")
    path = process_root / process_slug / "openspec" / "changes" / change_name / "tasks.md"
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*-\s+\[.\]", text, re.MULTILINE))


def _static_check_pass(trace: list[dict[str, Any]], process_root: Path) -> bool | None:
    # Prefer the structured result written by static-check.sh; fall back to
    # scanning the trace for legacy or per-process usage.
    result_file = process_root / ".context" / "static-check-result.json"
    if result_file.exists():
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "passed" in data:
                return bool(data["passed"])
        except Exception:
            pass

    found = None
    for entry in trace:
        if entry.get("category") != "bash":
            continue
        command = str(entry.get("args_summary", {}).get("command", ""))
        if STATIC_CHECK_RE.search(command):
            if entry.get("exit_code", 0) != 0:
                return False
            found = True
    return found


def _test_coverage(process_root: Path) -> float | None:
    """Return total coverage percentage from the latest .coverage database."""
    coverage_file = process_root / ".coverage"
    if not coverage_file.exists():
        return None
    try:
        output = subprocess.check_output(
            [sys.executable, "-m", "coverage", "json", "-o", "-"],
            cwd=process_root,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        data = json.loads(output)
        return round(float(data["totals"]["percent_covered"]), 2)
    except Exception as exc:
        logging.warning("Could not read coverage data from %s: %s", coverage_file, exc)
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
    match = re.search(
        r"(\d+)\s+files?\s+changed(?:,\s+(\d+)\s+insertions?\(\+\))?(?:,\s+(\d+)\s+deletions?\(-\))?",
        output,
    )
    if not match:
        return 0
    return sum(int(g or 0) for g in match.groups()[1:])


def _changed_files_count(process_root: Path, base: str = "main") -> int:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=process_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return 0
    files = [line.strip() for line in output.splitlines() if line.strip()]
    return len(files)


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
    results = data.get("results") if isinstance(data, dict) else None
    if results is None:
        results = data.get("checks") if isinstance(data, dict) else []
    if not isinstance(results, list):
        results = []
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


def _session_duration(trace: list[dict[str, Any]]) -> tuple[int, str]:
    if len(trace) < 2:
        return 0, "estimated"
    try:
        start = _parse_iso(trace[0]["timestamp"])
        end = _parse_iso(trace[-1]["timestamp"])
        return int((end - start).total_seconds()), "exact"
    except Exception:
        return 0, "estimated"


def _unique_files_touched(trace: list[dict[str, Any]]) -> int:
    unique_files = set()
    for e in trace:
        if e.get("category") in ("read", "write", "edit"):
            target = e.get("target", "")
            if target:
                unique_files.add(target)
    return len(unique_files)


def _retry_count(trace: list[dict[str, Any]]) -> int:
    retries = 0
    prev: dict[str, Any] | None = None
    for e in trace:
        if (
            prev
            and prev.get("exit_code", 0) != 0
            and prev.get("tool") == e.get("tool")
            and prev.get("target") == e.get("target")
        ):
            retries += 1
        prev = e
    return retries


def _test_runs(trace: list[dict[str, Any]]) -> int:
    return sum(
        1
        for e in trace
        if e.get("category") == "bash"
        and TEST_COMMAND_RE.search(
            str(e.get("args_summary", {}).get("command", ""))
            or str(e.get("target", ""))
        )
    )


def _compute_session_metrics(trace: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, str]]:
    duration, duration_confidence = _session_duration(trace)
    confidence = {"session_duration_seconds": duration_confidence}

    session = {
        "session_duration_seconds": duration,
        "trace_line_count": len(trace),
        "total_tool_calls": len(trace),
        "tool_calls_by_category": dict(Counter(e.get("category", "other") for e in trace)),
        "unique_skills": sorted(
            {
                e.get("target", "")
                for e in trace
                if e.get("category") == "skill" and e.get("target")
            }
        ),
        "unique_files_touched": _unique_files_touched(trace),
        "test_runs": _test_runs(trace),
        "error_count": sum(1 for e in trace if e.get("exit_code", 0) != 0),
        "retry_count": _retry_count(trace),
    }
    for key in session:
        if key not in confidence:
            confidence[key] = "exact"
    return session, confidence


def _stage_completion_stats(state: dict[str, Any]) -> tuple[int, int, float]:
    nodes = state.get("nodes", [])
    total = len(nodes)
    completed = sum(1 for n in nodes if n.get("status") == "completed")
    failed = sum(1 for n in nodes if n.get("status") == "validation_failed")
    rate = round(completed / total, 2) if total else 0.0
    return failed, completed, rate


def _stage_rework_count(stage_order: list[str]) -> int:
    seen: set[str] = set()
    count = 0
    for stage in stage_order:
        if stage in seen:
            count += 1
        seen.add(stage)
    return count


def _workflow_adherence_score(
    stage_order: list[str], workflow_steps: list[dict[str, Any]]
) -> float:
    template_ids = [s.get("id") for s in workflow_steps if s.get("id")]
    if not template_ids:
        return 1.0
    lcs = _lcs_length(stage_order, template_ids)
    return round(lcs / len(template_ids), 2)


def _human_gate_stats(
    state: dict[str, Any],
    human_gate_stages: set[str],
    stage_durations: dict[str, int],
) -> tuple[int, float, int]:
    passed = 0
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
            passed += 1
    count = len(human_gate_stages)
    rate = round(passed / count, 2) if count else 1.0
    wait = sum(stage_durations.get(s, 0) for s in human_gate_stages)
    return count, rate, wait


def _combined_stage_durations(
    trace: list[dict[str, Any]], state: dict[str, Any]
) -> dict[str, int]:
    durations_trace = _stage_durations(trace)
    durations_node = _node_durations(state)
    return {
        k: durations_trace.get(k, durations_node.get(k, 0))
        for k in set(durations_trace) | set(durations_node)
    }


def _human_gate_stages(
    stage_order: list[str], workflow_steps: list[dict[str, Any]]
) -> set[str]:
    return {
        s.get("id")
        for s in workflow_steps
        if s.get("human_gate") and s.get("id") in stage_order
    }


def _compute_workflow_metrics(
    trace: list[dict[str, Any]],
    state: dict[str, Any],
    workflow_steps: list[dict[str, Any]],
    variables: dict[str, Any],
    process_root: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    stage_order = _stage_order_from_trace(trace)
    stage_durations = _combined_stage_durations(trace, state)

    failed_nodes, completed_nodes, stage_completion_rate = _stage_completion_stats(state)
    stage_rework_count = _stage_rework_count(stage_order)

    current_stage = state.get("current_run", {}).get("current_stage")
    artifact_completion_rate = _artifact_completion_rate(
        current_stage, workflow_steps, variables, process_root
    )
    workflow_adherence_score = _workflow_adherence_score(stage_order, workflow_steps)

    human_gate_stages = _human_gate_stages(stage_order, workflow_steps)
    human_gate_count, human_gate_pass_rate, human_gate_wait_seconds = _human_gate_stats(
        state, human_gate_stages, stage_durations
    )

    workflow = {
        "stage_transition_count": max(0, len(stage_order) - 1),
        "stage_durations": stage_durations,
        "stage_completion_rate": stage_completion_rate,
        "stage_rework_count": stage_rework_count,
        "artifact_completion_rate": artifact_completion_rate,
        "validation_failure_count": failed_nodes,
        "workflow_adherence_score": workflow_adherence_score,
        "human_gate_count": human_gate_count,
        "human_gate_wait_seconds": human_gate_wait_seconds,
        "human_gate_pass_rate": human_gate_pass_rate,
        "build_codebase_knowledge_duration_seconds": stage_durations.get("build-codebase-knowledge", 0),
    }
    confidence = {
        "stage_durations": "estimated",
        "human_gate_wait_seconds": "estimated",
        "artifact_completion_rate": "exact",
        "workflow_adherence_score": "exact",
        "build_codebase_knowledge_duration_seconds": "estimated",
    }
    return workflow, confidence


def _is_handoff_command(entry: dict[str, Any]) -> bool:
    # Handoffs are recorded as structured LincolnHandoff trace entries by
    # stage_loader, so we detect them by category rather than regex-parsing Bash text.
    return entry.get("category") == "handoff"


def _handoff_count(trace: list[dict[str, Any]]) -> int:
    return sum(1 for e in trace if _is_handoff_command(e))


def _time_to_first_handoff(trace: list[dict[str, Any]]) -> int:
    count = _handoff_count(trace)
    if not trace or not count:
        return 0
    first_ts = next((e.get("timestamp") for e in trace if _is_handoff_command(e)), None)
    if not first_ts:
        return 0
    try:
        return int((_parse_iso(first_ts) - _parse_iso(trace[0]["timestamp"])).total_seconds())
    except Exception:
        return 0


def _agent_switches(stage_order: list[str], primary_agents: dict[str, str]) -> int:
    switches = 0
    prev_stage: str | None = None
    for stage in stage_order:
        if prev_stage and primary_agents.get(prev_stage) and primary_agents.get(stage):
            if primary_agents[prev_stage] != primary_agents[stage]:
                switches += 1
        prev_stage = stage
    return switches


def _compute_collaboration_metrics(
    trace: list[dict[str, Any]],
    stage_order: list[str],
    primary_agents: dict[str, str],
    human_gate_count: int,
) -> tuple[dict[str, Any], dict[str, str]]:
    handoff_count = _handoff_count(trace)
    collaboration = {
        "handoff_count": handoff_count,
        "agent_switches": _agent_switches(stage_order, primary_agents),
        "pm_turns": human_gate_count,
        "time_to_first_handoff": _time_to_first_handoff(trace),
    }
    confidence: dict[str, str] = {
        "agent_switches": "exact" if primary_agents else "pending",
        "pm_turns": "estimated",
        "time_to_first_handoff": "exact" if handoff_count else "estimated",
    }
    return collaboration, confidence


def _compute_quality_metrics(
    trace: list[dict[str, Any]],
    state: dict[str, Any],
    workflow_steps: list[dict[str, Any]],
    variables: dict[str, Any],
    process_root: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    confidence: dict[str, str] = {}
    process_slug = get_process_slug(state, None)

    requirements_score = _requirements_clarity_score(process_root, process_slug, variables)
    design_completeness = _design_doc_completeness(
        workflow_steps, variables, process_root, process_slug
    )
    tdd_phases = _tdd_plan_red_green_refactor(process_root, process_slug, variables)
    openspec_count = _openspec_task_count(process_root, process_slug, variables)
    static_pass = _static_check_pass(trace, process_root)
    coverage = _test_coverage(process_root)
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
    confidence["test_coverage"] = "exact" if coverage is not None else "pending"
    confidence["audit_score"] = "exact" if audit_counts is not None else "pending"
    confidence["pr_size"] = "exact" if pr_size > 0 else "estimated"
    return quality, confidence


def _pr_merge_info(state: dict[str, Any]) -> tuple[bool, int, str | None]:
    pr_timestamps = _pr_event_timestamps(state)
    pr_submitted_ts = pr_timestamps.get("pr_submitted")
    merged_ts = pr_timestamps.get("merged")
    pr_merged = bool(merged_ts) or any(
        n.get("status") == "merged" for n in state.get("nodes", [])
    )
    latency = 0
    if pr_submitted_ts and merged_ts:
        try:
            latency = int((_parse_iso(merged_ts) - _parse_iso(pr_submitted_ts)).total_seconds())
        except Exception:
            latency = 0
    return pr_merged, latency, merged_ts


def _delta_seconds(start_ts: str | None, end_ts: str | None) -> int:
    if not start_ts or not end_ts:
        return 0
    try:
        return int((_parse_iso(end_ts) - _parse_iso(start_ts)).total_seconds())
    except Exception:
        return 0


def _compute_outcome_metrics(trace: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    pr_merged, pr_merge_latency_seconds, merged_ts = _pr_merge_info(state)

    first_clarify_ts = next(
        (e.get("timestamp") for e in trace if e.get("stage") == "clarify"),
        trace[0].get("timestamp") if trace else None,
    )
    first_pr_ts = next(
        (e.get("timestamp") for e in trace if e.get("tool") == "mcp__plugin_ecc_github__create_pull_request"),
        None,
    )

    return {
        "issue_closed": None,
        "pr_merged": pr_merged,
        "pr_merge_latency_seconds": pr_merge_latency_seconds,
        "knowledge_synced": None,
        "time_to_pr_seconds": _delta_seconds(first_clarify_ts, first_pr_ts),
        "time_to_merge_seconds": _delta_seconds(first_clarify_ts, merged_ts),
    }


def _load_primary_agents(project_root: Path) -> dict[str, str]:
    return _stage_primary_agents(_load_stage_manifest(project_root))


def _outcome_confidence(outcome: dict[str, Any], merged_ts: str | None) -> dict[str, str]:
    return {
        "issue_closed": "pending",
        "knowledge_synced": "pending",
        "pr_merge_latency_seconds": "exact" if merged_ts else "pending",
    }


def _with_s2_ratio(
    outcome: dict[str, Any], session: dict[str, Any], process_root: Path
) -> dict[str, Any]:
    changed_files = _changed_files_count(process_root)
    unique_files_touched = session["unique_files_touched"]
    ratio = round(unique_files_touched / max(1, changed_files), 2)
    return {**outcome, "unique_files_touched_ratio": ratio}


def compute_metrics(
    trace: list[dict[str, Any]],
    state: dict[str, Any],
    scenario: str,
    process_root: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Compute L1-L5 benchmark metrics from trace and state."""
    trace = sorted(trace, key=lambda e: e.get("timestamp", ""))
    variables = state.get("current_run", {}).get("variables", {})
    workflow_steps = _workflow_steps(state)
    primary_agents = _load_primary_agents(process_root)

    session, conf_session = _compute_session_metrics(trace)
    workflow, conf_workflow = _compute_workflow_metrics(
        trace, state, workflow_steps, variables, process_root
    )
    collaboration, conf_collab = _compute_collaboration_metrics(
        trace, _stage_order_from_trace(trace), primary_agents, workflow["human_gate_count"]
    )
    quality, conf_quality = _compute_quality_metrics(
        trace, state, workflow_steps, variables, process_root
    )
    outcome = _compute_outcome_metrics(trace, state)
    merged_ts = _pr_event_timestamps(state).get("merged")

    confidence: dict[str, str] = {}
    confidence.update(conf_session)
    confidence.update(conf_workflow)
    confidence.update(conf_collab)
    confidence.update(conf_quality)
    confidence.update(_outcome_confidence(outcome, merged_ts))
    outcome = _with_s2_ratio(outcome, session, process_root)
    confidence["unique_files_touched_ratio"] = "estimated"

    metrics = {
        "session": session,
        "workflow": workflow,
        "collaboration": collaboration,
        "quality": quality,
        "outcome": outcome,
    }
    return metrics, confidence
