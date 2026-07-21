# 需求文档: 2026-07-21-lew-49-handoff

<!-- status: approved -->
<!-- version: v1.0 -->

## 背景

- **Issue**: #76（LEW-49）
- **访谈摘要**: `issue-76/interviews/2026-07-21-lew-49-handoff/summary.md`
- **范围**: 先聚焦 PM→UX 交接，暂不处理 UI、前端、研发等后续阶段的交接。

Lincoln 是 AI-Native 产品工作流框架。当前人类 PM 完成需求澄清后，将工作交接给人类 UX 时，UX 无法从 handoff 文件中建立全局认知，进而无法驱动 UX Agent 或承担人类决策职责。本 issue 要求设计并落地 PM→UX 的人-人交接与 Agent-Agent 交接机制。

## 问题

1. 人类 UX 无法通过现有 handoff 文件了解：要做什么、流程是什么、有哪些页面、页面上有什么功能。
2. 缺少面向人类的主文档来组织 issue-package 下的 PM→UX 交接物品。
3. 缺少机器可读的 Agent-Agent 交接契约，无法约束 UX Agent 从哪份文档开始、按什么顺序阅读。
4. 现有 stage gate 没有把 PM→UX 产物作为 PM 准出的硬性标准。

## 用户

| 角色 | 需求 |
|------|------|
| 人类 PM | 在 commit/issue-branch 准出前，明确知道需要产出哪些 PM→UX 交接物 |
| 人类 UX | 只读一份主文档，就能理解全局功能、角色旅程、流程、页面关系、需求规格 |
| UX Agent | 从明确的契约 YAML 开始，按分层规则阅读上下文，避免信息过载 |
| 系统 | 自动校验 handoff 契约有效、版本一致，并索引到 documents.yaml |

## 方案

1. 在 issue-package 中固定 `handoffs/pm-to-ux/` 目录，存放：
   - `master-handoff-pm-to-ux-v{MAJOR}.{MINOR}.md`：人-人交接主文档
   - `pm-to-ux.handoff.yaml`：Agent-Agent 契约
2. 把 PM→UX 产物清单写入 `.claude/stages/clarify.yaml` 与 `.claude/stages/product-design-docs.yaml` 的 `artifacts.required`。
3. 新增 `.claude/templates/issue-package/handoffs/pm-to-ux/` 模板与 `designs/page-map.md.tpl`。
4. 新增 `handoff_contract_valid` 与 `handoff_versions_match` exit checks。
5. 更新 `scripts/stage_loader.py` 在 `handoff-report` 时刷新契约 approval 状态。
6. 更新 `.claude/agents/designer.md`、`_contract.md`，要求 UX Agent 先读契约 YAML。

## 验收标准

- [x] `issue-76/handoffs/pm-to-ux/` 存在 `master-handoff-pm-to-ux-v1.0.md` 与 `pm-to-ux.handoff.yaml`
- [x] `product-design-docs` exit gate 包含 `handoff_contract_valid` 与 `handoff_versions_match`
- [x] `scripts/stage_loader.py --action handoff-report` 能刷新契约 approval 状态
- [x] 未接触 issue 的人类只读 master-handoff 能理解全局
- [x] 新 UX Agent 只读契约 YAML 能复述任务范围
- [x] `page-map.md` 成为 PM→UX 准出的 required artifact

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。*

*PM→UX 交接：本需求文档是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
