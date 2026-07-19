# 需求文档: 2026-07-13-issue-47

<!-- status: approved -->

## 背景

- Issue: #47(Linear LEW-29)
- 访谈摘要: `issue-47/interviews/2026-07-13-issue-47/summary.md`

Lincoln 目前仅以 Claude Code 插件形态分发:`.claude/` 下的 agents、hooks、skills、stages 通过 `.claude-plugin/` 安装到 Claude Code,用户只有在 Claude Code 中才能获得 Lincoln 的阶段工作流辅助。

## 问题

- 使用 **codex** 或 **opencode** 的用户无法使用 Lincoln 的任何能力(角色、技能、阶段门控、状态协议)。
- 若为三套 harness 各维护一份手写配置,`.claude/` 的任何演进都需要同步三处,必然腐烂(违反 DRY)。
- Lincoln 的命令入口在各 harness 中命名不统一,缺少一致的 `lc-*` 命令契约。
- 不同 harness 能力不对等(Claude Code 有完整 hooks/skills/agents;codex 以 AGENTS.md + prompts 为主;opencode 有 agents/commands 配置但 hook 能力不同),阶段门控等强机制在弱能力 harness 上没有现成落点。

## 用户

- **codex 用户**:希望在 codex 中获得与 Claude Code 等价的 Lincoln 阶段引导与命令体验。
- **opencode 用户**:同上,在 opencode 中获得 Lincoln 辅助。
- **现有 Claude Code 用户**:在 `lc-*` 命名统一过程中不被破坏现有使用习惯。
- **Lincoln 框架维护者**:只维护 `.claude/` 单一事实源,适配产物自动派生。

## 方案

以 `.claude/` 为**单一事实源**,新增**安装时适配生成器**:

1. **派生机制**:扩展安装链路(`lincoln-setup.py` 或独立生成脚本),按目标 harness 从 `.claude/` 生成原生适配产物:
   - codex:生成 `AGENTS.md`(角色与阶段契约)+ prompts(命令入口)。
   - opencode:生成 opencode 配置(agents/commands)及对应 markdown。
   - claude-code:维持现状,命令命名对齐 `lc-*`。
2. **能力映射与降级**:定义 harness 能力矩阵(hooks/skills/agents/状态注入);弱能力 harness 用提示词约定 + `workflow-stage.yaml` 状态协议替代 hook 强制,保证最低可用体验(阶段引导、产物校验、human gate 语义不丢)。
3. **`lc-*` 命令统一**:建立命令映射表(如 `lincoln-status` → `lc-status`),三个 harness 暴露一致的 `lc-*` 命令集;迁移策略见 PRD。
4. **可验证**:每个 harness 的适配产物有结构校验(测试),安装后 `lc-status` 可运行并正确汇报阶段状态。

## 开放问题(PM 已于 2026-07-13 决策)

- [x] codex 的目标形态 → **设计阶段先做 spike 验证**(AGENTS.md + prompts 为候选起点,以 spike 结论为准)。
- [x] opencode 适配的目标版本/配置格式 → **设计阶段先做 spike 验证**(目录式 agents/commands 为候选起点,以 spike 结论为准)。
- [x] `lc-*` 命名 → **直接重命名**(破坏性,旧名不保留;配套迁移说明)。
- [x] 生成时机 → **安装时生成 + CI 漂移校验**(检测 `.claude/` 与派生产物不一致即失败)。

## 验收标准

- [ ] 在 codex 中完成一次 Lincoln 安装后,可通过 `lc-*` 命令获得阶段状态汇报与下一步指引。
- [ ] 在 opencode 中完成一次 Lincoln 安装后,同上。
- [ ] Claude Code 中现有功能不回归(263 测试基线 + hooks 行为不变)。
- [ ] 三个 harness 的命令清单一致,均为 `lc-*` 前缀。
- [ ] `.claude/` 变更后,重新运行生成器即可刷新全部适配产物(单一事实源成立)。
- [ ] 适配产物有自动化结构校验,CI 通过。

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认需求`。*
