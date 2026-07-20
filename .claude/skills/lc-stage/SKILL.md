---
name: lc-stage
description: 用自然语言驱动当前阶段的生命周期：查看状态、校验准入、提交产物、确认 gate、进入下一阶段
triggers:
  - "lc-stage"
  - "提交产物"
  - "提交本阶段产物"
  - "确认通过"
  - "审批通过"
  - "校验阶段"
  - "进入下一阶段"
inputs:
  - name: intent
    description: 自然语言意图（如"提交产物""确认通过"）；可选，缺省时汇报当前状态并询问下一步
    required: false
outputs:
  - 对应 stage_loader.py 动作的执行结果与下一步建议
required_tools:
  - Bash
  - Read
---

# lc-stage — 阶段生命周期自然语言入口

## Purpose

Using [lc-stage] to 用自然语言驱动当前阶段的生命周期：查看状态、校验准入、提交产物、确认 gate、进入下一阶段.


用户不需要记任何终端命令。Agent 把自然语言意图翻译成 `scripts/stage_loader.py` 动作并代为执行：

| 用户说 | 动作 | 底层命令（Agent 执行，用户无需关心） |
|--------|------|-----------------------------------|
| "现在什么状态" | status | `python3 scripts/lincoln-status.py --format markdown`（或 `/lc-status`） |
| "可以开始吗 / 校验准入" | validate-entry | `python3 scripts/stage_loader.py --stage <current_stage> --action validate-entry`（或 `/lc-validate`） |
| "提交产物 / 记录产物" | record-artifacts | `python3 scripts/stage_loader.py --stage <current_stage> --action record-artifacts`（或 `/lc-submit`） |
| "确认通过 / 审批通过" | approve-gate | 仅当人类 PM 明确确认后：`... --action approve-gate`（或 `/lc-approve`） |
| "生成交接 / 切换窗口" | handoff-report | 见 `/lc-handoff` |
| "进入下一阶段" | transition-next | 仅在当前阶段 gate 通过后执行 |

规则：

1. `<current_stage>` 由 Agent 从 `{process_slug}/workflow-stage.yaml`（team）或 `.context/workflow/<name>.yaml`（solo）的 `current_run.current_stage` 读取，不要让用户提供。
2. `human_gate: true` 的阶段，执行 `approve-gate` 前必须有人类 PM 的显式确认原话；Agent 不得自行审批，不得用本技能替代人类确认。
3. 执行后用一两句话向用户汇报结果与下一步，不要倾倒原始命令输出。
