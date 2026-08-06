# Lincoln 用户手册

本文档面向 Lincoln 的**最终用户**：独立开发者、vibe-coding maker，以及产品、设计、研发、QA 团队成员。如果你希望为 Lincoln 框架本身贡献代码或扩展，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 目录

- [安装 Lincoln](#安装-lincoln)
- [第一次打开](#第一次打开)
- [路径 A：轻量个人路径](#路径-a轻量个人路径)
- [路径 B：团队 issue 路径](#路径-b团队-issue-路径)
- [常用自然语言指令](#常用自然语言指令)
- [阶段与门控](#阶段与门控)
- [工作状态与交接](#工作状态与交接)
- [工具](#工具)
- [多 harness 支持](#多-harness-支持)
- [目录结构](#目录结构)
- [依赖](#依赖)
- [故障排查](#故障排查)

## 安装 Lincoln

### 方式一：全局 npm 插件（推荐）

```bash
npm install -g @sushanglewis/lincoln
lincoln install
```

`lincoln install` 会把 Lincoln 运行时框架同步到 `~/.claude/`、`~/.codex/`、`~/.opencode/`。项目侧只需保留 `.lincoln.yaml` 标记即可激活；没有标记的项目中 Lincoln hooks 会静默退出，不会污染空目录。

常用命令：

- `lincoln install` — 首次全局安装
- `lincoln update` — 拉取最新版本并重新同步
- `lincoln use <version>` — 切换已安装的全局版本
- `lincoln doctor` — 诊断安装状态
- `lincoln init-project` — 在当前项目创建 `.lincoln.yaml`
- `lincoln migrate-project` — 从旧 vendored 框架模型迁移到全局插件模型
- `lincoln record` — 启动访谈录音 TUI

### 方式二：作为 Claude Code 插件安装

Lincoln 支持以 Claude Code 插件形式安装。清单文件位于 `.claude-plugin/`：

- `.claude-plugin/plugin.json` — 插件元数据与技能入口
- `.claude-plugin/marketplace.json` — Marketplace 注册信息

安装方式取决于你使用的 Claude Code 插件管理器。通常将本仓库作为插件源引用即可。

### 方式三：手动初始化

如果你希望完全手动控制安装过程，可以：

1. 确保已安装 `python3`（≥3.10 推荐）、`node`（≥20）、`gh`（已登录）、`openspec`
2. 安装外部 skills：`superpowers`、`gsd`，可选 `oh-my-claudecode`
3. 运行 `python3 scripts/init-project.sh`
4. 配置 `.github/openspec-config.yml`

第一次打开仓库时，Lincoln 的 hooks 通常会自动触发安装。如果 Claude 没有自动开始，请对 Agent 说：

> 请帮我完成 Lincoln 的初始化安装。

Agent 会按以下步骤执行：

1. 询问是否需要录音转写能力（需要时才安装 ffmpeg 并构建 `tools/lincoln-record/`）
2. 询问是否需要运行 benchmark
3. 检查当前仓库的 Lincoln 环境，列出所有缺失依赖
4. 安装外部 skills 到 `~/.claude/skills/`
5. 安装 CLI 工具：openspec、gh
6. 配置 `.github/openspec-config.yml`
7. 运行 `scripts/init-project.sh`
8. 完成后汇报状态

### 更新 Lincoln

当 Lincoln 发布新版本后，运行：

```bash
lincoln update
```

它会查询 npm registry 最新版本，全局安装后重新执行 `lincoln install --yes`。使用 `--check` 可只查看是否有更新，`--dry-run` 可预览变更。

### 从旧 vendored 模型迁移

如果你的项目已经内嵌了 `.claude/`、`scripts/` 等框架文件，先确保全局 CLI 已安装，然后运行：

```bash
lincoln migrate-project --dry-run
lincoln migrate-project --yes
```

`migrate-project` 会比较项目中的框架文件与全局 payload 的 sha256：未修改的文件会被删除，已修改或用户自定义的文件会被保留并列出，同时在项目根目录生成 `.lincoln.yaml`。`.context/`、`issue-*/`、`.github/openspec-config.yml` 等用户数据始终保留。

## 第一次打开

在 Conductor / Claude Code 中打开仓库后，如果 Lincoln 还没有可驱动的工作状态（新仓库，或工作包尚未启动），Agent 会自动进入开场引导：

1. **摸排**：Agent 对仓库做概览级侦察（顶层结构、README、知识索引、开放 issues），不读源码、不做深度扫描。
2. **判断**：Agent 给出对你处境的评估——角色、流程位置、最可能的问题与目标，并标注置信度。
3. **询问和确认**：Agent 按 Johari 认知象限设计确认动作，每轮最多 3 个问题。
4. **有策略的开展**：只有当每个目标都有明确的验收标准、执行路径也确定之后，Agent 才开始实际工作。

已有进行中的工作时不会打扰——Agent 会直接继续当前阶段。

## 路径 A：轻量个人路径

适合：个人项目、独立 maker、vibe-coding 开发者。

特点：无需先建 GitHub issue，直接在本地项目上与 Agent 结对迭代。

1. 在 Conductor 中打开项目仓库。
2. 对 Claude 说「检查一下 Lincoln 环境」——Agent 会运行环境检测并列出缺失依赖。
3. 根据你的场景选择模板：
   - **已有源码，想让 Agent 先读懂代码再迭代**：使用 `existing-project-iteration`
   - **只有想法，先做方案/原型探索**：使用 `design-spike`
   - **要做市场/竞品/用户/相关者研究或决策支持**：使用 `pm-research`
4. 对 Claude 说：
   - 如果你选择 `existing-project-iteration`：
     > 请使用 Lincoln 的 `existing-project-iteration` 模板，帮我理解当前代码库并规划下一个功能迭代。
   - 如果你选择 `design-spike`：
     
003e 请使用 Lincoln 的 `design-spike` 模板，帮我澄清这个想法并产出设计评审与原型。

5. 后续如果决定引入团队流程或需要 GitHub issue 跟踪，对 Agent 说「开始处理 issue <N>」——Agent 会新建 issue 工作包，你再把手头已确认的需求/设计产物交给它整理到新的 `issue-<number>/` 目录。

个人路径的产物默认落在由模板自动选择的工作包目录（如 workspace 名或仓库名）下，其中代码知识库产物写入 `knowledge/`，设计、需求、调研产物写入 `<process_slug>/pages/docs/` 下的 HTML 页面，原型产物写入 `<process_slug>/pages/prototype/`。

## 路径 B：团队 issue 路径

适合：产品、设计、研发、QA 团队，以 GitHub issue 为单元进行多角色协作。

### 初始化一个 issue 工作包

每个需求都对应一个 GitHub issue 和一个 Lincoln feature 分支。对 Agent 说「开始处理 issue <N>」，Agent 会基于 issue 编号创建分支，生成该 issue 专属的工作包目录。

你也可以提供更细的偏好，Agent 会翻译成对应的初始化参数：

- 访谈/需求会话 ID（格式 `YYYY-MM-DD-descriptive-name`，省略时默认生成）
- 设计主题 ID（kebab-case，省略时默认生成）
- 工作包目录名（默认 `issue-<number>`）
- 工作流模板（`.claude/workflows/` 下，默认 `interview-to-knowledge`）
- 初始化后是否推送分支到远程

执行后会在分支上生成：

```
issue-<N>/
├── index.html                   # 人读门户：聚合阶段状态、导航与产物
├── assets/                      # 门户共享样式与运行时
│   ├── style.css
│   ├── app.js
│   └── js/package-data.js       # 由 workflow-stage.yaml 生成的导航数据
├── workflow-stage.yaml          # issue 运行时状态与 handoff 协议
├── documents.yaml               # 文档索引：各阶段产物与 human 确认状态
├── recordings/                  # 原始录音（gitignored）
├── interviews/<session-id>/     # 转写、摘要、原始洞察
├── pages/docs/                  # 需求、PRD、设计、TDD 计划等 HTML 页面
├── pages/prototype/             # 可交互原型 HTML 页面
├── openspec/changes/            # OpenSpec 变更提案
└── handoffs/                    # 阶段交接文档
```

`issue-<N>/workflow-stage.yaml` 是人类、Agent 之间共享的阶段交接协议。`issue-<N>/index.html` 是人类查看工作包状态与文档的入口，每次状态保存时由 `lincoln_index.py` 自动刷新 `assets/js/package-data.js`，驱动左侧导航、iframe 画布与右侧信息面板。

### 跨成员、跨 Agent 协作

分支名必须严格使用 `issue-<number>` 约定。任何成员或 Agent 收到上游节点的 handoff 时，按分支名即可定位对应 issue 与工作包（`{process_slug}/workflow-stage.yaml`），从而保障从需求到最终验收，issue、branch、PR 端到端一一对应。

对 Agent 说「列出所有活跃的 Lincoln 分支」，即可查看所有 issue 分支的阶段状态与等待对象。

## 常用自然语言指令

Lincoln 是 AI-Native 工作流——**你不需要在终端输入任何命令**。直接用自然语言描述意图，Agent 会自动翻译成对应脚本并代为执行；也可以在 agent harness 中用 `/lc-*` 显式调用技能：

| 你说 | Agent 做 |
|------|----------|
| 开始处理 issue 55 | `/lc-wf-interview-to-knowledge`（或 `/lc-init-branch`）初始化分支与工作包 |
| 现在什么状态 | `/lc-status` 汇报当前阶段、等待对象与下一步 |
| 提交本阶段产物 | `/lc-stage` 记录产物并刷新 `documents.yaml` |
| 确认通过 | `/lc-stage` 在人类 PM 显式确认后标记当前 gate |
| 生成交接 | `/lc-handoff` 生成 handoff 文档 |
| 进入下一阶段 | Agent 校验 gate 后执行阶段推进 |
| 检查 Lincoln 环境 | `/lc-setup` 检测依赖并列出缺失项 |
| 列出所有活跃分支 | Agent 列出所有 issue 分支的阶段状态与等待对象 |
| 审计工作流健康度 | Agent 输出 PASS/WARN/FAIL 健康报告 |
| 运行 benchmark | `/lc-benchmark` 生成 Lincoln 会话基准评测报告 |
| 启动 PM 研究工作流 | `/lc-wf-pm-research` 进入市场/竞品/用户/相关者研究 |
| 调用研究员角色 | `/lc-agent-researcher` 输出 researcher 角色契约与上下文 |
| 查看某 skill 的完整提示 | `/lc-skill-lc-first-principles` 输出对应 SKILL.md + prompts |
| 执行一个场景 | `/lc-scenario-make-prd` 按场景组合角色与技能序列 |

`/lc-stage` 技能覆盖完整的阶段生命周期意图映射。底层脚本始终由 Agent 执行，用户无需关心。

## 阶段与门控

每个阶段都有：

- **入口校验**：当前阶段上下文、前置产物是否就绪
- **产物要求**：阶段必须生成的文件或文档
- **出口校验**：产物完整性、内容检查
- **门控（gate）**：自动校验 + 可选的 `human_gate: true` 人工确认

`human_gate: true` 的步骤不能跳过，必须获得人类 PM 的显式 `confirm` 或已审批标记。

阶段准出校验通过 `scripts/validate_stage.py` 运行。

## 工作状态与交接

### 查看当前分支状态

对 Agent 说「现在什么状态」，Agent 会汇报：当前阶段、等待对象、已加载上下文、推荐技能、产物状态、下一步动作。需要机器可读的结果时，可以要求 JSON 或 Markdown 格式。

### 生成交接文档

暂停或切换协作者时，对 Agent 说「生成交接」，会生成 `.context/lc-handoff-<stage>.md` 或 `{process_slug}/handoffs/` 文档，包含当前阶段、已确认产物、待解决问题、下一角色、推荐技能。

阶段通过人类确认后，对 Agent 说「确认通过」，Agent 会标记该阶段 gate 已审批通过。

### PM→UX 交接

在 `product-design-docs` 阶段结束时，PM Agent 会生成 `{process_slug}/handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md` 与 `{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml`：

- **master-handoff** 是人类可读的交接文档，汇总需求背景、设计决策、场景、功能目录、数据模型、流程与可行性结论。
- **pm-to-ux.handoff.yaml** 是机器可读的 agent-agent 契约，定义接收方（lc-designer / lc-frontend-engineer）应读取的上下文包顺序与校验项。

UX Agent 接手时应先读 `pm-to-ux.handoff.yaml`，再读 master-handoff，然后按 `context_pack` 顺序读取 Tier-2 设计文档。

### 查看所有进行中的 Lincoln 分支

对 Agent 说「列出所有活跃的 Lincoln 分支」；只看等待自己的分支时说「哪些分支在等我」。

### 审计工作流健康度

对 Agent 说「审计工作流健康度」，Agent 会输出 PASS/WARN/FAIL 报告，覆盖状态一致性、产物完整性、门控合规性、技能覆盖、异常检测。

## 工具

Lincoln 提供以下配套工具：

- `@sushanglewis/lincoln` — 全局 CLI（`lincoln install`、`lincoln update`、`lincoln use`、`lincoln doctor`、`lincoln init-project`、`lincoln migrate-project`、`lincoln record`）
- `tools/lincoln/` — 基于 Ink/React 的 TUI 录音前端（`lincoln-record` CLI）
- `tools/lincoln-record/` — Rust 本地录音转写 CLI（whisper-rs + Metal 加速、说话人分离），推荐用于访谈录音的本地转写
- `tools/lincoln-installer/` — 旧版终端 TUI 安装器与更新器（已弃用，保留向后兼容）

安装与使用说明见各自目录下的 README 或 `--help`。全局 CLI 可通过 `lincoln --help` 查看所有命令。

## 多 harness 支持

Lincoln 的端到端逻辑（角色契约、阶段工作流、`lc-*` 命令）可适配到 codex 与 opencode。`.claude/` 是唯一事实源，各 harness 产物由适配器按 `.claude/harnesses/<name>.yaml` manifest 派生，**不要手改生成产物**。

需要对 Agent 说「生成 codex 适配」或「生成 opencode 适配」（也可说「安装时同时生成两个 harness 适配」一步到位）。生成产物：

- codex: `AGENTS.md`、`~/.codex/prompts/lc-*.md` 以及 `.codex-plugin/plugin.json`
- opencode: `.opencode/agent/*.md` 与 `.opencode/command/lc-*.md`

生成产物不入 git（`.opencode/`、`.codex-plugin/`、`AGENTS.md` 已加入 `.gitignore`）。CI 会校验 manifest 可生成、本地产物未漂移。

### Codex hooks 缺省回退陷阱

Codex 在 `.codex-plugin/plugin.json` **省略** `hooks` 字段时，会回退到默认的 `hooks/hooks.json`。因此 Lincoln 派生的 codex 插件清单会**显式写入 `"hooks": {}`**；缺失字段或空数组 `[]` 都会触发回退路径。新增 harness 能力时，必须在 manifest 中显式声明，未配置的能力务必置空对象/空集合，而非省略字段。

## 目录结构

```
.
├── issue-<number>/                     # issue 工作包（团队/协作场景）
│   ├── workflow-stage.yaml             # issue 运行时状态与 handoff 协议
│   ├── documents.yaml                  # 文档索引（自动生成）
│   ├── recordings/                     # 原始音频（gitignored）
│   ├── interviews/<session-id>/        # 转写与摘要
│   ├── pages/docs/                     # HTML 说明文档
│   ├── pages/prototype/                # HTML 可交互原型
│   ├── openspec/changes/               # OpenSpec 变更提案
│   └── handoffs/                       # 阶段交接文档
├── knowledge/                          # 项目级 Obsidian vault（合并到 main）
├── products/                           # 产品代码占位
├── oss/                                # 开源候选跟踪
├── .claude/                            # Claude Code 系统提示层（自动加载）
│   ├── agents/                         # Agent 角色模板
│   ├── hooks/                          # 生命周期 hooks
│   ├── schemas/                        # JSON Schema 校验
│   ├── skills/                         # 原生 skills
│   ├── stages/                         # 阶段上下文
│   ├── templates/issue-package/        # issue 工作包模板
│   ├── workflows/                      # SOP 工作流模板
│   ├── settings.json                   # Claude Code 项目设置
├── .context/                           # session 级临时文件（gitignored）
├── .github/                            # issue 模板、Actions、OpenSpec 配置
├── scripts/                            # 初始化、状态、审计工具
├── tests/                              # pytest 测试套件
└── tools/                              # lincoln TUI + lincoln-record + installer
```

## 依赖

- `python3`（≥3.10 推荐）
- `node` ≥ 20（用于 `tools/lincoln/` 与全局 `@sushanglewis/lincoln` CLI）
- `gh` CLI（已登录）
- `openspec` CLI：`npm install -g @fission-ai/openspec`
- `ffmpeg`（可选，仅录音转写需要）
- Rust 工具链（`cargo`，可选，仅构建 `tools/lincoln-record/` 需要）
- Pencil 应用或 Pencil MCP（用于 `.pen` 原型）
- `ecc` CLI（来自 everything-claude-code）
- Obsidian（可选，用于可视化浏览 vault）

此外，Lincoln 依赖若干外部 skill/CLI，清单见 `.claude/skills/dependencies.yaml`。初始化或升级后请对 Agent 说「检查 Lincoln 环境」。外部 skills 已 pin 到已知良好的上游 ref——需要升级时对 Agent 说「升级 Lincoln 外部依赖」，Agent 会比对上游漂移、跑 benchmark 验证无回归后更新 pin。

## 故障排查

### Lincoln 没有自动初始化

对 Agent 说：

> 请帮我完成 Lincoln 的初始化安装。

Agent 会按步骤检测依赖、安装外部 skills、运行 `scripts/init-project.sh`。

### 缺少外部 skill

对 Agent 说：

> 检查 Lincoln 环境。

Agent 会列出缺失项并引导安装。

### 当前阶段推进不了

通常是因为某个 gate 未满足或 `human_gate: true` 未获得人类确认。对 Agent 说：

> 现在什么状态？

Agent 会汇报当前阶段、等待对象和下一步动作。

### issue 工作包文件被误加入 main

Lincoln 提供 `scripts/check-main-merge-hygiene.py` 作为 PR → main 的 CI 门禁，会将任何含 `workflow-stage.yaml` 的工作包目录下所有文件拒之门外。如果本地误操作，Agent 也可以帮你清理。

### 多 harness 产物未生成

对 Agent 说：

> 生成 codex 适配和 opencode 适配。

Agent 会调用 `scripts/lincoln-setup.py generate-harness --harness codex --harness opencode`。

### 更新后行为异常

运行：

```bash
python3 scripts/bump_version.py --check
python3 scripts/check-dependency-drift.py
```

确认 manifests lockstep 对齐且外部 skill pins 未漂移。
