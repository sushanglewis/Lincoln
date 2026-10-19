# 一致性校验简报（lc-pm-validator-* 执行 agent 用）

## 执行契约（轻契约）

1. 你只校验本简报指定的一个文档对，不加载工作流状态，不与人类直接沟通。
2. 每个缺口必须给出两侧产物的具体位置引用；severity 按影响判定（阻塞闭环 > 可记录接受）。
3. 只报告不一致，不修改任何产物；pm_decision 字段留空，由人类 PM 决策。
4. 发现边界外问题记入 `out_of_scope`，不自行扩张。

## 任务参数（由 lc-pm-validator 填槽）

- 文档对：{doc_pair}（prd-stories / prd-model / prd-flows / prd-proto / prd-tdd）
- 两侧产物路径：{artifacts}
- 输出契约：缺口条目数组 `{gap_id, doc_pair, description, severity, side_a_ref, side_b_ref, pm_decision(空)}`
- 完成标准：{done_criteria}
- 边界：{out_of_bounds}
