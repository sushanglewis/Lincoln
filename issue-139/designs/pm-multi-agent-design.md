<!-- status: draft -->
<!-- version: v0.4 -->
# Lincoln PM 阶段多 Agent 体系设计

- Issue: #139 · 分支: issue-139 · 状态: draft（待人类 PM 评审）
- 目标：构建 **lc-pm（总协调）→ lc-pm-\*（阶段主管）→ lc-pm-\*-\*（执行 agent）** 三层组织；每层只加载与其职责相关的最小上下文；完整六子阶段流程（`pm-team`）为**显式可选**，默认轻量，避免 Lincoln 变重难用。

## 0. 研究依据

调研见 `issue-139/research/2026-10-19-pm-multi-agent-research/findings.md`（MetaGPT / ChatDev / AG2 / OpenAI Agents SDK / CrewAI / PyRIT）。取向：Flows 确定性流水线 + 层级委派；结构化红队（challenge-feedback.json）；显式 human-in-the-loop；避免端到端全自动、GroupChat 定序、无契约派发、单点上下文爆炸。

## 1. 设计原则

1. **三层组织，分层契约**：lc-pm 唯一面向人类 PM；六个 lc-pm-* 主管对 lc-pm 负责；lc-pm-*-* 执行 agent 遵循**轻契约**（brief 内嵌），不继承 Lincoln 全量角色契约——不同层级的上下文需求不同，契约必须不同构。
2. **主 agent 不撰写提示词**：主管排遣时从 `.claude/templates/dispatch/` 取模板**机械填槽**；主管的角色文件只保留「什么任务交给谁 + 对方输出什么 + 模板路径」的排遣规范表。
3. **计划即授权**：fan-out 许可随阶段计划一次授予；计划外排遣再报批。
4. **human_gate 不可跳过**；挑战与交叉验证逐条决策闭环。
5. **轻默认、重可选**：完整六子阶段（pm-team）由人类 PM 显式选择，router 不得默认启用，避免所有需求被迫走重流程。

## 2. 三层组织模型

```
人类 PM
  └── lc-pm（tier-1 总协调者，唯一人类接口）
        ├── lc-pm-intake ── lc-pm-intake-github / -support / -community / -market / -interview
        ├── lc-pm-analyst ── lc-pm-analyst-business / -tech / -market / -current
        ├── lc-pm-mvp ── lc-pm-mvp-persona / -scenario / -path
        ├── lc-pm-challenge ── lc-pm-challenge-user / -boundary / -exception / -fallback / -security / -legacy / -migration
        ├── lc-pm-author ── lc-pm-author-requirements / -stories / -flows / -model
        └── lc-pm-validator ── lc-pm-validator-prd-stories / -prd-model / -prd-flows / -prd-proto / -prd-tdd
```

### 2.1 分层上下文契约与预算（v0.4 核心）

| 层 | 加载什么 | 明确不加载 | 上下文预算原则 |
|----|----------|------------|----------------|
| lc-pm（tier-1） | default.md 契约、当前 stage 摘要、六主管排遣规范表索引、决策日志 | tier-3 的原始产出、主管的过程稿 | 只见「整合后的 gate 材料」，不见原始 fan-out 产物 |
| lc-pm-*（tier-2） | 自身角色文件（含排遣规范表 + 模板路径）、lc-pm 简报、上游产物、brief 模板（填槽时读取） | 其他主管的过程稿、workflow 全量状态 | 排遣时**读模板填槽，不撰写提示词**；brief 模板文件平时不进上下文 |
| lc-pm-*-*（tier-3） | **仅 brief 本身**（内嵌轻契约 + 任务参数 + 输出契约） | default.md 全量契约、stage yaml、workflow-stage.yaml、门户 | 一次性执行体：最小输入、结构化输出、返回即焚 |

关键决策：tier-3 不继承 `default.md`——全量契约（工作流、门控、交接、红灯规则）对执行单元是噪声。轻契约随 brief 模板携带（4 条规则），执行 agent 的上下文 = 简报本身，这是各 agent 上下文优化的基石。

### 2.2 排遣模板机制（主 agent 减压）

- `.claude/templates/dispatch/` 六个模板：`intake-brief.md`、`analysis-brief.md`、`mvp-brief.md`、`challenge-brief.md`、`doc-draft-brief.md`、`gap-audit-brief.md`。
- 模板结构 = 轻契约（4 条）+ 任务参数槽位（渠道/维度/目标/输入/完成标准/边界）。
- 主管 SOP 第 3 步固定为「取模板 → 机械填槽 → Task 派发」，禁止临场撰写提示词；主管只需知道**任务→人→输出**三元组（排遣规范表），这就是主 agent 需要知道的全部。
- 排遣数量上限内嵌各主管角色文件（3–5 个），default.md 的子代理调度原则继续兜底。

