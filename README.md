# Lincoln — AI-Native 研发工作流与产研协作体系

> 中文 | [English](README.en.md)

Lincoln 是一个贯穿 **IDE、Agent Harness、代码托管、知识管理、技能、插件与自动化程序** 的 AI-Native 研发工作流体系。它以**阶段**为节奏、以**门控**为质量保障、以**可重复 SOP** 为骨架，把需求澄清、产品设计、原型、TDD 计划、OpenSpec 提案、任务拆分、研发实现和知识库沉淀串成一条可人机协作的流水线。

- **全流程，而非单点工具**：每个阶段都有明确的角色、技能与产物约定——Agent 在恰当的节点介入，而不是替代人的判断。
- **规范化，但不繁琐**：阶段门控、human gate、分支卫生，以及「过程文档留分支、耐用知识入 vault」的双轨机制，让协作可追溯、可交接、可审计。
- **低侵入、可插拔**：以 harness 插件的形态融入你的项目——技能、hooks、工作流模板与多 harness 适配沿同一元模型扩展，不要求你为它改造自己的项目。

## 最新版本

[![Release](https://img.shields.io/badge/release-v1.6.0-blue)](RELEASE.md)

**v1.6.0** 已发布：Lincoln 切换为全局 npm 插件模型，通过 `npm install -g @sushanglewis/lincoln` 安装，项目侧使用 `.lincoln.yaml` 选择性激活。

查看完整发布说明：[RELEASE.md](RELEASE.md)

## 快速开始

打开仓库后，直接用自然语言告诉 Agent 你的目标即可。Lincoln 会自动进入对应的工作流：

- **开始处理 issue 55** → 初始化 `issue-55` 分支与工作包，进入 `interview-to-knowledge` 团队工作流
- **使用 existing-project-iteration 理解这个代码库** → 扫描源码并生成 `knowledge/` 功能知识库，再规划下一个迭代
- **用 design-spike 探索这个想法** → 澄清需求并产出设计评审与可交互原型
- **现在什么状态** → 汇报当前阶段、等待对象、推荐技能与下一步动作

## 安装

### 前置条件

- Node.js ≥ 20
- Python 3.10+（`lincoln install` 会自动探测 `python3.12 / 3.11 / 3.10` 并创建虚拟环境）
- 已安装至少一个 agent harness：`Claude Code`、`Codex` 或 `OpenCode`

### 安装 Lincoln

```bash
npm install -g @sushanglewis/lincoln
lincoln install --yes
```

> **注意**：`npm install -g` 只是把 CLI 和框架 payload 安装到 npm 全局目录；**必须执行 `lincoln install`**，才会把 hooks、agents、skills、scripts 等完整运行时体系同步到 `~/.claude/`、`~/.codex/`、`~/.opencode/`。

如果之前安装过旧版 `lincoln-install`，需要先卸载（旧包与新版 bin 名冲突）：

```bash
npm uninstall -g lincoln-install
npm install -g @sushanglewis/lincoln
lincoln install --yes
```

若要强制重装，可加上 `--force`：

```bash
npm install -g @sushanglewis/lincoln --force
lincoln install --yes
```

### 验证安装

```bash
lincoln --version
lincoln doctor --json
```

`lincoln doctor --json` 会输出 Node、Python、PyYAML、npm、全局 marker、payload hooks、venv、项目 marker 等检查项。

### 在项目中启用

Lincoln hooks 默认**不会**在空目录激活。进入项目后执行：

```bash
cd your-project
lincoln init-project
```

这会在项目根目录创建 `.lincoln.yaml` 标记文件，之后在该目录打开 Claude Code 即可使用 `/lc-*` 命令。

### 更新 Lincoln

```bash
lincoln update
```

### 从旧版 vendored 模式迁移

如果你的项目之前是把 Lincoln 框架源码直接提交到仓库里的，可以用：

```bash
lincoln migrate-project --dry-run   # 先看看会删哪些文件
lincoln migrate-project --yes       # 确认迁移
```

旧版 `npx lincoln-install` / `npx lincoln-update` 仍保留但已弃用，建议迁移到全局 CLI。

第一次使用？阅读 [USAGE.md](USAGE.md) 获取完整安装与使用指南。

## Lincoln 能做什么

### 阶段驱动的工作流引擎

每个阶段定义在 `.claude/stages/<stage-id>.yaml`，内含角色、可调用的技能、门控条件与产物要求。`workflow-stage.yaml` 作为运行时状态，由 Lincoln 的阶段加载器驱动阶段校验、产物记录与 gate 推进。

### 预设 SOP 工作流模板

| 工作流 | 场景 | 模式 |
|--------|------|------|
| `interview-to-knowledge` | 从访谈录音到 GitHub Issues 再到 Obsidian 知识库沉淀 | team |
| `existing-project-iteration` | 已有源码，先建知识库再迭代 | solo |
| `bug-fix` | 明确 bug，轻量设计后快速修复 | solo |
| `design-spike` | 需求尚不清晰，做方案预研或原型 | solo |
| `oss-first-design` | 强依赖开源方案，先调研再设计 | solo |
| `pm-research` | 体系化完成竞品/市场/用户/相关者研究 | solo |

完整模板说明见 [`.claude/workflows/README.md`](.claude/workflows/README.md)。

### Issue 工作包（HTML 门户）

每个需求对应一个 GitHub issue 和一个 Lincoln feature 分支。工作包目录 `issue-<N>/` 包含：

- `index.html` — 人读门户，聚合阶段状态、导航与产物
- `workflow-stage.yaml` — 机器状态与 handoff 协议
- `documents.yaml` — 产物索引与 human 确认状态
- `pages/docs/` — 需求、PRD、设计、TDD 计划等 HTML 页面
- `pages/prototype/` — 可交互原型 HTML 页面
- `handoffs/` — 阶段交接文档

## 自然语言交互

Lincoln 是 AI-Native 工作流——**你不需要在终端输入任何命令**。直接用自然语言描述意图，Agent 会自动翻译成对应脚本并代为执行。

| 你说 | Agent 做 |
|------|----------|
| 开始处理 issue 55 | 初始化分支与工作包，进入 `interview-to-knowledge` |
| 现在什么状态 | 汇报当前阶段、等待对象与下一步 |
| 提交本阶段产物 | 记录产物并刷新 `documents.yaml` |
| 确认通过 | 在人类 PM 显式确认后标记 gate 通过 |
| 生成交接 | 生成 handoff 文档 |
| 检查 Lincoln 环境 | 检测依赖并列出缺失项 |
| 列出所有活跃分支 | 列出所有 issue 分支的阶段状态与等待对象 |
| 运行 benchmark | 生成 Lincoln 会话基准评测报告 |
| 启动 PM 研究工作流 | 进入 `pm-research` 研究链路 |

更多命令与用法见 [USAGE.md](USAGE.md)。

## 两种使用方式

### 轻量个人路径（vibe-coding / 独立 maker）

适合本地项目、个人想法快速迭代。无需先建 GitHub issue，直接选择 workflow 模板即可开始。产物落在工作包目录下，可随时升级为团队流程。

### 团队 issue 路径（产品 / 设计 / 研发 / QA）

每个需求使用独立的 Lincoln feature 分支（命名约定 `issue-<N>`）。阶段状态随分支提交，下游角色 checkout 同一分支继续。过程文档不合并到 `main`，通过 PR 只合并最终代码产物。

详细路径说明见 [USAGE.md](USAGE.md)。

## 工具

- `@sushanglewis/lincoln` — 全局 CLI：`lincoln install`、`lincoln update`、`lincoln use`、`lincoln doctor`、`lincoln init-project`、`lincoln migrate-project`、`lincoln record`
- `tools/lincoln/` — 基于 Ink/React 的 TUI 录音前端（`lincoln-record` CLI）
- `tools/lincoln-record/` — Rust 本地录音转写 CLI（whisper-rs + Metal 加速、说话人分离）
- `tools/lincoln-installer/` — 旧版终端 TUI 安装器与更新器（已弃用，保留向后兼容）

## 多 harness 支持（codex / opencode）

Lincoln 的端到端逻辑（角色契约、阶段工作流、`lc-*` 命令）可适配到 codex 与 opencode。`.claude/` 是唯一事实源，各 harness 产物由适配器自动生成，**不要手改生成产物**。

需要对 Agent 说「生成 codex 适配」或「生成 opencode 适配」。生成产物不入 git，CI 会校验 manifest 可生成、本地产物未漂移。

## 扩展与贡献

Lincoln 的 `.claude/` 是开放的系统提示层，欢迎基于同一套元模型贡献新的 Agent 角色、skills、hooks 或工作流模板。

提交 PR 前请阅读：

- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献者护栏、核心与领域包边界、测试分层与 eval 门禁规范
- [CLAUDE.md](CLAUDE.md) — Agent 契约、人类门控规则与产物规范
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 新增工作流模板的步骤

## 了解更多

- [USAGE.md](USAGE.md) — 完整用户手册
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献者指南
- [RELEASE.md](RELEASE.md) — 发布说明与 Changelog
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 工作流模板总览
- [OpenSpec 文档](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)

## License

Lincoln 本体以 [MIT License](LICENSE) 发布，Copyright (c) 2026 苏尚lewis (sushanglewis)。

外部 skills、CLI 与插件的许可证声明见 [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml) 与 [`.claude/agents/external/NOTICES.md`](.claude/agents/external/NOTICES.md)。
