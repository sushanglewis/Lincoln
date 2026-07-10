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
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.lincoln_benchmark_eval import evaluate_against_thresholds  # noqa: E402
from scripts.lincoln_benchmark_metrics import compute_metrics, load_trace  # noqa: E402
from scripts.lincoln_benchmark_report import build_markdown_report  # noqa: E402
from scripts.lincoln_paths import get_process_slug  # noqa: E402

REPORT_SCHEMA_VERSION = "1.0.0"
SESSION_STOP_DEDUP_SECONDS = 5

SCENARIO_MAP = {
    "interview-to-knowledge": "S1",
    "existing-project-iteration": "S2",
    "bug-fix": "S3",
    "design-spike": "S4",
    "oss-first-design": "S5",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_scenario(state: dict[str, Any]) -> str:
    template = (
        state.get("workflow", {}).get("template")
        or state.get("current_run", {}).get("workflow_template")
        or ""
    )
    return SCENARIO_MAP.get(template, "S1")


def _linear_id(state: dict[str, Any]) -> str:
    """Derive the Linear issue id from environment, branch, or state metadata."""
    env_id = os.environ.get("LINCOLN_LINEAR_ID") or os.environ.get("LINEAR_ISSUE_ID")
    if env_id:
        match = re.search(r"\b(lew-\d+)\b", env_id, re.IGNORECASE)
        return match.group(1).upper() if match else env_id

    branch = state.get("current_run", {}).get("branch", "")
    match = re.search(r"\b(lew-\d+)\b", branch, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    issue_number = state.get("current_run", {}).get("issue_number")
    if issue_number and str(issue_number).strip():
        return f"LEW-{issue_number}"

    return "unknown"


def _trace_files(process_dir: Path, project_root: Path) -> list[str]:
    return sorted(
        str(p.relative_to(project_root))
        for p in (process_dir / ".trace").glob("lincoln-trace*.jsonl")
        if p.exists()
    )


def _build_metadata(
    state: dict[str, Any], process_slug: str, trace_files: list[str]
) -> dict[str, Any]:
    return {
        "process_slug": process_slug,
        "run_id": state.get("current_run", {}).get("run_id", "unknown"),
        "branch": state.get("current_run", {}).get("branch", "unknown"),
        "issue_number": str(state.get("current_run", {}).get("issue_number", "")),
        "linear_id": _linear_id(state),
        "current_stage": state.get("current_run", {}).get("current_stage", "unknown"),
        "trace_files": trace_files,
        "workflow_template": state.get("workflow", {}).get("template", "unknown"),
    }


def _build_payload(
    report_id: str,
    generated_at: str,
    scenario: str,
    trigger: str,
    metadata: dict[str, Any],
    metrics: dict[str, Any],
    confidence: dict[str, str],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    return {
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


def _write_report_files(
    benchmark_dir: Path,
    trigger: str,
    generated_at: str,
    markdown: str,
    payload: dict[str, Any],
) -> dict[str, Path]:
    timestamp = generated_at.replace(":", "").replace("-", "").replace("T", "-")[:15]
    md_path = benchmark_dir / f"lincoln-benchmark-{trigger}-{timestamp}.md"
    json_path = benchmark_dir / f"lincoln-benchmark-{trigger}-{timestamp}.json"
    _atomic_write(md_path, markdown.encode("utf-8"))
    _atomic_write(json_path, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
    return {"markdown": md_path, "json": json_path}


def _recent_session_stop_exists(benchmark_dir: Path) -> bool:
    latest = 0.0
    for existing in benchmark_dir.glob("lincoln-benchmark-session_stop-*.json"):
        try:
            mtime = existing.stat().st_mtime
            if mtime > latest:
                latest = mtime
        except Exception:
            pass
    if not latest:
        return False
    return (datetime.now(timezone.utc).timestamp() - latest) < SESSION_STOP_DEDUP_SECONDS


def write_benchmark_report(
    state_file: Path,
    trigger: str,
    project_root: Path = _PROJECT_ROOT,
) -> dict[str, Path | None] | None:
    from scripts.stage_loader import load_state

    state_file = state_file.resolve()
    # Derive the project root from the state file location; this prevents an
    # attacker from using --project-root to redirect report writes or audit runs.
    if len(state_file.parents) >= 2:
        project_root = state_file.parents[1]

    state = load_state(state_file)
    process_slug = get_process_slug(state, state_file)
    process_dir = project_root / process_slug
    benchmark_dir = process_dir / "benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    if trigger == "session_stop" and _recent_session_stop_exists(benchmark_dir):
        return None

    scenario = detect_scenario(state)
    trace = load_trace(project_root, process_slug)
    metrics, confidence = compute_metrics(trace, state, scenario, project_root)
    evaluation = evaluate_against_thresholds(metrics, scenario)
    report_id = uuid.uuid4().hex
    generated_at = _now()
    trace_files = _trace_files(process_dir, project_root)
    metadata = _build_metadata(state, process_slug, trace_files)
    payload = _build_payload(
        report_id, generated_at, scenario, trigger, metadata, metrics, confidence, evaluation
    )
    markdown = build_markdown_report(
        report_id, scenario, trigger, metrics, confidence, evaluation, state, trace_files, generated_at
    )
    return _write_report_files(benchmark_dir, trigger, generated_at, markdown, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Lincoln benchmark report")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument(
        "--trigger",
        choices=["handoff", "pr_created", "pr_merged", "session_stop", "manual"],
        default="manual",
    )
    args = parser.parse_args(argv)

    result = write_benchmark_report(args.state_file, args.trigger)
    if result is None:
        print("Benchmark report skipped (recent session_stop report exists)")
        return 0
    print(f"Benchmark report written to:\n  {result['markdown']}\n  {result['json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
