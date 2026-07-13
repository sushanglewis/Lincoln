# Lincoln — AI-Native 研发工作流与产研协作体系

> **Lincoln 是什么？** Lincoln 是一个基于 **Conductor + Claude Code + OpenSpec + GitHub + Obsidian** 的 AI-Native 研发工作流体系。它以**阶段**为节奏、以**门控**为质量保障、以**可重复 SOP** 为骨架，把需求澄清、产品设计、原型、TDD 计划、OpenSpec 提案、任务拆分、研发实现和知识库沉淀串成一条可人机协作的流水线。
>
> 它既适合 **vibe-coding 开发者、独立 maker** 在本地项目上与 Agent 结对迭代；也适合 **产品、设计、研发、QA** 团队以 GitHub issue 为单元进行多角色协作。

## 首次打开？让 Claude 帮你完成安装

Lincoln 的 hooks 通常会在你第一次打开仓库时自动触发安装。如果 Claude 没有自动开始，请复制下面的提示词发送给 Claude：

> 请帮我完成 Lincoln 的初始化安装：
> 1. 先问我两个问题，并根据回答决定安装范围：
>    - 是否需要**录音转写**能力（访谈录音 → 文字稿）？需要才安装 ffmpeg 和 Whisper。
>    - 是否需要运行 **benchmark**（Lincoln 基准评测）？
> 2. 检查当前仓库的 Lincoln 环境，列出所有缺失的依赖。
> 3. 安装外部 skills：superpowers、gsd（均跟踪上游仓库 main 分支）到 `~/.claude/skills/`，并确保 ref 正确。
> 4. 安装 CLI 工具：openspec、gh；仅当我需要录音转写时，再安装 ffmpeg 和一个 Whisper 实现（优先 faster-whisper）。
> 5. 安装 oh-my-claudecode 插件。
> 6. 交互式配置 `.github/openspec-config.yml`（询问我 GitHub owner 和 repo name）。
> 7. 运行 `scripts/init-project.sh` 完成项目初始化。
> 8. 如果我需要 benchmark，介绍 `scripts/lincoln_benchmark.py` 的用法。
> 9. 完成后汇报状态。
>
> 安装任何全局工具或写入配置前，请先向我确认。

