---
name: lc-research-report
description: 整合 PM 研究全流程产物，输出可交付、可沉淀的研究报告。
version: 1.0.0
triggers:
  - "lc-research-report"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/report.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-research-report

## Purpose

Using [lc-research-report] to 整合 PM 研究全流程产物，输出可交付、可沉淀的研究报告.

## When to Use

- `pm-research` workflow 的 `lc-research-report` 阶段。
- PM 需要 整合 PM 研究全流程产物，输出可交付、可沉淀的研究报告。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/report.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
