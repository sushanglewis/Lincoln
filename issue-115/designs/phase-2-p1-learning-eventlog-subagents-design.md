# Phase 2 / P1 设计方案：摩擦学习 + 事件追踪扩展 + 子代理委托

<!-- status: approved -->
<!-- approved_by: human-pm -->
<!-- approved_at: 2026-08-29 -->

## 1. 背景与目标

- 研究基线：PR #18 / `lew-70-research-baseline` 分支
- 研究笔记：`issue-70/docs/research/openhands-teamai-research-oss-options.md`
- Phase 1 实现：PR #22（已合并）
- 跟踪 Issue：#70
- PM 决策（延续）：
  - Lincoln 是 Claude Code / Codex / OpenCode 的 harness 插件，**不自研执行器**。
  - 所有设计必须能在三种 harness 上生效或优雅降级。
  - 人类门控不可跳过；高危/不可逆操作仍需 PM 显式确认。

## 2. 范围

本 Phase 只处理 P1 项，按优先级排序：

1. **Friction-Based Learning + Recall Precheck**
   - 在 `on-stop.sh` 中根据摩擦信号打分，高摩擦会话提示贡献者沉淀经验。
   - 知识库召回前做相关性预检查，避免每次会话加载全量知识。

2. **扩展 Trace 事件模型 + Condenser**
   - 扩展现有 `.trace/lc-trace.jsonl` 的 `category` 枚举，记录关键 stage/工具/门控/摘要事件。
   - 长会话或事件过多时生成摘要（Condensation），由 `stage_loader.py --action handoff-report` 在写 handoff 文档前自动调用。

3. **Sub-Agent 委托**
   - 在复杂 stage（如 design-review、security-review）中并行调用 specialist agent。
   - 复用 Claude Code / Codex / OpenCode 的 agent 机制，不自建执行器。

4. **MR 知识挖掘**（可选纳入，工作量低）
   - 扩展 `.github/workflows/knowledge-sync.yml`，解析 PR review 评论与代码变更。
   - 自动沉淀决策依据到 `issue-<N>/docs/decisions/`，由 `sync-knowledge` stage 人工把关后进入 `knowledge/`。

5. **Skill Marketplace + git 缓存**（本 phase 暂缓或轻量设计）
   - 分析改进 `scripts/lincoln-setup.py` 的 skill 同步与版本锁定机制。
   - 若与 P0/P1 其他项冲突，可作为独立后续任务保留。

6. **Phase 1 安全门控缺陷修复**（本期一并修复）
   - H1：`scripts/security_analyzer.py` 中 Bash 命令匹配可被 `sudo`、`cd &&` 等前缀绕过。
   - H2：Write/Edit 路径判断未规范化，导致包内绝对路径被误判为外部、路径穿越被误判为内部。

## 3. 现状分析

### 3.1 当前 Hook 与事件能力

- `.claude/hooks/on-stop.sh`：会话结束时更新 `last_updated_at`。
- `.claude/hooks/post-tool-use.sh`：已写入 `.trace/lc-trace.jsonl`（工具调用、退出码、目标、stage）。
- `.claude/hooks/pre-tool-use.sh`：已集成 SecurityAnalyzer（PR #22）。
- `issue-70/workflow-stage.yaml` 的 `nodes[]`：追加式 stage 级别记录，但缺少 LLM/工具/门控级事件。

### 3.2 当前知识库与召回

- `knowledge/`：业务/技术双轨组织。
- `.github/workflows/knowledge-sync.yml`：PR 合并后根据 PR 描述写入知识库。
- **缺少**：会话结束时的经验捕获、召回前的相关性预检查。

### 3.3 当前 Agent 协作

- `.claude/agents/*.md`：定义 pm/designer/engineer/qa/researcher 等角色。
- `.claude/stages/<stage>.yaml` 已有 `agent: { primary, reviewers, handoff_to }`。
- **缺少**：在单个 stage 内并行调用多个 specialist agent 的声明与结果合并策略。

## 4. 设计详情

### 4.1 Friction-Based Learning + Recall Precheck

#### 4.1.1 架构原则

