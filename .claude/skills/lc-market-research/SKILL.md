---
name: lc-market-research
description: 分析市场规模、趋势、细分与动态，为产品定位与机会判断提供事实基础。
version: 1.0.0
triggers:
  - "lc-market-research"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/market-research.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-market-research

## Purpose

Using [lc-market-research] to 分析市场规模、趋势、细分与动态，为产品定位与机会判断提供事实基础.

## When to Use

- `pm-research` workflow 的 `lc-market-research` 阶段。
- PM 需要 分析市场规模、趋势、细分与动态，为产品定位与机会判断提供事实基础。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/market-research.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
