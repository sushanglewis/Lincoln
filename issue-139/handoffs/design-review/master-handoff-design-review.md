<!-- status: draft -->
# 评审交接：PM 多 Agent 体系方案与实现（issue-139 / PR #140）

## 1. 交接背景

- **任务来源**：GitHub issue #139 —— 设计 PM「需求 → PRD」各子阶段的专业化 agent 协作体系，并在 Lincoln 框架落地。
- **交付物**：设计文档 v0.4 + 框架实现（角色 / stage / 工作流 / 排遣模板 / schema / 路由），单一 PR：https://github.com/sushanglewis/Lincoln/pull/140 （分支 `issue-139`，4 个 commit）。
- **当前状态**：全部自动化校验通过；人类 PM 尚未 confirm（human_gate pending）。
- **评审目的**：请审阅方案合理性与实现正确性，重点关注第 5 章评审清单。

## 2. 方案一页速览

**三层组织**：`lc-pm`（tier-1 总协调者，唯一人类接口）→ 六个 `lc-pm-*`（tier-2 阶段主管：intake / analyst / mvp / challenge / author / validator）→ `lc-pm-*-*`（tier-3 执行 agent，无角色文件，由主管排遣）。

**四个核心机制**：

1. **分层上下文契约**：tier-3 不继承 `default.md` 全量契约，只遵循 brief 模板内嵌的 4 条轻契约；执行 agent 上下文 = 简报本身。
2. **排遣模板机械填槽**：主管不撰写提示词，从 `.claude/templates/dispatch/`（6 个模板）取模板填槽派发，主管只掌握「任务→人→输出」三元组。
3. **结构化红队**：挑战条目遵循 `.claude/schemas/challenge-feedback.json`，PM 的 fix/accept 决策落同一结构。
4. **轻重分流**：`interview-to-knowledge` 恢复原序为轻量默认；新增 `pm-team` 重型工作流（六子阶段全流程），router 推荐时必须向人类 PM 说明流程重量并获显式选择。

**设计演进**：v0.1 六阶段映射 → v0.2 调研驱动（6 框架桌面调研）→ v0.3 三层组织 → v0.4 分层契约 + 排遣模板 + 轻重分流。

## 3. 实现文件地图

| 层 | 文件 | 说明 |
|----|------|------|
| tier-1 | `.claude/agents/pm.md` | 总协调者契约：单一人类接口、计划即授权、执行模式规则（轻默认/重可选） |
| tier-2 | `.claude/agents/pm-{intake,analyst,mvp,challenge,author,validator}.md` | 各含 3 条方法论、SOP、产出物、排遣规范表（含模板列与数量上限） |
| tier-3 载体 | `.claude/templates/dispatch/*.md` | 6 个 brief 模板，头部内嵌轻契约 4 条 + 任务参数槽位 |
| 工作流 | `.claude/workflows/pm-team.yaml`（新增，重型）；`interview-to-knowledge.yaml`（恢复原序） | pm-team：router → requirement-intake → clarify → product-design-docs → challenge → product-prototype → tdd-development-plan |
| stage | `.claude/stages/requirement-intake.yaml`、`challenge.yaml`（新增，归 pm-team）；共享 stage 的 workflows 列表追加 pm-team | requirement-intake.primary=lc-pm-intake；challenge.primary=lc-pm-challenge（output_schema 引用 challenge-feedback.json） |
| 路由 | `lc-workflow-router/prompts/router-prompt.md`、`lc-wf/SKILL.md`、`workflows/README.md`、`harnesses/command-map.yaml` | pm-team 信号 + 重型须显式选择规则；lc-wf-pm-team 已登记 |

## 4. 关键决策与权衡（评审时请重点质询）

1. **组织不靠代码**：三层关系全部由 prompt 契约表达（角色文件互相引用），无引擎改动；stage `agent` 字段的 `parallel_specialists` / `merge_strategy: priority` / `output_schema` 是既有 schema 能力，未扩展 schema。
2. **stage.primary per-stage 单值限制**：轻量模式下 clarify 的「lc-pm 委派 lc-pm-author 驻场」只能写在 prompt 层（lc-pm.md 与 pm-team step 描述），stage YAML 无法按工作流覆盖 primary。备选方案是 schema 增加 `agent_overrides`（需引擎支持），本期未做。
3. **tier-3 不物化角色文件**：28 个三级实例由 6 个模板承载，避免角色目录爆炸；代价是三级 agent 的行为边界完全依赖模板填槽质量。
4. **新 stage 不配专用 skill**：主管方法论写在角色文件里，待真实运行后再按需沉淀 skill。
5. **human_gate 只增不减**：pm-team 比标准流程多 2 个 stage、2 个 gate，是「重」的主要来源，也是 router 必须显式确认的原因。

## 5. 评审清单

**方案层**

- [ ] 三层职责划分是否有重叠或真空（特别是 lc-pm 总协调 vs lc-pm-author 阶段主管的边界）
- [ ] 「计划即授权」是否会削弱人类 PM 对 fan-out 的控制（对比 default.md 子代理调度原则第 3 条）
- [ ] tier-3 轻契约 4 条是否充分；是否有必须继承自 default.md 的规则被切断
- [ ] 轻重分流边界：轻量模式下 tier-2 主管介入深度是否清晰可执行
- [ ] 六子阶段与既有 stage 的映射是否有逻辑漏洞（如可行性结论同时进 clarify 与 feasibility.html 的双写问题）

**实现层**

- [ ] 六个 tier-2 角色文件：方法论/SOP/产出物/排遣规范表是否齐全且互相一致
- [ ] dispatch 模板：槽位是否完备、输出契约与各主管排遣表是否一致
- [ ] `pm-team.yaml` 的 steps/artifacts 与 stage YAML 的 artifacts 是否一致（R3 校验已覆盖，可复核）
- [ ] `challenge-feedback.json` 的维度枚举与 pm-challenge 排遣表七维度是否一一对应
- [ ] router 规则是否真的能做到「不默认启用 pm-team」（措辞是否会被模型忽略）

**验证层（已跑通，可复现）**

```bash
python3 -m pytest tests/test_yaml_schemas.py -q   # 37 passed
./scripts/check-prompt-drift.py --strict --focus pm  # 0 error（79 条既有告警与本方案无关）
python3 scripts/run-infrastructure-tests.py  # 162 passed
./scripts/check-harness-drift.sh  # passed
```

已知环境噪声（非本方案问题）：`static-check.sh` exit 1 因外部 agent 未 vendor（基线相同）；drift 的 79 条告警全部指向 oss-first-design 与未 vendor 外部 agent。

## 6. 已知限制与开放问题

1. dispatch 模板未经真实排遣运行验证（建议合入后用一个真实 issue 走 pm-team 验证）。
2. `pm-research`（solo）与 requirement-intake 的复用关系仅文字约定，无机制保证。
3. tier-2 主管在轻量工作流（bug-fix / design-spike 等）中的角色未定义——目前只有 pm-team 与共享 stage 的 reviewer/parallel_specialists 提到它们。
4. 人类 PM 尚未 confirm；本文件所依据的设计文档版本为 v0.4，如有变更需重出本 handoff。

## 7. 评审输出建议格式

结构化反馈，按 severity（critical/high/medium/low）分类，每条给出文件位置与具体建议；结论字段 `approvable: true|false`。评审意见可直接留在 PR #140 或本目录新增文件。