- **不新增 LLM 调用**：friction scoring 完全基于已有 hook 信号（退出码、重试、人工纠正）。
- **可配置阈值**：通过 `.claude/policies/friction.yaml` 定义信号权重与阈值。
- **人类最终确认**：高摩擦会话仅生成提示，由贡献者决定是否写入 `knowledge/`。
- **Recall precheck 轻量**：用关键词/向量相似度判断当前任务与知识库条目的相关性，无关时跳过召回。

#### 4.1.2 Friction 信号定义

| 信号 | 来源 | 权重 | 说明 |
|------|------|------|------|
| tool_failed | post-tool-use exit_code != 0 | +2 | 工具执行失败 |
| tool_rejected | pre-tool-use 返回 BLOCKED | +3 | 被安全/门控拦截 |
| retry_spike | 同一 stage 内同一工具连续失败 >=3 | +3 | 反复重试 |
| human_override | 人类 PM 明确纠正或回退 | +5 | 强摩擦信号 |
| long_session | 单个 node 持续时间 > 阈值 | +1 | 上下文压力 |

```yaml
# .claude/policies/friction.yaml
schema_version: 1.0.0
thresholds:
  prompt_user: 5
  auto_suggest: 3
weights:
  tool_failed: 2
  tool_rejected: 3
  retry_spike: 3
  human_override: 5
  long_session: 1
long_session_minutes: 30
retry_count_threshold: 3
```

#### 4.1.3 on-stop.sh 集成

在 `on-stop.sh` 末尾异步调用（不阻塞 hook 退出）：

1. 读取当前 node 的 trace 文件尾部（最多 500 行）。
2. 统计失败次数、被拦截次数、重试次数、会话时长。
3. 计算 friction score。
4. 若 score >= `prompt_user`，写入 `issue-<N>/.trace/friction-prompt.md` 并在 stderr 提示用户。
5. 若 score >= `auto_suggest` 但 < `prompt_user`，仅写入 `issue-<N>/.trace/friction-suggestion.md`，不打扰用户。

提示模板包含：
- 检测到的摩擦信号列表。
- 建议沉淀到 `knowledge/` 的路径（如 `knowledge/05-learnings/`）。
- 一键命令：`python3 scripts/lincoln-knowledge.py suggest ...`（可选）。

性能约束：
- 使用 `tail -n 500` 限制读取行数。
- 整个调用包在 `( ... ) &` 后台异步执行。
- 失败静默：`|| true`。

#### 4.1.4 Recall Precheck

新增 `scripts/lincoln_recall.py`：

- **输入**：当前 task 描述（从 workflow-stage.yaml 的 current_stage + 用户最近消息推断）。
- **处理**：
  1. 提取关键词（简单分词 + 项目术语表）。
  2. 对 `knowledge/` 中的每条文档计算关键词重叠或轻量向量相似度。
  3. 返回 Top-K 相关文档路径与分数。
- **输出**：JSON 或 Markdown 摘要。
- **集成点**：
  - `on-session-start.sh` 在注入 context 前调用，仅注入相关条目。
  - `lc-build-codebase-knowledge` 在扫描前调用，避免全量扫描。

**降级策略**：若未安装可选依赖（如 sentence-transformers），回退到关键词匹配，不阻塞会话。

接口示例：

```bash
RECALL_JSON=$("$PYTHON" scripts/lincoln_recall.py \
    --stage "$CURRENT_STAGE" \
    --state-file "$STATE_FILE" \
    --top-k 5 --format json 2>/dev/null || echo '{"docs":[]}')
```

hook 把结果渲染成 `=== Lincoln 相关知识 ===` markdown 块拼到 stdout；失败或空结果时跳过该块。

### 4.2 扩展 Trace 事件模型 + Condenser

#### 4.2.1 架构原则

- **单一事实源**：不新建 `lc-eventlog.jsonl`，而是扩展现有 `lc-trace.jsonl` 的 `category` 枚举。
- **补充而非替代**：扩展后的 trace 是 `nodes[]` 的细粒度补充，不替代现有 stage 状态机。
- **追加式持久化**：参考 OpenHands，事件追加到 JSON Lines 文件；base state 仍由 `workflow-stage.yaml` 承载。
- **Condenser 可选**：仅当事件数量超过阈值时触发摘要。

#### 4.2.2 扩展后的 category 枚举

```
tool | skill | agent | read | write | edit | bash | stage_lifecycle | gate | condensation | session
```

Trace 事件行示例：

