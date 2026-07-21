Facts before creating `issue-76/designs/handoff-contracts/data-model.md`:

1. **Callers/references**: This document describes the data model for the PM→UX handoff contract. It supports the `pm-to-ux.handoff.yaml` schema and is part of the design package for `handoff-contracts`.
2. **No existing duplicate**: `Glob("issue-76/designs/handoff-contracts/*")` does not include `data-model.md`.
3. **Data I/O**: Static markdown design artifact; no data files read/written. Field names listed are synthetic/specification only.
4. **User instruction verbatim**: From the plan: "产出完整设计包（含新增 `page-map.md` 设计），生成 `handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md` 与 `handoffs/pm-to-ux/pm-to-ux.handoff.yaml`；该阶段 exit gate 要求上述产物全部存在且 PM 确认。"

<!-- version: v1.0 -->

# 数据模型: handoff-contracts

## 核心实体

### HandoffContract

| 字段 | 类型 | 说明 |
|------|------|------|
| contract_version | string | 契约 schema 版本，如 "1.0.0" |
| issue_number | string | GitHub issue 编号 |
| feature_slug | string | design_id |
| from_stage | string | 上游阶段 |
| to_stage | string | 下游阶段 |
| from_agent | string | 上游 Agent 角色 |
| to_agent | string | 下游 Agent 角色 |
| handoff_type | string | "pm-to-ux" |
| human_master_doc | object | {path, version} |
| based_on | array | [{path, version}] |
| context_pack | object | {tier_0, tier_1, tier_2} |
| reading_rules | array | 字符串规则列表 |
| open_questions | array | [{id, question, owner, status}] |
| approval | object | {pm_confirmed, approved_at, approved_by} |

### DocumentIndexEntry

| 字段 | 类型 | 说明 |
|------|------|------|
| path | string | 工作包内相对路径 |
| stage | string | 产生该文档的阶段 |
| status | string | 节点状态 |
| gate_passed | boolean | 是否通过 gate |
| human_confirmed | boolean | 是否人工确认 |
| approved_by | string | 确认者 |
| version | string | 检测到的版本（仅 handoff 文档） |
