# 用户故事: 2026-07-21-subagent-principles

## 用户故事一：控制 sub-Agent 成本

- 作为：Lincoln 的人类 PM
- 我希望：Agent 在没有必要时不要启动 sub-Agent
- 以便：提高模型缓存命中率，降低会话 token 成本
- 验收标准：
  - `.claude/agents/_contract.md` 明确写出“优先单 session 线性执行”。
  - `.claude/agents/default.md` 的 Core Rules 更新为仅在必要时 dispatch。

## 用户故事二：fan-out 需经我批准

- 作为：Lincoln 的人类 PM
- 我希望：Agent 在启动多个 sub-Agent 并行前向我说明原因并征得同意
- 以便：避免不必要的并行计算和上下文碎片化
- 验收标准：
  - 契约中新增 fan-out 前必须 announce 计划、理由、预期产物并等待显式批准的规则。
  - Red Flags 表包含“开多个子 agent 并行会更快，先跑再说”的反模式。

## 用户故事三：sub-Agent 任务清晰可验收

- 作为：Lincoln 的人类 PM
- 我希望：每个 sub-Agent 收到的 Prompt 都有清晰目标、路线、完成标准和产物
- 以便：sub-Agent 不空转，返回结果可直接整合
- 验收标准：
  - 契约中定义 SMART  brief 的五个要素（Specific / Measurable / Actionable / Relevant / Time-bounded）。
  - Red Flags 表包含“这个任务先丢给子 agent 探索一下”的反模式。

## 用户故事四：契约可持久化验证

- 作为：Lincoln 维护者
- 我希望：sub-Agent 原则被测试保护，不会随时间丢失
- 以便：后续修改契约时不会意外破坏规则
- 验收标准：
  - `tests/test_agent_contract.py` 新增断言验证 `_contract.md` 包含 `Sub-Agent Dispatch Principles` 章节及关键 Red Flag 条目。
