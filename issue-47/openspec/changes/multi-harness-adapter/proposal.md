# OpenSpec 提案: multi-harness-adapter

## 背景

- Issue: #47(Linear LEW-29)
- 设计文档: `issue-47/designs/issue-47/design-review.md`(PM approved)
- TDD 计划: `issue-47/designs/issue-47/tdd-plan.md`

## 变更概述

新增 harness 适配层,使 Lincoln 端到端逻辑(角色、技能、阶段工作流、状态协议、命令入口)在 codex 与 opencode 上可用:

1. `.claude/harnesses/` — 新增 harness manifest(codex.yaml、opencode.yaml、claude-code.yaml)与共享 `command-map.yaml`(`lc-*` 命令单一来源)。
2. `scripts/lincoln_harness_adapter.py` — manifest 驱动的适配生成器,幂等,支持 `--check` 漂移校验。
3. `lc-*` 命令统一:Claude Code 侧 `lincoln-*` 入口直接重命名(破坏性,配套迁移提示)。
4. `lincoln-setup.py bootstrap --harness <name>` 串联依赖安装与适配生成;漂移校验接入 static-check。
5. 门控与 CI/CD 从轻:门控统一经 `stage_loader.py` + 命令提示词约定;CI 仅漂移校验。

## 影响范围

- 新增:`.claude/harnesses/`、`scripts/lincoln_harness_adapter.py`、`scripts/check-harness-drift.sh`、`tests/test_lincoln_harness_adapter.py`
- 修改:`.claude/skills/`(lincoln-* → lc-* 重命名)、`scripts/lincoln-setup.py`、`scripts/static-check.sh`、`README.md`、`CLAUDE.md`、`.gitignore`、`.claude/skills/routing.yaml`、`tests/test_lincoln_setup.py`
- 生成(不入 git):`AGENTS.md`、`~/.codex/prompts/lc-*.md`、`.opencode/`

## 兼容性

- **破坏性**:`lincoln-*` 命令名移除,统一为 `lc-*`;安装时检测旧名残留并提示迁移;既有 `{process_slug}/workflow-stage.yaml` 状态协议不变(schema 2.0 无新字段)。
- 既有 263 测试为零回归基线;重命名涉及的 fixture 同步更新。

## 关联设计

- [设计文档](../../designs/issue-47/design-review.md)
- [TDD 计划](../../designs/issue-47/tdd-plan.md)
- [数据模型](../../designs/issue-47/data-model.md)
