# Design Review: issue-47

<!-- status: approved -->

## 背景

- Issue: #47(Linear LEW-29)
- 关联需求: `issue-47/requirements/2026-07-13-issue-47/requirements.md`(PM approved)
- 关联访谈: `issue-47/interviews/2026-07-13-issue-47/summary.md`
- PM 追加范围指引(2026-07-13): 端到端逻辑全部适配 codex/opencode;**门控检查与 CI/CD 从轻**;其余部分全量适配。

## 设计目标

1. 以 `.claude/` 为单一事实源,派生 codex 与 opencode 的原生适配产物,覆盖 Lincoln 端到端逻辑(角色、技能、阶段工作流、状态协议、命令入口)。
2. 三个 harness 暴露一致的 `lc-*` 命令集(直接重命名,旧名移除)。
3. 门控检查与 CI/CD 采用轻量实现:弱能力 harness 以 `scripts/stage_loader.py` + 提示词约定兜底,CI 仅做漂移校验。
4. 安装链路(`lincoln-setup.py`)支持选择目标 harness 并生成适配产物,生成幂等。

## 范围

### 范围内

- 适配生成器:manifest 驱动,从 `.claude/`(agents/skills/stages/routing)生成各 harness 产物。
- codex 适配:`AGENTS.md`(项目级契约)+ `~/.codex/prompts/lc-*.md`(命令入口);skills 复用 SKILL.md 约定(实现阶段验证 codex skills 目录约定)。
- opencode 适配:`.opencode/agent/*.md`、`.opencode/command/lc-*.md`、可选 `.opencode/plugin/*.js`(会话事件轻量 hook)。
- `lc-*` 命令映射与 Claude Code 侧重命名(含迁移说明、旧名检测提示)。
- 轻量门控:所有 harness 统一以 `scripts/stage_loader.py` 为门控执行器;无 hooks 的 harness 由命令提示词约束执行顺序。
- 轻量 CI:一个 drift-check 脚本/测试,重新生成适配产物并要求零 diff。
- README/CLAUDE.md 多 harness 安装说明。

### 范围外(后续迭代)

- codex/opencode 插件市场或包管理器分发渠道。
- 深度 CI/CD(自动发布、跨 harness E2E 流水线)。
- opencode plugin 的完整 hook 体系(仅做最小会话事件注入)。
- codex MCP/工具配置适配。

## 关键决策

| 决策 | 选项 | 理由 |
|------|------|------|
| 适配产物来源 | `.claude/` 单一事实源 + 生成器派生 | PM 已确认;避免三份配置漂移 |
| 生成时机 | 安装时生成 + CI 漂移校验 | PM 已确认;产物不进 git,CI 保证可重生且一致 |
| `lc-*` 策略 | 直接重命名(破坏性) | PM 已确认;长期维护成本最低,配套迁移说明 |
| codex 形态 | `AGENTS.md` + `~/.codex/prompts/*.md`;skills 目录实现阶段验证 | spike:官方 docs 确认 AGENTS.md 与 prompts/skills 机制存在,具体路径以仓库 docs/agents_md.md 与实现验证为准 |
| opencode 形态 | 目录式 `.opencode/agent/` + `.opencode/command/` + 可选 `plugin/` | spike 已确认(Context7/opencode 源码 schema):frontmatter 支持 description/mode/model/permission,command 支持 $ARGUMENTS |
| 门控实现 | 统一 `stage_loader.py` CLI;无 hooks harness 用命令提示词约束 | PM 指示从轻;门控语义(准入/准出/human gate)不依赖 harness 原生 hook 即可成立 |
| CI 范围 | 仅漂移校验 + 既有测试 | PM 指示从轻 |

## 验收标准

- [ ] codex 安装后:`AGENTS.md` 生成且包含阶段契约;`lc-status` prompt 可调用并正确汇报阶段。
- [ ] opencode 安装后:`.opencode/agent/` 与 `.opencode/command/lc-*` 生成;命令可调用。
- [ ] Claude Code:`lc-*` 命令集生效,旧命令移除,既有 263 测试零回归。
- [ ] 生成器幂等;CI 漂移校验通过(重新生成零 diff)。
- [ ] 门控在 codex/opencode 上以 `stage_loader.py` 可执行(entry/exit/human gate 语义保留)。

## 关联文档

- [场景分析](./scenarios.md)
- [功能目录](./feature-catalog.md)
- [数据模型](./data-model.md)
- [流程图](./flows.md)
- [可行性分析](./feasibility.md)

---
*PM 确认时请添加 `<!-- status: approved -->` 或 `[x] PM 已确认设计文档`。*
