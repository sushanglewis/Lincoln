<!-- status: draft -->
<!-- version: v0.3 -->
# Lincoln PM 阶段多 Agent 体系设计

- Issue: #139 · 分支: issue-139 · 状态: draft（待人类 PM 评审）
- 目标：将「需求 → PRD」的 PM 工作拆解为 6 个专业子阶段，构建 **lc-pm（总协调）→ lc-pm-\*（阶段主管）→ lc-pm-\*-\*（执行 agent）** 三层组织，定义每层的工作方法论、SOP、产出物与排遣方式，并落地到 Lincoln 框架。

## 0. 研究依据

调研方法与结论见 `issue-139/research/2026-10-19-pm-multi-agent-research/findings.md`（桌面调研 MetaGPT / ChatDev / AG2 / OpenAI Agents SDK / CrewAI / PyRIT）。核心取向：

1. **Flows 确定性流水线 + 层级委派**（CrewAI crews vs flows、AG2 nested chat）：PM 六阶段顺序是业务约束，由 workflow 模板固定；组织内采用层级委派——主管整合裁决、下级返回结构化产物。
2. **结构化红队**（PyRIT、ChatDev 双角色互审）：挑战条目必须结构化、带证据与 severity，且机器可校验——challenge stage 声明 `output_schema: .claude/schemas/challenge-feedback.json`。
3. **显式 human-in-the-loop**（全部框架的生产级标配）：human_gate 不可跳过；本设计进一步收敛为「lc-pm 是人类 PM 的唯一接口」。
4. **避免项**：端到端全自动（无 gate）、自由 GroupChat 决定阶段顺序、无契约派发子 agent、单点上下文爆炸。

## 1. 设计原则

1. **三层组织**：lc-pm 是唯一面向人类 PM 的总协调者；六个 lc-pm-* 子阶段主管对 lc-pm 负责；lc-pm-*-* 执行 agent 由主管排遣，无独立角色文件。
2. **计划即授权**：主管在阶段计划中报备 fan-out 清单，lc-pm 审批计划即授予排遣授权；计划外排遣需再报批。fan-out 不引入 stage YAML 级执行引擎，一律由主管经 Task 工具派发。
3. **人类门控不可跳过**：所有 human_gate 由 lc-pm 统一呈现、人类 PM 显式 confirm；挑战与交叉验证的每个条目必须 PM 逐条决策闭环。
4. **结构化与可追溯**：每层产物结构化（条目/文档/决策记录），每条需求、挑战、缺口可回溯来源与决策。

## 2. 三层组织模型

```
人类 PM
  └── lc-pm（tier-1 总协调者，唯一人类接口）
        ├── lc-pm-intake（tier-2 需求采集主管）
        │     └── lc-pm-intake-github / -support / -community / -market / -interview（tier-3）
        ├── lc-pm-analyst（tier-2 可行性分析主管）
        │     └── lc-pm-analyst-business / -tech / -market / -current（tier-3）
        ├── lc-pm-mvp（tier-2 MVP 方案主管）
        │     └── lc-pm-mvp-persona / -scenario / -path（tier-3）
        ├── lc-pm-challenge（tier-2 方案挑战主管，红队）
        │     └── lc-pm-challenge-user / -boundary / -exception / -fallback / -security / -legacy / -migration（tier-3）
        ├── lc-pm-author（tier-2 PRD 生成主管）
        │     └── lc-pm-author-requirements / -stories / -flows / -model（tier-3）
        └── lc-pm-validator（tier-2 交叉验证主管）
              └── lc-pm-validator-prd-stories / -prd-model / -prd-flows / -prd-proto / -prd-tdd（tier-3）
```

三级 agent 不物化为角色文件——它们是排遣时的实例，工作范围、输出契约与完成标准由对应 tier-2 角色文件的「排遣规范表」定义。

### 2.1 tier-1：lc-pm 总协调者

- **工作方法论**：单一人类接口（所有 gate 与决策项经其汇总、排序、去重后呈现）；计划即授权；不越级指挥 tier-3；跨阶段版本与决策一致性把关。
- **SOP**：启动确认（目标/范围/验收标准）→ 向主管下达 SMART 简报 → 审批阶段计划（含排遣清单）→ 验收 gate 材料并向人类 PM 呈现 → 决策登记与分派 → 修订复核 → stage_loader 推进 handoff。
- **产出物**：人类 PM 决策日志；阶段简报与计划审批记录；handoff 文档；`workflow-stage.yaml` 状态推进。
- **排遣方式**：只面向六个 tier-2 主管；单阶段单主管；tier-3 升级沿 主管 → lc-pm → 人类 PM 链路上行。

### 2.2 tier-2：lc-pm-* 阶段主管（六人）

