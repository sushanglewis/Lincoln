# Lincoln 工作流模板目录

本目录存放 Lincoln 预设的 SOP（标准操作流程）工作流模板。每个 `.yaml` 文件描述一个从需求输入到知识沉淀的完整阶段序列，Agent 可基于当前场景路由到对应模板执行。

- 如果要**使用** Lincoln，请从根目录 [`README.md`](../README.md) 开始。
- 如果要**新增**工作流，在本目录创建 `*.yaml` 文件，并更新本 README 的路由表和模板列表。

## 快速路由

| 场景 | 推荐模板 | 文件 |
|------|----------|------|
| 有利益相关者访谈录音，需要提取需求并推进到研发 | `interview-to-knowledge` | [`interview-to-knowledge.yaml`](interview-to-knowledge.yaml) |
| 项目已有源码，但缺乏结构化功能知识库 | `existing-project-iteration` | [`templates/existing-project-iteration.yaml`](templates/existing-project-iteration.yaml) |
| 已有明确 bug/issue，需要快速定位修复 | `bug-fix` | [`templates/bug-fix.yaml`](templates/bug-fix.yaml) |
| 仅做方案预研，不进入研发实现 | `design-spike` | [`templates/design-spike.yaml`](templates/design-spike.yaml) |
| 强依赖开源方案，需要先调研再设计 | `oss-first-design` | [`templates/oss-first-design.yaml`](templates/oss-first-design.yaml) |

## 模板详解

### `interview-to-knowledge`（默认）

- **适用场景**：从访谈录音到 GitHub Issues 再到 Obsidian 知识库沉淀的完整链路。
- **阶段**：ingest → clarify → product-design-docs → product-prototype → tdd-development-plan → propose → split → implement → sync-knowledge
- **文件**：[`interview-to-knowledge.yaml`](interview-to-knowledge.yaml)

### `existing-project-iteration`

- **适用场景**：已有源码但知识库为空，先扫描代码生成 `knowledge/` 功能文档，再进入标准流程。
- **特点**：在 clarify 之前插入 `build-codebase-knowledge` 阶段。
- **文件**：[`templates/existing-project-iteration.yaml`](templates/existing-project-iteration.yaml)

### `bug-fix`

- **适用场景**：明确 bug/issue，轻量设计后快速进入修复。
- **特点**：跳过 `product-prototype`，`product-design-docs` 轻量化为设计评审文档，聚焦回归测试。
- **文件**：[`templates/bug-fix.yaml`](templates/bug-fix.yaml)

### `design-spike`

- **适用场景**：需求尚不明确，仅做方案预研或原型探索，不进入研发实现。
- **特点**：终止于 `product-prototype` 并直接同步到知识库。
- **文件**：[`templates/design-spike.yaml`](templates/design-spike.yaml)

### `oss-first-design`

- **适用场景**：设计方案强依赖开源项目或技术框架，需要先调研可选方案。
- **特点**：在 `clarify` 和 `product-design-docs` 之间插入 `explore-opensource` 阶段。
- **文件**：[`templates/oss-first-design.yaml`](templates/oss-first-design.yaml)

## 工作流元模型

所有模板共享同一套元模型：

- **Stage（阶段）**：工作流中的单一步骤，有明确的入口/出口校验和产物要求。定义见 [`.claude/stages/stage-manifest.yaml`](../stages/stage-manifest.yaml)。
- **Gate（门控）**：阶段准出条件，包括自动校验（artifact 存在、内容检查）和人工确认（`human_gate: true`）。
- **Artifact（产物）**：阶段生成的文件，例如 `requirements.md`、`design-review.md`、`tdd-plan.md`、OpenSpec 提案等。
- **Skill（技能）**：阶段可调用的方法论子技能或 Lincoln 原生技能。路由表见 [`.claude/skills/routing.yaml`](../skills/routing.yaml)。
- **Role（角色）**：阶段默认 Agent 角色（pm、designer、engineer、qa、researcher、knowledge-curator、release-coordinator）。

## 如何新增工作流

1. 在本目录（或 `templates/` 子目录）创建 `<workflow-name>.yaml`。
2. 遵循 [`workflow-template.schema.json`](../schemas/workflow-template.schema.json) 的字段约定。
3. 更新本 README 的**快速路由表**和**模板详解**。
4. 如需在 `lc-workflow-router` 中暴露该模板，同步更新 `.claude/skills/lc-workflow-router/` 中的路由逻辑。

## 相关文件

- [`.claude/stages/stage-manifest.yaml`](../stages/stage-manifest.yaml) — 阶段注册表与门控要求
- [`.claude/skills/routing.yaml`](../skills/routing.yaml) — 阶段到技能的映射
- [`.claude/schemas/workflow-template.schema.json`](../schemas/workflow-template.schema.json) — 工作流模板 JSON Schema
- [`CLAUDE.md`](../../CLAUDE.md) — Agent 契约与自动上下文加载说明
- [`scripts/init-lincoln-branch.sh`](../../scripts/init-lincoln-branch.sh) — 创建 issue 工作包并初始化 `{process_slug}/workflow-stage.yaml`
