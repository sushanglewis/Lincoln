# Contributing to Lincoln

欢迎为 Lincoln 贡献代码、文档、测试、工作流模板、Agent 角色与 skills。本文件同时约束**人类贡献者**与**Agent 贡献者**，提交 PR 前请完整阅读。

## 目录

- [Lincoln 的范围](#lincoln-的范围)
- [核心 vs 领域包边界](#核心-vs-领域包边界)
- [贡献者护栏（PR 硬性要求）](#贡献者护栏pr-硬性要求)
- [如何提交 Issue](#如何提交-issue)
- [如何提交 PR](#如何提交-pr)
- [本地开发环境](#本地开发环境)
- [测试分层约定](#测试分层约定)
- [修改 stage / skill / agent 契约时](#修改-stage--skill--agent-契约时)
- [如何新增工作流模板](#如何新增工作流模板)
- [如何新增 Agent 角色](#如何新增-agent-角色)
- [如何新增 Skill](#如何新增-skill)
- [如何新增 Harness 适配](#如何新增-harness-适配)
- [发布前验收](#发布前验收)
- [获得帮助](#获得帮助)

## Lincoln 的范围

Lincoln 的目标是为 AI-Native 研发工作流提供一套**可复用、可扩展、可审计**的元模型与基础设施。我们借鉴 superpowers 的核心零依赖原则，对范围保持严格纪律。

## 核心 vs 领域包边界

- **核心**：阶段/门控/路由器元模型 + 工作流引擎 + harness 适配器
  - `.claude/stages/`
  - `.claude/schemas/`
  - `.claude/harnesses/`
  - `.claude/hooks/`
  - `.claude/settings.json`
  - `scripts/`（通用基础设施脚本）

- **领域包**：垂直能力，属于可选扩展，不进入核心判断标准
  - `interview-to-knowledge` 工作流
  - `oss-first-design` 工作流
  - `tools/lincoln-record/`
  - 特定行业的 agent 角色或 skills

判断标准：**"这对完全不同项目的人有用吗？"** 如果答案为否，就不进核心。

**默认规则**：新能力优先做成独立 skill 或工作流模板，而不是修改核心元模型。

## 贡献者护栏（PR 硬性要求）

1. **PR 模板必填**：使用 `.github/pull_request_template.md`，逐项填写，不留空。
2. **先查重**：提交前搜索已有 issue/PR，确认不与进行中的工作重复（`gh pr list` / issue 搜索）。
3. **披露生成方式**：PR 描述中说明生成所用的模型、harness 与版本（如 `claude-fable-5 + Claude Code`）。
4. **一个 PR 只解决一个问题**：混合多个不相关改动的 PR 会被要求拆分。
5. **human_gate 不可跳过**：任何 PR 不得移除或绕过阶段门控与 human 确认环节。
6. **不手改生成产物**：codex / opencode 适配产物由 `scripts/lincoln-setup.py generate-harness` 自动生成，**不要手动编辑**。
7. **同步更新文档**：修改命令表、工作流、角色、skills 时，同步更新 `README.md`、`USAGE.md`、`.claude/workflows/README.md` 等用户/贡献者文档。

## 如何提交 Issue

1. 使用 `.github/ISSUE_TEMPLATE/` 中的模板。
2. 清晰描述问题、复现步骤、期望行为与实际行为。
3. 如果是功能请求，请先说明它解决了什么具体问题，以及为什么属于 Lincoln 的核心或推荐领域包。
4. 如果是文档问题，请标注 `documentation` 标签。

## 如何提交 PR

1. **Fork 仓库**（如果是外部贡献者）或从 `main` 切出 feature 分支。
2. **命名分支**：非 issue 驱动的小改动可用 `docs/xxx`、`fix/xxx`、`feat/xxx`；issue 驱动的改动使用 `issue-<N>`。
3. **小步提交**：每个 commit 只解决一个最小完整问题，commit message 遵循现有风格。
4. **本地验证**：
   - 运行 `bash scripts/static-check.sh`
   - 运行 `pytest tests/`
   - 如果修改了 stage/skill/agent，运行 benchmark 并附前后对比
5. **填写 PR 模板**：逐项填写，不遗漏。
6. **等待审查**：维护者会进行 code review，必要时要求补充测试或文档。
7. **合并后**：如果是 issue 工作包，按 Lincoln 流程把过程知识同步到 `knowledge/` vault。

## 本地开发环境

### 必需依赖

- `python3` ≥ 3.10
- `node` ≥ 20
- `gh` CLI（已登录）
- `openspec` CLI

### 可选依赖

- `ffmpeg`（录音转写）
- Rust 工具链（`cargo`，构建 `tools/lincoln-record/`）
- `Pencil`（原型设计）

### 初始化

```bash
python3 scripts/init-project.sh
```

或使用安装器：

```bash
npx lincoln-install
```

### 运行测试

```bash
# 全部测试
pytest tests/

# 基础设施测试
python3 scripts/run-infrastructure-tests.py

# 静态检查
bash scripts/static-check.sh

# README 约束
pytest tests/test_readme_natural_language.py
```

## 测试分层约定

- `tests/`：**确定性、非 LLM** 的契约与单元测试，进 CI（`static-check.sh`），必须全绿。
- benchmark / eval（`scripts/lincoln_benchmark*.py`）：**LLM 行为评测**，慢且非确定，手动触发，不阻塞 CI。

新增测试时：

- 优先覆盖契约与边界条件，而不是端到端行为。
- 如果测试需要读取 `.claude/` 文件，使用项目根目录的相对路径，并在 `conftest.py` 中提供 fixtures。
- 不要引入需要外部 LLM 调用的测试到 `tests/`。

## 修改 stage / skill / agent 契约时

这些文件是"塑造 agent 行为的代码"，按 eval 门禁规范修改：

1. 修改 `.claude/stages/*.yaml`、`.claude/skills/**`、`.claude/agents/**` 前后，跑一遍 benchmark，在 PR 描述中附前后对比（无回归）。
2. 升级外部 skills 的 pin（`dependencies.yaml`）时同样要求 benchmark 验证（见该文件头部注释的升级流程）。
3. 修改后运行 `python3 scripts/lincoln_command_map.py --refresh` 重新生成命令表，并运行相关测试。

## 如何新增工作流模板

1. 在 `.claude/workflows/` 创建 `<workflow-name>.yaml`，声明 `execution_mode: solo|team`。
2. 遵循 `.claude/schemas/workflow-template.schema.json` 的字段约定。
3. 运行 `python3 scripts/lincoln_command_map.py --refresh` 自动登记 `lc-wf-<name>` 命令。
4. 运行 `python3 scripts/lincoln-setup.py generate-harness --harness codex --harness opencode` 重新生成适配产物。
5. 在 `.claude/skills/lc-wf/SKILL.md` 的命令映射表中补充触发词。
6. 更新 `.claude/workflows/README.md` 的快速路由表与模板详解。
7. 如果该工作流面向最终用户，在 `USAGE.md` 中补充说明。

## 如何新增 Agent 角色

1. 在 `.claude/agents/` 创建 `<role>.md`，参考 `_contract.md` 与现有角色。
2. 明确角色的目标场景、可调用的 skills、不可越界的行为。
3. 运行 `python3 scripts/lincoln_command_map.py --refresh` 生成 `lc-agent-<role>` 命令。
4. 更新相关文档（`README.md`、`USAGE.md`、`.claude/workflows/README.md`）。

## 如何新增 Skill

1. 在 `.claude/skills/` 下创建目录或文件，包含 `SKILL.md` 与必要的 `prompts/`。
2. 如果依赖外部 skill，在 `.claude/skills/dependencies.yaml` 中声明并 pin 到固定 ref。
3. 运行 `python3 scripts/lincoln_command_map.py --refresh` 生成 `lc-skill-<name>` 命令。
4. 在 `.claude/stages/` 中需要引用该 skill 的阶段里更新 `skills` 字段。
5. 补充测试（如适用）和文档。

## 如何新增 Harness 适配

1. 在 `.claude/harnesses/` 创建 `<harness>.yaml` manifest。
2. 在 `scripts/lincoln-setup.py` 中注册该 harness 的生成逻辑（如果现有逻辑不覆盖）。
3. 运行 `python3 scripts/lincoln-setup.py generate-harness --harness <harness>`。
4. 运行 `pytest tests/test_lincoln_harness_adapter.py` 验证生成产物。
5. 确保新增 harness 默认关闭任何可能触发回退陷阱的能力（参考 codex `hooks: {}` 的处理）。
6. 更新 `USAGE.md` 中的多 harness 支持说明。

## 发布前验收

每次发布前，对每个已生成适配的 harness 各跑一遍：

| Harness | 一句话验收 |
|---------|-----------|
| Claude Code | 干净会话发「帮我开始一个新需求」 → 必须触发开场引导 / `lc-workflow-router`，并停在 clarify human_gate 前 |
| codex | 干净会话发同一句话 → `AGENTS.md` 契约生效、`lc-*` prompts 可用，且没有任何 hooks 被自动激活 |
| opencode | 干净会话发同一句话 → `.opencode/` 契约生效、`lc-*` 命令可用，且没有多余能力被默认开启 |

任何一条不满足，不得发布。

### 发布流程（维护者）

1. 确保所有 PR 已合并，`main` 分支测试全绿。
2. 运行 `python3 scripts/bump_version.py bump X.Y.Z`。
3. 运行 `python3 scripts/bump_version.py --check` 验证 lockstep。
4. 运行 `python3 scripts/package-lincoln-plugin.py check --check-dirty`。
5. 运行 `python3 scripts/package-lincoln-plugin.py package` 生成 `dist/lincoln-X.Y.Z.tar.gz`。
6. 创建 PR 合并 release 改动。
7. 在 `main` 上打 tag `vX.Y.Z` 并推送。
8. 创建 GitHub Release 并上传 tarball。
9. 发布/更新 npm 包 `lincoln-install` / `lincoln-update`（需要 `NPM_TOKEN`）。

## 获得帮助

- 查看 [USAGE.md](USAGE.md) 了解 Lincoln 的使用方式。
- 查看 [CLAUDE.md](CLAUDE.md) 了解 Agent 契约与产物规范。
- 查看 [`.claude/workflows/README.md`](.claude/workflows/README.md) 了解工作流模板。
- 在 GitHub Discussions 或 Issues 中提问。

感谢你的贡献！
