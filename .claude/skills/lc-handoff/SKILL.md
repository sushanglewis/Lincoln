---
name: lc-handoff
description: 为当前阶段生成交接文档，并标记人类审批通过
triggers:
  - "生成交接文档"
  - "lc-handoff"
  - "handoff"
inputs:
  - name: stage
    description: 当前阶段 ID，如 clarify
    required: false
outputs:
  - "{process_slug}/handoffs/lc-handoff-{stage}.md"
required_tools:
  - Read
  - Bash
  - Write
---

# lc-handoff

为当前阶段生成交接文档，并在人类 PM 确认后标记 gate 审批通过。

执行步骤：
1. 读取 `<process_slug>/workflow-stage.yaml` 确定当前 stage 和 process_slug。
2. 收集当前 stage 的产物、决策、待解决问题。
3. 写入 `<process_slug>/handoffs/lc-handoff-{stage}.md`。
4. 人类 PM 确认后，调用 `python scripts/stage_loader.py --stage {stage} --action approve-gate`。
5. 调用 `python scripts/stage_loader.py --action append-node` 追加节点记录。
