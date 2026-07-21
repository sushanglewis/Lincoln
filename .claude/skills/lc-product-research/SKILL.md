---
name: lc-product-research
description: 研究相关产品/解决方案的能力、价值主张、使用场景与优劣势。
version: 1.0.0
triggers:
  - "lc-product-research"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/product-research.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-product-research

## Purpose

Using [lc-product-research] to 研究相关产品/解决方案的能力、价值主张、使用场景与优劣势.

## When to Use

- `pm-research` workflow 的 `lc-product-research` 阶段。
- PM 需要 研究相关产品/解决方案的能力、价值主张、使用场景与优劣势。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/product-research.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
