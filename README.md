# Lincoln — AI-Native 产研协作体系

> **Lincoln 是什么？** Lincoln 是一个基于 **Conductor + Claude Code + OpenSpec + GitHub + Obsidian** 的 AI-Native 产研协作体系。它以 issue 为单元、以阶段为节奏、以门控为质量保障，将需求澄清、产品设计、原型、TDD 计划、OpenSpec 提案、GitHub Issues 拆分、研发实现和知识库沉淀串联成可重复的 SOP，让产品经理、设计师、工程师与 Agent 在各自擅长的环节高效协作。

> **使用者还是开发者？**
> - **使用者**（产品、设计、研发、QA）：直接跳到 [快速开始](#快速开始)。
> - **开发者**（工作流开发者、框架维护者）：阅读 [框架文档](#框架文档) 和 [`CLAUDE.md`](CLAUDE.md)。

## 快速开始

在 GitHub 上点击 **Use this template** 创建项目仓库，然后 clone 到本地 Conductor 工作区。

### 初始化一个 issue 工作包

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

### 场景 A：从访谈录音开始

```bash
# 1. 放入访谈录音
cp ~/Downloads/2026-07-08-stakeholder.m4a issue-21/recordings/

# 2. 启动 Lincoln，Claude Code 会根据当前 stage 自动路由
#    - 处理访谈录音
#    - 澄清需求
#    - 生成产品设计文档
#    - 生成产品原型
#    - 生成 TDD 研发计划
#    - 生成 OpenSpec 提案
#    - 拆分到 GitHub
#    - PR 合并后同步到知识库
```

### 场景 B：已有代码库但无知识库

运行 `lincoln-workflow-router`，选择 `existing-project-iteration` 模板。Agent 会先扫描代码库生成 `knowledge/` 功能文档，再进入 clarify 阶段。

### 场景 C：明确 bug/issue

选择 `bug-fix` 模板。clarify 阶段会自动注入调试相关技能，流程跳过原型、聚焦回归测试。

### 场景 D：方案预研或开源优先

- `design-spike`：终止于原型或 TDD 计划，直接沉淀知识。
- `oss-first-design`：clarify 后自动触发开源方案调研。

> 全部模板的详细说明见 [`.claude/workflows/README.md`](.claude/workflows/README.md)。

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

阶段通过人类 PM 确认后：

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
- PM 在本地推进阶段后，push feature 分支到远程；下游角色 checkout 同一分支继续。
- 每个阶段都有 `.claude/stages/<stage-id>/` 下的专属上下文（`AGENTS.md`、`CHECKLIST.md`、`SKILLS.md`、`PROMPT.md`）。

Agent 启动时，`.claude/hooks/on-session-start.sh` 会自动解析 `{process_slug}/workflow-stage.yaml`、加载当前阶段上下文、读取 handoff 文档并注入推荐技能，无需手动先读 README 再读 CLAUDE.md。

---

## 工作流概览

```
访谈录音 → 转写摘要 → 需求澄清 → 产品设计 → Pencil 原型 → TDD 研发计划 → OpenSpec 提案 → GitHub Issues → 代码实现 → PR 合并 → Obsidian 知识库
```

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
├── issue-<number>/                     # issue 工作包（feature branch 独有，不合并 main）
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
│   ├── settings.json                   # Claude Code 项目设置
│   └── README.md（工作流索引）           # ← 路由到这里看所有模板
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
- `ffmpeg`
- `faster-whisper` 或 OpenAI Whisper API key
- `gh` CLI（已登录）
- `openspec` CLI：`npm install -g @fission-ai/openspec`
- Pencil 应用或 Pencil MCP（用于 `.pen` 原型）
- `ecc` CLI（来自 everything-claude-code）
- Obsidian（可选，用于可视化浏览 vault）

此外，Lincoln 依赖若干外部 skill/CLI，清单见 `.claude/skills/dependencies.yaml`。初始化或升级后请运行：

```bash
scripts/check-skill-dependencies.sh
```

---

## 作为 Claude Code 插件安装

Lincoln 支持以 Claude Code 插件形式安装。清单文件位于 `.claude-plugin/`：

- `.claude-plugin/plugin.json` — 插件元数据与技能入口。
- `.claude-plugin/marketplace.json` — Marketplace 注册信息。

安装方式取决于你使用的 Claude Code 插件管理器（例如 oh-my-claudecode）。通常将本仓库作为插件源引用即可。

---

## 规范约束

Agent 必须遵守：
- [`.claude/agents/default.md`](.claude/agents/default.md) — Agent 行为总则
- [`CLAUDE.md`](CLAUDE.md) — Agent 启动自检与汇报契约
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 工作流模板索引
- [`.claude/stages/stage-manifest.yaml`](.claude/stages/stage-manifest.yaml) — 阶段注册表与门控要求
- `scripts/validate_stage.py` — 准入准出校验 runner

人类产品经理拥有以下节点的最终确认权：
- 需求澄清完成
- 产品设计文档确认
- Pencil 原型确认
- 研发实现完成

---

## 了解更多

- [OpenSpec 文档](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — Lincoln 工作流模板总览
