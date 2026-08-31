# OpenHands / TeamAI 可借鉴模式调研

<!-- status: approved -->

## 研究问题

Lincoln 作为 AI-Native 产品研协框架，需要识别并评估成熟开源 coding-agent 项目中可被借鉴到自身 stage / skill / hook / knowledge 体系的架构与工程模式。本次调研聚焦两个问题：

1. **OpenHands**（`All-Hands-AI/OpenHands` / `OpenHands/OpenHands`）与 **TeamAI**（`Tencent/teamai-cli`）分别提供了哪些可复用的机制？
2. 这些机制与 Lincoln 现有子系统的映射关系如何？哪些应优先采纳，哪些应暂缓或仅作参考？

## 候选方案对比表

评分维度与权重：

| 维度 | 权重 | 说明 |
|------|------|------|
| Business Fit | 30% | 与 Lincoln 产品研协场景的战略契合度 |
| Technical Fit | 25% | 与 Lincoln 现有架构（stage/skill/hook/knowledge）的匹配度 |
| Maintenance / Maturity | 20% | 社区规模、更新频率、长期维护可持续性 |
| Documentation | 15% | 官方文档完整度、架构说明清晰度 |
| Integration Cost | 10% | 引入 Lincoln 所需改造工作量 |

### 评分结果

| 候选方案 | Business Fit (30%) | Technical Fit (25%) | Maintenance (20%) | Docs (15%) | Integration (10%) | 加权总分 | 结论 |
|----------|--------------------|---------------------|-------------------|------------|-------------------|----------|------|
| **OpenHands** | 8 | 8 | 9 | 8 | 7 | **8.10** | 核心运行时模式参考 |
| **TeamAI** | 7 | 9 | 7 | 7 | 8 | **7.70** | 团队 harness / 知识分发参考 |
| 自研基线（现状 Lincoln） | 6 | 7 | 6 | 6 | 5 | **6.15** | 作为对照，不额外投入 |

> 计算方式：各维度得分 × 权重后求和。例如 OpenHands：8×0.30 + 8×0.25 + 9×0.20 + 8×0.15 + 7×0.10 = 2.40 + 2.00 + 1.80 + 1.20 + 0.70 = **8.10**。

## Top Candidate 详情

### OpenHands

- **仓库**：https://github.com/OpenHands/OpenHands
- **核心 SDK 仓库**：https://github.com/OpenHands/software-agent-sdk
- **License**：MIT
- **Stars**：~85,428（OpenHands/OpenHands，截至 2026-08-28）
- **最近推送**：2026-08-28
- **技术栈**：Python（SDK / Agent Server）+ TypeScript（Agent Canvas 前端）
- **定位**：自托管的 coding agent 控制中心，支持本地、Docker、远程/云端多种后端，可通过 Agent-Client Protocol（ACP）接入 Claude Code、Codex、Gemini 等第三方 agent。

**可借鉴的核心模式**：

1. **事件溯源状态（Event-Sourced State / EventLog）**
   - 所有交互以不可变事件追加到 `ConversationState` 的 `EventLog` 中。
   - 事件分类：LLM 可转换事件（`MessageEvent`、`ActionEvent`、`SystemPromptEvent`、`ObservationBaseEvent`）与内部事件（`ConversationStateUpdateEvent`、`CondensationRequest`、`Condensation`、`PauseEvent`）。
   - 持久化采用双路径：`base_state.json` 存元数据，每条事件存为独立 JSON 文件，支持增量持久化与确定性回放。
   - **Lincoln 映射**：`issue-70/workflow-stage.yaml` 的 `nodes[]` 已是追加式事件记录，可借鉴双路径持久化与事件分类思想，增强 `scripts/stage_loader.py` 的状态恢复能力。

2. **类型化 Action–Observation 循环**
   - LLM 输出 JSON tool call → 校验为 Pydantic `Action` → `ToolExecutor` 执行 → 返回 `Observation`。
   - MCP 工具通过 `MCPToolDefinition` / `MCPToolExecutor` 成为一等公民。
   - **Lincoln 映射**：Lincoln 的 skill 调用可类比为 Action；未来若引入 LLM 驱动的 stage 执行器，可采用 Closed Action Vocabulary 模型提升可控性。

