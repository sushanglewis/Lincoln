# P0 Lincoln 框架需求

## 元信息

- **来源访谈**: —
- **GitHub Issue**: [#33](https://github.com/sushanglewis/Lincoln/issues/33)
- **实现 PR**: [#38](https://github.com/sushanglewis/Lincoln/pull/38)
- **对应功能**: [[p0-lc-overall-framework]]
- **状态**: 已确认 / 已实现

---

## 需求背景

Lincoln 需要在 Conductor + Claude Code 环境中为产品经理、设计师、研发工程师和 Agent 提供一套可复用的协作流程。P0 阶段聚焦框架本身：统一路由、清晰阶段、受控产物、简洁契约。

## 用户与场景

1. **开发 Lincoln 本身**
   - 在 Lincoln 仓库下基于 GitHub issue 创建 workspace。
   - Agent 读取 issue 与 Lincoln 框架资源，按阶段交付产物。
   - 人类验收后提 PR，仅合并 durable assets 到 `main`。

2. **以 Lincoln 为模板孵化新产品**
   - Use template 创建新仓库，在 Conductor 中创建项目。
   - Agent 将开源代码同步到 `oss/`，将现有代码同步到 `products/`。
   - 复用 Lincoln 阶段框架推进需求澄清、设计、实现、知识沉淀。

## 功能需求

### FR1: 统一阶段框架

每个阶段必须声明：
- 阶段 ID 与名称
- 负责 Agent 与评审 Agent
- 所需技能（required / optional）
- 必须产出的 artifacts
- 入口 / 出口检查
- 是否设有人工门控

### FR2: 单 YAML 阶段定义

阶段元数据从文件夹结构迁移到 `.claude/stages/<stage>.yaml`，阶段专属提示词保留在同级子目录。

### FR3: 会话启动自动注入上下文

通过 `.claude/hooks/on-session-start.sh` 读取 `{process_slug}/workflow-stage.yaml`，自动加载当前阶段的 `AGENTS.md`、`CHECKLIST.md`、`PROMPT.md`、`SKILLS.md`。

### FR4: Issue 驱动的过程包

提供 `scripts/init-lincoln-branch.sh` 基于模板生成 `issue-<n>/` 过程包，包含：
- `workflow-stage.yaml`
- `interviews/`, `requirements/`, `designs/`, `openspec/`, `handoffs/` 目录与模板

### FR5: main 分支保护

过程产物不得合入 `main`。`scripts/check-main-merge-hygiene.py` 在 PR 阶段拦截分支级产物。

### FR6: 可观测性

提供 `lc-status` 查看当前阶段与等待对象，提供 `lc-audit` 审计工作流健康度。

## 非功能需求

- **简洁性**: `default.md` 等 system prompt 必须抽象简洁，避免过度膨胀。
- **稳定性**: 面向不同用户、阶段、开发阶段，路由框架保持稳定。
- **不过度路由**: 能一次获取必要信息时，不拆分为多次 loop。
- **低耦合**: 阶段、技能、Agent 之间通过声明式 YAML 解耦。
- **子代理节制**: 不一次启动超过 5 个子代理，优先线性执行以提升缓存命中率。
- **AI 优先检查**: 门控与产物检查优先使用 Agent 推理，脚本仅做结构校验。

## 验收标准

- [x] `.claude/stages/` 下所有阶段均为单 YAML 定义。
- [x] `.claude/skills/routing.yaml` 覆盖所有 interview-to-knowledge 阶段。
- [x] `scripts/init-lincoln-branch.sh` 可生成完整 issue 过程包。
- [x] `check-main-merge-hygiene.py` 正确拒绝过程产物进入 `main`。
- [x] `lc-status` 与 `lc-audit` 可运行并输出有效报告。
- [x] 所有 stage YAML 通过 schema 校验与单元测试。

## 相关链接

- [[p0-lc-overall-framework]]
- [Issue #33](https://github.com/sushanglewis/Lincoln/issues/33)
- [PR #38](https://github.com/sushanglewis/Lincoln/pull/38)
