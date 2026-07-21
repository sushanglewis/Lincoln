---
name: lc-collect-intelligence
description: 基于权威报告、官方动态、开放 API、官网等渠道，体系化收集研究所需的权威信息并标注来源。
version: 1.0.0
triggers:
  - "lc-collect-intelligence"
inputs:
  - name: topic
    description: 研究主题或产品决策背景
    required: false
outputs:
  - "{process_slug}/research/{session_id}/collected-intelligence.md"
required_tools:
  - Bash
  - Read
  - Write
---

# lc-collect-intelligence

## Purpose

Using [lc-collect-intelligence] to 基于权威报告、官方动态、开放 API、官网等渠道，体系化收集研究所需的权威信息并标注来源.

## When to Use

- `pm-research` workflow 的 `lc-collect-intelligence` 阶段。
- PM 需要 基于权威报告、官方动态、开放 API、官网等渠道，体系化收集研究所需的权威信息并标注来源。 时。

## Inputs

- `session_id`: 研究 session 标识
- 当前阶段之前的所有研究产物

## Outputs

- `{process_slug}/research/{session_id}/collect-intelligence.md`

## Rules

- 严格基于已有研究产物，避免引入未经验证的假设。
- 所有外部事实必须标注来源。
- human_gate 阶段必须获得人类 PM 显式确认。
