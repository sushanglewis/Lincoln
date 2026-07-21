---
name: lc-competitive-analysis
description: 分析竞争格局，评估竞争对手定位、能力、优势与劣势，形成差异化洞察。
version: 1.0.0
triggers:
  - "lc-competitive-analysis"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/competitive.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-competitive-analysis

## Purpose

Using [lc-competitive-analysis] to 分析竞争格局，评估竞争对手定位、能力、优势与劣势，形成差异化洞察.

## When to Use

- `pm-research` workflow 的 `lc-competitive-analysis` 阶段。
- PM 需要 分析竞争格局，评估竞争对手定位、能力、优势与劣势，形成差异化洞察。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/competitive-analysis.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
