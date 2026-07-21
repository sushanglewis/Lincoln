Facts before creating `issue-76/designs/handoff-contracts/flows.md`:

1. **Callers/references**: Referenced by `.claude/templates/issue-package/handoffs/pm-to-ux/master-handoff-pm-to-ux.md.tpl` under "功能流程", and will be linked from `issue-76/handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md`. Required artifact in `.claude/stages/product-design-docs.yaml`: `designs/{design_id}/flows.md`.
2. **No existing duplicate**: `Glob("issue-76/designs/handoff-contracts/*")` does not include `flows.md`.
3. **Data I/O**: Static markdown design artifact; no data files read/written.
4. **User instruction verbatim**: From the plan: "产出完整设计包（含新增 `page-map.md` 设计），生成 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md` 与 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml`；该阶段 exit gate 要求上述产物全部存在且 PM 确认。"

<!-- version: v1.0 -->

# 流程图: handoff-contracts

## 主流程

```mermaid
graph TD
    A[ingest: 文档化输入] --> B[clarify: PM 澄清需求]
    B --> C[product-design-docs: 产出 design 与 handoff]
    C --> D{exit gate 通过?}
    D -->|是| E[product-prototype: UI 规格/字段规格]
    D -->|否| F[PM 补充/修正]
    F --> C
    E --> G[tdd-development-plan]
```

## PM→UX 交接准出流程

```mermaid
graph TD
    A[PM 产出 requirement 文档] --> B[PM 产出 design 文档]
    B --> C[PM 产出 master-handoff]
    C --> D[PM 产出 pm-to-ux.handoff.yaml]
    D --> E[运行 validate-exit]
    E --> F{handoff_contract_valid & handoff_versions_match?}
    F -->|是| G[PM 确认 gate]
    F -->|否| H[修正文档或契约]
    H --> D
```

## 状态机

- `draft` → `validated`（exit gate 通过）
- `validated` → `approved`（PM human_gate 确认）
- `approved` → `handed-off`（UX Agent 开始读取契约）

---

*PM→UX 交接：本流程图是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
