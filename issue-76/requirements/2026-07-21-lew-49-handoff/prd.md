# PRD: 2026-07-21-lew-49-handoff

<!-- version: v1.0 -->

## 产品目标

为 Lincoln 建立标准化、可校验、对人类和 Agent 都友好的 PM→UX 交接机制，使 UX 能在接手 issue 的第一时间建立全局认知并驱动 Agent 工作。

## 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| F-001 人-人交接主文档 | 在 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md` 中组织所有 PM→UX 交接物品 | 高 |
| F-002 Agent-Agent 契约 | 在 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml` 中声明阅读顺序、版本、开放问题、approval | 高 |
| F-003 页面关系图 | 新增 `designs/{design_id}/page-map.md` 描述页面与页面关系 | 高 |
| F-004 Stage 准出检查 | 在 `product-design-docs` exit gate 检查 handoff 契约有效性与版本一致性 | 高 |
| F-005 自动状态刷新 | `stage_loader.py --action handoff-report` 自动刷新契约 approval 状态 | 中 |
| F-006 文档索引版本 | `lincoln_documents.py` 索引 handoff 文档并解析版本 | 中 |
| F-007 工作包预创建 | `init-lincoln-branch.sh` 预创建 `handoffs/pm-to-ux/` 目录 | 中 |

## 非功能需求

- 模板与实例分离：模板只读地保留在 `.claude/templates/issue-package/`，实例写在工作包中。
- 版本 scheme：统一使用 `v{MAJOR}.{MINOR}`。
- 松耦合：主文档只通过 md 链接路由，不内嵌详细内容。
- 可扩展：契约 schema 先以 PM→UX 为例，后续可泛化为通用 Agent handoff schema。

## 发布标准

- 所有新增模板、stage、workflow、agent、script 变更提交到 issue-76 分支。
- `issue-76` 工作包内产出完整 ingest、clarify、product-design-docs 产物。
- `python3 scripts/stage_loader.py --stage product-design-docs --action validate-exit` 通过。

## 风险

- `prototype.pen` 在 product-prototype 阶段由 UI 产出，若后续 workflow 调整可能影响本设计；当前已将其降为 optional。
- 非 interview 工作流 stage gate 不匹配是 latent bug，已决定另开 issue 处理。

---

*PM→UX 交接：本 PRD 是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
