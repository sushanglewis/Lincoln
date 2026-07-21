---
name: lc-storytelling
description: 基于金字塔原理与科学论述逻辑，将研究成果结构化为动人的、可说服决策者的故事。
version: 1.0.0
triggers:
  - "lc-storytelling"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/narrative.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-storytelling

## Purpose

Using [lc-storytelling] to 基于金字塔原理与科学论述逻辑，将研究成果结构化为动人的、可说服决策者的故事.

## When to Use

- `pm-research` workflow 的 `lc-storytelling` 阶段。
- PM 需要 基于金字塔原理与科学论述逻辑，将研究成果结构化为动人的、可说服决策者的故事。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/storytelling.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
