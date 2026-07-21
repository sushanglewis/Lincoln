# PRD: 2026-07-21-subagent-principles

## 产品目标

将 issue #75 中关于 sub-Agent 使用的四条原则固化为 Lincoln Agent 行为契约的一部分，使所有 Lincoln Agent 在 dispatch sub-Agent 时有统一、可验证的准则，从而提高缓存命中率并降低用户成本。

## 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 单 session 优先 | 在 `_contract.md` 和 `default.md` 中明确主 session 优先线性完成工作，仅在必要时 dispatch sub-Agent | P0 |
| fan-out 许可 | 多 sub-Agent 并行前必须向 PM announce 计划、理由、预期产物并等待显式批准 | P0 |
| SMART prompt | 定义 sub-Agent prompt 必须包含的五个要素，并给出示例结构 | P0 |
| Red Flags 扩展 | 在 `_contract.md` 和 `default.md` 的 Red Flags 表中新增三条相关反模式 | P0 |
| 测试保护 | `tests/test_agent_contract.py` 新增断言确保 `_contract.md` 包含新增章节与关键 Red Flag | P0 |

## 非功能需求

- 不引入新的运行时依赖或外部服务。
- 不改变现有 `.claude/agents/*.md` 角色文件的结构（它们通过引用 `_contract.md` 自动继承新原则）。
- 所有现有基础设施测试保持通过。

## 发布标准

- `_contract.md` 和 `default.md` 更新完成。
- `tests/test_agent_contract.py` 扩展并通过。
- `pytest tests/test_agent_contract.py -v` 全绿。
- 相关产物已记录到 `issue-75/workflow-stage.yaml`。

## 风险

- **风险**: 规则过严导致合法并行场景受阻。  
  **缓解**: 规则保留“必要时”的例外，并强调向 PM 说明后获批即可执行。
- **风险**: 新增的 Red Flags 条目与现有条目重复。  
  **缓解**: 新条目聚焦 fan-out、SMART prompt、结果采信三个独特反模式。

---

*PM→UX 交接：本 PRD 是 [`handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md`](../handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md) 的 Tier-2 产物。*
