# Phase 1 / P0 设计方案：安全门控 + 三 Harness 分发 + Hook/MCP 规范

## 1. 背景与目标

- 研究基线：PR #18 / `lew-70-research-baseline` 分支
- 研究笔记：`issue-70/docs/research/openhands-teamai-research-oss-options.md`
- 跟踪 Issue：#19
- PM 决策：
  - Lincoln 是 Claude Code / Codex / OpenCode 的 harness 插件，不自研执行器。
  - 允许 `git push`、外部 API 调用；**文件删除必须人工确认**。
  - harness 分发与 hook/MCP 规范需要覆盖 Claude Code / Codex / OpenCode。

## 2. 范围

本 Phase 只处理 P0 项：

1. **SecurityAnalyzer + ConfirmationPolicy**
   - 文件删除类操作强制 human_gate。
   - 允许 `git push`、外部 API 调用（可记录日志，不阻塞）。
   - 三 harness 均须生效。

2. **Harness 分发完善**
   - `scripts/lincoln_harness_adapter.py` 能可靠同步 skills/rules/hooks/MCP 到 Claude Code / Codex / OpenCode。
   - 三 harness 的命令键集、agent 集合、安全策略保持一致。

3. **Hook / MCP 声明式配置**
   - 统一 `.claude/hooks/` 与 `.claude/skills/dependencies.yaml` 的跨 harness 分发规范。
   - 新增 `.claude/hooks/hooks.yaml` 与 `.claude/mcp/mcp.yaml`。

## 3. 现状分析

### 3.1 现有安全机制

`.claude/hooks/pre-tool-use.sh` 已具备：

- stage 状态检查（entry/exit/paused）。
- side-effect 工具清单（Bash, Edit, Write, NotebookEdit, GitHub MCP, Pencil MCP）。
- `.pen`、录音、workflow-stage.yaml、跨 process_slug 写入保护。
- **缺少**：按工具参数内容（如 `command: rm`）进行风险分级与确认策略。

### 3.2 现有 Harness 适配

`scripts/lincoln_harness_adapter.py`：

- 读取 `.claude/harnesses/<name>.yaml` 生成 codex/opencode 产物。
- 当前生成：
  - codex：`AGENTS.md`、`~/.codex/prompts/lc-*.md`、`.codex-plugin/plugin.json`
  - opencode：`.opencode/agent/*.md`、`.opencode/command/lc-*.md`
- **缺少**：skills、rules、hooks、MCP 的同步目标。

### 3.3 现有依赖声明

`.claude/skills/dependencies.yaml`：

- 声明外部 skills、CLIs、plugins。
- **缺少**：hooks 与 MCP servers 的声明式配置及跨 harness 分发说明。

## 4. 设计详情

### 4.1 SecurityAnalyzer + ConfirmationPolicy

#### 4.1.1 架构原则

- **不替代底层 harness 执行器**：Lincoln 只提供风险分析逻辑和确认策略，实际 tool 执行仍由 Claude Code / Codex / OpenCode 完成。
- **单一事实源**：风险规则放在 `.claude/security/risk-policy.yaml`，三 harness 共用。
- **最小侵入**：对 Claude Code 通过 `pre-tool-use.sh` 拦截；对 Codex/OpenCode 通过生成的 agent prompt + 插件声明共同约束。

#### 4.1.2 风险分级

| 级别 | 含义 | 默认策略 |
|------|------|---------|
| low | 只读或低风险文件操作 | 直接执行 |
| medium | 可能改变仓库状态但不破坏数据 | 记录日志，直接执行 |
| high | 不可逆数据删除 | **必须 human_gate 确认** |
| unknown | 无法判定 | 按 high 处理（可配置） |

#### 4.1.3 风险规则（第一版）

```yaml
# .claude/security/risk-policy.yaml
schema_version: 1.0.0
policies:
  - name: file-deletion
    tool: Bash
    condition: command matches any of ["rm", "rmdir", "trash", "mv .* /dev/null"]
    level: high
    message: "文件/目录删除操作不可逆，需人工确认。"
    confirm: true

  - name: recursive-delete
    tool: Bash
    condition: command matches "rm -r" or "rm -rf"
    level: high
    message: "递归删除风险极高，需人工确认。"
    confirm: true

  - name: git-push
    tool: Bash
    condition: command matches "git push"
    level: medium
    message: "git push 将改变远程仓库状态。"
    confirm: false
    log: true

  - name: external-api-call
    tool: Bash
    condition: command matches any external HTTP client (curl, wget, httpie)
    level: medium
    message: "正在调用外部 API。"
    confirm: false
    log: true

  - name: file-write-outside-process
    tool: Write|Edit
    condition: target outside current process_slug
    level: high
    message: "不允许写入当前 issue 工作包之外的产物目录。"
    confirm: true
```

