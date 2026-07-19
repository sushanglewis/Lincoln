# 用户故事: 2026-07-13-issue-47

## 用户故事一:codex 用户首次安装

- 作为: 使用 codex 的开发者
- 我希望: 按 README 指引完成 Lincoln 安装后,在 codex 中直接使用 `lc-status`、`lc-setup` 等命令
- 以便: 获得与 Claude Code 用户相同的阶段工作流引导,无需了解 `.claude/` 内部结构
- 验收标准: 安装生成 `AGENTS.md` 与 prompts;`lc-status` 正确输出当前阶段、等待对象与下一步动作

## 用户故事二:opencode 用户首次安装

- 作为: 使用 opencode 的开发者
- 我希望: 安装后 opencode 中出现 Lincoln 的 agents 与 `lc-*` 命令
- 以便: 按 Lincoln 的 interview-to-knowledge 工作流推进需求
- 验收标准: opencode 配置中可见 Lincoln agents/commands;命令行为与命令清单文档一致

## 用户故事三:现有 Claude Code 用户的命名迁移

- 作为: 已在 Claude Code 中使用 Lincoln 的用户
- 我希望: 命令统一为 `lc-*` 时得到清晰迁移提示,且不丢失已初始化的工作包状态
- 以便: 平滑过渡到新命名,不破坏进行中的 issue 工作
- 验收标准: 升级后既有 `{process_slug}/workflow-stage.yaml` 仍可被读取;迁移说明文档存在

## 用户故事四:框架维护者的单一事实源

- 作为: Lincoln 框架维护者
- 我希望: 修改 `.claude/` 中的角色/技能/阶段定义后,运行一个命令即可重新生成全部 harness 适配产物
- 以便: 避免三份配置漂移,降低维护成本
- 验收标准: 生成器是幂等的;派生产物与 `.claude/` 的一致性有 CI 校验

## 用户故事五:弱能力 harness 上的阶段门控

- 作为: 在 codex(无 hooks 机制)中使用 Lincoln 的用户
- 我希望: 阶段准入/准出与 human gate 仍有可执行的校验方式
- 以便: 不因为 harness 能力弱而丧失 Lincoln 的质量保障
- 验收标准: 门控以 `scripts/stage_loader.py` + 提示词约定落地;human gate 语义在文档与命令输出中明确不可跳过