如果你只需要走[轻量个人路径](#快速开始)，可以跳过 `gh`、`ffmpeg`、Whisper 和 `.github/openspec-config.yml` 配置，只保留 `python3`、Claude Code 环境与 Lincoln 自身 hooks。

> **我从哪里开始？**
> - **vibe-coding / 独立 maker**（个人项目、AI 结对编程）：跳到 [快速开始](#快速开始) 的轻量个人路径。
> - **团队协作者**（产品、设计、研发、QA，以 GitHub issue 驱动）：跳到 [快速开始](#快速开始) 的团队 issue 路径。
> - **框架开发者 / 贡献者**（扩展 agent、skills、hooks、工作流模板）：阅读 [框架文档](#框架文档)、[`CLAUDE.md`](CLAUDE.md) 和 [扩展与贡献 Lincoln](#扩展与贡献-lincoln)。

## 快速开始

Lincoln 提供两种启动方式，选择适合你的即可。

### 路径 A：轻量个人路径（vibe-coding / 独立 maker）

如果你已经有一个本地项目，或者只是有一个想法想和 Agent 一起快速迭代，可以直接从 workflow 模板开始，无需先建 GitHub issue。

1. 在 Conductor 中打开项目仓库。
2. 让 Claude 运行：
   ```bash
   python scripts/lincoln-setup.py check
   ```
3. 根据你的场景选择模板：
   - **已有源码，想让 Agent 先读懂代码再迭代**：使用 `existing-project-iteration`
   - **只有想法，先做方案/原型探索**：使用 `design-spike`
4. 对 Claude 说：
   - 如果你选择 `existing-project-iteration`：
     > 请使用 Lincoln 的 `existing-project-iteration` 模板，帮我理解当前代码库并规划下一个功能迭代。
   - 如果你选择 `design-spike`：
     > 请使用 Lincoln 的 `design-spike` 模板，帮我澄清这个想法并产出设计评审与原型。
5. 后续如果决定引入团队流程或需要 GitHub issue 跟踪，可运行：
   ```bash
   scripts/init-lincoln-branch.sh --issue-number <number> ...
   ```
   新建一个 issue 工作包，再把个人路径中已确认的需求/设计产物手动整理到新的 `issue-<number>/` 目录。

> 个人路径的产物默认落在由模板自动选择的工作包目录（如 workspace 名或仓库名）下，其中代码知识库产物写入 `knowledge/`，设计、需求、调研产物分别写入 `<process_slug>/designs/`、`<process_slug>/requirements/`、`<process_slug>/docs/research/`。

### 路径 B：团队 issue 路径（默认）

在 GitHub 上点击 **Use this template** 创建项目仓库，然后 clone 到本地 Conductor 工作区。

#### 初始化一个 issue 工作包

每个需求都对应一个 GitHub issue 和一个 Lincoln feature 分支。`scripts/init-lincoln-branch.sh` 会基于 issue 编号创建分支，并从 `.claude/templates/issue-package/` 复制模板生成该 issue 专属的工作包目录：

```bash
# 在 main 分支上运行（会自动切出 issue-<number> 分支）
scripts/init-lincoln-branch.sh --issue-number 21 \
  --session-id 2026-07-08-stakeholder \
  --design-id checkout-redesign \
  --push
```

参数说明：
- `--issue-number`：GitHub issue 编号，必填。
- `--session-id`：访谈/需求会话 ID，格式 `YYYY-MM-DD-descriptive-name`；省略时默认生成。
- `--design-id`：设计主题 ID，kebab-case；省略时默认生成。
- `--process-slug`：工作包目录名，默认 `issue-<number>`。
- `--push`：初始化后推送分支到远程。

执行后会在分支上生成：

```
issue-21/
├── workflow-stage.yaml          # issue 运行时状态与 handoff 协议
├── recordings/                  # 原始录音（gitignored）
├── interviews/<session-id>/     # 转写、摘要、原始洞察
├── requirements/<session-id>/   # 需求文档、用户故事、PRD
├── designs/<design-id>/         # 设计评审、场景、数据模型、流程、原型、TDD 计划
├── openspec/changes/            # OpenSpec 变更提案
├── docs/research/               # 开源方案调研、决策记录
└── handoffs/                    # 阶段交接文档
```

`issue-21/workflow-stage.yaml` 是人类、Agent 之间共享的阶段交接协议；`.claude/templates/issue-package/workflow-stage.yaml` 只是生成它的模板。

> 全部模板的详细说明见 [`.claude/workflows/README.md`](.claude/workflows/README.md)。工作流模板是场景参考，人类可以基于当前场景要求 Agent 按某个固定 workflow 执行，不强制自动路由。

---

## 新增能力（v1.2.0）

- **Issue 驱动的工作包**：`scripts/init-lincoln-branch.sh --issue-number ...` 生成 issue 专属分支与 `{process_slug}/` 工作包，过程文档不再污染 `main`。
- **模板化工作包**：`.claude/templates/issue-package/` 提供统一目录结构与 `workflow-stage.yaml` 模板。
- **状态文件实例化**：运行时状态保存在 `{process_slug}/workflow-stage.yaml`，而非 `.claude/workflow-stage.yaml`。
- **工作流模板目录**：[`.claude/workflows/README.md`](.claude/workflows/README.md) 集中维护所有 SOP 模板说明。
- **Claude Code 插件化**：新增 `.claude-plugin/` 清单，支持作为 Claude Code 插件安装。

---

## 工作状态与交接

### 查看当前分支状态

```bash
python scripts/lincoln-status.py --format table
```

输出包含：当前阶段、等待对象、已加载上下文、推荐技能、产物状态、下一步动作。支持 `--format json|table|markdown`。

### 生成交接文档

暂停或切换协作者时：

```bash
python scripts/stage_loader.py --stage <current-stage> --action handoff-report
```

生成 `.context/lincoln-handoff-<stage>.md` 或 `{process_slug}/handoffs/` 文档，包含当前阶段、已确认产物、待解决问题、下一角色、推荐技能。

阶段通过人类确认后：

```bash
python scripts/stage_loader.py --stage <current-stage> --action approve-gate
```

标记该阶段 gate 已审批通过。

### 查看所有进行中的 Lincoln 分支

```bash
scripts/list-active-lincoln-branches.sh
# 仅查看等待我的分支
scripts/list-active-lincoln-branches.sh --waiting-for-me
```

### 审计工作流健康度

```bash
python scripts/lincoln-audit.py --format markdown
```

输出 PASS/WARN/FAIL 报告，覆盖状态一致性、产物完整性、门控合规性、技能覆盖、异常检测。

---

## 框架文档

Lincoln 框架的核心定义直接内联在 `.claude/` 中：

- [`.claude/stages/stage-manifest.yaml`](.claude/stages/stage-manifest.yaml) — Stage、Gate、Artifact、Role 的注册表与能力边界。
- [`.claude/skills/routing.yaml`](.claude/skills/routing.yaml) — 按阶段映射外部技能与 Lincoln 原生技能。
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 所有 SOP 工作流模板的索引与路由说明。
- [`.claude/schemas/`](.claude/schemas/) — `workflow-stage`、`stage-definition`、`workflow-template` 的 JSON Schema。
- [`CLAUDE.md`](CLAUDE.md) — Agent 启动自检、人类门控规则、handoff 协议、技能调用规范。

---

## 分支级工作流与阶段状态

- 每个需求使用独立的 Lincoln feature 分支（例如 `issue-21`）。
- 阶段状态随分支提交，保存在 `{process_slug}/workflow-stage.yaml`。
- 过程文档（`recordings/`、`interviews/`、`requirements/`、`designs/`、`openspec/`、`docs/research/`）随 feature 分支传递，**不合并到 `main`**。
- 当前负责人在本地推进阶段后，push feature 分支到远程；下游角色 checkout 同一分支继续。
- 每个阶段都有 `.claude/stages/<stage-id>/` 下的专属上下文（`AGENTS.md`、`CHECKLIST.md`、`SKILLS.md`、`PROMPT.md`）。

Agent 启动时，`.claude/hooks/on-session-start.sh` 会自动解析 `{process_slug}/workflow-stage.yaml`、加载当前阶段上下文、读取 handoff 文档并注入推荐技能，无需手动先读 README 再读 CLAUDE.md。

---

## 工作流概览

### 完整团队链路

```
访谈录音 → 转写摘要 → 需求澄清 → 产品设计 → Pencil 原型 → TDD 研发计划 → OpenSpec 提案 → GitHub Issues → 代码实现 → PR 合并 → Obsidian 知识库
```

### 轻量个人链路（vibe-coding）

```
想法/本地代码 → 需求澄清 → 设计评审 → TDD 计划 → 代码实现 → 本地验证 → 知识库同步
```

个人路径可以跳过访谈录音、OpenSpec 提案和 GitHub Issues 拆分，直接在手边项目上与 Agent 迭代；当需要升级成团队协作时，再补齐中间阶段。

详细模板选择见 [`.claude/workflows/README.md`](.claude/workflows/README.md)。

---

## 工具

Lincoln 提供两个配套工具：

- `tools/lincoln/` — 基于 Ink/React 的 TUI 录音前端（`lincoln` CLI）。
- `tools/record-interview/` — Python 录音后端，被 TUI 调用，也可独立使用。

安装与使用说明见各自目录下的 README。

---

## 目录结构

```
.
├── issue-<number>/                     # issue 工作包（团队/协作场景；个人 vibe-coding 可先使用由模板自动选择的工作包目录，后续再迁移）
│   ├── workflow-stage.yaml             # issue 运行时状态与 handoff 协议
│   ├── recordings/                     # 原始音频（gitignored）
│   ├── interviews/<session-id>/        # 转写与摘要
│   ├── requirements/<session-id>/      # 需求文档
│   ├── designs/<design-id>/            # 设计文档、Pencil 原型、TDD 计划
│   ├── openspec/changes/               # OpenSpec 变更提案
│   ├── docs/research/                  # 调研与决策记录
│   └── handoffs/                       # 阶段交接文档
├── knowledge/                          # 项目级 Obsidian vault（合并到 main）
├── products/                           # 产品代码占位
├── oss/                                # 开源候选跟踪
├── .claude/                            # Claude Code 系统提示层（自动加载）
│   ├── agents/                         # Agent 角色模板
│   ├── hooks/                          # 生命周期 hooks（settings.json 自动挂接）
│   ├── schemas/                        # JSON Schema 校验
│   ├── skills/                         # 原生 skills（含 routing.yaml、dependencies.yaml）
│   ├── stages/                         # 阶段上下文
│   ├── templates/issue-package/        # issue 工作包模板
│   ├── workflows/                      # SOP 工作流模板
│   │   └── README.md（工作流索引）       # ← 路由到这里看所有模板
│   ├── settings.json                   # Claude Code 项目设置
├── .context/                           # 交接文档（gitignored）
├── .github/                            # issue 模板、Actions、OpenSpec 配置
├── scripts/                            # 初始化、状态、审计工具
├── tests/                              # pytest 测试套件
└── tools/                              # lincoln TUI + record-interview CLI
```

---

## 依赖

- `python3`（≥3.10 推荐）
- `node` ≥ 20（用于 `tools/lincoln/`）
- `gh` CLI（已登录）
- `openspec` CLI：`npm install -g @fission-ai/openspec`
- `ffmpeg`（可选，仅录音转写需要）
- `faster-whisper` 或 OpenAI Whisper API key（可选，仅录音转写需要）
- Pencil 应用或 Pencil MCP（用于 `.pen` 原型）
- `ecc` CLI（来自 everything-claude-code）
- Obsidian（可选，用于可视化浏览 vault）

Benchmark（可选）：`scripts/lincoln_benchmark.py` 提供 Lincoln 工作流的基准评测入口，需要时运行 `python3 scripts/lincoln_benchmark.py --help` 查看用法。

此外，Lincoln 依赖若干外部 skill/CLI，清单见 `.claude/skills/dependencies.yaml`。初始化或升级后请让 Claude 运行：

```bash
python scripts/lincoln-setup.py check
```

---

## 作为 Claude Code 插件安装

Lincoln 支持以 Claude Code 插件形式安装。清单文件位于 `.claude-plugin/`：

- `.claude-plugin/plugin.json` — 插件元数据与技能入口。
- `.claude-plugin/marketplace.json` — Marketplace 注册信息。

安装方式取决于你使用的 Claude Code 插件管理器（例如 oh-my-claudecode）。通常将本仓库作为插件源引用即可。

---

## 规范约束

- Agent 启动时会由 `.claude/hooks/on-session-start.sh` 自动加载当前阶段上下文，无需手动遍历所有文件。
- 具体行为契约见 [`CLAUDE.md`](CLAUDE.md)；阶段级上下文见 `.claude/stages/<stage-id>/`。
- `human_gate: true` 阶段必须获得人类最终确认后才能继续。
- 阶段准出校验通过 `scripts/validate_stage.py` 运行。

---

## 扩展与贡献 Lincoln

Lincoln 的 `.claude/` 是开放的系统提示层，欢迎基于同一套元模型贡献新的扩展：

- **Agent 角色模板**（`.claude/agents/`）：为特定场景定义新的角色行为与上下文。
- **Skills 子技能**（`.claude/skills/`）：封装方法论子技能或 Lincoln 原生技能。
- **Hooks 生命周期扩展**（`.claude/hooks/`）：在会话启动、工具调用前后等时机注入自定义逻辑。
- **Workflow 工作流模板**（`.claude/workflows/`）：为不同场景定义从需求输入到知识沉淀的完整阶段序列。

提交 PR 前请参考：

- [`CLAUDE.md`](CLAUDE.md) — Agent 契约、人类门控规则与产物规范。
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 新增工作流模板的步骤。
- [`.claude/stages/stage-manifest.yaml`](.claude/stages/stage-manifest.yaml) — 阶段、门控、产物与角色的注册表。
- [`.claude/skills/routing.yaml`](.claude/skills/routing.yaml) — 阶段到技能的映射关系。
- [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml) — 外部 skill 与 CLI 依赖清单。

> 提示：新增 workflow 模板时，请同步更新 `.claude/workflows/README.md` 的快速路由表与模板详解；新增 skills 或 hooks 时，请确保与 `.claude/settings.json` 和 `dependencies.yaml` 兼容，并补充必要的验证与测试。

---

## License 与第三方致谢

Lincoln 本体以 [MIT License](LICENSE) 发布,Copyright (c) 2026 苏尚lewis (sushanglewis)。

Lincoln 引用以下开源项目作为外部 skills、插件与 CLI 依赖(声明见 [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml),均按其各自许可证使用):

| 项目 | 来源 | 用途 | 许可证 |
|---|---|---|---|
| superpowers | [obra/superpowers](https://github.com/obra/superpowers) | 通用技能(brainstorming、TDD 等) | MIT |
| gsd | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | 流程技能(import、docs-update 等) | MIT |
| oh-my-claudecode | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 可选多智能体编排插件 | MIT |
| openspec | [Fission-AI/openspec](https://github.com/Fission-AI/openspec) | 变更提案 CLI | MIT |
| gh | [cli/cli](https://github.com/cli/cli) | GitHub CLI | MIT |
| ffmpeg | [FFmpeg](https://ffmpeg.org/) | 可选,录音转写 | LGPL/GPL(见官网) |
| faster-whisper | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 可选,本地语音转写 | MIT |

外部 agent 定义由 `scripts/sync-external-agents.sh` 按 manifest 同步,来源与许可证见 [`.claude/agents/external/NOTICES.md`](.claude/agents/external/NOTICES.md)(everything-claude-code、oh-my-claudecode、wshobson/agents,均为 MIT)。

---

## 了解更多

- [OpenSpec 文档](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — Lincoln 工作流模板总览
