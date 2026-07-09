# workflow-router 阶段 Agent 规范

## 阶段目的

在会话启动时评估项目上下文，选择最适合的 Lincoln 工作流模板。

## 入口条件

- `<process_slug>/workflow-stage.yaml` 中 `current_run.workflow_template` 为空
- 或 PM 明确要求重新评估

## 允许的操作

- 基于 session-start hook 已加载的状态和仓库结构评估上下文
- 向 PM 提出最多 3 个澄清问题
- 通过 `scripts/stage_loader.py` 设置 `current_run.workflow_template` 和 `current_stage`

## 禁止的操作

- 在未获 PM 确认前进入任何实施阶段
- 修改任何阶段产物

## 人类确认

PM 必须显式确认推荐模板（`confirm` / "确认"），或指定其他模板名。