- **通用 SOP**：接收 lc-pm 简报 → 制定阶段计划（三级 agent 排遣清单 + 输出契约 + 整合方式）报 lc-pm 审批 → 按获批计划经 Task 排遣 tier-3 → 整合校验三级产物（结构校验、冲突标注）→ 产出阶段产物 → 向 lc-pm 提交 gate 材料 → 按决策修订 → 移交。
- **各自方法论/产出物/排遣规范表**：见 `.claude/agents/pm-{intake,analyst,mvp,challenge,author,validator}.md`（每个文件含 3 条工作方法论、产出物清单、排遣规范表：触发条件/简报要点/输出契约/数量上限）。
- **数量纪律**：单阶段排遣上限 3–5 个三级 agent；default.md 子代理调度原则全部适用（SMART 简报强制、主管拥有整合与决策权）。

### 2.3 tier-3：lc-pm-*-* 执行 agent

- **定位**：一次性任务执行体；遵循 `SUBAGENT-STOP`（不 intake、不准入校验、不写 workflow-stage.yaml）；不与人类 PM 直接沟通。
- **通用工作方法论**：只处理一个明确边界任务；输出结构化并自带证据/来源；发现边界外问题回报主管，不自行扩张。
- **SOP**：接收 SMART 简报 → 按输出契约执行 → 自检完成标准 → 向主管返回结构化产物。
- **产出物**：由排遣规范表的输出契约定义（需求条目数组 / challenge 条目 / 缺口条目 / 文档草案等）。
- **禁止**：越级沟通；替人类 PM 做取舍；未经主管显式授权做二级 fan-out。

### 2.4 沟通与升级协议

| 通道 | 内容 | 规则 |
|------|------|------|
| 人类 PM ↔ lc-pm | 目标确认、gate 确认、逐条决策 | 唯一直接通道 |
| lc-pm ↔ lc-pm-* | 简报、计划审批、gate 材料、决策分派 | 计划外事项先报批 |
| lc-pm-* ↔ lc-pm-*-* | SMART 简报、结构化产物回收 | 主管验收后才可采用 |
| 跨阶段 | handoff 文档（经 lc-pm） | 主管之间不横向私传产物 |

## 3. 六阶段 → 角色映射总表

| # | 子阶段 | tier-2 主管 | 承载 stage | 审阅/并行 | human_gate | 关键产物 |
|---|--------|------------|------------|-----------|------------|----------|
| 1 | 需求采集 | lc-pm-intake | requirement-intake | lc-researcher | 是（清单确认） | 需求清单 + 来源台账 |
| 2 | 可行性分析 | lc-pm-analyst | clarify（并行专家） | lc-researcher / lc-architect | 是（矛盾项决策） | PRD 可行性章节 |
| 3 | MVP 方案 | lc-pm-mvp | clarify（并行专家） | — | 是（范围确认） | 最小成功可行路径 |
| 4 | 方案挑战 | lc-pm-challenge | challenge | lc-architect / lc-qa / lc-security-reviewer | 是（逐条决策） | 挑战报告 + PM 决策记录 |
| 5 | PRD 生成 | lc-pm-author | clarify + product-design-docs（主管） | lc-designer | 是（PRD 定稿 + 原型确认） | PRD（UI/UX、流程图、序列图、业务模型） |
| 6 | 交叉验证 | lc-pm-validator | tdd-development-plan（reviewer） | lc-qa | 是（缺口闭环） | 一致性校验报告 |

PRD 生成的前置条件：人类 PM 已在 `product-prototype` 阶段通过交互式原型确认过方案（lc-pm-author 任 PM 侧 reviewer）。

## 4. 各阶段设计

### 4.1 需求采集（requirement-intake，主管 lc-pm-intake）

- 渠道即并行单元：GitHub issue / 客诉频道 / 社区帖子 / 市场调研 / 访谈产物，每个渠道排遣一个 lc-pm-intake-* 采集 agent。
- 三级输出契约：需求条目 `{title, source_url, quote, confidence, date, segments}`，无 URL 来源必须标注录音时间戳。
- 主管归并：主题聚类去重，冲突条目并列呈现；取舍决策经 lc-pm 呈人类 PM（human_gate）。
- 产物：`{process_slug}/intake/requirements.md`、`{process_slug}/intake/sources.md`。

### 4.2 可行性分析（clarify 内并行，主管 lc-pm-analyst）

- 四路正交并行：lc-pm-analyst-business / -tech / -market / -current。
- 结论服务决策：「做/不做/怎么做」输入；四路矛盾（如技术可行但市场价值低）标注为待决策项，经 lc-pm 呈 PM。
- 产物：PRD 可行性章节 + 矛盾项清单。

### 4.3 MVP 方案（clarify 内并行，主管 lc-pm-mvp）

