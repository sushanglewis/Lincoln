# PM 多 Agent 体系

## 元信息

- **来源访谈**: —
- **来源需求**: GitHub issue #139
- **GitHub Issue**: [#139](https://github.com/sushanglewis/Lincoln/issues/139)
- **实现 PR**: [#140](https://github.com/sushanglewis/Lincoln/pull/140)
- **状态**: 已合并
- **标签**: lincoln, framework, agent, multi-agent, pm, workflow

---

## 业务知识

### 背景与问题

PM 把需求转化为 PRD 要经历六个子阶段（需求采集、可行性分析、MVP 方案、方案挑战、PRD 生成、交叉验证）。此前这些工作全部压在 lc-pm 单一角色上：上下文爆炸、无专业化分工、方案无人系统性挑战、人类 PM 被多个 agent 直接打扰。同时若把重流程强加给所有需求，Lincoln 会变得难用。

### 用户需求

- PM 各子阶段由专业化 agent 辅助，agent 间有清晰分工与协作规范。
- 大上下文场景下，角色可 spawn 多个 sub-agent 分头处理。
- human_gate 不可跳过，人类 PM 不被下属 agent 直接打扰。
- 重流程显式可选，默认轻量。

### 验收标准

- [x] 三层组织：lc-pm 总协调（唯一人类接口）→ 六个 lc-pm-* 阶段主管 → lc-pm-*-* 执行 agent。
- [x] tier-3 轻契约内嵌排遣模板，执行 agent 不继承全量角色契约。
- [x] 主管排遣 = 模板机械填槽，只掌握「任务→人→输出」三元组。
- [x] challenge 结构化红队 + PM 逐条决策闭环（challenge-feedback.json）。
- [x] pm-team 重型工作流须人类 PM 显式选择，默认轻量。

### 价值

PM 体系从「单角色全包」演进为「总协调 + 专业化分工」，子阶段质量（采集证据、可行性、红队挑战、交叉验证）有了明确责任人；轻/重分流保证框架对不同规模需求都可控可用。

---

## 技术知识

### 实现概述

- **角色层**：`.claude/agents/pm.md` 重写为总协调者；新增 `pm-{intake,analyst,mvp,challenge,author,validator}.md` 六个 tier-2 主管（各含方法论/SOP/产出物/排遣规范表）。
- **排遣层**：`.claude/templates/dispatch/` 六个 brief 模板（intake/analysis/mvp/challenge/doc-draft/gap-audit），头部内嵌 tier-3 轻契约 4 条 + 槽位；主管机械填槽后经 Task 派发。
- **阶段层**：新增 `.claude/stages/requirement-intake.yaml`（primary lc-pm-intake）与 `.claude/stages/challenge.yaml`（primary lc-pm-challenge，`output_schema` 引用 `.claude/schemas/challenge-feedback.json`）；共享 stage 的 workflows 列表追加 `pm-team`。
- **工作流层**：`.claude/workflows/pm-team.yaml`（team，重型六子阶段全流程）；`interview-to-knowledge` 恢复原序为轻量默认；lc-workflow-router 增加 pm-team 信号与「重型须显式选择」规则。
- **门控裁决**：`default.md` 子代理调度原则第 3 条增加 pm 三层体系例外（计划即授权）；lc-pm.md 增加轻量模式判定标准（不改产物/不增 gate/不增交互轮次）。
- **设计文档**：`docs/designs/pm-multi-agent-design.md`（v0.4.1，含 §7.5 评审加固裁决与 §10 v0.5+ 演进方向）；调研档案（MetaGPT/ChatDev/AG2/OpenAI Agents SDK/CrewAI/PyRIT/Kimi Agent Swarm）随 PR #140 归档。

### 关键决策

- 组织关系全靠 prompt 契约表达，不引入 fan-out 引擎、不改 hooks；stage `agent` 块用既有 `parallel_specialists` / `merge_strategy` / `output_schema` 字段承载声明。
- tier-3 不物化为角色文件，由模板承载（避免角色目录爆炸）。
- 排遣表达与 harness 无关，codex/opencode 适配产物经 `lincoln-setup.py generate-harness` 派生。