#### 4.1.4 实现位置

新增文件：

- `scripts/security_analyzer.py`：风险分析器，输入 tool name + args，输出 `{level, policy, message, confirm_required}`。
- `.claude/security/risk-policy.yaml`：可编辑的风险规则。
- `.claude/hooks/pre-tool-use.sh`：在现有 stage 检查之后，调用 `security_analyzer.py`；若 `confirm_required=true`，设置 stage 状态为 `waiting_for_human` 并退出非 0。

修改文件：

- `.claude/hooks/pre-tool-use.sh`：在 174-204 行之间插入风险分析调用。

#### 4.1.5 三 harness 落地策略

| Harness | 落地方式 | 说明 |
|---------|---------|------|
| Claude Code | `.claude/hooks/pre-tool-use.sh` | 原生支持 pre-tool-use hook，可直接拦截。 |
| Codex | `.codex/hooks/pre-tool-use.sh` + `AGENTS.md` 安全约束 | 启用 pre-tool-use hook，调用同一 `security_analyzer.py`；`AGENTS.md` 作为补充约束。 |
| OpenCode | `.opencode/hooks/pre-tool-use.sh` + agent 系统提示 | 启用 pre-tool-use hook，调用同一 `security_analyzer.py`；agent 系统提示作为补充约束。 |

> 三 harness 共用 `scripts/security_analyzer.py` 与 `.claude/security/risk-policy.yaml` 作为单一事实源。Codex/OpenCode 的 hook 脚本为生成产物，由 `scripts/lincoln_harness_adapter.py` 从 `.claude/hooks/pre-tool-use.sh` 派生，并在目标 harness 中替换状态文件解析路径。

#### 4.1.6 human_gate 暂停与恢复

- 当风险分析触发确认时，`pre-tool-use.sh` 输出：
  ```
  BLOCKED: 文件/目录删除操作不可逆，需人工确认。
  Run: python3 scripts/stage_loader.py --stage <current_stage> --action approve-gate --approved-by human-pm
  ```
- 同时向 `issue-<N>/logs/security.log` 写入 JSON 日志：
  ```json
  {"timestamp": "2026-08-29T12:00:00Z", "stage": "...", "tool": "Bash", "level": "high", "policy": "file-deletion", "action": "blocked", "command": "rm -rf foo"}
  ```
- Agent 进入 `waiting_for_human` 状态，只允许 Read/Grep/Glob。
- PM 确认后运行 approve-gate，恢复 side-effect 工具执行。

### 4.2 Harness 分发完善

#### 4.2.1 新增同步目标

在 `.claude/harnesses/codex.yaml` 与 `.claude/harnesses/opencode.yaml` 中增加：

```yaml
targets:
  # 已有 targets...

  - kind: skill
    source: .claude/skills/*/SKILL.md
    output: "{home}/.codex/skills/{parent}/{name}.md"   # codex
    output: "{project}/.opencode/skills/{parent}/{name}.md" # opencode
    scope: home | project
    transform: copy

  - kind: rule
    source: .claude/rules/**/*.md
    output: "{project}/.codex/rules/{relative_path}.md"
    output: "{project}/.opencode/rules/{relative_path}.md"
    scope: project
    transform: copy

  - kind: hook
    source: .claude/hooks/*.sh
    output: "{project}/.codex/hooks/{name}.sh"
    output: "{project}/.opencode/hooks/{name}.sh"
    scope: project
    transform: copy

  - kind: mcp
    source: .claude/mcp/mcp.yaml
    output: "{project}/.codex/mcp.yaml"
    output: "{project}/.opencode/mcp.yaml"
    scope: project
    transform: mcp-config
```

#### 4.2.2 `scripts/lincoln_harness_adapter.py` 扩展

- 新增 transform：`copy`、`mcp-config`。
- `copy`：直接复制文件，保留目录结构。
- `mcp-config`：读取 `.claude/mcp/mcp.yaml`，按 harness 输出对应格式（codex 使用其原生 MCP 配置格式；opencode 使用其格式；Claude Code 保持 `.claude/mcp/mcp.yaml` 原生）。
- 增加 `--harness claude-code` 支持：校验 `.claude/` 事实源一致性，不生成产物（因为 Claude Code 直接使用 `.claude/`）。

