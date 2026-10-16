<!-- status: draft -->
# Lincoln PM 阶段多 Agent 体系设计

- Issue: #139 · 分支: issue-139 · 状态: draft（待人类 PM 评审）
- 目标：将「需求 → PRD」的 PM 工作拆解为 6 个专业子阶段，为每个子阶段定义主管 Agent、审阅角色、sub-agent 并行派发协议与 human gate，并落地到 Lincoln 框架（`.claude/agents/`、`.claude/stages/`、`.claude/workflows/`）。

## 1. 设计原则

1. **主管角色 + Task 派发**：每个子阶段由一个主管角色（primary agent）负责汇总与裁决；上下文过大或来源/维度多于一个时，主管经 Task 工具派发 sub-agent 并行处理，不引入 stage YAML 级 fan-out 引擎。
2. **子 agent 契约**：子 agent 遵循 `.claude/agents/default.md` 的 `SUBAGENT-STOP` 块——不重新执行 intake/准入校验/handoff，不写 `{process_slug}/workflow-stage.yaml`，只向主管汇报结果。
3. **人类门控不可跳过**：每个子阶段的定稿处设 `human_gate: true`，由人类 PM 显式 `confirm`；挑战阶段的每一条挑战必须 PM 决策闭环（修复升版 或 记录接受及理由），未决策不得视为闭环。
4. **复用优先**：6 个子阶段尽量复用现有角色（lc-pm / lc-researcher / lc-architect / lc-qa / lc-designer / lc-security-reviewer），仅新增 2 个专职角色（lc-requirement-scout、lc-challenger）。
5. **可追溯**：每条需求可回溯到来源（URL/录音/issue），每个挑战可回溯到提出者与决策记录。

## 2. 六阶段 → 角色映射总表

| # | 子阶段 | 主管角色 | 审阅/并行专家 | human_gate | 关键产物 |
|---|--------|----------|----------------|------------|----------|
| 1 | 需求采集 requirement-intake | lc-requirement-scout（新增） | lc-researcher | 是 | 需求清单 + 来源台账 |
| 2 | 可行性分析 feasibility | lc-pm | lc-researcher / lc-architect（并行专家） | 是 | PRD 可行性章节 |
| 3 | MVP 方案 mvp-design | lc-pm | lc-architect | 是 | 最小成功可行路径 |
| 4 | 方案挑战 challenge | lc-challenger（新增） | lc-pm / lc-architect / lc-qa / lc-security-reviewer | 是 | 挑战报告 + PM 决策记录 |
| 5 | PRD 生成 prd-authoring | lc-pm | lc-designer | 是 | PRD（含 UI/UX、流程图、序列图、业务模型） |
| 6 | 交叉验证 cross-validation | lc-qa | lc-pm / lc-designer（并行专家） | 是 | 一致性校验报告 |

PRD 生成的前置条件：人类 PM 已在 `product-prototype` 阶段通过交互式原型确认过方案（该阶段原有 human_gate 保持不变）。

## 3. 各阶段设计

### 3.1 需求采集（requirement-intake）

- **主管**：lc-requirement-scout。职责：确定采集渠道 → 派发采集 → 去重归并 → 与 PM 确认需求清单。
- **sub-agent 派发触发条件**：来源渠道数 > 1 时按渠道 fan-out。标准渠道：GitHub issue、客诉频道、社区帖子、市场调研、访谈录音（ingest 产物）。
- **每个采集子 agent 的输出契约**：结构化需求条目 `{title, source_url, quote, confidence, date, segments}`；无来源 URL 的条目必须标注录音时间戳。
- **汇总协议**：主管按主题聚类去重，冲突条目并列呈现，由人类 PM 裁决；产出统一需求清单与来源台账。
- **产物**：`{process_slug}/intake/requirements.md`（统一需求清单）、`{process_slug}/intake/sources.md`（来源台账）。

### 3.2 可行性分析（融入 clarify 阶段）

- **主管**：lc-pm；`clarify` stage 的 `agent.parallel_specialists` 登记 lc-researcher、lc-architect。
- **sub-agent 派发**：四路并行——业务可行性、技术可行性（lc-architect）、市场价值（lc-researcher）、业务现状（产品数据/既有 issue）。
- **merge_strategy**：`priority`——主管 lc-pm 拥有最终裁决权，专家意见作为证据附在 PRD 可行性章节。
- **产物**：并入 `{process_slug}/pages/docs/prd.html` 可行性章节与 `feasibility.html`（既有产物，不变）。

### 3.3 MVP 方案（融入 clarify 阶段）

