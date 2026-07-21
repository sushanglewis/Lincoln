---
name: lc-analyze-frameworks
description: 提供并应用分析框架（SWOT、波特五力、商业模式画布、PEST、用户分析等），必要时生成 ECharts/HTML 可视化方案。
version: 1.0.0
triggers:
  - "lc-analyze-frameworks"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/analysis-frameworks.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-analyze-frameworks

## Purpose

Using [lc-analyze-frameworks] to 提供并应用分析框架（SWOT、波特五力、商业模式画布、PEST、用户分析等），必要时生成 ECharts/HTML 可视化方案.

## When to Use

- `pm-research` workflow 的 `lc-analyze-frameworks` 阶段。
- PM 需要 提供并应用分析框架（SWOT、波特五力、商业模式画布、PEST、用户分析等），必要时生成 ECharts/HTML 可视化方案。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/analyze-frameworks.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
