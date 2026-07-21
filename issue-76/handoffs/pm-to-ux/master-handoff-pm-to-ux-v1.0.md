<!-- version: v1.0 -->
<!-- status: approved -->

# PM→UX 交接总览: LEW-49 / GitHub #76

## 1. 这个故事怎么走到今天

本 issue（LEW-49 / GitHub #76）源于 Lincoln 工作流中的人类 PM 向人类 UX 交接时，UX 无法从现有 handoff 文件中建立全局认知。UX 明确需要五项信息：整体功能、角色及用户旅程、功能流程、页面与页面关系、具体需求规格说明书。

已确认关键决策：

- 先聚焦 **PM→UX 交接**；UI、前端、研发等后续交接暂不处理。
- 交接产物集中在 `issue-{N}/handoffs/pm-to-ux/`。
- Agent-Agent 契约格式为 **YAML**，版本 scheme 为 `v{MAJOR}.{MINOR}`。
- `prototype.pen` 由 **UI 在 UX 节点之后**产出，不属于 PM→UX 准出范围。
- 非 interview 工作流的 stage gate 不匹配问题 **另开 issue** 处理。

## 2. UX 要做什么

### 任务范围

1. 阅读本总览，建立全局认知。
2. 按需深入 Tier-2 文档（功能目录、场景、流程、页面关系、需求规格）。
3. 确认开放问题已澄清或已分配 owner。
4. 驱动 UX Agent 时，要求 Agent 先读 `pm-to-ux.handoff.yaml`，再读本总览，然后按 Tier-2 链接继续。

### 验收标准

- [x] 未接触 issue 的人类只读本总览能理解全局功能、角色旅程、流程、页面关系、需求规格位置。
- [x] 新 UX Agent 只读 `pm-to-ux.handoff.yaml` 能复述任务范围。
- [x] `product-design-docs` exit gate 检查 handoff 契约有效且版本一致。

## 3. 整体功能

见 [`designs/handoff-contracts/feature-catalog.md`](../../designs/handoff-contracts/feature-catalog.md)。

核心功能：

- F-001 人-人交接主文档
- F-002 Agent-Agent 交接契约
- F-003 页面关系图
- F-004 Stage 准出检查
- F-005 自动状态刷新
- F-006 文档索引版本
- F-007 工作包预创建

## 4. 角色与用户旅程

见 [`designs/handoff-contracts/scenarios.md`](../../designs/handoff-contracts/scenarios.md) 与 [`requirements/2026-07-21-lew-49-handoff/user-stories.md`](../../requirements/2026-07-21-lew-49-handoff/user-stories.md)。

主要角色：人类 PM、人类 UX、UX Agent、Lincoln 系统。

## 5. 功能流程

见 [`designs/handoff-contracts/flows.md`](../../designs/handoff-contracts/flows.md)。

主流程：ingest → clarify → product-design-docs → product-prototype → tdd-development-plan。
PM→UX 交接准出流程：PM 产出 requirement/design/handoff → 运行 validate-exit → PM 确认 gate。

## 6. 页面与页面关系

见 [`designs/handoff-contracts/page-map.md`](../../designs/handoff-contracts/page-map.md)。

关键页面：PM→UX 交接总览（P-001，入口页）、功能目录、场景分析、流程图、页面关系图、需求规格。

## 7. 需求规格说明书

- [`requirements/2026-07-21-lew-49-handoff/requirements.md`](../../requirements/2026-07-21-lew-49-handoff/requirements.md)
- [`requirements/2026-07-21-lew-49-handoff/prd.md`](../../requirements/2026-07-21-lew-49-handoff/prd.md)

## 8. 开放问题与待决策点

| 编号 | 问题 | Owner | 状态 |
|------|------|-------|------|
| Q-001 | UI→前端、前端→研发等后续交接是否复用本模式？ | 后续 issue | open |
| Q-002 | `page-map.md` 是否需要在 product-prototype 阶段补充交互细节？ | UI 阶段 | open |

## 9. PM 回执

- [x] PM 已确认 PM→UX 交接产物完整
- [x] PM 已确认 `page-map.md` 纳入 PM→UX 准出清单
- [x] PM 已确认 `prototype.pen` 由 UI 阶段产出，不属于 PM→UX 准出范围

---

*Agent 契约指针: [`pm-to-ux.handoff.yaml`](./pm-to-ux.handoff.yaml)*
