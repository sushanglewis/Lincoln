---
name: lc-stakeholder-research
description: 识别并研究产品相关者（用户、买单方、建设方、维护方），找到他们的发声渠道并分析其诉求。
version: 1.0.0
triggers:
  - "lc-stakeholder-research"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/stakeholder-research.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-stakeholder-research

## Purpose

Using [lc-stakeholder-research] to 识别并研究产品相关者（用户、买单方、建设方、维护方），找到他们的发声渠道并分析其诉求.

## When to Use

- `pm-research` workflow 的 `lc-stakeholder-research` 阶段。
- PM 需要 识别并研究产品相关者（用户、买单方、建设方、维护方），找到他们的发声渠道并分析其诉求。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/stakeholder-research.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
