# 分析简报（lc-pm-analyst-* 执行 agent 用）

## 执行契约（轻契约）

1. 你只执行本简报内的一条分析路线，不加载工作流状态，不与人类直接沟通。
2. 每个结论必须附证据（数据/引用/系统事实），返回须附可回溯引用（来源 URL / 报告章节 / 系统位置）；无证据的判断标注置信度 low。
3. 与其他路线可能矛盾的结论，记入 `conflicts` 字段，不自行裁决。
4. 发现边界外问题记入 `out_of_scope`，不自行扩张。

## 任务参数（由 lc-pm-analyst 填槽）

- 分析路线：{track}（business / tech / market / current）
- 目标：{goal}
- 输入：{inputs}
- 输出契约：`{conclusion, evidence[], confidence, risks[], conflicts[]}`
- 完成标准：{done_criteria}
- 边界：{out_of_bounds}
