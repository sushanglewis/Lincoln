---
name: lc-init-branch
description: 基于 GitHub issue 初始化 Lincoln issue work package 和 feature branch
triggers:
  - "初始化 Lincoln 分支"
  - "lc-init-branch"
  - "创建 Lincoln feature branch"
  - "初始化 issue 工作包"
inputs:
  - name: issue_number
    description: GitHub issue 编号，如 21
    required: true
  - name: session_id
    description: 会话 ID，如 2026-06-27-stakeholder；可选，默认基于 issue 生成
    required: false
  - name: design_id
    description: 设计 ID，如 checkout-redesign；可选，默认基于 issue 生成
    required: false
  - name: process_slug
    description: 过程包目录名；可选，默认 issue-{number}
    required: false
outputs:
  - git branch issue-{number}（若当前在 main）
  - 分支根目录下的 {process_slug}/ 过程包（designs/ docs/ interviews/ openspec/ recordings/ requirements/）
  - '"{process_slug}/workflow-stage.yaml" 含 issue_number'
required_tools:
  - Bash
  - Read
  - Write
---

# lc-init-branch

PM 在 Conductor 中基于 GitHub issue 初始化 workspace 后，调用此 skill 创建对应的过程包：

1. 若当前在 `main`，切出 `issue-{number}` feature branch；若已处于 feature branch，则使用该分支。
2. 从 `.claude/templates/issue-package/` 复制完整模板到 `{process_slug}/`。
3. 写入 `{process_slug}/workflow-stage.yaml`，设置 `issue_number`、`session_id`、`design_id`、`process_slug`。
4. Commit 初始过程包，可选 `--push` 到远程。

示例：

```bash
scripts/init-lincoln-branch.sh --issue-number 21 --session-id 2026-07-08-stakeholder --design-id checkout-redesign --push
```

过程包只存在于 feature branch，不合并到 `main`。