3. **SecurityAnalyzer + ConfirmationPolicy**
   - `SecurityAnalyzer` 对 tool call 进行 low/medium/high/unknown 风险评级（内置 `LLMSecurityAnalyzer`）。
   - `ConfirmationPolicy`（如 `ConfirmRisky`）决定是否需要用户确认，默认 high 风险触发确认，agent 进入 `WAITING_FOR_CONFIRMATION` 状态。
   - 风险评估与执行强制分离，便于自定义实现。
   - **Lincoln 映射**：可在 `.claude/hooks/pre-tool-use.sh` 中集成风险扫描；高危工具（如 Bash 删除、git push）触发 human_gate 暂停，与 Lincoln 现有人工门控结合。

4. **Condenser（上下文压缩）**
   - 当历史事件过长时，Condenser 丢弃旧事件并以 `CondensationEvent` 摘要替代；默认 `LLMSummarizingCondenser` 可在不降低性能的情况下降低约 50% API 成本。
   - Condenser 本身无状态，摘要作为事件回写到 EventLog。
   - **Lincoln 映射**：长会话（如多轮 clarify 或 explore-opensource）可在 `scripts/stage_loader.py` 或 handoff 文档生成时引入摘要机制，避免上下文爆炸。

5. **Workspace Factory（本地/远程可移植）**
   - `Conversation` 作为工厂，根据 workspace 类型实例化 `LocalConversation` 或 `RemoteConversation`。
   - 支持 `LocalWorkspace`、`DockerWorkspace`、`RemoteWorkspace`。
   - **Lincoln 映射**：Lincoln 当前主要运行在本地 Claude Code；若未来需要远程 agent 服务器或多 harness 支持，可借鉴工厂模式封装 `scripts/lincoln_harness_adapter.py`。

6. **Skill / Plugin / Marketplace 分层**
   - `AgentContext(load_public_skills=True)` 从 `OpenHands/extensions` 拉取 skill。
   - Skill 为 Markdown 指南（`skills/<name>/SKILL.md`），Plugin 为带 hooks/scripts 的可执行包。
   - 支持 marketplace 注册与运行时加载。
   - **Lincoln 映射**：Lincoln 的 `.claude/skills/` 已是 Markdown 结构；可借鉴 marketplace 注册与 git 缓存更新机制，改进 `scripts/lincoln-setup.py` 的 skill 同步。

7. **Sub-Agent 委托作为工具**
   - Agent Server 支持多 agent 协作，复杂任务可委托给专用 agent（如代码审查 agent、测试 agent）。
   - **Lincoln 映射**：Lincoln 已有多 agent 模板（`.claude/agents/`），但协作主要通过 workflow 阶段串行；可借鉴“委托即工具”模式，在复杂 stage 中并行调用 reviewer/specialist agent。

### TeamAI

- **仓库**：https://github.com/Tencent/teamai-cli
- **License**：MIT（LICENSE 文件明确声明 MIT）
- **Stars**：~678（截至 2026-08-28）
- **最近推送**：2026-08-28
- **技术栈**：TypeScript / Node.js CLI
- **定位**：面向团队的 AI agent harness，通过共享 git 仓库统一管理 skills、rules、hooks、MCP、env、知识库，并分发到 Claude Code / Codex / Cursor / CodeBuddy / OpenCode 等多种 AI 工具。

**可借鉴的核心模式**：

1. **Harness / Tool 抽象层与 git-native 分发**
   - `teamai init` 将团队配置仓库关联到本地项目或用户目录；`teamai push` 开 MR，`teamai pull` 在 SessionStart 自动同步。
   - Skill 同步到 `~/.claude/skills/`、`~/.codex/skills/`、`~/.cursor/skills/` 等，实现一套配置跨工具分发。
   - **Lincoln 映射**：`scripts/lincoln_harness_adapter.py` 可借鉴其多 harness 同步逻辑；Lincoln 的 `.claude/` 层天然可被类似机制分发到 codex/opencode（已有 harnesses 目录）。

