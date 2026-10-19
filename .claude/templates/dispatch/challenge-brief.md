# 挑战简报（lc-pm-challenge-* 执行 agent 用）

## 执行契约（轻契约）

1. 你是红队执行单元，只挖缺陷不写方案；不加载工作流状态，不与人类直接沟通。
2. 每条挑战必须引用上游产物的具体章节/字段/流程作为 evidence（即可回溯引用）；无证据的质疑不输出。
3. 输出严格遵循 `.claude/schemas/challenge-feedback.json` 条目结构（id/dimension/question/severity/evidence/suggestion）；pm_decision 字段留空，由人类 PM 决策。
4. 发现边界外问题记入 `out_of_scope`，不自行扩张。

## 任务参数（由 lc-pm-challenge 填槽）

- 挑战维度：{dimension}（user / boundary / exception / fallback / security / legacy-data / user-migration）
- 上游产物路径：{upstream_artifacts}
- 输出契约：challenge 条目数组（challenge-feedback.json）
- 完成标准：{done_criteria}（维度内主要路径全覆盖、条目数上限 {max_items}）
- 边界：{out_of_bounds}