### 2.3 Harness 适配（Claude Code / Codex / OMC）

| Harness | 排遣载体 | 上下文策略 |
|---------|----------|------------|
| Claude Code | Task 工具派发；主管主会话承载 tier-1/2 契约 | 模板填槽后直接 Task；子 agent 只收到 brief 文本 |
| Codex | 本仓库 AGENTS.md 由 adapter 从 `.claude/agents/*.md` 派生（你正在读的就是）；tier-3 经 harness 的子 agent 派发能力 | brief 模板同样经 `templates/dispatch/` 承载，与 harness 无关；adapter 只翻译角色契约，不翻译 brief |
| OMC（oh-my-claudecode，可选层） | 编排型技能（plan/team/verify）增强主管调度能力 | Lincoln 不依赖 OMC；声明为 optional dependency，缺失时 tier-2 用 Task 直派 |

设计要点：**排遣表达与 harness 无关**——模板 + 填槽 + SMART 是通用契约；各 harness 的差异由 `lincoln_harness_adapter.py` 在契约承载层消化（claude → agents/*.md + hooks；codex → AGENTS.md），运行期 dispatch 由各 harness 原生子 agent 能力执行。hooks 零改动：`on-session-start.sh` 按 current_stage 自动加载 stage 上下文与主管 agent 文件。

### 2.4 tier-1 / tier-2 / tier-3 职责速览

- **lc-pm（tier-1）**：方法论——单一人类接口、计划即授权、不越级指挥、跨阶段一致性把关。SOP——启动确认 → SMART 简报 → 计划审批 → gate 呈现 → 决策登记分派 → handoff。产出物——决策日志、审批记录、handoff 文档、状态推进。
- **lc-pm-\*（tier-2）**：通用 SOP——接收简报 → 阶段计划（排遣清单报批）→ 模板填槽排遣 → 整合校验 → gate 材料 → 决策修订 → 移交。各角色文件含方法论 3 条、产出物清单、排遣规范表（触发条件/简报要点/输出契约/数量上限/模板路径）。
- **lc-pm-\*-\*（tier-3）**：轻契约 4 条（只做简报内任务/结构化输出自带证据/边界外上报不扩张/自检后返回）；禁止越级沟通、替 PM 决策、未授权二级 fan-out。

### 2.5 沟通与升级协议

| 通道 | 内容 | 规则 |
|------|------|------|
| 人类 PM ↔ lc-pm | 目标确认、gate 确认、逐条决策 | 唯一直接通道 |
| lc-pm ↔ lc-pm-* | 简报、计划审批、gate 材料、决策分派 | 只见整合产物，不见 tier-3 原始输出 |
| lc-pm-* ↔ lc-pm-*-* | 模板填槽简报、结构化产物回收 | 主管验收后才可采用 |
| 跨阶段 | handoff 文档（经 lc-pm） | 主管之间不横向私传产物 |

## 3. 六阶段 → 角色映射总表

| # | 子阶段 | tier-2 主管 | 承载 stage（pm-team） | human_gate | 关键产物 |
|---|--------|------------|----------------------|------------|----------|
| 1 | 需求采集 | lc-pm-intake | requirement-intake | 清单确认 | 需求清单 + 来源台账 |
| 2 | 可行性分析 | lc-pm-analyst | clarify（并行专家） | 矛盾项决策 | PRD 可行性章节 |
| 3 | MVP 方案 | lc-pm-mvp | clarify（并行专家） | 范围确认 | 最小成功可行路径 |
| 4 | 方案挑战 | lc-pm-challenge | challenge | 逐条决策 | 挑战报告 + PM 决策记录 |
| 5 | PRD 生成 | lc-pm-author | clarify + product-design-docs（主管） | PRD 定稿 + 原型确认 | PRD（UI/UX、流程图、序列图、业务模型） |
| 6 | 交叉验证 | lc-pm-validator | tdd-development-plan（reviewer） | 缺口闭环 | 一致性校验报告 |

共享 stage（clarify / product-design-docs / product-prototype / tdd-development-plan）同时服务于既有轻量工作流；tier-2 主管在轻量模式下按需介入，不叠加额外 gate。已知 schema 限制：stage `agent.primary` 为 per-stage 单值，轻量模式下 clarify 的驻场主管语义由 lc-pm 委派规则（prompt 层）承载，不引入代码改动。

## 4. 模式选择：轻默认、重可选（v0.4 新增）

- **默认轻量**：`interview-to-knowledge` 等既有工作流恢复原序（ingest → clarify → product-design-docs → product-prototype → …），不含 requirement-intake / challenge；tier-2 主管按阶段需要介入。
- **重型可选**：新增 `pm-team` 工作流（team）：workflow-router → requirement-intake → clarify → product-design-docs → challenge → product-prototype → tdd-development-plan，六子阶段全流程。
- **启用前人类确认**：lc-workflow-router 推荐 pm-team 时必须向人类 PM 说明流程重量（+2 stage、+2 human_gate、挑战逐条决策），PM 显式选择才启用；决定记入决策日志与 `.context/lc-intake.md`。该规则已固化在 `pm.md`（执行模式规则）与 `router-prompt.md`。

## 5. 各阶段设计要点

1. **需求采集**（lc-pm-intake）：渠道即并行单元；三级条目 `{title, source_url, quote, confidence, date, segments}`；取舍经 lc-pm 呈 PM。
2. **可行性分析**（lc-pm-analyst）：四路正交（business/tech/market/current）；矛盾项标注待决策。
3. **MVP 方案**（lc-pm-mvp）：最小成功路径 = 核心用户 × 核心场景 × 最短闭环；范围变更是 PM 决策。
4. **方案挑战**（lc-pm-challenge）：七维度红队；输出契约 `challenge-feedback.json`（id/dimension/question/severity/evidence/suggestion，pm_decision 留空待 PM）。
5. **PRD 生成**（lc-pm-author）：PRD 主线文档；六问自检；业务与技术分离；原型确认后 freeze。
6. **交叉验证**（lc-pm-validator）：文档对并行校验；缺口逐条 PM 闭环。

## 6. 与现有工作流的融合

- `interview-to-knowledge` 恢复原序（轻量默认）；requirement-intake / challenge 两 stage 的 `workflows` 登记为 `pm-team`；共享 stage 的 workflows 列表追加 `pm-team`。
- 路由：`lc-workflow-router` 增加 pm-team 信号与「重型须显式选择」规则；lc-wf 命令映射登记 `lc-wf-pm-team`。
- 既有 gate、exit_checks、产物路径不变。

## 7. 框架落地清单

| 变更 | 文件 |
|------|------|
| 角色 | `pm.md`（tier-1 + 执行模式规则）；`pm-intake/analyst/mvp/challenge/author/validator.md`（排遣规范表含模板列） |
| 排遣模板 | `.claude/templates/dispatch/*.md`（6 个，内嵌 tier-3 轻契约） |
| 工作流 | 新增 `pm-team.yaml`；`interview-to-knowledge.yaml` 恢复原序 |
| stage 接线 | requirement-intake/challenge 归 pm-team；共享 stage workflows 追加 pm-team；其余接线同 v0.3 |
| schema | `.claude/schemas/challenge-feedback.json`（同 v0.2） |
| 路由 | `lc-workflow-router/prompts/router-prompt.md`、`lc-wf/SKILL.md`、`workflows/README.md` |

## 7.5 评审前加固裁决（2026-10-19，回应评审计划提出的四个问题）

1. **「计划即授权」× default.md 原则 3 的冲突**：已在 `default.md` 子代理调度原则第 3 条增加 pm 三层体系例外条款——获批阶段计划范围内的排遣视为已授权，计划外仍逐次报批；例外不适用于其他角色与主会话 fan-out。
2. **tier-3 可回溯引用统一**：六个 dispatch 模板的轻契约第 2 条均显式要求「返回须附可回溯引用」（来源 URL / 时间戳 / 产物章节 / 条目 ID，按模板类型具体化）。
3. **轻量模式判定标准**（lc-pm.md）：tier-2 介入不得改变产物清单、不得新增 human_gate、不得新增与人类 PM 的交互轮次；预计需要新增确认轮次时应建议升级 pm-team。
4. **可行性双写裁决**：业务可行性与四路汇总结论的唯一权威源 = PRD 可行性章节（clarify 产出）；`feasibility.html` 仅承载技术可行性归档，不复制 PRD 结论，双向链接，漂移时以 PRD 为准。

## 8. 已知限制（补充）

- **Codex adapter 与 tier 隔离**：codex 会话通过 AGENTS.md 一次性注入全部角色契约（tier-1/2 同上下文），tier 隔离在 codex 侧仅在排遣时成立（brief 才注入 tier-3 上下文）；这与 Claude Code 按需加载等价但不完全同构，列为 harness 级已知限制，不阻塞。

## 9. 验收标准

- 新 stage / 工作流通过 schema 校验；`check-prompt-drift.py --strict --focus pm` 无新增告警/错误。
- tier-3 轻契约只存在于 brief 模板，未被任何全量契约依赖；主管角色文件均含模板路径列。
- `pm-team` 未出现在任何默认路由逻辑中；启用前确认规则存在于 lc-pm 与 router prompt。
- 本 issue 工作包 `stage_loader.py validate-entry` 通过；人类 PM 显式确认（human_gate）。
