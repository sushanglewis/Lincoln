<!-- status: approved -->
# PM 多 Agent 体系调研（2026-10-19）

- Session: 2026-10-19-pm-multi-agent-research · 关联 issue: #139 · 设计文档: `issue-139/designs/pm-multi-agent-design.md`
- 方法：桌面调研 6 个代表性多智能体框架的公开文档（原始材料存 `raw/`），提炼可迁移的模式与教训。

## 1. 调研对象与核心机制

| 框架 | 核心机制 | 与 #139 的相关性 |
|------|----------|------------------|
| MetaGPT | `Code = SOP(Team)`：一行需求 → 用户故事/竞品分析/需求/数据结构/API/文档；PM/架构师/工程师角色 + 编排好的 SOP | 直接验证「SOP 驱动 + 角色专业化 + 分阶段结构化产物」路线；Lincoln 的 stage/skill 即 SOP |
| ChatDev | ChatChain 可配置阶段序列；角色研讨会对（如程序员+评审双角色互审）；Human-Agent-Interaction 模式让人类在链中担任 reviewer | 验证 challenge 阶段的「红队互审」模式；人类以 reviewer 身份介入对应我们的 human_gate |
| AG2 (AutoGen) | GroupChat + manager 仲裁；nested chats（编排器派生子会话并汇总）；human-in-the-loop 工作流 | nested chat = 主管 + Task 派发的子 agent 模型；子 agent 返回摘要、主管整合 |
| OpenAI Agents SDK | handoffs、agents-as-tools、guardrails（输入/输出校验）、sessions、tracing | guardrails ↔ 我们的 entry/exit checks；handoffs ↔ 阶段交接契约；tracing ↔ 可观测性汇报 |
| CrewAI | Crews（角色+目标+工具自治协作）vs Flows（事件驱动、显式控制流）；层级流程有 manager 代理委派与校验 | 我们的形态 = Flows 保确定性 + 阶段内层级委派；主管的「校验结果」职责有先例 |
| PyRIT (Microsoft) | AI 红队框架：结构化风险识别、攻击剧本、评分 | challenger 的 severity 分级 + 证据要求 + 结构化输出 |

## 2. 可迁移模式（Design → Lincoln 映射）

1. **SOP 优先于自由群聊**：MetaGPT/CrewAI 均证明确定性流水线适合可重复产研流程；PM 六阶段用 flow（stage 链）而非 crew（自由协商）——当前设计正确，保持。
2. **阶段内层级委派**：CrewAI hierarchical process 与 AG2 nested chat 一致——主管 agent 拥有整合与裁决权，子 agent 返回结构化摘要。映射到 Lincoln：主管 = stage primary，子 agent 契约 = `SUBAGENT-STOP` + 结构化输出。
3. **红队互审要结构化**：PyRIT/ChatDev 的红队都强调证据 + 分级 + 可决策条目。当前 challenger 设计已含 `{id, dimension, question, severity, evidence, suggestion}`，本期补强：为 challenge stage 声明 `output_schema`（`.claude/schemas/challenge-feedback.json`），与 design-review-feedback 同款。
4. **human-in-the-loop 是生产级标配**：全部框架在关键节点留人审。我们的 human_gate 位置（intake 清单确认、挑战逐条决策、PRD 定稿、原型确认）与 ChatDev 的 human-reviewer 模式等价，保持。
5. **Guardrails 显式化**：OpenAI Agents SDK 的 guardrails = 我们的 entry/exit checks；可增加输出 schema 校验（见第 3 点）。

## 3. 教训与避免项

1. **避免端到端全自动**：MetaGPT 全自动生成代码但质量需人审兜底；PM 方案无 gate 的自动化会被设计缺陷反噬——human_gate 不可跳过是硬约束。
2. **避免自由 GroupChat 决定阶段顺序**：AG2 GroupChat 适合探索型任务，PM 阶段顺序是业务约束，必须由 workflow 模板固定。
3. **避免子 agent 无契约派发**：AG2/CrewAI 都要求任务边界明确；对应 default.md 的 SMART 简报强制规则。
4. **避免单点上下文爆炸**：nested chat 的价值正是把大上下文卸载到子会话——支撑 issue #139 中「大上下文时 spawn 多个 sub-agent」的诉求。

## 3.5 外部参照：Kimi Agent Swarm（2026-10 官方帮助中心，raw/kimi-agent-swarm.txt）

官方事实（kimi.com/help/agent/agent-swarm）：水平扩展架构，主 Agent 指挥最多 300 个子 Agent、4000 步工具调用，自身仅监督约 15 步；PARL 训练，**冻结子智能体、只训练协调器**（功劳责任清晰归属调度决策）；显式防治两种塌缩——**串行崩溃**（指挥官把活全丢给一个子代理退化为单兵）与**虚假并行**（为刷指标盲目拆任务），用三维度奖励（结果质量/真正并行/子任务完成率）约束；以**关键步骤**（每阶段最慢子代理耗时累计）衡量并行收益；**上下文分片**——子智能体各自记"小本子"、只向指挥官汇报关键结论。

对 Lincoln 的映射见设计文档 §10（v0.5+ 演进方向）：我们的三层组织 + 排遣模板 + 有界结构化返回与 Swarm 的"协调器 + 冻结队员 + 上下文分片"同构；Swarm 的防塌缩奖励机制与关键步骤度量是 Lincoln 目前缺失、可在 prompt 层补的自检项。

## 4. 对设计方案的修订（v0.1 → v0.2）

1. 设计文档增加「研究依据」章节，明确设计取向：**Flows 确定性流水线 + 阶段内层级委派 + 结构化红队 + 显式 human gate**。
2. challenge stage 增加 `agent.output_schema: .claude/schemas/challenge-feedback.json`（新增 schema），使挑战条目机器可校验。
3. 其余六阶段映射与角色设计经调研复核无颠覆性变更。
