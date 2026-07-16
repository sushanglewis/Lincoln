# 需求文档: 2026-07-15-issue-59

<!-- status: approved -->

## 背景

- Issue: #59
- 访谈摘要: `issue-59/interviews/2026-07-15-issue-59/summary.md`
- 审批依据: PM 于 2026-07-15 在 Conductor 中显式批准实现计划（含本需求的完整阐释与方案 A 选型）。

## 问题

- README 以 10+ 处终端命令代码块教用户操作,学习曲线陡峭,导致潜在用户放弃 Lincoln。
- 会话启动时 Lincoln 不掌握也不主动掌握项目全貌:无状态文件或 `current_stage: not_started` 时,hook 仅输出一行 init 命令即退出,零摸排、零引导。
- 现有机制只判断"项目"(选哪个工作流模板),不判断"人"(用户是谁、什么角色、位于流程哪里、解决什么问题、目标是什么)。
- 澄清过程缺乏对用户认知位置的定位(知道自己知道/知道自己不知道/不知道自己知道/不知道自己不知道),提问策略一刀切。
- "反复确认直到有验收标准答案与执行路径"的编排散落在各阶段,没有统一的开场引导。

## 用户

- 首次接触 Lincoln、不愿学习终端命令的潜在用户(流失风险最高)。
- 使用 claude-code / codex / opencode 的 PM、设计师、研发等角色。
- Lincoln 框架自身的维护者(本框架行为变更的直接影响者)。

## 方案

方案 A(PM 已批准):扩展现有入口,不新建独立 intake 阶段。

1. **hook 注入**:`.claude/hooks/on-session-start.sh` 在 fresh repo 与 `not_started` 两路径注入"开场引导"指令块,指向 intake-prompt。
2. **intake 流程**:扩展 `lc-workflow-router`,新增 `prompts/intake-prompt.md`——摸排(≤8 次只读、不读源码、禁深度扫描)→ 判断(角色/流程位置/问题/目标/象限初判)→ 展示判断 + Johari 确认(每轮 ≤3 问)→ 路由交接。
3. **契约更新**:`default.md` Universal Cycle 前置开场定向;`CLAUDE.md` 启动协议与 router 触发条件同步;`clarify-requirements` 接入认知象限与收敛标准。
4. **README 改写**:双语言文件消灭全部命令代码块,改为"对 Agent 说 X"自然语言表述,新增开场行为说明小节。

## 验收标准

- [ ] README.md 与 README.en.md 的用户面向章节不含任何终端命令调用(代码块与内联),由 pytest 守卫。
- [ ] 无状态文件或 `current_stage: not_started` 时,会话启动 hook 输出包含"开场引导"指令块;活跃阶段不输出,由 pytest 守卫。
- [ ] intake-prompt 定义概览级摸排(信号清单 + ≤8 次只读操作上限 + 禁止深度扫描)与五要素处境判断(角色/流程位置/问题/目标/置信度)。
- [ ] intake-prompt 定义 Johari 四象限确认策略(知道自己知道/知道自己不知道/不知道自己知道/不知道自己不知道),每轮确认问题 ≤3 个。
- [ ] 用户对目标与执行路径确认前,不做实现性工作(契约与 prompt 均有明文禁忌)。
- [ ] clarify-requirements 收敛标准更新为:每个开放问题都有明确验收标准答案与确定的执行路径。
- [ ] 既有 269 个测试保持全绿,新增测试覆盖上述行为;codex/opencode 派生产物重新生成且漂移检查通过。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。(已于 2026-07-15 计划审批确认)*
