# 场景分析: issue-47

## 用户画像

- **codex 开发者**: 日常使用 OpenAI Codex CLI,不装 Claude Code;希望通过 `lc-*` 命令获得 Lincoln 阶段引导。
- **opencode 开发者**: 使用 sst/opencode,习惯 `.opencode/` 目录式配置;期望 Lincoln 以原生 agents/commands 形态出现。
- **存量 Claude Code 用户**: 已有进行中的 issue 工作包;升级后旧命令名消失,需要明确迁移指引。
- **框架维护者**: 修改 `.claude/` 后运行一条命令刷新全部 harness 产物,CI 防止漂移。

## 核心场景

### 场景一:codex 用户安装并使用

- 触发条件: codex 用户克隆 Lincoln 仓库,运行 `python scripts/lincoln-setup.py bootstrap --harness codex`。
- 用户行为: 安装器生成 `AGENTS.md`(项目根,含 Lincoln 阶段契约与 `lc-*` 命令说明)与 `~/.codex/prompts/lc-*.md`;用户在 codex 中输入 `/lc-status`。
- 预期结果: codex 按 prompt 指引运行 `python scripts/lincoln-status.py`,输出当前阶段、等待对象、下一步动作;阶段推进全部经 `scripts/stage_loader.py`。

### 场景二:opencode 用户安装并使用

- 触发条件: opencode 用户运行 `lincoln-setup.py bootstrap --harness opencode`。
- 用户行为: 安装器生成 `.opencode/agent/lincoln-*.md` 与 `.opencode/command/lc-*.md`;用户在 opencode 中输入 `/lc-status` 或切换 lincoln-pm agent。
- 预期结果: 命令模板驱动对应脚本;agent frontmatter(mode/model/permission)正确;行为与命令清单文档一致。

### 场景三:存量用户升级(破坏性重命名)

- 触发条件: 已用旧命令名(lincoln-status 等)的 Claude Code 用户拉取新版本。
- 用户行为: 安装器检测旧命令残留并打印迁移提示(旧名 → `lc-*` 映射表);用户按指引更新肌肉记忆/脚本。
- 预期结果: 既有 `{process_slug}/workflow-stage.yaml` 状态无损读取;README 迁移小节可查。

### 场景四:维护者改 `.claude/` 后重新生成

- 触发条件: 维护者修改了 `.claude/agents/` 或阶段定义。
- 用户行为: 运行生成命令刷新 codex/opencode 产物;CI 漂移校验重新生成并比对。
- 预期结果: 生成幂等(无语义变化则零 diff);若有 diff 且未提交产物更新,CI 失败提示。

### 场景五:弱能力 harness 上的门控

- 触发条件: codex 用户到达 clarify 阶段出口(human gate)。
- 用户行为: agent 按提示词约定运行 `stage_loader.py --action validate-exit`;缺少 human 审批标记时校验失败并暂停。
- 预期结果: 无 hooks 强制也能保持门控语义;human gate 不可跳过的约束体现在命令输出与状态文件中。

## 边界场景

- 用户同时安装多个 harness(如 claude-code + codex):生成器各自独立产物,状态文件共享同一份 `{process_slug}/workflow-stage.yaml`,不冲突。
- 非 git 仓库目录运行安装器:明确报错并退出(依赖仓库结构)。
- Windows 环境:本期仅承诺 macOS/Linux(与既有 dependencies.yaml 平台策略一致)。

## 异常场景

- codex prompts/skills 目录约定与假设不符:实现阶段 spike 验证失败 → 回退为仅 `AGENTS.md` 内联命令说明,`lc-*` 以文档命令形式存在。
- opencode 版本差异导致 frontmatter 字段变化:生成器只对已 spike 的字段子集输出,未知字段不写入。
- 生成中途失败(磁盘/权限):生成器按 harness 原子提交(先写临时目录再移动),不留半成品。
