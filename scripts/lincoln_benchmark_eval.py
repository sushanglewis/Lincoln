#!/usr/bin/env python3
"""Scenario-specific thresholds and evaluation for Lincoln benchmark reports."""

from __future__ import annotations

from typing import Any

THRESHOLDS: dict[str, dict[str, dict[str, Any]]] = {
    "S1": {
        "time_to_merge_seconds": {"green": 3 * 24 * 3600, "yellow": 7 * 24 * 3600, "direction": "minimize"},
        "human_gate_wait_seconds": {"green": 4 * 3600, "yellow": 8 * 3600, "direction": "minimize"},
        "human_gate_pass_rate": {"green": 1.0, "yellow": 0.8, "direction": "maximize"},
        "requirements_clarity_score": {"green": 4, "yellow": 3, "direction": "maximize"},
        "static_check_pass": {"green": True, "yellow": None, "direction": "maximize"},
        "pr_size": {"green": 400, "yellow": 800, "direction": "minimize"},
        "session_start_tokens": {"green": 2500, "yellow": 5000, "direction": "minimize"},
    },
    "S2": {
        "build_codebase_knowledge_duration_seconds": {"green": 3600, "yellow": 2 * 3600, "direction": "minimize"},
        "unique_files_touched_ratio": {"green": 1.0, "yellow": 1.5, "direction": "minimize"},
        "pr_size": {"green": 300, "yellow": 600, "direction": "minimize"},
        "session_start_tokens": {"green": 2500, "yellow": 5000, "direction": "minimize"},
    },
    "S3": {
        "time_to_pr_seconds": {"green": 3600, "yellow": 4 * 3600, "direction": "minimize"},
        "retry_count": {"green": 1, "yellow": 3, "direction": "minimize"},
        "test_runs": {"green": 2, "yellow": 1, "direction": "maximize"},
        "pr_size": {"green": 100, "yellow": 300, "direction": "minimize"},
        "session_start_tokens": {"green": 2500, "yellow": 5000, "direction": "minimize"},
    },
    "S4": {
        "time_to_first_handoff": {"green": 30 * 60, "yellow": 2 * 3600, "direction": "minimize"},
        "explored_options_count": {"green": 2, "yellow": 1, "direction": "maximize"},
        "design_doc_completeness": {"green": 1.0, "yellow": 0.8, "direction": "maximize"},
        "session_start_tokens": {"green": 2500, "yellow": 5000, "direction": "minimize"},
    },
    "S5": {
        "time_to_first_handoff": {"green": 3600, "yellow": 4 * 3600, "direction": "minimize"},
        "oss_candidates_evaluated": {"green": 3, "yellow": 1, "direction": "maximize"},
        "session_start_tokens": {"green": 2500, "yellow": 5000, "direction": "minimize"},
    },
}


def _flatten_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for group in metrics.values():
        if isinstance(group, dict):
            for key, value in group.items():
                flat[key] = value
    return flat


def _evaluate_boolean(value: Any, expected: bool) -> str:
    return "green" if value == expected else "red"


def _evaluate_numeric(value: float, green: float, yellow: float | None, direction: str) -> str:
    if direction == "maximize":
        if value >= green:
            return "green"
        if yellow is not None and value >= yellow:
            return "yellow"
        return "red"
    if yellow is None:
        return "green" if value <= green else "red"
    if value <= green:
        return "green"
    if value <= yellow:
        return "yellow"
    return "red"


def _evaluate_tdd(phases: dict[str, bool]) -> dict[str, Any]:
    passed = sum(1 for v in phases.values() if v)
    return {
        "value": f"{passed}/3",
        "threshold": "3/3 phases",
        "status": "green" if passed == 3 else "yellow" if passed == 2 else "red",
    }


def evaluate_against_thresholds(metrics: dict[str, Any], scenario: str) -> dict[str, Any]:
    """Compare computed metrics against scenario thresholds and return statuses."""
    evaluation: dict[str, Any] = {}
    flat = _flatten_metrics(metrics)

    for metric, cfg in THRESHOLDS.get(scenario, {}).items():
        value = flat.get(metric)
        if value is None:
            continue
        green = cfg.get("green")
        yellow = cfg.get("yellow")
        direction = cfg.get("direction", "minimize")
        if isinstance(green, bool):
            status = _evaluate_boolean(value, green)
        else:
            status = _evaluate_numeric(value, green, yellow, direction)
        evaluation[metric] = {"value": value, "threshold": cfg, "status": status}

    if flat.get("tdd_plan_red_green_refactor"):
        evaluation["tdd_plan_red_green_refactor"] = _evaluate_tdd(flat["tdd_plan_red_green_refactor"])

    return evaluation
