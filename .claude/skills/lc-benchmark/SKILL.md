---
name: lc-benchmark
description: Generate a Lincoln benchmark report on explicit request.
triggers:
  - lc-benchmark
  - 运行 benchmark
  - 生成 benchmark 报告
inputs:
  - name: trigger
    description: Optional trigger context (manual, handoff, pr_created, pr_merged, session_stop)
    required: false
outputs:
  - "{process_slug}/benchmark/lc-benchmark-{trigger}-{timestamp}.md"
  - "{process_slug}/benchmark/lc-benchmark-{trigger}-{timestamp}.json"
required_tools:
  - Bash
---

# lc-benchmark

## Purpose

Using [lc-benchmark] to generate a Lincoln session benchmark report.

Run Lincoln benchmark metrics and write the Markdown + JSON report pair to the
active issue package's `benchmark/` directory. Benchmark is opt-in: it is no
longer triggered automatically on session stop or PR events.

## When to Use

- The PM or QA explicitly asks for a benchmark report.
- After a meaningful milestone (handoff, PR creation/merge) when humans want
to review L1-L5 metrics.
- During release readiness review.

## Inputs

- Active `{process_slug}/workflow-stage.yaml` (auto-resolved).
- Optional `--trigger` context to label the report.

## Outputs

- `{process_slug}/benchmark/lc-benchmark-{trigger}-{timestamp}.md`
- `{process_slug}/benchmark/lc-benchmark-{trigger}-{timestamp}.json`

## Rules

- Default trigger is `manual`.
- Do not run benchmark after every tool use or session stop.
- Reports should be generated only when a human explicitly requests metrics or
when a release/hygiene gate requires them.

## Invocation

Prefer using the `lc-benchmark` command or Skill tool. Equivalent CLI:

```bash
python3 scripts/lc-benchmark-cli.py
python3 scripts/lc-benchmark-cli.py --trigger handoff
python3 scripts/lc-benchmark-cli.py --state-file issue-<N>/workflow-stage.yaml --trigger manual
```
