---
name: lc-one-id
description: |
  查询并维护 Lincoln one-id 索引，按功能点、页面、字段等 ID 定位相关产物。
  当你需要追溯某个 feature/page/field/doc 对应的设计文档、字段规格、原型页或实现产物时，调用本 skill。
triggers:
  - "one-id"
  - "lincoln_id"
  - "按 id 查询"
  - "feature 关联"
  - "页面 id"
  - "字段 id"
inputs:
  - name: query
    description: |
      自然语言查询或 exact CLI 子命令。
      例如：
      - "lookup page/web-dashboard"
      - "related feature/checkout-redesign"
      - "list --type field"
      - "create page/list-page --title 列表页 --path issue-9999-test/pages/prototype/web/list/page.html"
    required: true
outputs:
  - one-id 条目详情或关联产物路径列表
required_tools:
  - Bash
  - Read
---

# lc-one-id

## Purpose

Using [lc-one-id] to 查询并维护 Lincoln one-id 索引。

one-id 是 Lincoln 跨阶段追溯的核心机制：PM/UX 阶段为页面、功能点、字段等建立稳定 ID，UE、研发、QA 阶段通过该 ID 查找相关产物，而不是凭路径猜测。

one-id 索引文件位于 `{process_slug}/.lincoln/one-id/` 下，由 `scripts/lincoln_id.py` 管理。

## When to use

-  downstream 阶段（TDD 计划、实现、验收）需要确认某个 feature/page/field 的上游产物。
-  创建或更新 one-id 条目时。
-  检查某个 ID 是否已存在或查找关联项时。

## How to use

本 skill 会把你的 `query` 解析为 `scripts/lincoln_id.py` 命令，并通过 Bash 执行。

常用命令：

- 查询单个条目：
  ```bash
  scripts/lincoln_id.py lookup <type>/<id>
  ```

- 查询某个条目的所有关联项：
  ```bash
  scripts/lincoln_id.py related <type>/<id>
  ```

- 按类型列出所有条目：
  ```bash
  scripts/lincoln_id.py list --type <page|feature|field|doc>
  ```

- 创建或更新条目：
  ```bash
  scripts/lincoln_id.py create <type>/<id> \
    --title "<title>" \
    --path "<relative-path>" \
    --source "<origin>" \
    --relation "<type>/<id>"
  ```

`scripts/lincoln_id.py` 会自动发现当前工作区最新的 `issue-*/workflow-stage.yaml`，本 skill 不传递 `--state-file`。如果自动发现指向了错误的 issue 包，先让目标包成为最新 mtime，或清理旧沙盒包。

## Output handling

- 如果查询成功，返回条目 YAML 内容或关联列表，并据此读取对应产物文件。
- 如果 ID 不存在或类型非法，脚本会返回非零退出码；此时应向用户汇报，而不是继续基于缺失信息推进。
