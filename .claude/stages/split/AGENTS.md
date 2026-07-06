# split 阶段 Agent 规范

## 阶段目的

将 OpenSpec 变更提案中的 tasks 拆分为可执行的 GitHub Issues，建立从需求到代码追踪的完整链路。

## 入口条件

1. 前置阶段 `propose` 已完成并通过退出校验
2. 入口校验通过：`openspec_tasks_ready`（`{process_slug}/openspec/changes/<change_name>/tasks.md` 存在且包含可识别的任务列表）
3. 当前 workflow state 中 `current_stage` 为 `split`

## 允许的操作

- 读取 `{process_slug}/openspec/changes/<change_name>/tasks.md` 解析任务列表
- 读取 `.github/openspec-config.yml` 获取目标仓库信息
- 使用 GitHub MCP 或 `gh` CLI 创建 GitHub Issues
- 写入 `.github/linked-issues.yaml` 记录任务与 Issue 的映射关系
- 更新 `{process_slug}/requirements/<session_id>/requirements.md` 记录 Issue 编号
- 调用 validator 执行入口/退出校验
- 向人类汇报已创建的 Issue 列表

## 禁止的操作

- **禁止**创建没有明确验收标准的 Issue
- **禁止**一个 Issue 映射多个 OpenSpec 任务（必须一对一）
- **禁止**绕过 OpenSpec CLI 手动生成 tasks
- **禁止**在 Issue 中遗漏来源访谈、需求文档、OpenSpec 变更的链接
- **禁止**跳过校验直接进入下一阶段

## 副作用策略

- 所有写入操作均为追加或新建，不删除已有文件
- `.github/linked-issues.yaml` 如已存在，应追加新映射而非覆盖
- `{process_slug}/requirements/<session_id>/requirements.md` 的更新以追加 Issue 编号的形式进行

## 人类确认节点

- 本阶段 **无** `human_gate`，但创建 Issue 后必须向人类汇报
- 如人类要求修改 Issue 内容，Agent 应协助编辑后重新校验

## 下一阶段

`implement` — 研发实现阶段

## 关键规则

1. 每个 Issue 的标题必须清晰、可执行
2. 每个 Issue 的正文必须包含：用户故事、验收标准、来源访谈路径、来源需求路径、来源 OpenSpec 变更路径、相关转录时间戳
3. Issue 必须应用标签：`from-interview`、`openspec`
4. 完成后告知人类："Issues 已就绪，可进入研发阶段。"
