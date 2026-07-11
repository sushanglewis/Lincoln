#!/usr/bin/env python3
"""Markdown rendering for Lincoln benchmark reports."""

from __future__ import annotations

import json
from typing import Any


def _render_summary(evaluation: dict[str, Any]) -> list[str]:
    if not evaluation:
        return ["- No threshold evaluation available for this scenario yet.", ""]
    red = [m for m, v in evaluation.items() if v.get("status") == "red"]
    yellow = [m for m, v in evaluation.items() if v.get("status") == "yellow"]
    green = [m for m, v in evaluation.items() if v.get("status") == "green"]
    lines = [f"- Green: {len(green)}, Yellow: {len(yellow)}, Red: {len(red)}"]
    if red:
        lines.append(f"- Red flags: {', '.join(red)}")
    if yellow:
        lines.append(f"- Watch items: {', '.join(yellow)}")
    lines.append("")
    return lines


def _format_value(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) or "—"
    if value is None:
        return "—"
    return str(value)


def _render_metrics_group(title: str, group: dict[str, Any], confidence: dict[str, str]) -> list[str]:
    lines = [f"## {title}", "", "| Metric | Value | Confidence |", "|--------|-------|------------|"]
    for key, value in group.items():
        conf = confidence.get(key, "exact")
        lines.append(f"| `{key}` | {_format_value(value)} | {conf} |")
    lines.append("")
    return lines


def _render_evaluation(evaluation: dict[str, Any]) -> list[str]:
    if not evaluation:
        return []
    lines = ["## Threshold Evaluation", "", "| Metric | Value | Status |", "|--------|-------|--------|"]
    for metric, result in evaluation.items():
        status = result.get("status", "unknown")
        lines.append(f"| `{metric}` | {result.get('value')} | {status} |")
    lines.append("")
    return lines


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


def _render_recommendations(metrics: dict[str, Any], evaluation: dict[str, Any]) -> list[str]:
    lines = ["## Recommendations", ""]
    recs = _generate_recommendations(metrics, evaluation)
    if recs:
        for rec in recs:
            lines.append(f"- {rec}")
    else:
        lines.append("- No automated recommendations.")
    lines.append("")
    return lines


def _render_data_sources(trace_files: list[str]) -> list[str]:
    lines = ["## Data Sources", ""]
    for tf in trace_files:
        lines.append(f"- `{tf}`")
    lines.append("")
    return lines


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
    """Render a benchmark report as Markdown."""
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

    lines.extend(_render_summary(evaluation))

    for title, group_key in [
        ("L1 Session Activity", "session"),
        ("L2 Workflow Progress", "workflow"),
        ("L3 Human-AI Collaboration", "collaboration"),
        ("L4 Output Quality", "quality"),
        ("L5 Business Outcome", "outcome"),
    ]:
        lines.extend(_render_metrics_group(title, metrics.get(group_key, {}), confidence))

    lines.extend(_render_evaluation(evaluation))
    lines.extend(_render_recommendations(metrics, evaluation))
    lines.extend(_render_data_sources(trace_files))

    return "\n".join(lines)
