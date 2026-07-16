# OpenSpec 提案: session-opening-guidance

<!-- status: approved -->

## 背景

- Issue: #59
- 设计文档: `issue-59/designs/issue-59/design-review.md`
- TDD 计划: `issue-59/designs/issue-59/tdd-plan.md`

## 变更概述

让 Lincoln 在会话开始时基于可掌握的信息自然引导用户:

1. 会话启动 hook 在"无状态文件"与"current_stage: not_started"路径注入"开场引导"指令块(指针 + 四步骨架),替代当前的一行 init 命令提示。
2. `lc-workflow-router` 扩展 intake 能力:新增 `prompts/intake-prompt.md`,定义概览摸排(≤8 次只读、不读源码、禁深度扫描)、五要素处境判断、Johari 认知象限确认(每轮 ≤3 问)、路由交接。
3. 契约同步:default.md Universal Cycle 前置开场定向;CLAUDE.md 启动协议与 router 触发条件更新;clarify-requirements 接入认知象限与收敛标准。
4. README.md / README.en.md 消灭全部终端命令教学,改为自然语言入口。

## 影响范围

- 修改:`.claude/hooks/on-session-start.sh`、`.claude/skills/lc-workflow-router/{SKILL.md,prompts/router-prompt.md}`、`.claude/agents/default.md`、`CLAUDE.md`、`.claude/skills/clarify-requirements/prompts/main.md`、`.claude/skills/lc-workflow/SKILL.md`、`.claude/stages/workflow-router.yaml`、`README.md`、`README.en.md`
- 新增:`.claude/skills/lc-workflow-router/prompts/intake-prompt.md`、`tests/test_session_start_guidance.py`、`tests/test_intake_skill.py`、`tests/test_readme_natural_language.py`
- 派生影响:codex/opencode 产物需重新生成(default.md 变更)。

## 兼容性

- stage 注册表、JSON schema、command-map 不变;workflow 模板不变。
- 活跃阶段(`current_stage` 非 not_started)行为完全不变(回归测试守卫)。
- 既有 269 个测试保持全绿。

## 关联设计

- [设计文档](./design.md)
- [任务拆分](./tasks.md)
- [详细规格](./specs/)
