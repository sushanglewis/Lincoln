# 需求文档: 2026-08-28-issue-70

<!-- status: draft -->

## 背景

- Issue: #70
- 任务：调研 OpenHands（`All-Hands-AI/OpenHands`）与 TeamAI（`Tencent/teamai-cli`）两个开源 coding-agent 项目，识别可借鉴到 Lincoln 框架的架构、流程与工程模式。
- 本次任务为**纯研究性质**，不产出可运行代码、UI 原型或 OpenSpec 变更提案。

## 问题

Lincoln 作为 AI-Native 产品研协框架，需要持续吸收成熟 coding-agent 项目的工程实践，以改进自身的 stage/skill/hook/knowledge 体系。当前对以下两个项目的可借鉴部分缺乏系统性评估：

1. **OpenHands**：大型开源 autonomous coding agent，拥有事件驱动的状态机、类型化 Action/Observation 循环、SecurityAnalyzer、ConfirmationPolicy、Condenser、Workspace Factory 等机制。
2. **TeamAI（teamai-cli）**：腾讯开源 TypeScript 多智能体协作 harness，拥有 skill/rule/hook/MCP 分发、git-native 团队配置、friction-based learning、recall precheck、双轨代码图、session analytics、MR 知识挖掘等机制。

## 用户

- **Lincoln 框架维护者**：需要了解哪些模式可直接映射到 Lincoln 现有文件与子系统，降低实现风险。
- **Lincoln 产品经理（PM）**：需要基于加权评分和明确优先级做出采纳/暂缓决策。
- **未来 Contributor**：需要一份可追溯的参考文档，理解 Lincoln 设计选择背后的外部依据。

## 方案

采用 Lincoln `oss-first-design` 工作流中的 `explore-opensource` 阶段：

1. 使用一手资料（官方文档、README、LICENSE、源代码）核实两个项目的许可证、活跃度、技术栈与架构。
2. 按 Lincoln 研究笔记模板产出 `issue-70/docs/research/openhands-teamai-research-oss-options.md`，包含：研究问题、候选方案加权评分表、Top candidate 详情、自研基线、可借鉴模式映射、推荐结论、关键待澄清问题、参考链接。
3. 在 `oss/projects.yaml` 中登记两个项目为 `reference_only`，记录其作为模式参考的价值。
4. 本阶段完成后即停止，不进入 `product-design-docs`、`product-prototype`、`tdd-development-plan`、`propose`、`split` 等下游阶段。

## 验收标准

- [ ] 研究笔记包含全部八段结构，加权评分表权重之和为 1.0，且两个项目均有独立评分。
- [ ] 每一个推荐采纳的模式都映射到 Lincoln 的具体文件或子系统（如 `scripts/stage_loader.py`、`.claude/stages/*.yaml`、`.claude/skills/*` 等）。
- [ ] `oss/projects.yaml` 成功解析，新增两条 `reference_only` 记录。
- [ ] `explore-opensource` 阶段的 `validate-entry` 与 `validate-exit` 均通过。
- [ ] PM 对研究笔记和注册表进行评审并显式确认。

## 范围决策

- **纳入范围**：workflow-router → clarify → explore-opensource。
- **不纳入范围**：product-design-docs、product-prototype、tdd-development-plan、propose、split、implement、sync-knowledge（知识同步仅在研究 PR 合并后执行）。
- **框架兼容性说明**：`oss-first-design` 工作流未包含 `ingest` 阶段，但 `clarify` 阶段定义要求 `ingest` 已完成。由于本任务无访谈录音，已在 `issue-70/workflow-stage.yaml` 中标记 `ingest` 为不适用（N/A）并完成，以保证阶段校验可运行。该处理方式将记录在决策记录中。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。*