2. **Friction-Based Learning（摩擦驱动的经验捕获）**
   - Stop hook 根据“摩擦信号”打分：用户中断/纠正 AI、拒绝工具调用、AI 反复重试失败工具等。
   - 仅高摩擦会话触发 `/teamai-share-learnings` 提示，将经验总结为学习文档推送到团队仓库。
   - **Lincoln 映射**：可在 `.claude/hooks/on-stop.sh` 中集成 friction 评分，自动提示贡献者将踩坑经验写入 `knowledge/` 或 issue 工作包，降低知识流失。

3. **Recall Subagent + Precheck**
   - `teamai recall enable` 部署 `teamai-recall` subagent 到各 AI 工具的 `agents/` 目录。
   - 任务前 subagent 提取关键词、运行 `teamai recall --check` 相关性预检查，无关任务跳过检索，相关任务返回结构化团队知识摘要。
   - **Lincoln 映射**：Lincoln 的 `lc-build-codebase-knowledge` 或 `sync-to-knowledge` 可引入 recall precheck，避免每次会话都加载完整知识库。

4. **双轨代码图（AST + Heuristic）**
   - `teamai import` 解析仓库为 `teamwiki/` 图：组件、接口、配置、跨仓库 import 边。
   - AST track：WASM tree-sitter 解析 TypeScript/JavaScript/Python/Go 的 import/require/call site/implements，生成 `DEPENDS_ON` / `REFERENCES` / `IMPLEMENTS` 边（`code-ast`，带置信度）。
   - Heuristic track：正则提取，覆盖 AST track 不支持的语言（Java/Rust 等），失败时降级。
   - **Lincoln 映射**：可为 Lincoln 的 benchmark / codebase-knowledge 阶段引入类似双轨图，提升代码变更影响分析能力。

5. **Session Analytics 与 Digest**
   - `teamai session save` 记录脱敏会话摘要；`teamai digest` 生成团队周报（token 用量、对话量、干预率）。
   - `teamai dashboard` 提供实时会话状态、干预次数、token 用量。
   - **Lincoln 映射**：Lincoln 已有 `scripts/lincoln_benchmark*.py`，可扩展为持续的 session analytics，用于评估 agent 协作效率与人工门控频率。

6. **MR 知识挖掘（CI `extract-mr`）**
   - `teamai ci extract-mr --url <url>` 在 CI 中提取 MR 评论、变更说明，合并后写入知识库。
   - **Lincoln 映射**：Lincoln 的 `.github/workflows/knowledge-sync.yml` 可扩展为不仅读取 PR 描述，还解析 review 评论与变更内容，自动沉淀决策依据。

7. **Team Hooks 与 MCP 声明式配置**
   - `hooks/hooks.yaml` 声明 PreToolUse 等事件钩子，`teamai pull` 注入到各 AI 工具。
   - `mcp/mcp.yaml` 声明 MCP server，`teamai pull` 写入各工具原生配置。
   - **Lincoln 映射**：Lincoln 的 `.claude/hooks/` 与 `.claude/skills/dependencies.yaml` 已具备类似结构；可统一为跨 harness 的 hook/mcp 分发规范。

## 自研基线（Lincoln 现状）

Lincoln 当前已具备：

- **Stage 状态机**：`issue-70/workflow-stage.yaml` 记录追加式 `nodes[]`，`scripts/stage_loader.py` 负责校验与转段。
- **Skill 体系**：`.claude/skills/<skill>/SKILL.md` + prompts，与 TeamAI 的 Markdown skill 类似。
- **Hook 机制**：`.claude/hooks/on-session-start.sh`、`pre-tool-use.sh`、`post-tool-use.sh`、`on-stop.sh`。
- **Agent 模板**：`.claude/agents/*.md` 定义 pm/designer/engineer/qa/researcher 等角色。
- **知识库**：`knowledge/` 按业务/技术双轨组织，`knowledge-sync.yml` 在 PR 合并后触发同步。
- **多 harness 适配**：`scripts/lincoln_harness_adapter.py` 从 `.claude/` 派生 codex/opencode 配置。

**差距**：

- 缺乏事件溯源的完整状态模型（只有 stage 级别节点，没有 LLM 调用/工具调用级事件）。
- 缺乏自动化的风险分析与确认策略（依赖手工 human_gate）。
- 缺乏长上下文压缩机制。
- 缺乏 friction-based 知识捕获与 recall precheck。
- 缺乏代码图与 MR 知识挖掘。
- 缺乏系统化的 session analytics。

