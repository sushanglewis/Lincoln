Facts before creating `issue-76/designs/handoff-contracts/feature-catalog.md`:

1. **Callers/references**: This file is referenced by the PM→UX master handoff template (`.claude/templates/issue-package/handoffs/pm-to-ux/master-handoff-pm-to-ux.md.tpl`) under the "整体功能" section, and will be linked from `issue-76/handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md`. It corresponds to the required artifact `designs/{design_id}/feature-catalog.md` declared in `.claude/stages/product-design-docs.yaml`.
2. **No existing duplicate**: `Glob("issue-76/designs/handoff-contracts/*")` returns no matches; the directory does not yet exist.
3. **Data I/O**: This is a static markdown design artifact. It does not read or write data files, secrets, or runtime state.
4. **User instruction verbatim**: From the plan: "产出完整设计包（含新增 `page-map.md` 设计），生成 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md` 与 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml`；该阶段 exit gate 要求上述产物全部存在且 PM 确认。"

<!-- version: v1.0 -->

# 功能目录: handoff-contracts

## 功能清单

| 功能编号 | 功能名称 | 优先级 | 验收标准 |
|----------|----------|--------|----------|
| F-001 | 人-人交接主文档 | 高 | `handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md` 存在，且通过链接可访问所有 Tier-2 产物 |
| F-002 | Agent-Agent 交接契约 | 高 | `handoffs/pm-to-ux/pm-to-ux.handoff.yaml` 存在，包含 context_pack、reading_rules、approval |
| F-003 | 页面关系图 | 高 | `designs/{design_id}/page-map.md` 存在，描述页面与页面关系 |
| F-004 | Stage 准出检查 | 高 | `product-design-docs` exit gate 调用 `handoff_contract_valid` 与 `handoff_versions_match` |
| F-005 | 自动状态刷新 | 中 | `handoff-report` 刷新契约 approval 状态 |
| F-006 | 文档索引版本 | 中 | `documents.yaml` 显示 handoff 文档版本 |
| F-007 | 工作包预创建 | 中 | `init-lincoln-branch.sh` 创建 `handoffs/pm-to-ux/` |

## 非功能需求

- 可维护性：模板集中放在 `.claude/templates/issue-package/`，不复制进每个工作包。
- 可扩展性：契约 schema 先聚焦 PM→UX，字段命名保留泛化空间。
- 一致性：所有 handoff 文档使用 `v{MAJOR}.{MINOR}` 版本。

## 验收映射

- [x] F-001 对应验收标准
- [x] F-002 对应验收标准
- [x] F-003 对应验收标准
- [x] F-004 对应验收标准

---

*PM→UX 交接：本清单是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
