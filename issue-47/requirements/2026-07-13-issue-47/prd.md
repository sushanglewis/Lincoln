# PRD: 2026-07-13-issue-47

## 产品目标

- 让 Lincoln 的阶段工作流能力(角色、技能、门控、状态协议)在 **codex** 与 **opencode** 两个 harness 上可用,体验与 Claude Code 对齐。
- 建立 `lc-*` 统一命令契约,三个 harness 命令集一致。
- 保持 `.claude/` 单一事实源:适配产物全部派生,不允许手写副本长期存在。

## 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 适配生成器(codex) | 从 `.claude/` 生成 `AGENTS.md` + codex prompts(角色契约、阶段引导、`lc-*` 命令入口) | P0 |
| 适配生成器(opencode) | 从 `.claude/` 生成 opencode agents/commands 配置与 markdown | P0 |
| `lc-*` 命令映射 | 定义命令映射表(现有 lincoln-* 入口 → lc-*),三 harness 一致暴露 | P0 |
| 能力矩阵与降级策略 | 文档化 hooks/skills/agents/状态注入在各 harness 的映射;弱能力路径用 stage_loader.py + 提示词约定兜底 | P0 |
| 安装链路集成 | `lincoln-setup.py` 增加 harness 选择与适配产物生成步骤;README 提示词同步 | P1 |
| 漂移校验 | 测试/CI 校验派生产物与 `.claude/` 一致(可重新生成且幂等) | P1 |
| 迁移说明 | `lc-*` 命名迁移指南(重命名或别名策略待定,见开放问题) | P1 |
| 分发 | 评估 codex/opencode 侧的分发方式(仓库引用/插件市场) | P2 |

## 非功能需求

- 生成器幂等:重复运行不产生 diff(除时间戳类内容外)。
- 派生产物必须标注"自动生成,请勿手改"及来源路径。
- 不引入新的运行时依赖(生成器使用仓库现有 Python + yaml 栈)。
- Claude Code 现有行为零回归:全部现有测试通过,hooks 语义不变。

## 发布标准

- codex 与 opencode 上各完成一次端到端安装 + `lc-status` 阶段汇报验证。
- 三 harness 命令清单文档一致且均为 `lc-*`。
- CI 绿:既有 263 测试 + 新增适配结构校验全部通过。
- README/CLAUDE.md 完成多 harness 安装说明更新。

## 风险

- **harness 能力差异被低估**:codex/opencode 的 agents/commands 机制可能与假设不符 —— 设计阶段先做最小 spike 验证各自格式。
- **lc-* 重命名破坏存量用户**:若采用破坏性重命名,需清晰的升级提示;别名方案增加维护面 —— 待 PM 在 human gate 决策。
- **派生表达力不足**:`.claude/` 中部分机制(hooks 强制注入)无法翻译到弱 harness —— 用降级策略兜底,但需接受体验差异并文档化。
- **范围蔓延**:MVP 应限定为"安装生成 + lc-* 命令 + 状态协议",分发渠道(opencode 插件市场等)放 P2。
