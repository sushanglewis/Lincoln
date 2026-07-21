Facts before creating `issue-76/designs/handoff-contracts/scenarios.md`:

1. **Callers/references**: Referenced by `.claude/templates/issue-package/handoffs/pm-to-ux/master-handoff-pm-to-ux.md.tpl` under "角色与用户旅程", and will be linked from `issue-76/handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md`. Required artifact in `.claude/stages/product-design-docs.yaml`: `designs/{design_id}/scenarios.md`.
2. **No existing duplicate**: `Glob("issue-76/designs/handoff-contracts/*")` currently only contains `feature-catalog.md`; `scenarios.md` does not exist.
3. **Data I/O**: Static markdown design artifact; no data files read/written.
4. **User instruction verbatim**: From the plan: "产出完整设计包（含新增 `page-map.md` 设计），生成 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md` 与 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml`；该阶段 exit gate 要求上述产物全部存在且 PM 确认。"

<!-- version: v1.0 -->

# 场景分析: handoff-contracts

## 用户画像

1. **人类 PM**：负责澄清需求，产出 requirement 文档，并在 `product-design-docs` exit gate 确认 PM→UX 交接物完整。
2. **人类 UX**：接手 PM 的交接，阅读 master-handoff 建立全局认知，驱动 UX Agent 工作。
3. **UX Agent**：从 `pm-to-ux.handoff.yaml` 开始阅读，按分层规则读取上下文，产出设计产物。

## 核心场景

### 场景一：PM 完成需求澄清并准备交接

- 触发条件：PM 在 clarify 阶段完成 requirements.md、user-stories.md、prd.md。
- 用户行为：PM 进入 product-design-docs 阶段，产出 design 文档与 PM→UX handoff 产物。
- 预期结果：`product-design-docs` exit gate 通过，handoff 契约被 PM 确认。

### 场景二：UX 接手 issue 并建立全局认知

- 触发条件：PM 已确认 PM→UX 交接。
- 用户行为：UX 打开 `master-handoff-pm-to-ux-v*.md`。
- 预期结果：UX 能独立回答整体功能、角色旅程、流程、页面关系、需求规格位置。

### 场景三：UX Agent 开始工作

- 触发条件：UX 要求 Agent 基于交接文档工作。
- 用户行为：Agent 读取 `pm-to-ux.handoff.yaml`。
- 预期结果：Agent 按 Tier-0 → Tier-1 → Tier-2 顺序读取，不直接读原始录音。

## 边界场景

- 当 `based_on` 文档版本升级时，`handoff_versions_match` 校验失败，提示重新生成契约。

## 异常场景

- 当 `handoffs/pm-to-ux/` 目录不存在时，`init-lincoln-branch.sh` 已预创建，避免遗漏。

---

*PM→UX 交接：本场景分析是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
