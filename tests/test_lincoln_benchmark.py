"""Tests for scripts/lincoln_benchmark.py."""

import json
from pathlib import Path

import pytest
import yaml

from scripts import lincoln_benchmark, lincoln_benchmark_metrics


def _write_state(tmp_path: Path, state: dict) -> Path:
    slug = state.get("current_run", {}).get("variables", {}).get("process_slug", "lc-test")
    path = tmp_path / slug / "workflow-stage.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def base_state(tmp_path):
    return _write_state(
        tmp_path,
        {
            "schema_version": "2.0.0",
            "workflow": {"name": "interview-to-knowledge", "template": "interview-to-knowledge"},
            "current_run": {
                "run_id": "run-123",
                "branch": "issue-27",
                "current_stage": "clarify",
                "status": "in_progress",
                "issue_number": "27",
                "variables": {
                    "process_slug": "lc-test",
                    "session_id": "2026-07-10-test",
                    "design_id": "test-design",
                    "change_name": "test-change",
                },
            },
            "nodes": [],
            "recovery": {},
        },
    )


def _trace_entry(
    tool: str,
    category: str,
    target: str,
    stage: str = "clarify",
    exit_code: int = 0,
    timestamp: str = "2026-07-10T10:00:00Z",
    sequence_id: str = "seq",
    args_summary: dict | None = None,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "sequence_id": sequence_id,
        "timestamp": timestamp,
        "run_id": "run-123",
        "stage": stage,
        "tool": tool,
        "category": category,
        "target": target,
        "exit_code": exit_code,
        "args_summary": args_summary or {},
    }


def test_detect_scenario_interview_to_knowledge():
    state = {"workflow": {"template": "interview-to-knowledge"}}
    assert lincoln_benchmark.detect_scenario(state) == "S1"


def test_detect_scenario_existing_project_iteration():
    state = {"current_run": {"workflow_template": "existing-project-iteration"}}
    assert lincoln_benchmark.detect_scenario(state) == "S2"


def test_detect_scenario_bug_fix():
    state = {"workflow": {"template": "bug-fix"}}
    assert lincoln_benchmark.detect_scenario(state) == "S3"


def test_detect_scenario_defaults_to_s1():
    assert lincoln_benchmark.detect_scenario({}) == "S1"


def test_load_trace_merges_child_files(base_state):
    trace_dir = base_state.parent / ".trace"
    trace_dir.mkdir(exist_ok=True)
    parent = _trace_entry("Bash", "bash", "cmd1", sequence_id="s1")
    child = _trace_entry("Write", "write", "child.md", sequence_id="s2")
    (trace_dir / "lc-trace.jsonl").write_text(json.dumps(parent) + "\n", encoding="utf-8")
    (trace_dir / "lc-trace-agent-x.jsonl").write_text(json.dumps(child) + "\n", encoding="utf-8")

    trace = lincoln_benchmark.load_trace(base_state.parent.parent, "lc-test")
    assert len(trace) == 2
    tools = {e["tool"] for e in trace}
    assert tools == {"Bash", "Write"}


def test_load_trace_dedups_by_sequence_id(base_state):
    trace_dir = base_state.parent / ".trace"
    trace_dir.mkdir(exist_ok=True)
    entry = _trace_entry("Bash", "bash", "x", sequence_id="dup")
    (trace_dir / "lc-trace.jsonl").write_text(
        json.dumps(entry) + "\n" + json.dumps(entry) + "\n", encoding="utf-8"
    )
    trace = lincoln_benchmark.load_trace(base_state.parent.parent, "lc-test")
    assert len(trace) == 1


