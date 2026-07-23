<!-- version: v1.0 -->
<!-- status: draft -->

# PRD: {process_slug}

> 本文档是 issue #{issue_number} 的根级 PRD，位于 `{process_slug}/prd.md`，作为串联整个产研流程的主线文档。
> 经人类 PM 确认后，必须运行 `python scripts/lincoln_prd.py freeze` 生成不可变快照 `prd-v{major}.{minor}.md`。

## 版本历史

| 版本 | 日期 | 修改内容 | 确认人 |
|------|------|----------|--------|
| v1.0 | | 初始版本 | |

## 1. 需求背景

<!-- L1: 人类 PM 确认 -->

-

## 2. 用户故事

<!-- L1: 人类 PM 确认 -->

-

## 3. 功能拆解

<!-- L2: AI 辅助梳理，人类 PM 确认 -->

| 功能编号 | 功能名称 | 优先级 | 对应用户故事 | 验收标准索引 |
|----------|----------|--------|--------------|--------------|
| F-001 | | 高 | | |
| F-002 | | 中 | | |

## 4. 业务流程图

<!-- L2: AI 辅助绘制，人类 PM 确认 -->

```mermaid
graph TD
    A[开始] --> B[步骤]
    B --> C[结束]
```

## 5. 验收标准

<!-- L1: 人类 PM 确认 -->

- [ ] 验收标准 1
- [ ] 验收标准 2

## 6. 业务规则

<!-- L1: 人类 PM 确认 -->

-

## 7. 非功能需求

<!-- L2: AI 辅助梳理，人类 PM 确认 -->

-

## 8. 关联系统/接口

<!-- L2: AI 辅助梳理，人类 PM 确认 -->

-

## 9. 相关产物链接

<!-- 本表格随阶段推进持续更新，确保 PRD 始终是产研主线的单一入口。 -->

| 产物 | 路径 | 说明 |
|------|------|------|
| 访谈摘要 | [`interviews/{session_id}/summary.md`](interviews/{session_id}/summary.md) | 原始访谈提炼 |
| 需求文档 | [`requirements/{session_id}/requirements.md`](requirements/{session_id}/requirements.md) | 澄清后的结构化需求 |
| 用户故事 | [`requirements/{session_id}/user-stories.md`](requirements/{session_id}/user-stories.md) | 用户故事与验收标准 |
| 设计总览 | [`designs/{design_id}/design-review.md`](designs/{design_id}/design-review.md) | product-design-docs 阶段产物 |
| 用户场景 | [`designs/{design_id}/scenarios.md`](designs/{design_id}/scenarios.md) | 用户场景与角色 |
| 功能清单 | [`designs/{design_id}/feature-catalog.md`](designs/{design_id}/feature-catalog.md) | 功能与验收映射 |
| 流程图 | [`designs/{design_id}/flows.md`](designs/{design_id}/flows.md) | 业务流程与界面流转 |
| 页面关系图 | [`designs/{design_id}/page-map.md`](designs/{design_id}/page-map.md) | 页面结构与导航 |
| UI 规格 | [`designs/{design_id}/ui-spec.md`](designs/{design_id}/ui-spec.md) | product-prototype 阶段产物 |
| 原型 | [`designs/{design_id}/prototype.pen`](designs/{design_id}/prototype.pen) | Pencil 可交互原型 |
| TDD 计划 | [`designs/{design_id}/tdd-plan.md`](designs/{design_id}/tdd-plan.md) | tdd-development-plan 阶段产物 |
| OpenSpec 提案 | [`openspec/changes/{change_name}/proposal.md`](openspec/changes/{change_name}/proposal.md) | propose 阶段产物 |

## 10. 风险与开放问题

<!-- L1: 人类 PM 确认 -->

| 风险/问题 | 影响 |  owner  | 状态 |
|-----------|------|---------|------|
| | | | |

---

*PM→UX 交接：本 PRD 是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md`](handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