## 可借鉴模式与 Lincoln 映射

| 来源项目 | 模式 | Lincoln 映射文件/子系统 | 优先级 | 预估工作量 |
|----------|------|------------------------|--------|-----------|
| OpenHands | EventLog + 双路径持久化 | `scripts/stage_loader.py`、`issue-70/workflow-stage.yaml` 扩展 | P1 | 中 |
| OpenHands | 类型化 Action–Observation | `.claude/skills/*` 调用契约、`scripts/lincoln_harness_adapter.py` | P1 | 中 |
| OpenHands | SecurityAnalyzer + ConfirmationPolicy | `.claude/hooks/pre-tool-use.sh`、stage YAML `human_gate` | P0 | 低-中 |
| OpenHands | Condenser | `scripts/stage_loader.py` handoff/摘要、`issue-70/handoffs/` | P1 | 中 |
| OpenHands | Workspace Factory | `scripts/lincoln_harness_adapter.py`、新增 `openhands/` 后端 | P2 | 高 |
| OpenHands | Skill/Plugin Marketplace | `.claude/skills/*`、`scripts/lincoln-setup.py`、`.claude/workflows/README.md` | P1 | 中 |
| OpenHands | Sub-Agent 委托 | `.claude/agents/*`、`scripts/stage_loader.py` 并行 stage | P1 | 中 |
| TeamAI | git-native harness 分发 | `scripts/lincoln_harness_adapter.py`、`.claude/harnesses/*` | P0 | 低-中 |
| TeamAI | Friction-Based Learning | `.claude/hooks/on-stop.sh`、`knowledge/` 写入 | P1 | 中 |
| TeamAI | Recall Subagent + Precheck | `scripts/lincoln_benchmark_metrics.py`、knowledge recall | P1 | 中 |
| TeamAI | 双轨代码图 | `scripts/lc-benchmark-cli.py`、新增 `scripts/codebase_graph.py` | P2 | 高 |
| TeamAI | Session Analytics / Digest | `scripts/lincoln_benchmark*.py`、`.github/workflows/` | P2 | 中-高 |
| TeamAI | MR 知识挖掘 | `.github/workflows/knowledge-sync.yml` | P1 | 低-中 |
| TeamAI | Team Hooks / MCP 声明式配置 | `.claude/hooks/*`、`.claude/skills/dependencies.yaml` | P0 | 低 |

## 推荐结论（已根据 PM 约束调整）

- **P0（立即评估/原型）**：
  1. **SecurityAnalyzer + ConfirmationPolicy**：在 `.claude/hooks/pre-tool-use.sh` 中增加风险扫描。允许 `git push`、外部 API 调用；**文件删除必须触发 human_gate**。与 Lincoln 现有人工门控无缝结合，不自研执行器。
  2. **TeamAI 式 harness 分发**：完善 `scripts/lincoln_harness_adapter.py`，使 `.claude/` 层的 skills/rules/hooks/MCP 能可靠同步到 **Claude Code / Codex / OpenCode** 三种 harness。
  3. **TeamAI 式 Team Hooks / MCP 声明式配置**：统一 `.claude/hooks/` 与 `.claude/skills/dependencies.yaml` 的跨 harness 分发规范，保持 Lincoln 做轻做薄。

- **P1（下一阶段纳入 roadmap）**：
  1. **Friction-Based Learning + Recall Precheck**：在 `on-stop.sh` 中集成 friction scoring，高摩擦会话自动提示贡献者写入 `knowledge/`；知识库召回前做相关性预检查，避免全量加载。
  2. **EventLog + Condenser**：扩展 `workflow-stage.yaml` 的事件模型与持久化，支持长会话摘要；不替代底层 harness 执行器，仅增强 Lincoln 自身状态可追溯性。
  3. **Skill Marketplace + git 缓存**：改进 `scripts/lincoln-setup.py` 的 skill 同步与版本锁定。
  4. **Sub-Agent 委托**：在复杂 stage（如 design-review、security-review）中并行调用 specialist agent，复用 Claude Code / Codex / OpenCode 的 agent 机制。
  5. **MR 知识挖掘**：扩展 `.github/workflows/knowledge-sync.yml` 解析 review 评论与代码变更。

