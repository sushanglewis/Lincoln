# Lincoln — Agent Contract

本文件定义 Lincoln 仓库中 Claude Code Agent 的契约。它作为 Claude Code 项目级系统提示的一部分，由 `.claude/hooks/on-session-start.sh` 在会话启动时自动注入当前阶段上下文，Agent 不需要手动“先读 README 再读 CLAUDE.md”。

如果你是 Lincoln 模板的使用者，请从根目录 [`README.md`](README.md) 开始；如果你是框架开发者，才需要阅读本文件。

## `.claude/` 的定位

`.claude/` 是 Lincoln 在 Claude Code 机制下的**抽象系统提示层**，包含：

- `agents/` — Agent 角色模板（default、pm、designer、engineer、qa、researcher 等）。
- `skills/` — Lincoln 原生技能与外部技能路由（`routing.yaml`、`dependencies.yaml`）。
- `stages/` — 阶段上下文（`AGENTS.md`、`CHECKLIST.md`、`SKILLS.md`、`PROMPT.md`）。
- `workflows/` — SOP 工作流模板定义与索引 [`README.md`](.claude/workflows/README.md)。
- `templates/issue-package/` — issue 工作包模板（只读，用于初始化）。
- `schemas/` — JSON Schema 校验。
- `hooks/` — 生命周期 hooks，由 `.claude/settings.json` 自动挂接。

这些文件不描述某个具体 issue 的执行状态，而是提供**角色行为、阶段校验、技能路由、工作流模板**等抽象规则。具体 issue 的状态和产物保存在 `{process_slug}/workflow-stage.yaml` 及其同目录工作包中。

## Session Startup Protocol

每个 Agent 进入 Lincoln 会话时，Claude Code hooks 已经自动完成以下加载：

1. 依赖检测（`.claude/skills/dependencies.yaml`）。
2. 解析当前分支的 `{process_slug}/workflow-stage.yaml`。若不存在则回退到 legacy `.claude/workflow-state.yaml`。
3. 读取 `current_run.current_stage` 并加载 `.claude/stages/<current_stage>/` 下的 `AGENTS.md`、`CHECKLIST.md`、`SKILLS.md`、`PROMPT.md`。
4. 读取上一个 node 的 handoff 文档。
5. 输出 Lincoln 状态摘要。

Agent 启动后应：

1. 简要汇报当前阶段、已加载上下文、推荐技能、等待对象、下一步动作。
2. 运行 `python3 scripts/stage_loader.py --stage <current_stage> --action validate-entry` 进行准入校验。
3. 根据当前阶段和上下文继续工作。

如果 `.claude/workflow-stage.yaml` 存在但 `{process_slug}/workflow-stage.yaml` 不存在，说明需要迁移或初始化 issue 工作包；请提示人类运行：

```bash
scripts/init-lincoln-branch.sh --issue-number <number>
```

## 模板 vs 实例：状态文件

必须区分以下两个文件：

| 文件 | 性质 | 用途 |
|------|------|------|
| `.claude/templates/issue-package/workflow-stage.yaml` | **模板** | 只读。`init-lincoln-branch.sh` 复制它并填入 issue 专属信息。 |
| `{process_slug}/workflow-stage.yaml` | **实例** | issue 运行时的真实状态文件，人类-human、人类-Agent、Agent-Agent 之间共享的阶段交接协议。 |

Agent 只应读取和更新 **实例** `{process_slug}/workflow-stage.yaml`，不应直接修改模板。

## Issue 工作包

每个 issue 对应一个分支（如 `issue-21`）和一个工作包目录（默认 `{process_slug}=issue-21`）：

```
issue-21/
├── workflow-stage.yaml          # 阶段状态与 handoff 协议
├── recordings/                  # 原始录音（只读）
├── interviews/<session-id>/
├── requirements/<session-id>/
├── designs/<design-id>/
├── openspec/changes/
├── docs/research/
└── handoffs/
```

过程文档随 feature 分支传递，不合并到 `main`。Agent 在任何阶段产生的产物都应写入 `{process_slug}/` 下的对应目录，并可通过 `scripts/stage_loader.py --stage <stage> --action record-artifacts` 将产物路径持久化回 `{process_slug}/workflow-stage.yaml`。

## Human Gate Rules

- `human_gate: true` 的步骤不能跳过。
- 必须获得人类 PM 的显式 `confirm` 或已审批标记。
- 在 `human_gate: true` 阶段，Agent 必须直接向人类 PM 发送消息，不得用 `TaskCreate`/`TaskUpdate` 暂存或拆分“发消息”动作。
- 在 human_gate 阶段，子技能仅用于探索或结构化，不得替代人类确认。

## Handoff Protocol

暂停或切换窗口时：

```bash
python3 scripts/stage_loader.py --stage <current_stage> --action handoff-report
```

更新 `.context/lincoln-handoff-<stage>.md` 或 `{process_slug}/handoffs/` 文档。人类 PM 确认后：

```bash
python3 scripts/stage_loader.py --stage <current_stage> --action approve-gate
```

标记该阶段 gate 审批通过。

## Observability Reporting

每个回复必须简要说明：

- 当前阶段
- 本次调用使用的技能
- 产物位置或修改的文件
- 校验状态（entry passed / exit pending / human gate waiting）

## Skill Invocation Rules

- 通过 `Skill` 工具调用技能，技能名来自 `.claude/skills/routing.yaml`。
- 不得用技能调用替代 `human_gate`。
- 实施类技能（如 `subagent-driven-development`、`executing-plans`）必须在 PM 明确批准后才能调用。
- `lincoln-workflow-router` 仅在 `{process_slug}/workflow-stage.yaml` 中 `current_run.workflow_template` 为空时触发。

## 核心原则

1. **工作流优先**：任何操作必须符合当前阶段及其校验规则。
2. **人类门控不可跳过**：`human_gate: true` 必须获得人类 PM 显式确认。
3. **产物可追溯**：每个需求、每个功能都必须能关联回原始访谈、OpenSpec 变更、GitHub Issue/PR。
4. **知识库双轨维护**：每个合并的 issue 必须同时沉淀业务知识和技术知识到 Obsidian vault。
5. **不修改原始录音**：`{process_slug}/recordings/` 中的文件只读。
6. **Pencil 原型受控处理**：`.pen` 文件只能通过 Pencil 应用或 Pencil 工具处理。
7. **只更新实例状态**：永远不要直接修改 `.claude/templates/issue-package/workflow-stage.yaml`。

## 沟通风格

- 使用中文与人类 PM 交流。
- 汇报进度时简洁，重点说明当前步骤、产物位置、下一步需要人类做什么。
- 不确定时暂停并提问，不猜测。

## 相关文件

- [`README.md`](README.md) — 用户快速开始指南。
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — 工作流模板索引。
- [`.claude/stages/stage-manifest.yaml`](.claude/stages/stage-manifest.yaml) — 阶段注册表。
- [`.claude/skills/routing.yaml`](.claude/skills/routing.yaml) — 技能路由。
- [`.claude/agents/default.md`](.claude/agents/default.md) — Agent 行为总则。