```json
{
  "schema_version": "2.0.0",
  "sequence_id": 42,
  "timestamp": "2026-08-29T12:00:00Z",
  "run_id": "20260829120000-xxx",
  "stage": "phase-2-p1-design",
  "node_id": "phase-2-p1-design-20260829",
  "category": "tool",
  "tool": "Bash",
  "target": "scripts/stage_loader.py",
  "exit_code": 0,
  "args_summary": "--stage phase-2-p1-design --action validate-entry"
}
```

新增事件类别说明：
- `stage_lifecycle`：`stage_started` / `stage_completed`
- `gate`：`gate_approved` / `gate_rejected`
- `condensation`：摘要事件，记录被摘要的事件范围
- `session`：`session_started` / `session_stopped`

#### 4.2.3 写入点

- `post-tool-use.sh`：写入 `tool` 事件（已存在，category 保持 `tool`）。
- `pre-tool-use.sh`：被拦截时写入 `tool_blocked`（category `tool`，`exit_code` 或 `blocked` 标记）。
- `stage_loader.py`：`record-artifacts`、`approve-gate`、`handoff-report` 等 action 写入 `stage_lifecycle` / `gate` 事件。
- `on-stop.sh`：写入 `session_stopped`（category `session`）。

#### 4.2.4 Condenser

不新增独立 CLI。新增 `scripts/lincoln_condenser.py` 作为库函数：

- 由 `stage_loader.py --action handoff-report` 在写 handoff 文档前自动调用。
- 当当前 stage 的 trace 行数超过 `threshold`（默认 200）时触发。
- 读取事件，按 stage 分组，生成摘要（初期可用规则摘要；未来可接入 LLM）。
- 将摘要作为 `condensation` 事件追加到 trace，并在 handoff 文档 frontmatter 中引用。
- 不删除原始事件，保留可追溯性。

handoff 文档 frontmatter 增加：

```yaml
condensation:
  event_count: 312
  threshold: 200
  summary_events: [evt-012, evt-089]
```

### 4.3 Sub-Agent 委托

#### 4.3.1 架构原则

- **复用 harness agent 机制**：Claude Code 的 `/agent`、Codex 的 agent prompt、OpenCode 的 agent 目录。
- **并行调用**：一个 stage 可同时触发多个 specialist agent，结果汇总后返回主 agent。
- **结果合并**：采用结构化输出（schema），主 agent 按优先级合并。
- **配置内嵌 stage YAML**：不新建独立文件，避免与现有 `agent:` 字段双源冲突。

#### 4.3.2 使用场景

| Stage | Specialist Agents | 输出 |
|-------|-------------------|------|
| design-review | architect, security-reviewer, pm | 评审意见列表 |
| security-review | security-reviewer, python-reviewer | 风险报告 |
| explore-opensource | researcher, engineer | 候选方案评分表 |

#### 4.3.3 实现方式

在 `.claude/stages/<stage>.yaml` 的 `agent:` 字段扩展：

```yaml
# .claude/stages/phase-2-p1-design.yaml
agent:
  primary: lc-architect
  reviewers:
    - lc-engineer
    - lc-researcher
  handoff_to: lc-pm
  parallel_specialists:
    - lc-architect
    - lc-security-reviewer
  merge_strategy: priority  # priority | vote | consensus
  output_schema: .claude/schemas/design-review-feedback.json
```

`stage_loader.py --action validate-entry` 时校验：
- `parallel_specialists` 中每个 agent 在 `.claude/agents/` 中存在对应文件。
- `output_schema` 文件存在且为合法 JSON Schema。

实际调用由 harness 完成（Lincoln 不自建执行器）：
- Claude Code：通过 agent prompt 提示主 agent 调用 `/agent <name>`。
- Codex：生成 `AGENTS.md` 时附带 delegation 说明。
- OpenCode：在 `.opencode/agent/` 中生成 specialist agent，由主 agent 引用。

第一阶段先提供规范与示例，第二阶段再视 harness 支持情况增加自动化。

### 4.4 MR 知识挖掘

#### 4.4.1 架构原则