- **P2（长期参考，保持轻量）**：
  1. **跨仓库代码图**：Lincoln 不自建重型图引擎，仅在相关 stage/docs 声明依赖外部工具（如 tree-sitter、lsif、scip）；`scripts/lc-benchmark-cli.py` 负责调用与消费图输出，不维护解析实现。
  2. **Workspace Factory**：若未来需要远程 harness 支持；当前 Lincoln 作为本地 harness 插件，暂不投入。
  3. **Session Analytics Dashboard**：若需要量化 agent 协作效率；可在现有 `scripts/lincoln_benchmark*.py` 基础上轻量扩展。

## 关键待澄清问题（PM 已回复）

1. **Lincoln 是否计划引入 LLM 驱动的自主 stage 执行器？**
   - **PM 决策**：Lincoln 定位为 Claude Code、Codex、OpenCode 的 harness 插件，**不自研执行器**。
   - **影响**：OpenHands 的 Action–Observation 循环仅作参考，不直接移植；重点借鉴其风险分析、事件模型、上下文压缩与 skill 组织方式。

2. **是否需要支持除 Claude Code 之外的 agent harness？**
   - **PM 决策**：需要支持 **Claude Code、Codex、OpenCode** 三种 harness。
   - **影响**：TeamAI 的 git-native harness 抽象层与 `scripts/lincoln_harness_adapter.py` 的优先级提升；只需覆盖这三种目标，不必兼容 Cursor/CodeBuddy 等。

3. **是否允许 agent 执行高危操作？**
   - **PM 决策**：允许 `git push`、外部 API 调用；**文件删除必须人工确认**。
   - **影响**：`SecurityAnalyzer + ConfirmationPolicy` 仍列为 P0，但策略可收窄为“删除类操作强制 human_gate”，`git push` 与 API 调用可放行或仅记录日志。

4. **是否希望将知识捕获从“手动写文档”升级为“摩擦驱动自动提示”？**
   - **PM 决策**：同意采用摩擦驱动自动提示。
   - **作用说明**：不再依赖贡献者主动写文档，而是在检测到高摩擦信号（用户打断/纠正 AI、拒绝工具调用、AI 反复重试失败、人工覆盖决策等）时，由 `on-stop.sh` 自动提示贡献者沉淀经验。好处是：
     - 降低文档化负担，只在“真踩坑”时触发；
     - 捕获的是真实痛点，而非假想场景；
     - 经验直接关联到触发它的上下文，未来 agent 或 recall subagent 可复用；
     - 与 Lincoln 的 `knowledge/` 双轨知识库天然衔接。
   - **影响**：`on-stop.sh` 需接入 friction scoring，并新增 `lc-share-learnings` 提示模板。

5. **是否需要跨仓库代码图来支持影响分析？**
   - **PM 决策**：需要，但 Lincoln 自身要做轻做薄，**仅在 stage 或说明性约束中声明依赖外部项目/工具**。
   - **影响**：不内嵌重型代码图实现，优先复用现有工具（如 tree-sitter、lsif、scip）或外部服务；Lincoln 只负责在相关 stage/docs 中声明依赖、格式与使用约束。

## 参考链接

- OpenHands 主仓库：https://github.com/OpenHands/OpenHands
- OpenHands Software Agent SDK：https://github.com/OpenHands/software-agent-sdk
- OpenHands 文档（Architecture Overview）：https://docs.openhands.dev/sdk/arch/overview
- OpenHands 论文（arXiv:2511.03690）：https://arxiv.org/abs/2511.03690
- TeamAI 仓库：https://github.com/Tencent/teamai-cli
- TeamAI 使用指南：https://github.com/Tencent/teamai-cli/blob/main/docs/usage-guide.md
- TeamAI 中文 README：https://github.com/Tencent/teamai-cli/blob/main/README.zh-CN.md
- Lincoln `oss-first-design` 工作流：`.claude/workflows/oss-first-design.yaml`
- Lincoln `explore-opensource` skill：`.claude/skills/lc-explore-opensource/prompts/explore-opensource.md`

---
*PM 确认时请添加 `<!-- status: approved -->`。*