def test_compute_metrics_session_activity(base_state):
    trace = [
        _trace_entry("Bash", "bash", "echo a", timestamp="2026-07-10T10:00:00Z", sequence_id="s1"),
        _trace_entry("Skill", "skill", "brainstorm", timestamp="2026-07-10T10:00:30Z", sequence_id="s2"),
        _trace_entry("Bash", "bash", "pytest", timestamp="2026-07-10T10:01:00Z", sequence_id="s3"),
        _trace_entry("Bash", "bash", "pytest", exit_code=1, timestamp="2026-07-10T10:01:30Z", sequence_id="s4"),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, confidence = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    session = metrics["session"]
    assert session["total_tool_calls"] == 4
    assert session["tool_calls_by_category"]["bash"] == 3
    assert session["tool_calls_by_category"]["skill"] == 1
    assert session["unique_skills"] == ["brainstorm"]
    assert session["test_runs"] == 2
    assert session["error_count"] == 1
    assert session["session_duration_seconds"] == 90
    assert confidence["session_duration_seconds"] == "exact"


def test_compute_metrics_retry_count(base_state):
    trace = [
        _trace_entry("Bash", "bash", "flaky", exit_code=1, sequence_id="s1"),
        _trace_entry("Bash", "bash", "flaky", exit_code=1, sequence_id="s2"),
        _trace_entry("Bash", "bash", "flaky", exit_code=0, sequence_id="s3"),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, _ = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    assert metrics["session"]["retry_count"] == 2


def test_compute_metrics_build_codebase_knowledge_duration(base_state):
    trace = [
        _trace_entry("Bash", "bash", "x", stage="build-codebase-knowledge", timestamp="2026-07-10T10:00:00Z", sequence_id="s1"),
        _trace_entry("Bash", "bash", "y", stage="build-codebase-knowledge", timestamp="2026-07-10T10:00:30Z", sequence_id="s2"),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, confidence = lincoln_benchmark.compute_metrics(trace, state, "S2", base_state.parent.parent)
    assert metrics["workflow"]["build_codebase_knowledge_duration_seconds"] == 30
    assert confidence["build_codebase_knowledge_duration_seconds"] == "estimated"
    evaluation = lincoln_benchmark.evaluate_against_thresholds(metrics, "S2")
    assert "build_codebase_knowledge_duration_seconds" in evaluation


def test_compute_metrics_workflow_progress(base_state):
    trace = [
        _trace_entry("Bash", "bash", "x", stage="clarify", sequence_id="s1"),
        _trace_entry("Bash", "bash", "x", stage="product-design-docs", sequence_id="s2"),
        _trace_entry("Bash", "bash", "x", stage="clarify", sequence_id="s3"),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, _ = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    workflow = metrics["workflow"]
    assert workflow["stage_transition_count"] == 2
    assert workflow["stage_rework_count"] == 1
    assert workflow["workflow_adherence_score"] > 0


def test_compute_metrics_collaboration_handoff(base_state):
    trace = [
        _trace_entry("Bash", "bash", "echo", stage="clarify", timestamp="2026-07-10T10:00:00Z", sequence_id="s1"),
        _trace_entry("LincolnHandoff", "handoff", "", stage="clarify", timestamp="2026-07-10T10:05:00Z", sequence_id="s2"),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, confidence = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    assert metrics["collaboration"]["handoff_count"] == 1
    assert metrics["collaboration"]["time_to_first_handoff"] == 5 * 60
    assert confidence["time_to_first_handoff"] == "exact"


def test_compute_metrics_static_check(base_state):
    trace = [
        _trace_entry("Bash", "bash", "bash scripts/static-check.sh", exit_code=0, sequence_id="s1", args_summary={"command": "bash scripts/static-check.sh"}),
    ]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    metrics, _ = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    assert metrics["quality"]["static_check_pass"] is True


def test_evaluate_against_thresholds_s1():
    metrics = {
        "session": {"total_tool_calls": 10},
        "workflow": {"human_gate_wait_seconds": 3 * 3600, "human_gate_pass_rate": 1.0},
        "quality": {"requirements_clarity_score": 4, "pr_size": 200},
        "outcome": {"time_to_merge_seconds": 2 * 24 * 3600},
    }
    evaluation = lincoln_benchmark.evaluate_against_thresholds(metrics, "S1")
    assert evaluation["human_gate_wait_seconds"]["status"] == "green"
    assert evaluation["pr_size"]["status"] == "green"
    assert evaluation["human_gate_pass_rate"]["status"] == "green"
    assert evaluation["time_to_merge_seconds"]["status"] == "green"


def test_evaluate_tdd_plan_phases():
    metrics = {
        "session": {}, "workflow": {}, "collaboration": {}, "quality": {}, "outcome": {}
    }
    metrics["quality"]["tdd_plan_red_green_refactor"] = {"red": True, "green": True, "refactor": True}
    evaluation = lincoln_benchmark.evaluate_against_thresholds(metrics, "S1")
    assert evaluation["tdd_plan_red_green_refactor"]["status"] == "green"


def test_write_benchmark_report(base_state):
    result = lincoln_benchmark.write_benchmark_report(base_state, "manual", base_state.parent.parent)
    assert result is not None
    assert result["markdown"].exists()
    assert result["json"].exists()
    payload = json.loads(result["json"].read_text(encoding="utf-8"))
    assert payload["scenario"] == "S1"
    assert payload["trigger"] == "manual"
    assert "metrics" in payload
    assert payload["metadata"]["linear_id"] == "LEW-27"


def test_write_benchmark_report_linear_id_from_env(base_state, monkeypatch):
    monkeypatch.setenv("LINCOLN_LINEAR_ID", "LEW-999")
    result = lincoln_benchmark.write_benchmark_report(base_state, "manual", base_state.parent.parent)
    payload = json.loads(result["json"].read_text(encoding="utf-8"))
    assert payload["metadata"]["linear_id"] == "LEW-999"


def test_write_benchmark_report_session_stop_dedup(base_state):
    lincoln_benchmark.write_benchmark_report(base_state, "session_stop", base_state.parent.parent)
    result = lincoln_benchmark.write_benchmark_report(base_state, "session_stop", base_state.parent.parent)
    assert result is None


def test_benchmark_report_conforms_to_schema(base_state):
    result = lincoln_benchmark.write_benchmark_report(base_state, "manual", base_state.parent.parent)
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / ".claude" / "schemas" / "benchmark-report.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    payload = json.loads(result["json"].read_text(encoding="utf-8"))
    # Minimal structural validation using the schema's required fields.
    required = schema["required"]
    for key in required:
        assert key in payload, f"missing {key}"
    for group in payload["metrics"]:
        assert group in schema["properties"]["metrics"]["properties"]


def test_compute_metrics_does_not_mutate_trace(base_state):
    trace = [
        _trace_entry("Bash", "bash", "x", sequence_id="s1"),
    ]
    original = [dict(e) for e in trace]
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    assert trace == original


def test_compute_metrics_quality_with_artifacts(base_state):
    project_root = base_state.parent.parent
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    variables = state["current_run"]["variables"]
    slug = variables["process_slug"]
    session_id = variables["session_id"]
    design_id = variables["design_id"]
    change_name = variables["change_name"]

    req_dir = project_root / slug / "requirements" / session_id
    req_dir.mkdir(parents=True)
    req_dir.joinpath("requirements.md").write_text(
        "# Requirements\n\n## Background\n## Problem\n## Solution\n## Acceptance Criteria\n",
        encoding="utf-8",
    )

    design_dir = project_root / slug / "designs" / design_id
    design_dir.mkdir(parents=True)
    for name in ["design-review.md", "scenarios.md", "feature-catalog.md", "data-model.md", "flows.md", "feasibility.md"]:
        design_dir.joinpath(name).write_text("ok", encoding="utf-8")
    design_dir.joinpath("tdd-plan.md").write_text(
        "# TDD Plan\n\n## Red\n## Green\n## Refactor\n", encoding="utf-8"
    )

    openspec_dir = project_root / slug / "openspec" / "changes" / change_name
    openspec_dir.mkdir(parents=True)
    openspec_dir.joinpath("tasks.md").write_text("- [ ] task 1\n- [ ] task 2\n", encoding="utf-8")

    trace = [
        _trace_entry("Bash", "bash", "bash scripts/static-check.sh", exit_code=0, sequence_id="s1", args_summary={"command": "bash scripts/static-check.sh"}),
        _trace_entry("Skill", "skill", "code-review", sequence_id="s2"),
    ]

    metrics, _ = lincoln_benchmark.compute_metrics(trace, state, "S1", project_root)
    quality = metrics["quality"]
    assert quality["requirements_clarity_score"] == 4
    assert quality["design_doc_completeness"] == 1.0
    assert quality["tdd_plan_red_green_refactor"]["red"] is True
    assert quality["openspec_task_count"] == 2
    assert quality["static_check_pass"] is True
    assert quality["code_review_calls"] == 1


def test_compute_metrics_with_nodes(base_state):
    state = yaml.safe_load(base_state.read_text(encoding="utf-8"))
    state["nodes"] = [
        {
            "stage_id": "clarify",
            "node_id": "clarify-1",
            "status": "completed",
            "gate_passed": True,
            "started_at": "2026-07-10T09:00:00Z",
            "completed_at": "2026-07-10T09:30:00Z",
        },
        {
            "stage_id": "product-design-docs",
            "node_id": "design-1",
            "status": "validation_failed",
            "started_at": "2026-07-10T10:00:00Z",
        },
    ]
    trace = [
        _trace_entry("Bash", "bash", "x", stage="clarify", timestamp="2026-07-10T09:00:00Z", sequence_id="s1"),
        _trace_entry("Bash", "bash", "x", stage="product-design-docs", timestamp="2026-07-10T10:00:00Z", sequence_id="s2"),
    ]
    metrics, _ = lincoln_benchmark.compute_metrics(trace, state, "S1", base_state.parent.parent)
    assert metrics["workflow"]["stage_completion_rate"] == 0.5
    assert metrics["workflow"]["validation_failure_count"] == 1
    assert metrics["workflow"]["human_gate_pass_rate"] == 0.5
    assert metrics["workflow"]["stage_durations"]["clarify"] == 1800


def test_evaluate_thresholds_other_scenarios():
    metrics = {
        "session": {"retry_count": 4},
        "workflow": {"human_gate_wait_seconds": 2 * 3600},
        "quality": {"pr_size": 500},
        "outcome": {"time_to_pr_seconds": 2 * 3600, "time_to_first_handoff": 3600},
        "collaboration": {},
    }
    assert lincoln_benchmark.evaluate_against_thresholds(metrics, "S3")["retry_count"]["status"] == "red"
    assert lincoln_benchmark.evaluate_against_thresholds(metrics, "S4")["time_to_first_handoff"]["status"] == "yellow"
    assert lincoln_benchmark.evaluate_against_thresholds(metrics, "S5")["time_to_first_handoff"]["status"] == "green"
    assert lincoln_benchmark.evaluate_against_thresholds(metrics, "S2")["pr_size"]["status"] == "yellow"


def test_main_cli(base_state):
    from scripts.lincoln_benchmark import main
    argv = [
        "--state-file", str(base_state),
        "--trigger", "manual",
    ]
    assert main(argv) == 0
    files = list((base_state.parent / "benchmark").glob("lc-benchmark-manual-*.json"))
    assert len(files) >= 1


def test_load_trace_skips_malformed_lines(base_state):
    trace_dir = base_state.parent / ".trace"
    trace_dir.mkdir(exist_ok=True)
    (trace_dir / "lc-trace.jsonl").write_text(
        "not json\n" + json.dumps(_trace_entry("Bash", "bash", "x", sequence_id="s1")) + "\n",
        encoding="utf-8",
    )
    trace = lincoln_benchmark.load_trace(base_state.parent.parent, "lc-test")
    assert len(trace) == 1


def test_run_audit_parses_results_key(tmp_path):
    audit_script = tmp_path / "scripts" / "lincoln-audit.py"
    audit_script.parent.mkdir(parents=True)
    audit_script.write_text(
        '#!/usr/bin/env python3\n'
        'import json\n'
        'print(json.dumps({"results": [{"status": "PASS"}, {"status": "FAIL"}, {"status": "WARN"}]}))\n',
        encoding="utf-8",
    )
    audit_script.chmod(0o755)
    counts = lincoln_benchmark_metrics._run_audit(tmp_path)
    assert counts == {"PASS": 1, "FAIL": 1, "WARN": 1}


def test_run_audit_parses_checks_key(tmp_path):
    audit_script = tmp_path / "scripts" / "lincoln-audit.py"
    audit_script.parent.mkdir(parents=True)
    audit_script.write_text(
        '#!/usr/bin/env python3\n'
        'import json\n'
        'print(json.dumps({"checks": [{"status": "PASS"}, {"status": "PASS"}]}))\n',
        encoding="utf-8",
    )
    audit_script.chmod(0o755)
    counts = lincoln_benchmark_metrics._run_audit(tmp_path)
    assert counts == {"PASS": 2}


def test_load_primary_agents_reads_stage_files(tmp_path):
    stages_dir = tmp_path / ".claude" / "stages"
    stages_dir.mkdir(parents=True)
    (stages_dir / "clarify.yaml").write_text(
        "id: clarify\nagent:\n  primary: lc-pm\n  reviewers:\n  - lc-qa\n",
        encoding="utf-8",
    )
    (stages_dir / "implement.yaml").write_text(
        "id: implement\nagent:\n  primary: lc-engineer\n",
        encoding="utf-8",
    )
    agents = lincoln_benchmark_metrics._load_primary_agents(tmp_path)
    assert agents == {"clarify": "lc-pm", "implement": "lc-engineer"}


def test_load_primary_agents_missing_stages_dir_returns_empty(tmp_path):
    assert lincoln_benchmark_metrics._load_primary_agents(tmp_path) == {}


def test_run_audit_returns_none_when_script_missing(tmp_path):
    assert lincoln_benchmark_metrics._run_audit(tmp_path) is None


def test_run_audit_returns_none_for_invalid_json(tmp_path):
    audit_script = tmp_path / "scripts" / "lincoln-audit.py"
    audit_script.parent.mkdir(parents=True)
    audit_script.write_text("not json\n", encoding="utf-8")
    audit_script.chmod(0o755)
    assert lincoln_benchmark_metrics._run_audit(tmp_path) is None
