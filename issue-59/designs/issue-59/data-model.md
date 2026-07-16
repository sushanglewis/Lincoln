# 数据模型: issue-59

<!-- status: approved -->

## 实体

本变更不引入新的持久化实体。`workflow-stage.yaml` schema 不变(已验证 `current_run` 无 `additionalProperties: false` 限制)。

### 复用: current_run.context_assessment(既有)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| context_assessment | string | 选填 | workflow-router 已有约定;intake 收尾写一句话结论 |

### 复用: .context/lc-intake.md(新,session 级文档)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| 摸排摘要 | markdown 段落 | 必填 | 仓库/代码/issue/知识概览,≤10 行 |
| 处境判断 | markdown 列表 | 必填 | 角色/流程位置/问题/目标/象限初判 + 置信度 |
| 确认记录 | markdown 列表 | 必填 | 每轮问题与用户回答要点 |

生命周期:session 级,gitignored,与 `.context/lc-handoff-*.md` 相同;不跨成员共享。

## 关系

- intake-prompt.md(流程定义) 1 → 1 lc-intake.md(一次会话的实例记录)。
- context_assessment(结论摘要) 派生自 lc-intake.md。

## 约束

- 摸排过程除 `.context/lc-intake.md` 外不写任何文件。
- `workflow-stage.yaml` 仅通过 `scripts/stage_loader.py` 更新(既有约束,不变)。