#### 4.2.3 三 Harness 一致性校验

新增 CI 步骤：

```yaml
- name: Harness drift check
  run: |
    python3 scripts/lincoln_harness_adapter.py --harness codex --check
    python3 scripts/lincoln_harness_adapter.py --harness opencode --check
    python3 scripts/lincoln_harness_adapter.py --harness claude-code --check
```

### 4.3 Hook / MCP 声明式配置

#### 4.3.1 新增文件

- `.claude/hooks/hooks.yaml`：声明所有 hook 文件及其触发事件、执行顺序、适用 harness。
- `.claude/mcp/mcp.yaml`：声明 MCP servers、启用状态、环境变量、按 harness 的覆盖项。

#### 4.3.2 `.claude/hooks/hooks.yaml` 示例

```yaml
schema_version: 1.0.0
hooks:
  - name: pre-tool-use
    file: pre-tool-use.sh
    events: [pre_tool_use]
    harnesses: [claude-code, codex, opencode]
    order: 10

  - name: on-session-start
    file: on-session-start.sh
    events: [session_start]
    harnesses: [claude-code]
    order: 10

  - name: on-stop
    file: on-stop.sh
    events: [session_stop]
    harnesses: [claude-code]
    order: 10
```

#### 4.3.3 `.claude/mcp/mcp.yaml` 示例

```yaml
schema_version: 1.0.0
servers:
  pencil:
    command: npx
    args: ["-y", "@pencil/mcp-server"]
    env:
      PENCIL_API_KEY: ${PENCIL_API_KEY}
    enabled: true
    harness_overrides:
      codex:
        enabled: false   # codex 暂不需要 Pencil
```

- 环境变量支持从 `.env` 文件读取（通过 `python-dotenv` 在项目根加载），也允许用户显式导出。
- 敏感变量不会硬编码在 `mcp.yaml` 中；分发到各 harness 时保留 `${VAR}` 占位符，由运行时环境解析。
- `.env` 加入 `.gitignore`，并提供 `.env.example` 模板。

#### 4.3.4 与现有 `dependencies.yaml` 的关系

- `dependencies.yaml` 继续负责外部 skills/CLIs/plugins 的依赖声明与 pin 校验。
- `hooks.yaml` 与 `mcp.yaml` 负责 Lincoln 自身的 hook/MCP 分发。
- `scripts/lincoln-setup.py` 同时读取三者，完成环境安装与 harness 产物生成。

## 5. 文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `scripts/security_analyzer.py` | 风险分析器 |
| `.claude/security/risk-policy.yaml` | 风险规则配置 |
| `.claude/hooks/hooks.yaml` | Hook 声明式配置 |
| `.claude/mcp/mcp.yaml` | MCP 声明式配置 |
| `tests/test_security_analyzer.py` | 风险分析单元测试 |
| `tests/test_harness_adapter_extended.py` | 扩展的 harness 适配测试 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `.claude/hooks/pre-tool-use.sh` | 集成 `security_analyzer.py` |
| `.claude/harnesses/codex.yaml` | 增加 skill/rule/hook/mcp targets |
| `.claude/harnesses/opencode.yaml` | 增加 skill/rule/hook/mcp targets |
| `scripts/lincoln_harness_adapter.py` | 新增 transform、支持 `--harness claude-code`、MCP 配置转换 |
| `scripts/lincoln-setup.py` | 读取 hooks.yaml / mcp.yaml，生成分发产物 |
| `.github/workflows/static-check.yml` | 增加 harness drift check |

## 6. 风险策略矩阵

| 操作 | 工具 | 风险级别 | 默认行为 |
|------|------|---------|---------|
| 读取文件 | Read | low | 允许 |
| 写入当前 process_slug 内文件 | Write/Edit | medium | 允许，记录日志 |
| 写入其他 process_slug | Write/Edit | high | **阻塞，需 PM 确认** |
| `rm` / `rmdir` | Bash | high | **阻塞，需 PM 确认** |
| `rm -rf` | Bash | high | **阻塞，需 PM 确认** |
| `git push` | Bash | medium | 允许，记录日志 |
| `curl` / `wget` 外部 API | Bash | medium | 允许，记录日志 |
| 创建 GitHub Issue / PR / Merge | GitHub MCP | medium | 允许，记录日志 |
| Pencil 导出 | Pencil MCP | medium | 允许，记录日志 |
| 未知高危命令 | Bash | unknown → high | **阻塞，需 PM 确认** |

## 7. 依赖外部项目/工具

