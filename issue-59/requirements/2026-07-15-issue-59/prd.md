# PRD: 2026-07-15-issue-59

<!-- status: approved -->

## 产品目标

- 让 Lincoln 在会话开始就能基于可掌握的信息自然地指导和辅助用户:先摸排、再判断、询问确认、有策略开展。
- 消除 README 的终端命令教学,把 onboarding 从"学命令"改为"说话"。

## 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 开场引导注入 | hook 在 fresh repo 与 not_started 两路径注入开场引导指令块 | P0 |
| 概览摸排 | intake-prompt 定义信号清单与深度上限(≤8 次只读、不读源码、禁深度扫描) | P0 |
| 处境判断 | 五要素模型:角色/流程位置/问题/目标/象限初判 + 置信度 | P0 |
| 认知象限确认 | Johari 四象限提问策略,每轮 ≤3 问,收敛到验收标准 + 执行路径 | P0 |
| README 自然语言化 | 双语言消灭命令代码块,新增开场行为说明 | P0 |
| clarify 收敛标准 | 接入认知象限与"验收标准答案 + 执行路径"出口条件 | P1 |

## 非功能需求

- 复用优先:扩展 workflow-router/hook/default.md,不改 stage 注册表与 schema。
- 兼容性:`.claude/` 变更后 codex/opencode 派生产物重新生成,漂移检查通过。
- 可测试:hook 注入行为、prompt 内容标记、README 无命令均由 pytest 守卫;既有 269 基线不破坏。
- 双语言:README.md 与 README.en.md 结构镜像。

## 发布标准

- 验收标准 7 条全部满足(见 requirements.md)。
- `pytest tests/ -q` 全绿;`scripts/static-check.sh` 通过;`check-harness-drift.sh` 无漂移。
- PR 经 PM 评审合并。

## 风险

- hook 注入文本过长会稀释系统提示——缓解:hook 只注入指针与骨架,完整流程放 intake-prompt.md。
- 开场确认可能打扰熟练用户——缓解:摸排为概览级且有操作上限;活跃阶段(已有进行中工作流)不注入引导。
- codex/opencode 端行为依赖派生——缓解:default.md 变更后重新生成并跑漂移检查。
