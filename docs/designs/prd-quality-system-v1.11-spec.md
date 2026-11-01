# Lincoln PRD Quality System v1.11.0 实施 Spec

- 状态：实施中
- 父 Issue：#142
- 目标版本：v1.11.0
- 实施切片：#143 / #144 / #145 / #146 / #147 / #148

## 1. 背景与问题定义

Lincoln 已有阶段工作流、PRD 13 章骨架、版本快照、HTML 原型和 TDD 交叉验证，但现有自动门控主要验证标题、禁用词、文件存在和人工标记。测试甚至允许每章只有 `-` 的 PRD 通过。系统因此能证明“文档形态存在”，不能证明“需求可执行”。

本方案把 PRD 质量拆成四个可独立验证的契约：

1. **内容契约**：PRD 回答了哪些业务问题。
2. **追溯契约**：需求与来源、故事、验收、流程、原型、测试如何关联。
3. **评审契约**：谁对哪一版本的哪部分质量负责。
4. **生命周期契约**：何时形成需求基线、交付基线，变更后哪些结论失效。

## 2. 产品目标与非目标

### 目标

- 新 PRD 使用 core-v2 内容标准，空章节和纯占位内容无法通过。
- 核心需求有稳定 ID，并按阶段逐步补齐端到端追溯。
- 交付基线由 pm/design/engineering/qa 对同一版本批准。
- 原型与测试可以反向发现 PRD 缺口，且缺口有结构化闭环。
- 旧 13 章 PRD 和轻量工作流保持兼容。

### 非目标

- 不重写门户、渲染器或原型组件库。
- 不把叙事 PRD 全文转换为 YAML。
- 不在 CI 中调用外部 LLM 评分。
- 不强制 bug-fix 等轻量流程生成完整 PRD 文档包。

## 3. 角色与读者

| 角色 | 质量责任 |
|---|---|
| PM | 问题证据、价值、目标指标、范围、业务规则和决策 |
| Design | 用户场景、流程、交互状态、可用性和原型一致性 |
| Engineering | 需求可理解性、边界、依赖、技术约束和交付可行性 |
| QA | 验收可验证性、正常/边界/异常覆盖和测试追溯 |

PM 是唯一人类决策协调者；分角色评审不替代 human gate，而是让 human gate 的输入完整。

## 4. core-v2 内容契约

新 PRD 带 `<!-- prd-contract: core-v2 -->`，默认包含：

1. 版本说明
2. 修订记录
3. 执行摘要
4. 问题与证据
5. 用户与相关者
6. 目标与成功指标
7. 范围与非目标
8. 用户故事
9. 功能需求
10. 业务流程与规则
11. 验收标准
12. 非功能需求
13. 依赖与发布
14. 风险与开放问题
15. 相关产物链接

自动校验负责确定性底线：章节存在、内容非空、非纯占位、指标包含基线/目标值/时间窗、需求和验收具有稳定 ID。证据质量、取舍合理性等由评审角色负责，不伪装成正则表达式可以判断的事实。

无 core-v2 标记的旧 PRD 继续使用 legacy 13 章校验。

## 5. 追溯契约

文件：`{process_slug}/pages/docs/prd-traceability.yaml`。

```yaml
schema_version: "1.0.0"
prd_version: v1.0
requirements:
  - id: REQ-001
    title: 核心需求标题
    core: true
    sources:
      - id: SRC-001
        uri: "interviews/session/transcript.md#00:03:22"
    story_ids: [US-001]
    acceptance_criterion_ids: [AC-001]
    flow_step_ids: [FLOW-001]
    prototype_pages:
      - pages/prototype/web/example/page.html
    test_scenario_ids: [TEST-001]
```

阶段要求：

- `clarify`：核心需求具备来源、故事和验收标准。
- `prototype`：另具备流程步骤和原型页面。
- `tdd`：另具备测试场景。

通用校验：schema、PRD 版本、ID 唯一与前缀、路径范围、数组关系、核心需求覆盖。

## 6. 评审契约

文件：`{process_slug}/pages/docs/prd-review.yaml`。

每个版本记录 pm/design/engineering/qa 的 `pending / approved / changes_requested`，以及 actor、reviewed_at、notes。最终交付基线要求四方 approved；任一 changes_requested 或版本不一致均失败。

评审不是永久有效：PRD 升版后必须 reset-for-version，旧批准不得沿用到新版本。

## 7. 原型契约

HTML `script#pageData` 顶层增加：

```json
{
  "requirement_ids": ["REQ-001"],
  "story_ids": ["US-001"],
  "flow_step_ids": ["FLOW-001"],
  "hotspots": []
}
```

校验覆盖：登记文件存在、实际页面均登记、核心流程有页面、页面元数据与 sidecar 匹配。自由文本 hotspot 继续承担解释，不再作为唯一追溯机制。

## 8. 生命周期

### clarify：需求基线

- PRD core-v2、requirements/stakeholders/user-stories 完整。
- 追溯满足 clarify 阶段。
- PM human gate 通过。
- freeze 当前 PRD 版本，状态为 requirements-baselined。

### product-prototype：交付基线

- 设计文档、fields、ui-spec、HTML 原型完整。
- 追溯满足 prototype 阶段，原型双向校验通过。
- 四方评审通过，human gate 通过。
- PRD 升版并 freeze，状态为 delivery-baselined。

### TDD：验证闭环

- 追溯满足 tdd 阶段。
- 测试场景回问 PRD，缺口修复或显式接受。
- 修复导致 PRD 升版时，重新评审、freeze 和交叉验证。

`.pen` 在所有阶段均为可选；HTML 原型是默认评审与实现依据。

## 9. 工作流 profile

- `full-prd`：interview-to-knowledge、pm-team，执行完整 PM 产物契约。
- `lightweight`：bug-fix、design-spike、existing-project-iteration、framework-self-improvement、oss-first-design 等，允许有意的产物子集。

prompt-drift 对 full-prd 严格检查；lightweight 不再反复报告有意裁剪，但声明超出 Stage 能力的产物仍需诊断。

## 10. 文件所有权与集成边界

| 切片 | 所有权 |
|---|---|
| #143 | PRD 标准、clarify prompt、独立内容校验与 fixtures |
| #144 | 追溯 schema、独立校验器与 fixtures |
| #145 | 评审 schema、独立 CLI、生命周期文档 |
| #146 | 原型 prompt、独立原型追溯校验与 fixtures |
| #147 | Workflow、drift 工具、TDD prompt |
| #148 | Stage、SKILL outputs、Agent、共享 validator、文档与 Release |

共享接线只在 #148 进行，避免并行覆盖。

## 11. 测试与发布

### 确定性验证

- 各切片 focused pytest。
- 全量 `pytest tests/ -q`。
- `bash scripts/static-check.sh`。
- `./scripts/check-prompt-drift.py --strict --focus pm`。
- `python3 scripts/bump_version.py --check`。
- `python3 scripts/package-lincoln-plugin.py check --check-dirty`。

### 行为验证

- 按 CONTRIBUTING 执行契约 benchmark 前后对比。
- 重新生成 Codex/OpenCode harness 并检查 drift。
- 验证 legacy PRD、core-v2 不合格、core-v2 合格三条路径。

### 发布

功能 PR 使用 `release:skip`，最终发布 PR 使用 `release:minor`。合并后由 release-on-merge 生成 v1.11.0 和 `lincoln-v1.11.0` 标签；随后构建 tarball、创建 GitHub Release 并确认 npm 发布工作流。
