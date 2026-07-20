---
name: lc-wf
description: Lincoln workflow bundle 入口，按 lc-wf-<workflow-name> 启动对应 SOP（solo 或 team）
triggers:
  - "lc-wf-list"
  - "lc-wf-interview-to-knowledge"
  - "lc-wf-bug-fix"
  - "lc-wf-design-spike"
  - "lc-wf-existing-project-iteration"
  - "lc-wf-oss-first-design"
  - "启动 Lincoln 工作流"
inputs:
  - name: workflow
    description: 工作流名称（.claude/workflows/ 下的 yaml 文件名）
    required: false
outputs:
  - solo 模式生成 .context/workflow/<name>.yaml；team 模式生成 {process_slug}/workflow-stage.yaml
required_tools:
  - Bash
  - Skill
---

# lc-wf — Lincoln workflow bundle 入口

## Purpose

Using [lc-wf] to Lincoln workflow bundle 入口，按 lc-wf-<workflow-name> 启动对应 SOP（solo 或 team）.


所有 Lincoln SOP 工作流统一通过 `lc-wf-*` 启动，底层命令为 `python3 scripts/lincoln_workflow.py`。

## 命令映射

| 触发 | 命令 | 模式 |
|------|------|------|
| `lc-wf-list` | `python3 scripts/lincoln_workflow.py list` | — |
| `lc-wf-interview-to-knowledge` | `... start --workflow interview-to-knowledge --issue-number <N>` | team |
| `lc-wf-bug-fix` | `... start --workflow bug-fix` | solo |
| `lc-wf-design-spike` | `... start --workflow design-spike` | solo |
| `lc-wf-existing-project-iteration` | `... start --workflow existing-project-iteration` | solo |
| `lc-wf-oss-first-design` | `... start --workflow oss-first-design` | solo |

## 执行模式

- **solo**：实例写入 `.context/workflow/<name>.yaml`（session 级、gitignored，跟随 conductor workspace/session 生命周期）。适合单人在自己的 session 内独立完成全流程。
- **team**：转发 `scripts/init-lincoln-branch.sh --workflow <name> --issue-number <N>`，在 issue 分支上创建 `{process_slug}/workflow-stage.yaml`，供多成员经 branch 交接。

## 启动后

1. 运行 `python3 scripts/stage_loader.py --stage <current_stage> --action validate-entry` 进行准入校验。
2. 按当前 stage 的 `action` 调用对应子 skill（见 `lc-workflow` 的阶段→skill 映射）。
3. `human_gate: true` 阶段必须获得人类 PM 显式确认，不得跳过。
