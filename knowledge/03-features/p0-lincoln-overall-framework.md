# P0 Lincoln 整体框架

## 元信息

- **来源访谈**: —
- **来源需求**: [[p0-lc-framework]]
- **GitHub Issue**: [#33](https://github.com/sushanglewis/Lincoln/issues/33)
- **实现 PR**: [#38](https://github.com/sushanglewis/Lincoln/pull/38)
- **状态**: 已合并
- **标签**: lincoln, framework, stage, workflow, agent-contract

---

## 业务知识

### 背景与问题

Lincoln 是一个面向 Conductor + Claude Code 的 AI-Native 产品 R&D 协作框架。在 v1.2.0 之前，阶段定义、技能路由、Agent 行为契约分散在多个文件和目录中，导致：

- 新增阶段或调整流程时需要在多处修改，容易遗漏。
- Agent 启动时无法一次性拿到当前阶段所需的全部上下文。
- 过程产物（访谈录音、设计稿、OpenSpec 变更）与框架代码混在同一仓库，污染 `main` 分支。
- 不同使用场景（开发 Lincoln 本身 / 以 Lincoln 为模板孵化新产品）缺少统一、清晰的路由框架。

### 用户需求

- 为 Conductor 中的 Claude Code 会话提供稳定的阶段路由框架。
- 每个阶段明确指定：负责 Agent、推荐技能、必须产出、人工门控状态。
- 过程产物保留在 feature branch，不进入 `main`。
- 框架不过度路由、不过分耦合、不一次性启动过多子代理。
- 优先利用 Claude Code 的 hooks 与 AI 能力完成检查，而非硬编码脚本。

### 验收标准

- [x] 阶段定义从文件夹结构收敛为单 YAML（`.claude/stages/<stage>.yaml`）。
- [x] 工作流模板使用统一 `workflow-stage.yaml` 驱动当前阶段与上下文注入。
- [x] 新增 `scripts/init-lincoln-branch.sh` 生成 issue 专属过程包。
- [x] `scripts/check-main-merge-hygiene.py` 阻止过程产物合入 `main`。
- [x] Agent 契约（`CLAUDE.md` / `.claude/agents/default.md`）简洁、抽象、可扩展。

### 价值

P0 框架为 Lincoln 后续所有功能迭代提供了统一骨架：新增阶段只需添加一个 YAML 和若干提示词文件；使用 Lincoln 作为模板的团队也能复用同一套路由与产物规范。

---

## 技术知识

### 实现概述

PR #38 将 Lincoln 从分散的 stage 文件夹重构为单 YAML stage 框架，并补充了 issue 驱动的工作包能力。

核心变更：

1. **Stage YAML 化**
   - 原 `.claude/stages/<stage>/` 下的元数据收敛到 `.claude/stages/<stage>.yaml`。
   - 每个 stage YAML 声明 `id`, `name`, `description`, `human_gate`, `agent`, `skills`, `artifacts`, `gates`。
   - 阶段专属提示词保留在 `.claude/stages/<stage>/{AGENTS,CHECKLIST,PROMPT,SKILLS}.md`。

2. **统一 workflow-stage.yaml**
   - `{process_slug}/workflow-stage.yaml` 记录当前阶段、运行状态、已产出产物。
   - `.claude/hooks/on-session-start.sh` 读取该文件并注入当前阶段上下文。

3. **技能与依赖声明**
   - `.claude/skills/routing.yaml` 按阶段映射所需技能。
   - `.claude/skills/dependencies.yaml` 声明外部 skill / CLI 依赖及安装方式。

4. **Issue 过程包**
   - `scripts/init-lincoln-branch.sh --issue-number <n>` 基于 `.claude/templates/issue-package/` 生成 `issue-<n>/`。
   - 过程包包含 `workflow-stage.yaml`、访谈/需求/设计/OpenSpec/交接目录模板。

5. **main-merge 卫生检查**
   - `scripts/check-main-merge-hygiene.py` 阻止 `recordings/`, `interviews/`, `designs/`, `requirements/` 等分支过程产物进入 `main`。

6. **可观测性**
   - `scripts/lincoln-status.py` 输出当前阶段、等待对象、推荐技能、产物状态。
   - `scripts/lincoln-audit.py` 审计状态一致性、产物完整性、门控合规性。

### 关键文件位置

| 文件 | 说明 |
|------|------|
| `.claude/stages/stage-manifest.yaml` | Stage 注册表与能力边界 |
| `.claude/stages/*.yaml` | 各阶段定义 |
| `.claude/stages/*/{AGENTS,CHECKLIST,PROMPT,SKILLS}.md` | 阶段专属提示词与检查清单 |
| `.claude/skills/routing.yaml` | 阶段到技能的映射 |
| `.claude/skills/dependencies.yaml` | 外部依赖声明 |
| `.claude/hooks/on-session-start.sh` | 会话启动时注入阶段上下文 |
| `scripts/init-lincoln-branch.sh` | 初始化 issue 过程包 |
| `scripts/stage_loader.py` | 阶段状态加载、handoff、校验、产物记录 |
| `scripts/lincoln-status.py` | 分支工作状态查询 |
| `scripts/lincoln-audit.py` | 工作流健康度审计 |
| `scripts/check-main-merge-hygiene.py` | main 合并卫生检查 |
| `.claude/templates/issue-package/` | issue 过程包模板 |

### 设计决策

- **单 YAML 优于文件夹元数据**：降低新增/修改阶段的认知负担，减少遗漏。
- **阶段提示词与阶段定义分离**：YAML 负责导航，Markdown 负责详细执行指令，避免 system prompt 过大。
- **过程产物不合并到 `main`**：保持 `main` 只保留 durable assets（框架、脚本、知识库）。
- **AI 优先检查**：门控与产物完整性优先由 Agent 读取并推理，脚本仅做结构性校验。

### 依赖

- `superpowers`（上游 obra/superpowers，main 分支；brainstorming 等通用技能）
- `gsd`（上游 gsd-build/get-shit-done，main 分支；import / discuss-phase 等流程技能）
- `openspec` v0.5.0（变更提案）
- `oh-my-claudecode`（可选，deep-interview）

---

## 相关链接

- [[p0-lc-framework]]
- [[stage-yaml-refactor]]
- [Issue #33](https://github.com/sushanglewis/Lincoln/issues/33)
- [PR #38](https://github.com/sushanglewis/Lincoln/pull/38)