- **扩展现有 knowledge-sync**：不新建工作流。
- **安全优先**：不记录代码中的潜在 secret；仅提取决策性评论与变更摘要。
- **不直接写 knowledge/**：产物先落到 issue 工作包，由 `sync-knowledge` stage 人工把关后沉淀。

#### 4.4.2 扩展点

修改 `.github/workflows/knowledge-sync.yml`：

1. 在 PR 合并后，除了 PR 描述，还读取 review 评论（通过 GitHub API）。
2. 提取包含 "decision"、"agreed"、"rejected"、"note:" 等关键词的评论。
3. 写入 `issue-<N>/docs/decisions/lew-70-<pr>-<decision>.md`。
4. 关联回 issue-70 研究笔记。

新增 `scripts/lincoln_mr_mine.py`：

- 输入：PR number、repo。
- 输出：Markdown 决策摘要。
- 可由 workflow 调用，也可本地手动运行。

### 4.5 Phase 1 安全门控缺陷修复（本期一并修复）

#### 4.5.1 H1：Bash 命令匹配绕过

**问题**：`file-deletion`、`git-push`、`external-api-call` 等规则使用 `re.match`（仅匹配行首），`sudo rm foo`、`cd /tmp && rm foo` 等常见写法不命中。

**修复**：
- 统一改为 `re.search`。
- 对 `&&`、`;`、`|` 等 shell 链式操作符切分命令后再逐段匹配。
- 为 `sudo`、`env`、`cd ... &&` 等前缀添加回归测试。

#### 4.5.2 H2：Write/Edit 路径判断未规范化

**问题**：`_target_matches` 只做 `target.lstrip("/")` 加字符串前缀比较，导致包内绝对路径被误判为外部、路径穿越被误判为内部。

**修复**：
- 在 `security_analyzer.py` 内将 target 解析为绝对路径（相对路径拼 `root` 后 `.resolve()`）。
- 与 `process_package_root` 做 `relative_to` 判断。
- hook 把已规范化的 `NORMALIZED_TARGET` 传给 analyzer。
- 补充绝对路径、路径穿越、`..` 前缀等边界测试。

## 5. 边界与不做什么

- **不自研 LLM 执行器**：Action-Observation 循环、Workspace Factory 仅作参考。
- **不构建重型代码图**：P2 的 AST + Heuristic 代码图不在本 phase。
- **不实现实时 Dashboard**：Session Analytics 仅扩展现有 benchmark 输出，不做 Web UI。
- **不替换现有 `nodes[]`**：扩展后的 trace 是补充，保持向后兼容。
- **不新建独立 EventLog 文件**：单一事实源为 `lc-trace.jsonl`。

## 6. 实现顺序与验收标准

| 顺序 | 项 | 验收标准 |
|------|-----|---------|
| 0 | 扩展 `lincoln_trace.py` category 枚举 | `lc-trace.jsonl` 可写入 `tool/stage_lifecycle/gate/session/condensation` 事件；schema 校验通过 |
| 1 | `scripts/lincoln_friction.py` + `on-stop.sh` 异步集成 | `on-stop.sh` 生成 friction 提示文件；测试覆盖 5 种信号 + 3 个阈值边界 |
| 2 | `scripts/lincoln_recall.py` + `on-session-start.sh` 集成 | 返回 Top-K 相关文档；关键词降级可用；失败时不阻塞会话 |
| 3 | `stage_loader.py` 写 stage/gate 事件到 trace | 每个 action 产生对应 trace 行；event_id 唯一 |
| 4 | Condenser 内嵌进 `handoff-report` | 事件超阈值时生成摘要；handoff 文档引用摘要 |
| 5 | stage YAML 扩展 `parallel_specialists` + `stage_loader` 校验 | schema 校验通过；引用的 agent 文件存在 |
| 6 | MR knowledge mining | workflow 扩展解析 review 评论；生成 `issue-<N>/docs/decisions/` 摘要 |
| 7 | 修复 Phase 1 H1/H2 | `sudo rm foo`、`cd && rm foo` 被拦截；包内绝对路径写入不拦截；路径穿越被拦截 |

## 7. 测试计划

### 7.1 新增单元测试

- `tests/test_friction_scorer.py`
  - `test_score_includes_tool_failed`
  - `test_score_includes_tool_rejected`
  - `test_retry_spike_detected_after_three_repeated_failures`
  - `test_human_override_adds_max_weight`
  - `test_long_session_adds_weight_when_threshold_exceeded`
  - `test_prompt_user_file_written_when_score_meets_threshold`
  - `test_suggestion_file_written_when_score_between_thresholds`
  - `test_no_file_when_score_below_auto_suggest`
- `tests/test_recall.py`
  - `test_recall_returns_top_k_by_keyword_overlap`
  - `test_recall_falls_back_to_keywords_when_embedding_unavailable`
  - `test_recall_returns_empty_when_no_match`
  - `test_recall_does_not_block_on_failure`
- `tests/test_trace_extended.py`
  - `test_trace_accepts_stage_lifecycle_category`
  - `test_trace_accepts_gate_category`
  - `test_trace_accepts_session_category`
  - `test_trace_event_id_is_unique`
- `tests/test_condenser.py`
  - `test_condenser_triggered_when_event_count_exceeds_threshold`
  - `test_condenser_appends_condensation_event`
  - `test_condenser_skipped_when_below_threshold`
- `tests/test_agent_delegation.py`
  - `test_stage_yaml_with_parallel_specialists_passes_validation`
  - `test_missing_agent_file_fails_validation`
  - `test_missing_output_schema_fails_validation`
- `tests/test_mr_mining.py`
  - `test_mine_extracts_decision_comments`
  - `test_mine_writes_to_issue_docs_decisions`
  - `test_mine_does_not_include_code_or_secrets`
  - `test_mine_is_idempotent`

### 7.2 集成 / 回归测试

- `tests/test_hooks.py` 现有 26 个用例必须在 EventLog/Trace 扩展叠加后继续通过。
- EventLog 关闭/不可写时 hook 仍按 Phase 1 行为工作（降级）。
- friction prompt 生成不影响 stage 状态机（human gate 不可绕过）。
- 并发写 `.jsonl` 安全性测试（追加模式 + 行级原子性）。
- 隐私负向测试：trace payload 不包含 `human_message` 原文。
- 跨 harness 一致性：Codex / OpenCode 上 trace/friction/recall 最低限度为「不写入也不报错」。

### 7.3 Phase 1 缺陷回归测试

- `tests/test_security_analyzer.py` 新增：
  - `test_rm_with_sudo_prefix_is_blocked`
  - `test_rm_after_cd_and_chain_is_blocked`
  - `test_absolute_path_inside_package_is_allowed`
  - `test_path_traversal_outside_package_is_blocked`
  - `test_git_push_with_sudo_prefix_is_logged`

### 7.4 静态检查与覆盖率

- 所有新增脚本通过 `static-check.sh`。
- 新增代码覆盖率 >= 80%。
- Phase 1 原有 51 个范围测试 100% 通过。

## 8. 配置与文件变更清单

### 新增文件

- `scripts/lincoln_friction.py`
- `scripts/lincoln_recall.py`
- `scripts/lincoln_condenser.py`
- `scripts/lincoln_mr_mine.py`
- `.claude/policies/friction.yaml`
- `.claude/schemas/design-review-feedback.json`（示例）
- 各新增测试文件

### 迁移文件

- `.claude/security/risk-policy.yaml` → `.claude/policies/security.yaml`（保留兼容符号链接至少一个 release）

### 修改文件

- `.claude/hooks/on-stop.sh`
- `.claude/hooks/on-session-start.sh`
- `.claude/hooks/post-tool-use.sh`
- `.claude/hooks/pre-tool-use.sh`
- `scripts/lincoln_trace.py`
- `scripts/stage_loader.py`
- `scripts/security_analyzer.py`
- `.claude/stages/phase-2-p1-design.yaml`
- `.claude/stages/phase-2-p1-implement.yaml`
- `.github/workflows/knowledge-sync.yml`
- `.claude/harnesses/codex.yaml` / `opencode.yaml`（如有必要生成 delegation 说明）

## 9. 风险与待澄清问题

1. **Recall precheck 是否允许调用 embedding 模型？**
   - 决策：默认仅关键词匹配；embedding 作为可选依赖，未安装时优雅降级。
2. **Trace 是否包含用户消息内容？**
   - 决策：默认不包含，仅记录元数据，避免隐私风险。
3. **Sub-agent 委托在 Codex/OpenCode 上的实际支持程度？**
   - 决策：第一阶段仅提供规范与示例，不自建执行器；待 harness 演进后补充自动化。
4. **Skill Marketplace 是否 out-of-scope for Phase 2？**
   - 决策：是的，本 phase 仅做轻量分析，不实现。

---

**PM 已审批。** 审批后进入 Phase 2 / P1 实现。
