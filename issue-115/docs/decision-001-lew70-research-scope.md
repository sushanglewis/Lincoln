# Decision Record 001: LEW-70 研究范围与工作流选择

## 背景

Issue #70 / Linear LEW-70 要求调研 OpenHands（`All-Hands-AI/OpenHands`）与 TeamAI（`Tencent/teamai-cli`）两个开源 coding-agent 项目，识别可被 Lincoln 借鉴的架构与工程模式。

## 决策

### 1. 工作流选择：使用 `oss-first-design` 而非默认 `interview-to-knowledge`

- **考虑因素**：
  - 任务为纯研究性质，没有访谈录音或访谈转录文件，不满足 `interview-to-knowledge` 中 `ingest` 阶段对录音文件的前置要求。
  - `oss-first-design` 显式包含 `explore-opensource` 阶段，其产物约定正是 `{process_slug}/docs/research/{change_name}-oss-options.md`，与本次任务输出完全匹配。
- **决策**：采用 `oss-first-design` 工作流，执行范围到 `explore-opensource` 为止，不进入 `product-design-docs`、`product-prototype`、`tdd-development-plan`、`propose`、`split`、`implement` 等下游阶段。
- **PM 确认**：人类 PM 在 `workflow-router` 阶段显式确认“同意使用 oss-first-design”。

### 2. `ingest` 阶段兼容性处理

- **问题**：`clarify` 阶段的准入校验要求 `ingest` 已完成，但 `oss-first-design` 工作流模板本身不包含 `ingest` 步骤。
- **决策**：由于本次任务无录音输入，`ingest` 不适用。在 `issue-70/workflow-stage.yaml` 中标记 `ingest` 为已完成（N/A），`gate_passed: true`，`approved_by: human-pm`，并记录本决策。
- **影响**：仅影响本次研究型 issue；未来有访谈录音的任务仍应正常执行 `ingest`。

### 3. 研究输出形式

- **决策**：
  1. 主研究笔记：`issue-70/docs/research/openhands-teamai-research-oss-options.md`，包含八段结构（研究问题、候选方案对比表、Top candidate 详情、自研基线、可借鉴模式映射、推荐结论、关键待澄清问题、参考链接）。
  2. 持久 OSS 注册表：`oss/projects.yaml` 新增两条 `reference_only` 记录，状态为模式参考，不作为依赖嵌入。
  3. 决策记录：本文件，记录研究范围、工作流选择、`ingest` 兼容处理方式。

### 4. 信息来源与约束

- **来源**：
  - GitHub MCP 获取仓库元数据（README、LICENSE、stars、最近推送时间、目录结构）。
  - WebSearch / WebFetch 获取官方文档与论文信息。
- **约束**：未下载、安装或执行任何第三方项目代码，符合 `lc-explore-opensource` 安全约束。

## 后果

- 产物仅用于指导 Lincoln 框架自身的 stage/skill/hook/knowledge 体系演进，不引入外部运行时依赖。
- `explore-opensource` 阶段完成后即暂停，等待 PM 对研究笔记与注册表的评审。

## 5. PM 对研究开放问题的答复（2026-08-29）

| 问题 | PM 决策 | 对推荐结论的影响 |
|------|---------|-----------------|
| Lincoln 是否自研执行器？ | Lincoln 是 Claude Code、Codex、OpenCode 的 harness 插件，**不自研执行器**。 | 不移植 OpenHands Action–Observation 执行循环；仅借鉴风险分析、事件模型、上下文压缩与 skill 组织。 |
| 需要支持哪些 harness？ | **Claude Code、Codex、OpenCode**。 | harness 分发与 hook/MCP 规范只需覆盖这三个目标。 |
| 是否允许高危操作？ | 允许 `git push`、外部 API 调用；**文件删除必须人工确认**。 | SecurityAnalyzer 策略收窄为：删除类操作强制 human_gate，其余可放行或仅记录。 |
| 是否采用摩擦驱动知识捕获？ | **同意**。摩擦信号触发后自动提示贡献者沉淀经验。 | `on-stop.sh` 接入 friction scoring，新增 `lc-share-learnings` 提示模板。 |
| 是否需要跨仓库代码图？ | **需要**，但 Lincoln 做轻做薄，仅声明外部工具依赖。 | 不自建图引擎，依赖 tree-sitter / lsif / scip 等外部工具；Lincoln 只负责 stage/docs 中的依赖说明与输出消费。 |

## 6. 研究基线合并与后续 Phase 拆分（2026-08-29）

- **PM 决策**：
  - 同意将研究基线合并到仓库，但不合并到 `main`。
  - 创建独立分支 `lew-70-research-baseline` 存放研究基线。
  - P0 / P1 / P2 各创建独立 GitHub Issue，分别进行方案设计，经 PM 批准后进入实现与独立 PR。

- **已执行**：
  - PR #18 已合并到分支 `lew-70-research-baseline`。
  - 已创建后续设计 Issue：
    - #19 — Phase 1 / P0：安全门控 + 三 harness 分发 + hook/MCP 规范
    - #20 — Phase 2 / P1：摩擦学习、recall precheck、EventLog/Condenser、skill 市场、sub-agent 委托、MR 知识挖掘
    - #21 — Phase 3 / P2：轻量跨仓库代码图 + session analytics

- **原则**：每个 Phase 独立设计、独立评审、独立实现、独立 PR；真正有效优化 Lincoln 后再提交 PR。

## 状态

`<!-- status: approved -->`

## 参考

- `issue-70/workflow-stage.yaml`
- `issue-70/requirements/2026-08-28-issue-70/requirements.md`
- `.claude/workflows/oss-first-design.yaml`
- `.claude/stages/explore-opensource.yaml`
- Linear LEW-70 / GitHub Issue #70
