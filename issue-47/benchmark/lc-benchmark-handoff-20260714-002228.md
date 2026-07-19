# Lincoln Benchmark Report

- **Report ID:** `e1c3982667f543b2b4106d15b4cd3907`
- **Scenario:** `S1`
- **Trigger:** `handoff`
- **Generated at:** 2026-07-14T00:22:28Z
- **Process:** issue-47
- **Current stage:** sync-knowledge
- **Workflow template:** interview-to-knowledge

## Executive Summary

- Green: 6, Yellow: 0, Red: 1
- Red flags: pr_size

## L1 Session Activity

| Metric | Value | Confidence |
|--------|-------|------------|
| `session_duration_seconds` | 0 | estimated |
| `trace_line_count` | 1 | exact |
| `total_tool_calls` | 1 | exact |
| `tool_calls_by_category` | {"handoff": 1} | exact |
| `unique_skills` | — | exact |
| `unique_files_touched` | 0 | exact |
| `test_runs` | 0 | exact |
| `error_count` | 0 | exact |
| `retry_count` | 0 | exact |

## L2 Workflow Progress

| Metric | Value | Confidence |
|--------|-------|------------|
| `stage_transition_count` | 0 | exact |
| `stage_durations` | {"tdd-development-plan": 0, "clarify": 0, "product-design-docs": 0, "propose": 0, "ingest": 0, "split": 0, "implement": 0, "product-prototype": 0} | estimated |
| `stage_completion_rate` | 0.53 | exact |
| `stage_rework_count` | 0 | exact |
| `artifact_completion_rate` | 0.0 | exact |
| `validation_failure_count` | 0 | exact |
| `workflow_adherence_score` | 0.11 | exact |
| `human_gate_count` | 0 | exact |
| `human_gate_wait_seconds` | 0 | estimated |
| `human_gate_pass_rate` | 1.0 | exact |
| `build_codebase_knowledge_duration_seconds` | 0 | estimated |

## L3 Human-AI Collaboration

| Metric | Value | Confidence |
|--------|-------|------------|
| `handoff_count` | 1 | exact |
| `agent_switches` | 0 | pending |
| `pm_turns` | 0 | estimated |
| `time_to_first_handoff` | 0 | exact |

## L4 Output Quality

| Metric | Value | Confidence |
|--------|-------|------------|
| `requirements_clarity_score` | 4 | exact |
| `design_doc_completeness` | 1.0 | exact |
| `tdd_plan_red_green_refactor` | {"red": true, "green": true, "refactor": true} | exact |
| `openspec_task_count` | 0 | exact |
| `static_check_pass` | True | exact |
| `test_coverage` | — | pending |
| `pr_size` | 27504 | exact |
| `audit_score` | {"PASS": 4, "WARN": 3} | exact |
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
| `human_gate_pass_rate` | 1.0 | green |
| `requirements_clarity_score` | 4 | green |
| `static_check_pass` | True | green |
| `pr_size` | 27504 | red |
| `tdd_plan_red_green_refactor` | 3/3 | green |

## Recommendations

- PR size is large; consider splitting the change into smaller reviewable units.

## Data Sources

- `issue-47/.trace/lc-trace.jsonl`
