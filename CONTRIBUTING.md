# Contributing to Lincoln

欢迎基于 Lincoln 元模型的贡献。提交 PR 前请读完本文件——它同时约束人类与 Agent 贡献者。

## 核心 vs 领域包边界

Lincoln 的范围纪律（借鉴 superpowers 的核心零依赖原则）：

- **核心**：阶段/门控/路由器元模型 + 工作流引擎（`.claude/stages/`、`.claude/schemas/`、`scripts/`、hooks、多 harness 适配器）。
- **领域包**：垂直能力（interview-to-knowledge、oss-first-design、`tools/lincoln-record` 等）属于可选包，不进入核心判断标准——"这对完全不同项目的人有用吗？"答案为否，就不进核心。

新能力默认做成独立 skill/工作流模板，而不是修改核心元模型。

## 贡献者护栏（PR 硬性要求）

1. **PR 模板必填**：使用 `.github/pull_request_template.md`，逐项填写，不留空。
2. **先查重**：提交前搜索已有 issue/PR，确认不与进行中的工作重复（`gh pr list` / issue 搜索）。
3. **披露生成方式**：PR 描述中说明生成所用的模型、harness 与版本（如 `claude-fable-5 + Claude Code`）。
4. **一个 PR 只解决一个问题**：混合多个不相关改动的 PR 会被要求拆分。
5. **human_gate 不可跳过**：任何 PR 不得移除或绕过阶段门控与 human 确认环节。

## 测试分层约定

- `tests/`：**确定性、非 LLM** 的契约与单元测试，进 CI（`static-check.sh`），必须全绿。
- benchmark / eval（`scripts/lincoln_benchmark*.py`）：**LLM 行为评测**，慢且非确定，手动触发，不阻塞 CI。

## 修改 stage / skill / 角色契约时

这些文件是"塑造 agent 行为的代码"，按 eval 门禁规范修改：

1. 修改 `.claude/stages/*.yaml`、`.claude/skills/**`、`.claude/agents/**` 前后，跑一遍 benchmark，在 PR 描述中附前后对比（无回归）。
2. 升级外部 skills 的 pin（`dependencies.yaml`）时同样要求 benchmark 验证（见该文件头部注释的升级流程）。

## 发布前：每个 harness 的一句话验收测试

每次发布前，对每个已生成适配的 harness 各跑一遍：

| Harness | 一句话验收 |
|---------|-----------|
| Claude Code | 干净会话发"帮我开始一个新需求" → 必须触发开场引导 / `lc-workflow-router`，并停在 clarify human_gate 前 |
| codex | 干净会话发同一句话 → `AGENTS.md` 契约生效、`lc-*` prompts 可用，且没有任何 hooks 被自动激活 |
| opencode | 干净会话发同一句话 → `.opencode/` 契约生效、`lc-*` 命令可用，且没有多余能力被默认开启 |

任何一条不满足，不得发布。
