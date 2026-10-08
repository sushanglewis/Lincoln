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

## Purpose

Using [lc-handoff] to 为当前阶段生成交接文档，并标记人类审批通过.


为当前阶段生成交接文档，并在人类 PM 确认后标记 gate 审批通过。

执行步骤：
1. 读取 `<process_slug>/workflow-stage.yaml` 确定当前 stage 和 process_slug。
2. 收集当前 stage 的产物、决策、待解决问题。
3. 对收集到的内容执行删减评审（见 `.claude/policies/less-is-more.md`）：交接文档只保留下游决策所需的信息——核心决策、范围、开放问题与上下文包链接；过程性细节链接到对应产物，不复述正文。
4. 写入 `<process_slug>/handoffs/lc-handoff-{stage}.md`，结论与待确认项置于文档开头。
5. 人类 PM 确认后，调用 `python scripts/stage_loader.py --stage {stage} --action approve-gate`。
6. 调用 `python scripts/stage_loader.py --action append-node` 追加节点记录。
