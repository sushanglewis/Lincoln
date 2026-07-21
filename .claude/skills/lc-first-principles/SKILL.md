---
name: lc-first-principles
description: 帮助 PM 回归底层真相，挑战假设，识别第一性原理，为研究奠定坚实基础。
version: 1.0.0
triggers:
  - "lc-first-principles"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/first-principles.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-first-principles

## Purpose

Using [lc-first-principles] to 帮助 PM 回归底层真相，挑战假设，识别第一性原理，为研究奠定坚实基础.

## When to Use

- `pm-research` workflow 的 `lc-first-principles` 阶段。
- PM 需要 帮助 PM 回归底层真相，挑战假设，识别第一性原理，为研究奠定坚实基础。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/first-principles.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