| 依赖 | 用途 | Lincoln 角色 |
|------|------|-------------|
| Claude Code CLI | 执行 pre-tool-use hook | harness 宿主 |
| Codex CLI | 执行 AGENTS.md / prompt 约束 | harness 宿主 |
| OpenCode CLI | 执行 agent / command 约束 | harness 宿主 |
| `pyyaml` | YAML 解析 | 已存在，用于 risk policy 与 manifest |
| `jsonschema` | 校验 hooks.yaml / mcp.yaml | 已存在（static-check 使用） |

Lincoln **不自建** risk LLM、hook 引擎或 MCP server；只提供规则配置与分发逻辑。

## 8. 测试策略

### 8.1 单元测试

- `tests/test_security_analyzer.py`：
  - `rm -rf /tmp/foo` → level=high, confirm_required=true
  - `git push origin main` → level=medium, confirm_required=false
  - `curl https://api.example.com` → level=medium, confirm_required=false
  - 空命令 / 未知命令 → level=unknown, confirm_required=true（可配置）

### 8.2 集成测试

- `tests/test_harness_adapter_extended.py`：
  - 生成 codex/opencode 产物后，检查 skills/rules/hooks/mcp 文件存在。
  - `--check` 模式下无 drift。

### 8.3 Hook 集成测试

- 模拟 `pre-tool-use.sh Bash '{"command":"rm -rf foo"}'` 并验证返回非 0 与提示信息。
- 模拟确认后再次调用验证返回 0。

### 8.4 覆盖率

目标：≥ 80%。

## 9. 验收标准

- [ ] `.claude/security/risk-policy.yaml` 可解析，规则覆盖文件删除、`git push`、外部 API 调用。
- [ ] `scripts/security_analyzer.py` 对 sample commands 的风险分级与策略判断正确。
- [ ] `.claude/hooks/pre-tool-use.sh` 在文件删除场景下阻塞并提示确认命令。
- [ ] `scripts/lincoln_harness_adapter.py --harness codex` 生成 skills/rules/hooks/mcp 产物。
- [ ] `scripts/lincoln_harness_adapter.py --harness opencode` 生成对应产物。
- [ ] `scripts/lincoln_harness_adapter.py --harness claude-code --check` 校验事实源无漂移。
- [ ] CI harness drift check 通过。
- [ ] 所有新增/修改代码通过 `code-reviewer` 与 `security-reviewer`。
- [ ] PM 审批设计文档后，才进入 TDD 实现阶段。

## 10. 迁移与回滚

- **迁移**：
  1. 新增文件 harmless，不影响现有流程。
  2. 更新 `pre-tool-use.sh` 后，首次调用会加载 `risk-policy.yaml`；若规则文件缺失，降级为现有行为（不新增阻塞）。
  3. 运行 `python3 scripts/lincoln-setup.py` 重新生成 harness 产物。

- **回滚**：
  - 若 `security_analyzer.py` 导致误拦截，可删除 `.claude/security/risk-policy.yaml` 或设置 `LINCOLN_SECURITY_MODE=permissive` 环境变量跳过分析。
  - harness 产物为生成文件，可随时删除并重新生成。

## 11. 关键待澄清问题（PM 已答复）

1. **Codex/OpenCode 的 hook 支持**：是否投入启用 codex/opencode 的 pre-tool-use hook，还是先用 prompt 约束覆盖 P0？
   - **PM 决策**：投入启用 Codex / OpenCode 的 pre-tool-use hook。
   - **落地**：由 `scripts/lincoln_harness_adapter.py` 生成 `.codex/hooks/pre-tool-use.sh` 与 `.opencode/hooks/pre-tool-use.sh`，调用同一 `security_analyzer.py`。

2. **日志记录位置**：风险操作日志写入 `issue-<N>/logs/security.log` 还是统一写入 `.claude/logs/`？
   - **PM 决策**：写入 `issue-<N>/logs/security.log`。
   - **落地**：`security_analyzer.py` 根据 `workflow-stage.yaml` 中的 `process_slug` 确定日志路径；目录不存在时自动创建。

3. **MCP 环境变量**：`.claude/mcp/mcp.yaml` 中的敏感变量是否允许从 `.env` 读取，还是必须显式导出？
   - **PM 决策**：允许从 `.env` 读取。
   - **落地**：`scripts/lincoln-setup.py` 与 harness adapter 使用 `python-dotenv` 加载 `.env`；`mcp.yaml` 保留 `${VAR}` 占位符，不存储明文密钥。

---

`<!-- status: approved -->`
