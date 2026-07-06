# sync-knowledge 阶段 Agent 规范

## 阶段目的

PR 合并后，将代码变更、Issue 讨论、设计决策沉淀到项目 Obsidian 知识库，确保业务知识和技术知识双轨保存，形成可追溯的知识资产。

## 入口条件

1. 前置阶段 `implement` 已完成（PR 已合并）
2. 触发条件：`on_pr_merge` — PR 合并后自动触发
3. 入口校验通过：
   - `pr_merged`（`.github/lincoln-sync-queue/pr-{pr_number}.yaml` 存在且状态为 `pending`）
   - `issue_exists`（Issue 编号在 `.github/linked-issues.yaml` 中存在）
4. 当前 workflow state 中 `current_stage` 为 `sync-knowledge`

## 允许的操作

- 读取 `.github/lincoln-sync-queue/pr-{pr_number}.yaml` 获取同步任务信息
- 读取 `.github/openspec-config.yml` 获取目标仓库信息
- 使用 GitHub MCP 获取 Issue 和 PR 详情
- 读取相关需求文档、OpenSpec 设计文档
- 审查合并的 PR diff
- 创建/更新 Obsidian 知识库文档：
  - `knowledge/01-interviews/<session_id>.md`
  - `knowledge/02-requirements/<requirement_id>.md`
  - `knowledge/03-features/<feature_slug>.md`
  - `knowledge/04-decisions/<decision_id>.md`
- 更新 `knowledge/00-index.md`
- 使用 Obsidian wikilinks（`[[...]]`）建立文档关联
- 检查与已有知识的冲突
- 调用 validator 执行入口/退出校验

## 禁止的操作

- **禁止**创建没有业务知识和技术知识双轨内容的功能文档
- **禁止**创建没有来源链接（访谈、需求、Issue、PR）的知识文档
- **禁止**覆盖人类编辑而不记录变更
- **禁止**在发现知识冲突时自动覆盖，必须暂停等待人类处理
- **禁止**跳过校验标记阶段为完成

## 副作用策略

- 知识文档的更新应为增量更新，保留已有内容
- 如需要修改人类已编辑的内容，应在文档中记录变更说明
- 不删除已有的知识文档，只追加或更新
- sync-queue 文件处理完成后，将其状态更新为 `completed`

## 人类确认节点

- 本阶段 **无** `human_gate`
- 但发现知识冲突时必须暂停并等待人类处理
- 完成后向人类汇报知识库更新摘要

## 下一阶段

本阶段是工作流的最后一个阶段，完成后工作流闭环。

对于同一访谈的后续迭代，从新的 `propose` 阶段开始。

## 关键规则

1. 每个功能文档必须同时包含：
   - `业务知识`：背景、用户需求、验收标准、价值
   - `技术知识`：实现概述、代码位置、设计决策、依赖关系、API/数据模型
2. 每个文档必须使用 Obsidian wikilinks 关联到来源文档
3. 发现知识冲突时，暂停并询问人类 PM
4. 更新 `knowledge/00-index.md` 索引
5. 处理完成后将 sync-queue 文件状态更新为 `completed`
