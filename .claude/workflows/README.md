# Lincoln 工作流目录

本目录统一存放 Lincoln 预设的 SOP（标准操作流程）工作流。每个 `.yaml` 文件描述一个从需求输入到知识沉淀的完整阶段序列，Agent 可基于当前场景路由到对应工作流执行。

- 如果要**使用** Lincoln，请从根目录 [`README.md`](../../README.md) 开始。
- 如果要**新增**工作流，在本目录创建 `*.yaml` 文件，并更新本 README 的路由表、`.claude/harnesses/command-map.yaml` 的 `lc-wf-*` 登记。

## 执行模式（execution_mode）

每个工作流在 yaml 中声明 `execution_mode`，分为两类：

| 模式 | 含义 | 实例文件位置 |
|------|------|--------------|
| `solo` | 单人用户在自己 conductor session 内独立完成全部节点 | `.context/workflow/<name>.yaml`（session 级、gitignored，跟随 workspace/session 生命周期） |
| `team` | 多个人类用户负责不同节点，经 branch + issue-package 交接 | `{process_slug}/workflow-stage.yaml`（随 feature 分支共享） |

启动命令统一为 `lc-wf-*`（claude-code 经 `lc-wf` skill，codex/opencode 经生成的命令文件），底层为 `python3 "${CLAUDE_PLUGIN_ROOT:-${LINCOLN_HOME:-$HOME/.lincoln/current}}/scripts/lincoln_workflow.py`："

- `lc-wf-list` — 列出所有工作流及其执行模式。
- `lc-wf-<name>` — 启动对应工作流。solo 直接生成 session 实例；team 需 `--issue-number <N>`，转发 `scripts/init-lincoln-branch.sh` 创建分支与 issue 工作包。

## 快速路由

| 场景 | 推荐工作流 | 模式 | 文件 |
|------|------------|------|------|
| 有利益相关者访谈录音，需要提取需求并推进到研发 | `interview-to-knowledge` | team | [`interview-to-knowledge.yaml`](interview-to-knowledge.yaml) |
| 项目已有源码，但缺乏结构化功能知识库 | `existing-project-iteration` | solo | [`existing-project-iteration.yaml`](existing-project-iteration.yaml) |
| 已有明确 bug/issue，需要快速定位修复 | `bug-fix` | solo | [`bug-fix.yaml`](bug-fix.yaml) |
| 仅做方案预研，不进入研发实现 | `design-spike` | solo | [`design-spike.yaml`](design-spike.yaml) |
| 强依赖开源方案，需要先调研再设计 | `oss-first-design` | solo | [`oss-first-design.yaml`](oss-first-design.yaml) |
| 需要做竞品/市场/用户/相关者研究，辅助产品决策 | `pm-research` | solo | [`pm-research.yaml`](pm-research.yaml) |

## 工作流详解

### `interview-to-knowledge`（默认，team）

- **适用场景**：从访谈录音到 GitHub Issues 再到 Obsidian 知识库沉淀的完整链路，含跨成员的 implement/PR 节点。
- **阶段**：ingest → clarify → product-design-docs → product-prototype → tdd-development-plan → propose → split → implement → sync-knowledge

### `existing-project-iteration`（solo）

- **适用场景**：已有源码但知识库为空，先扫描代码生成 `knowledge/` 功能文档，再进入标准流程。
- **特点**：在 clarify 之前插入 `build-codebase-knowledge` 阶段。

### `bug-fix`（solo）

- **适用场景**：明确 bug/issue，轻量设计后快速进入修复。
- **特点**：跳过 `product-prototype`，`product-design-docs` 轻量化为设计评审文档，聚焦回归测试。

### `design-spike`（solo）

- **适用场景**：需求尚不明确，仅做方案预研或原型探索，不进入研发实现。
- **特点**：终止于 `product-prototype` 并直接同步到知识库。

### `oss-first-design`（solo）

- **适用场景**：设计方案强依赖开源项目或技术框架，需要先调研可选方案。
- **特点**：在 `clarify` 和 `product-design-docs` 之间插入 `explore-opensource` 阶段。

### `pm-research`（solo）

- **适用场景**：PM 需要体系化地完成竞品分析、市场研究、产品研究、用户/相关者研究、第一性原理探索，并输出可说服决策者的研究报告。
- **阶段**：workflow-router → lc-research-scope → lc-first-principles → lc-stakeholder-research → lc-market-research → lc-product-research → lc-competitive-analysis → lc-analyze-frameworks → lc-storytelling → lc-collect-intelligence → lc-research-report
- **特点**：全程 solo，研究范围与最终报告设有人类 gate；中间阶段以 artifact 完整性为准出门控。

## 工作流元模型