- 最小成功路径 = 核心用户 × 核心场景 × 最短闭环；受可行性结论约束。
- 三级：lc-pm-mvp-persona / -scenario / -path。
- 范围变更是 PM 决策；产物为 MVP 方案 + 裁剪清单，移交 lc-pm-author。

### 4.4 方案挑战（challenge，主管 lc-pm-challenge，红队）

- 七维度并行：user / boundary / exception / fallback / security / legacy-data / user-migration。
- 三级输出契约遵循 `.claude/schemas/challenge-feedback.json`：`{id, dimension, question, severity, evidence, suggestion}`；证据必须引用上游产物具体位置。
- 决策闭环：汇总去重后逐条经 lc-pm 呈 PM——fix（方案升版重冻结）或 accept（记录理由与影响），`pm_decision + rationale` 落同一结构；未逐条决策不得 exit。
- 产物：`{process_slug}/designs/challenge-report.md`。

### 4.5 PRD 生成（clarify + product-design-docs，主管 lc-pm-author）

- PRD 是主线文档：上游结论以结论形式固化；PRD 只承载业务内容，技术设计进归档页。
- 定稿前「需求清晰度六问」自检；协调 lc-pm-analyst / lc-pm-mvp 并行输入；三级 agent 分头产出文档章节（requirements / stories / flows / model）。
- 人类 PM 经交互式原型确认（product-prototype）后 PRD freeze 快照。
- 产物：prd.html（+快照）、requirements/stakeholders/user-stories.html、设计文档包。

### 4.6 交叉验证（tdd-development-plan 内，主管 lc-pm-validator）

- 文档对并行校验：PRD↔用户故事、PRD↔数据模型、PRD↔流程图、PRD↔原型、PRD↔TDD 计划。
- 以测试场景反向挑战 PRD：测试写不出来通常意味着 PRD 有缺口。
- 每个缺口 PM 决策闭环（fix=升版重冻结 / accept=记录）；产物 `prd-cross-validation.html` + 缺口清单。

## 5. 子 agent 通用契约（tier-3 适用，主管监督执行）

1. 由主管经 Task 工具派发，一次任务一个明确产出；二级 fan-out 需主管显式授权。
2. 遵循 `SUBAGENT-STOP`：跳过 intake/准入/handoff；不写 `workflow-stage.yaml`。
3. 输出必须结构化并自带来源/证据；主管负责合并、去重与冲突标注。
4. 子 agent 不得替代 human_gate；需人类决策的项一律上交主管。

## 6. 与现有工作流的融合

- **interview-to-knowledge（team，canonical）**：
  - 新增 step `requirement-intake`（ingest → requirement-intake → clarify）。
  - 新增 step `challenge`（product-design-docs → challenge → product-prototype）。
  - 接线：requirement-intake.primary=lc-pm-intake；clarify.primary=lc-pm-author（parallel_specialists 含 lc-pm-analyst / lc-pm-mvp）；product-design-docs.primary=lc-pm-author；challenge.primary=lc-pm-challenge；product-prototype reviewer 由 lc-pm 改为 lc-pm-author；tdd-development-plan reviewers 增加 lc-pm-validator。
- **pm-research（solo）**：需求采集的市场/竞品补源复用其研究序列，不新增 stage。
- **不破坏既有 gate**：既有 stage 的 human_gate、exit_checks、产物路径不变。

## 7. 框架落地清单（本期 PR）

| 变更 | 文件 |
|------|------|
| 重写角色 | `.claude/agents/pm.md`（tier-1 总协调者契约） |
| 新增角色 | `.claude/agents/pm-intake.md`、`pm-analyst.md`、`pm-mvp.md`、`pm-challenge.md`、`pm-author.md`、`pm-validator.md` |
| 移除角色 | `lc-requirement-scout`、`lc-challenger`（演进为 lc-pm-intake / lc-pm-challenge） |
| 新增 stage | `.claude/stages/requirement-intake.yaml`、`.claude/stages/challenge.yaml` |
| 修改 stage | ingest / clarify / product-design-docs / product-prototype / tdd-development-plan 的 agent 接线 |
| 新增 schema | `.claude/schemas/challenge-feedback.json`（challenge stage 经 `output_schema` 引用） |
| 修改 workflow | `.claude/workflows/interview-to-knowledge.yaml`、`.claude/workflows/README.md` |

## 8. 验收标准

- 新 stage 通过 `stage-definition.schema.json` 校验；`check-prompt-drift.py --strict --focus pm` 无新增告警/错误。
- 六个 lc-pm-* 角色文件均含：工作方法论（≥3 条）、SOP、产出物清单、排遣规范表（触发条件/简报要点/输出契约/数量上限）。
- 每个子阶段的 stage `agent.primary` 均为 lc-pm-* 而非 lc-pm。
- 本 issue 工作包 `stage_loader.py validate-entry` 通过；人类 PM 在设计文档与框架变更上显式确认（human_gate）。
