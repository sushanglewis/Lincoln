# Lincoln Benchmark Report

- **Report ID:** `6e5579adda1e4d6f964c464753432996`
- **Scenario:** `S1`
- **Trigger:** `handoff`
- **Generated at:** 2026-07-13T15:35:54Z
- **Process:** issue-47
- **Current stage:** product-design-docs
- **Workflow template:** interview-to-knowledge

## Executive Summary

- Green: 3, Yellow: 0, Red: 3
- Red flags: human_gate_pass_rate, pr_size, tdd_plan_red_green_refactor

## L1 Session Activity

| Metric | Value | Confidence |
|--------|-------|------------|
| `session_duration_seconds` | 2409 | exact |
| `trace_line_count` | 2 | exact |
| `total_tool_calls` | 2 | exact |
| `tool_calls_by_category` | {"handoff": 2} | exact |
| `unique_skills` | — | exact |
| `unique_files_touched` | 0 | exact |
| `test_runs` | 0 | exact |
| `error_count` | 0 | exact |
| `retry_count` | 0 | exact |

## L2 Workflow Progress

| Metric | Value | Confidence |
|--------|-------|------------|
| `stage_transition_count` | 1 | exact |
| `stage_durations` | {"clarify": 0, "ingest": 0} | estimated |
| `stage_completion_rate` | 0.4 | exact |
| `stage_rework_count` | 0 | exact |
| `artifact_completion_rate` | 1.0 | exact |
| `validation_failure_count` | 0 | exact |
| `workflow_adherence_score` | 0.22 | exact |
| `human_gate_count` | 2 | exact |
| `human_gate_wait_seconds` | 0 | estimated |
| `human_gate_pass_rate` | 0.5 | exact |
| `build_codebase_knowledge_duration_seconds` | 0 | estimated |

## L3 Human-AI Collaboration

| Metric | Value | Confidence |
|--------|-------|------------|
| `handoff_count` | 2 | exact |
| `agent_switches` | 0 | pending |
| `pm_turns` | 2 | estimated |
| `time_to_first_handoff` | 0 | exact |

## L4 Output Quality

| Metric | Value | Confidence |
|--------|-------|------------|
| `requirements_clarity_score` | 4 | exact |
| `design_doc_completeness` | 1.0 | exact |
| `tdd_plan_red_green_refactor` | {"red": false, "green": false, "refactor": false} | exact |
| `openspec_task_count` | 0 | exact |
| `static_check_pass` | — | exact |
| `test_coverage` | — | pending |
| `pr_size` | 25702 | exact |
| `audit_score` | {"PASS": 5, "WARN": 2} | exact |
| `code_review_calls` | 0 | exact |

## L5 Business Outcome

| Metric | Value | Confidence |
|--------|-------|------------|
| `issue_closed` | — | pending |
| `pr_merged` | False | exact |
| `pr_merge_latency_seconds` | 0 | pending |
| `knowledge_synced` | — | pending |
| `time_to_pr_seconds` | 0 | exact |
| `time_to_merge_seconds` | 0 | exact |
| `unique_files_touched_ratio` | 0.0 | estimated |

## Threshold Evaluation

| Metric | Value | Status |
|--------|-------|--------|
| `time_to_merge_seconds` | 0 | green |
| `human_gate_wait_seconds` | 0 | green |
| `human_gate_pass_rate` | 0.5 | red |
| `requirements_clarity_score` | 4 | green |
| `pr_size` | 25702 | red |
| `tdd_plan_red_green_refactor` | 0/3 | red |

## Recommendations

- PR size is large; consider splitting the change into smaller reviewable units.

## Data Sources

- `issue-47/.trace/lincoln-trace.jsonl`
