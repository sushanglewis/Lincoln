---
name: lc-research-scope
description: 界定 PM 研究工作的范围、目标、问题与验收标准，作为后续研究阶段的单一事实来源。
version: 1.0.0
triggers:
  - "lc-research-scope"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/scope.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-research-scope

## Purpose

Using [lc-research-scope] to 界定 PM 研究工作的范围、目标、问题与验收标准，作为后续研究阶段的单一事实来源.

## When to Use

- `pm-research` workflow 的 `lc-research-scope` 阶段。
- PM 需要 界定 PM 研究工作的范围、目标、问题与验收标准，作为后续研究阶段的单一事实来源。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/scope.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
