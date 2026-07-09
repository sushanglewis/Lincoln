# workflow-router 检查清单

- [ ] 已确认 hook 加载的当前状态（必要时读取 `<process_slug>/workflow-stage.yaml`）
- [ ] 已扫描仓库关键目录
- [ ] 已从 `.claude/workflows/templates/` 中选定模板
- [ ] 置信度低时已向 PM 提问
- [ ] PM 已确认推荐模板
- [ ] 已更新 `current_run.workflow_template`
- [ ] 已更新 `current_run.current_stage`
- [ ] 已写入 `current_run.context_assessment`
