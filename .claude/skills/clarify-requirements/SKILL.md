---
name: clarify-requirements
description: 基于访谈内容与人类 PM 多轮澄清需求
triggers:
  - "澄清需求"
  - "clarify-requirements"
inputs:
  - name: session_id
    description: 访谈会话 ID，如 2026-06-27-stakeholder
    required: true
outputs:
  - "{process_slug}/pages/docs/requirements.html"
  - "{process_slug}/pages/docs/stakeholders.html"
  - "{process_slug}/pages/docs/user-stories.html"
  - "{process_slug}/pages/docs/prd.html"
  - "{process_slug}/pages/docs/snapshots/prd-v*.html"
required_tools:
  - Read
  - Bash
  - Write
  - Edit
---

# clarify-requirements

## Purpose

Using [clarify-requirements] to 基于访谈内容与人类 PM 多轮澄清需求.


基于访谈 transcript 和 summary 与人类 PM 多轮澄清，输出统一需求文档。

运行入口： prompts/main.md

**制品生成纪律**：在执行 prompts/main.md 中的任何写作步骤前，必须先 Read `.claude/policies/less-is-more.md`，并在交付前完成其中的删除测试。
