---
name: build-product-prototype
description: 基于已确认设计文档生成字段、界面规格和 Pencil 原型
triggers:
  - "生成产品原型"
  - "build-product-prototype"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID
    required: true
outputs:
  - "{process_slug}/pages/docs/fields.html"
  - "{process_slug}/pages/docs/ui-spec.html"
  - "{process_slug}/pages/prototype/**/*.html"
  - "{process_slug}/designs/{design_id}/prototype.pen"
required_tools:
  - Read
  - Bash
  - Write
  - mcp__pencil__batch_design
---

# build-product-prototype

## Purpose

Using [build-product-prototype] to 基于已确认设计文档生成字段、界面规格和 Pencil 原型.


基于已确认设计文档生成字段规格、UI 规格和 Pencil 原型。

运行入口： prompts/main.md

**制品生成纪律**：在执行 prompts/main.md 中的任何写作步骤前，必须先 Read `.claude/policies/less-is-more.md`，并在交付前完成其中的删除测试。
