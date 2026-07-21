# 需求文档: 2026-07-21-subagent-principles

<!-- status: draft -->

## 背景

- Issue: #75
- 来源: GitHub Issue 原文（见附件 `.context/attachments/github-4936170647/[GITHUB]-75.md`）
- 本 issue 无利益相关者访谈录音，因此 `ingest` 阶段跳过，直接以 GitHub Issue 作为需求输入。

## 问题

Lincoln 在驱动 Agent harness 工作时，sub-Agent 的使用缺乏统一原则，导致：
1. 会话被过度拆分到多个 sub-Agent，降低模型缓存命中率，增加用户成本。
2. 多 sub-Agent 并行（fan-out）模式未经用户知情同意即启动。
3. 交接给 sub-Agent 的 Prompt 目标不清、路线模糊，导致 sub-Agent 空转或返回不可用的结果。

## 用户

- **主要用户**: 使用 Lincoln 工作流的人类 PM / 研发团队。
- **间接受益者**: Lincoln Agent 自身（获得更清晰的 dispatch 指引）。

## 方案

在 Lincoln Agent 行为契约中新增 `Sub-Agent Dispatch Principles` 章节，把 issue #75 的四条原则写入系统提示，并通过 Red Flags 和测试保证可执行性：

1. **尽量线性的在单一会话中完成工作** —— 主 session 优先完成工作，除非任务过大或存在真正独立的并行工作流。
2. **尽少使用 sub-Agent 模式，除非有必要** —— 仅在独立探索、并行审查、上下文窗口受限等场景下 dispatch。
3. **启动多 sub-Agent 并行模式必须说明行为与必要性并获得用户许可** —— fan-out 前向 PM 说明计划、理由、预期产物，等待显式批准。
4. **sub-Agent Prompt 必须遵循 SMART 原则** —— 具体目标（Specific）、可衡量完成标准（Measurable）、可执行路线（Actionable）、相关上下文包（Relevant）、时间/产物边界（Time-bounded）。

## 验收标准

- [ ] `.claude/agents/_contract.md` 包含 `## Sub-Agent Dispatch Principles` 章节，覆盖四条原则及结果整合、失败处理、产物归属。
- [ ] `.claude/agents/default.md` 的 `Prefer linear execution` 规则引用并强化上述原则。
- [ ] 两份契约文件的 Red Flags 表新增针对 fan-out、SMART prompt、结果采信的反模式警示。
- [ ] `tests/test_agent_contract.py` 新增断言，确保 `_contract.md` 持久化包含该章节与关键 Red Flag 条目。
- [ ] 所有现有基础设施测试通过。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。*

*PM→UX 交接：本需求文档是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
