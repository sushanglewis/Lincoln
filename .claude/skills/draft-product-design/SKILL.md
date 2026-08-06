---
name: draft-product-design
description: 基于已确认需求生成产品设计评审文档包
triggers:
  - "生成产品设计文档"
  - "draft-product-design"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID，如 checkout-redesign
    required: true
outputs:
  - "{process_slug}/pages/docs/design-review.html"
  - "{process_slug}/pages/docs/scenarios.html"
  - "{process_slug}/pages/docs/feature-catalog.html"
  - "{process_slug}/pages/docs/data-model.html"
  - "{process_slug}/pages/docs/flows.html"
  - "{process_slug}/pages/docs/feasibility.html"
  - "{process_slug}/pages/docs/page-map.html"
  - "{process_slug}/pages/docs/version-log.html"
  - "{process_slug}/pages/docs/api-list.html"
  - "{process_slug}/pages/docs/handoff-pm-to-ux-v*.html"
  - "{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml"
  - "{process_slug}/handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md"
required_tools:
  - Read
  - Bash
  - Write
---

# draft-product-design

## Purpose

Using [draft-product-design] to 基于已确认需求生成产品设计评审文档包.


基于已确认需求生成面向 PM 评审的简洁产品设计文档包。

运行入口： prompts/main.md