- **主管**：lc-pm，lc-architect 支持。在 PRD 澄清过程中梳理最小成功可行路径（核心用户 × 核心场景 × 最短闭环）。
- **约束**：MVP 范围变更必须回到 human_gate 由 PM 确认。

### 3.4 方案挑战（challenge，新增 stage）

- **主管**：lc-challenger（参照 lc-security-reviewer 红队模式，专职「找设计缺陷」而非「写方案」）。
- **挑战维度（sub-agent fan-out）**：用户（各角色场景覆盖）、边界（输入/状态边界）、异常（失败路径与重试）、兜底（降级与默认值）、安全（权限与数据）、历史数据（存量迁移）、用户迁移（版本兼容）。
- **每条挑战的输出契约**：`{id, dimension, question, severity, evidence, suggestion}`。
- **决策闭环（不可替代为人类 gate）**：lc-challenger 汇总去重后逐条提交人类 PM——「修复（方案升版重冻结）」或「接受（记录理由与影响）」；PM 未逐条决策不得 exit。
- **产物**：`{process_slug}/designs/challenge-report.md`（挑战 + 决策记录一体）。
- **插入点**：`product-design-docs` 之后、`product-prototype` 之前。

### 3.5 PRD 生成（clarify + product-design-docs，既有阶段）

- **主管**：lc-pm，lc-designer 配合。PRD 必须包含 UI/UX 说明、流程图、序列图、业务模型；定稿前完成「需求清晰度六问」自检。
- 既有契约全部保留（PRD 版本标记、freeze 快照、human_gate）。

### 3.6 交叉验证（tdd-development-plan 内，既有机制强化）

- **主管**：lc-qa；复用 `prd-cross-validation.html` 模式。
- **sub-agent 派发**：按文档对并行校验（PRD↔用户故事、PRD↔数据模型、PRD↔流程图、PRD↔原型、PRD↔TDD 计划）。
- **决策权**：发现的缺口必须由人类 PM 决策闭环（修复升版 or 接受），与 lc-pm 角色文件第 8 条一致。

## 4. 子 agent 通用契约

1. 由主管经 Task 工具派发，一次任务一个明确产出；禁止子 agent 自行 fan-out 二级子 agent（二级派发需主管显式授权）。
2. 遵循 `SUBAGENT-STOP`：跳过 intake/准入校验/handoff 发现；不写 `workflow-stage.yaml`。
3. 输出必须结构化并自带来源/证据；主管负责合并、去重与冲突标注。
4. 子 agent 不得替代 human_gate；任何需要人类决策的项一律上交主管，由主管在 gate 处汇总提交 PM。

## 5. 与现有工作流的融合

- **interview-to-knowledge（team，canonical）**：
  - 新增 step `requirement-intake`（ingest → requirement-intake → clarify）。
  - 新增 step `challenge`（product-design-docs → challenge → product-prototype）。
  - `clarify` 阶段 `agent.parallel_specialists` 增加 lc-researcher、lc-architect（可行性四路并行）。
- **pm-research（solo）**：需求采集阶段直接复用其既有 research 序列（lc-research-scope → lc-collect-intelligence 等），不新增 stage；requirement-intake 作为其下游需求清单的标准格式参考。
- **不破坏既有 gate**：所有既有 stage 的 human_gate、exit_checks、产物路径不变；新增 stage 自身的 artifacts 与 workflow step artifacts 严格一致（R3 校验）。

## 6. 框架落地清单（本期 PR）

| 变更 | 文件 |
|------|------|
| 新增角色 | `.claude/agents/requirement-scout.md`、`.claude/agents/challenger.md` |
| 新增 stage | `.claude/stages/requirement-intake.yaml`、`.claude/stages/challenge.yaml` |
| 修改 stage | `ingest.yaml`（next_stage）、`clarify.yaml`（prerequisite + parallel_specialists）、`product-design-docs.yaml`（next_stage）、`product-prototype.yaml`（prerequisite_stage） |
| 修改 workflow | `.claude/workflows/interview-to-knowledge.yaml`（插入两个 step）、`.claude/workflows/README.md`（索引） |
| 适配产物 | `lincoln-setup.py generate-harness` 重新派生 codex/opencode |

## 7. 验收标准

- 新 stage 通过 `stage-definition.schema.json` 与 `scripts/validate_stage.py` 校验。
- `check-prompt-drift.py --strict --focus pm` 无新增告警/错误。
- 本 issue 工作包内 `stage_loader.py validate-entry/validate-exit` 通过。
- 人类 PM 在设计文档与框架变更上均显式确认（human_gate）。