所有工作流共享同一套元模型：

- **Stage（阶段）**：工作流中的单一步骤，有明确的入口/出口校验和产物要求。定义见 `.claude/stages/<stage-id>.yaml`。
- **Gate（门控）**：阶段准出条件，包括自动校验（artifact 存在、内容检查）和人工确认（`human_gate: true`）。
- **Artifact（产物）**：阶段生成的文件，例如 `requirements.md`、`design-review.md`、`tdd-plan.md`、OpenSpec 提案等。
- **Skill（技能）**：阶段可调用的方法论子技能或 Lincoln 原生技能，由阶段 yaml 的 `skills` 字段声明。
- **Role（角色）**：阶段默认 Agent 角色（pm、designer、engineer、qa、researcher、knowledge-curator、release-coordinator）。

## 单一权威来源（SSOT）与产物路径一致性

Lincoln 有四层配置可能引用同一产物路径，修改时必须同步，否则 Agent 会拿到脱钩的指引：

| 事实 | 权威来源 | 副本（必须与权威一致） |
|---|---|---|
| 产物路径 / 必交性 | `.claude/stages/<stage>.yaml` 的 `artifacts` | workflow `.yaml` 的 `artifacts`/`optional_artifacts`、对应 skill 的 `SKILL.md` `outputs`、agent `.md` 的产物规范 |
| 阶段顺序 | workflow `.yaml` 的 `steps` | stage `.yaml` 的 `prerequisite_stage` / `next_stage` |
| 主执行 skill | workflow step 的 `action` | stage `.yaml` `skills.required` 首位、agent `.md` 可调用技能 |
| 外部 skill 依赖 | `.claude/skills/dependencies.yaml` | stage `.yaml` `skills.required/optional` 中的 namespaced skill |

仓库提供 `scripts/check-prompt-drift.py` 自动校验以上四层一致性。本地修改后、提交前必须运行：

```bash
./scripts/check-prompt-drift.py --strict --focus pm   # PM 三阶段必须绿
./scripts/check-prompt-drift.py --strict               # 全量校验（逐步推进）
```

PM 三阶段（`clarify` / `product-design-docs` / `product-prototype`）的 drift 为阻塞项，其余阶段可在严格模式外先报告后治理。

## 如何新增工作流

1. 在本目录创建 `<workflow-name>.yaml`，声明 `execution_mode: solo|team`。
2. 遵循 [`workflow-template.schema.json`](../schemas/workflow-template.schema.json) 的字段约定（`execution_mode` 为必填）。
3. 若工作流使用已有 stage，必须保持该 stage 的 `artifacts` 与 workflow step 的 `artifacts`/`optional_artifacts` 一致；新增 stage 时同步更新 `.claude/skills/dependencies.yaml` 中引用的 skill。
4. 运行 `./scripts/check-prompt-drift.py --strict --focus pm` 确认无漂移。
5. 运行 `python3 "${CLAUDE_PLUGIN_ROOT:-${LINCOLN_HOME:-$HOME/.lincoln/current}}/scripts/lincoln_command_map.py" --refresh` 自动在 `.claude/harnesses/command-map.yaml` 登记 `lc-wf-<name>` 等命令，并同步 `.claude-plugin/plugin.json`，然后运行 `python3 "${CLAUDE_PLUGIN_ROOT:-${LINCOLN_HOME:-$HOME/.lincoln/current}}/scripts/lincoln-setup.py" generate-harness --harness codex --harness opencode` 重新生成适配产物。
6. 在 `.claude/skills/lc-wf/SKILL.md` 的命令映射表中补充触发词。
7. 更新本 README 的**快速路由表**和**工作流详解**。

## 相关文件

- `.claude/stages/*.yaml` — 阶段定义与门控要求
- [`.claude/schemas/workflow-template.schema.json`](../schemas/workflow-template.schema.json) — 工作流模板 JSON Schema
- [`.claude/schemas/workflow-stage.schema.json`](../schemas/workflow-stage.schema.json) — 运行时状态实例 JSON Schema
- [`.claude/templates/solo-workflow-context.yaml`](../templates/solo-workflow-context.yaml) — solo 实例模板
- [`.claude/templates/issue-package/`](../templates/issue-package/) — team issue 工作包模板
- [`scripts/lincoln_workflow.py`](../../scripts/lincoln_workflow.py) — `lc-wf-*` 底层 CLI
- [`scripts/init-lincoln-branch.sh`](../../scripts/init-lincoln-branch.sh) — 创建 issue 工作包并初始化 `{process_slug}/workflow-stage.yaml`
- [`CLAUDE.md`](../../CLAUDE.md) — Agent 契约与自动上下文加载说明
