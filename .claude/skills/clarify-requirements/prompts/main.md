# clarify-requirements

You are executing the Lincoln workflow step `clarify`: turn interview artifacts into a structured requirements document through multi-round clarification with the human PM.

## Goal

Produce a clear, agreed-upon `{process_slug}/pages/docs/requirements.html` and the root-level `{process_slug}/pages/docs/prd.html` that serves as the single source of truth and main thread for this issue.

## Input

- `session_id`: the interview session identifier

## 子技能准备

在执行本 prompt 前：
- 若存在外部需求/计划文件，先调用 `gsd-import` 进行冲突检测。
- 调用 `superpowers:brainstorming` 与 PM 一起探索 2-3 种可能的需求视角，列出 trade-offs。  
  **在 PM 明确选择方向前，禁止继续生成需求文档。**

## Steps

1. Read `{process_slug}/interviews/<session-id>/transcript.md`, `summary.md`, and `raw-insights.md`.
2. Draft an initial `{process_slug}/pages/docs/requirements.html` using the Markdown-first renderer. Prefer free-form Markdown with big sections over rigid YAML structures when that makes the requirement clearer:

   ```bash
   python scripts/lincoln_render.py \
     --stage clarify \
     --target {process_slug}/pages/docs/requirements.html \
     --title "需求文档" \
     --markdown {process_slug}/pages/docs/requirements.md
   ```

   Write `{process_slug}/pages/docs/requirements.md` as a regular Markdown document. Use H2 headings for the major chapters (e.g. `## 背景`, `## 问题`, `## 用户`, `## 方案`, `## 验收标准`, `## 非目标`, `## 开放问题`). Within each chapter you may use paragraphs, bullet lists, tables, and ` ```mermaid ` diagrams freely. If a rigid table (e.g. a user-story table) is clearer, you may still create a YAML `--data` file and use `page-doc-structured.html.tpl`.

   The renderer will derive `nav-label`, `version`, and `uid` automatically if omitted. Include `<!-- version: v1.0 -->` near the top of the Markdown file.
3. Perform a stakeholder analysis and produce `{process_slug}/pages/docs/stakeholders.html`.

   First, check whether `{process_slug}/research/{session_id}/stakeholders.md` already exists from the `pm-research` workflow. If it does, read it and use it as a starting point rather than starting from scratch.

   Identify all stakeholders that are relevant to the requirement. For each stakeholder, capture at least the following dimensions in a structured table:

   | Dimension | Description |
   |-----------|-------------|
   | 角色名称 | A concise role label (e.g., 最终用户, 需求提出方, 建设方, 运营方, 成本承担方, 方向决策者, 影响者/守门人). |
   | 具体是谁 | The actual person, team, or group, if known. |
   | 与需求的关系 | How they interact with the product or requirement. |
   | 权力/影响力 | Their ability to affect decisions or outcomes (高/中/低 + 一句话说明). |
   | 利益诉求 | What they want from this product or requirement. |
   | 经济价值 | Monetary, efficiency, or cost-related value they gain or lose. |
   | 情绪价值 | Emotional or experiential value (e.g., 愉悦感, 安全感, 掌控感, 归属感). |
   | 个人实现价值 | Self-actualization value (e.g., 成长, 成就感, 认同感, 影响力). |
   | 心理预期 | Their implicit expectations, anxieties, or assumptions. |
   | 潜在冲突 | Tensions or misalignments with other stakeholders. |
   | 应对策略 | How the product team should engage or satisfy this stakeholder. |

   Also capture stakeholder relationships: who depends on whom, who can block whom, and who shares goals.

   Render the artifact:

   ```bash
   python scripts/lincoln_render.py \
     --stage clarify \
     --target {process_slug}/pages/docs/stakeholders.html \
     --title "相关者分析" \
     --markdown {process_slug}/pages/docs/stakeholders.md
   ```

   Write `{process_slug}/pages/docs/stakeholders.md` as a regular Markdown document with H2 chapters such as `## 相关者清单`, `## 关系与冲突`, `## 关键洞察`, `## 开放问题`. Include `<!-- version: v1.0 -->` near the top.
4. Identify 1-3 ambiguities or missing details, and tag each with its Johari quadrant (认知象限): 知道自己知道 → 复述确认题; 知道自己不知道 → 直接回答 + coach; 不知道自己知道 → 展示已有资产; 不知道自己不知道 → 探查题.
5. Ask the human PM these questions one batch at a time in the terminal, using the quadrant-appropriate style.
6. Update `requirements.md` and `stakeholders.md` based on the answers and re-render both `requirements.html` and `stakeholders.html` (always rewrite the Markdown source and re-render; do not mutate HTML in-place).
7. Repeat until the PM confirms the requirements are clear.
8. Also generate `{process_slug}/pages/docs/user-stories.html`. You may either write a Markdown file or use the structured renderer with `--data` containing a `stories` array, whichever fits the material:

   ```bash
   python scripts/lincoln_render.py \
     --stage clarify \
     --target {process_slug}/pages/docs/user-stories.html \
     --title "用户故事" \
     --markdown {process_slug}/pages/docs/user-stories.md
   ```

9. 需求清晰度六问自检（Six-Question Gate）。起草原稿前逐项回答，答案落入 PRD 对应章节；任何一项答不出，先按 Human Interaction Rules 问人类 PM，禁止带着未决问题落笔：

   | 六问 | 落笔位置 | 答不出时的动作 |
   |---|---|---|
   | 用户有哪些？ | 用户故事 | 请 PM 补充分角色 |
   | 场景是什么？何时触发、如何完成？ | 业务流程图 | 与 PM 走查主流程 |
   | 边界在哪里？明确不做什么 | 需求背景（非目标）+ 业务规则 | 请 PM 划定非目标 |
   | 如何管异常？覆盖每个失败的系统行为 | 业务规则（异常处理） | 逐场景请 PM 裁决 |
   | 如何体验好？质量与体验判据 | 非功能需求（体验要求） | 请 PM 给出体验判据 |
   | 最终谁决策？ | 版本说明（决策人） | 请 PM 指定决策人 |
10. Generate the root-level PRD at `{process_slug}/pages/docs/prd.html` using the Markdown-first renderer:

   ```bash
   python scripts/lincoln_render.py \
     --stage clarify \
     --target {process_slug}/pages/docs/prd.html \
     --title "产品需求文档" \
     --markdown {process_slug}/pages/docs/prd.md
   ```

   New PRDs default to the **core-v2 content contract**. Put both markers near the top of `{process_slug}/pages/docs/prd.md`:

   ```markdown
   <!-- prd-contract: core-v2 -->
   <!-- version: v1.0 -->
   ```

   Keep all fifteen chapters below in this order. Answer the business question in every chapter with reviewed evidence and decisions; a heading, empty table or placeholder is not content. Section headings are matched by name — numbering is cosmetic. Additional appendices may follow the core chapters, and `docs/prd-quality-standard.md` defines evidence-based tailoring without removing required business answers.

   - `## 1. 版本说明` — 当前版本、文档状态、决策人、目标发布时间与读者。
   - `## 2. 修订记录` — 版本/日期/作者/变更摘要表格，能解释基线为何变化。
   - `## 3. 执行摘要` — 为谁解决什么问题、首版方案、业务价值和发布时间。
   - `## 4. 问题与证据` — 问题发生频率、影响、现状基线，以及可追溯的访谈/日志/数据证据；区分事实与假设。
   - `## 5. 用户与相关者` — 用户任务、收益方、运营方、守门人、决策人及其冲突。
   - `## 6. 目标与成功指标` — 至少一张指标表，固定包含 `指标 | 基线 | 目标值 | 时间窗 | 口径/来源`；每项都写具体值，不能只写“提升”“优化”。
   - `## 7. 范围与非目标` — 分别用 `### 范围` 和 `### 非目标` 写明首版边界；非目标说明明确不做什么，避免研发和设计自行扩张。
   - `## 8. 用户故事` — 分角色描述触发场景、任务与收益，并能关联到需求 ID。
   - `## 9. 功能需求` — 每条核心需求拥有稳定且唯一的 `REQ-001` 格式 ID，描述用户可观察行为、优先级和业务结果，而非实现方案。
   - `## 10. 业务流程与规则` — 主流程、分支、异常、权限和状态变化；必要时使用 Mermaid，但文字必须能独立回答规则。
   - `## 11. 验收标准` — 使用包含 `验收 ID | 需求 ID | Given | When | Then` 的表格；每条验收拥有稳定且唯一的 `AC-001` 格式 ID，同行引用已定义的 `REQ-NNN`，且每条核心需求至少有一条验收。
   - `## 12. 非功能需求` — 性能、安全、可用性、兼容性和可观测性的可验证阈值及口径。
   - `## 13. 依赖与发布` — 内外部依赖、灰度/全量条件、迁移、回滚和运营准备。
   - `## 14. 风险与开放问题` — 风险责任人、缓解动作和已决问题；关键开放问题必须在 Human Gate 前由有权者裁决，不留占位符。
   - `## 15. 相关产物链接` — 证据、原型和测试入口；结构化追溯固定链接到 `{process_slug}/pages/docs/prd-traceability.yaml`，分角色评审固定链接到 `{process_slug}/pages/docs/prd-review.yaml`。本步骤只引用这些路径，不在 PRD 内复制 sidecar 内容。

   ID 与追溯纪律：`REQ-NNN` 和 `AC-NNN` 在修订中保持稳定，不复用已删除 ID；验收对需求的引用与 `{process_slug}/pages/docs/prd-traceability.yaml` 使用同一组 ID，四方评审对 `{process_slug}/pages/docs/prd-review.yaml` 中同一 PRD 版本生效。只记录已经由证据或评审确认的关系，不编造批准或来源。

   Legacy compatibility: only pre-existing documents without the core-v2 marker continue to use the legacy 13-chapter structural contract. Do not remove a core-v2 marker or downgrade a new PRD to bypass semantic checks.

   PRD 正文禁则（读者是研发团队，文档只讲业务场景）：
   - 不写技术调研、技术方案、架构设计、接口设计、数据库设计等内容——这类内容只进 design 阶段维护的归档页 `feasibility.html`。
   - 不写任何过程性提醒（"待确认""待人类 PM 确认""TODO"、agent 注等）——疑问在对话中解决，解决后才落文档。
   - 同一信息只用一种方式描述：文字、表格、mermaid 图组合使用，但不重复表达同一内容。

   It must also carry:
   - `<!-- version: v1.0 -->` marker (added automatically by the renderer from the Markdown file or `--version`).
   - Meta tags: `doc-title`, `nav-group="Docs"`, `doc-version="v1.0"`, and a stable `doc-uid` (all injected by the renderer).
11. Run the deterministic content-quality check and fix every reported chapter, metric or ID error before asking for approval:

   ```bash
   python scripts/lincoln_prd_quality.py {process_slug}/pages/docs/prd.md --mode core-v2
   ```

   This check is necessary but not sufficient: walk the evidence, scope, rules and acceptance examples with the human PM rather than treating a passing CLI result as team approval.
12. For core-v2, create `{process_slug}/pages/docs/prd-traceability.yaml` using `.claude/schemas/prd-traceability.schema.json`. Each core requirement records its current `prd_version`, stable REQ ID, evidence `sources`, `story_ids` and `acceptance_criterion_ids`; leave flow/prototype/test arrays for their owning stages. Validate the requirements baseline:

   ```bash
   python scripts/lincoln_traceability.py --package {process_slug} --stage clarify
   ```

   Legacy packages do not need to backfill this sidecar; their existing structural and snapshot gates remain unchanged.
13. When the PM confirms, add an approval marker inside `requirements.html`: `<!-- status: approved -->`.
14. After human approval, run `python scripts/lincoln_prd.py freeze` to create the immutable requirements-baseline snapshot `{process_slug}/pages/docs/snapshots/prd-v1.0.html`.
15. Run `python scripts/stage_loader.py --stage clarify --action record-artifacts` to persist the artifact paths and refresh `{process_slug}/assets/js/package-data.js`.

## Human Interaction Rules

- Ask at most 3 questions per turn.
- After each answer, update the document and show the changed sections.
- If the PM edits `requirements.html`, `stakeholders.html`, or `prd.html` directly and runs `workflow-continue`, re-read the file and continue from there.
- Do not proceed to the next step until the PM explicitly confirms (e.g., says "confirm" or "确认").

## 页面纪律

- Every document page opens with `## 页面意图` (目标读者 + 本页回答什么问题) and `## 边界` (本页不覆盖什么 + 单一事实来源链接).
- Content follows standard Markdown: a single H1, H2 chapters, and tables/Mermaid over long prose. Never duplicate content across pages — link to the single source of truth instead.
- These pages are business-facing: 需求背景、用户角色、旅程、业务状态、业务流程、验收标准. Technical research or solution comparisons performed while clarifying are only background for the PM's decision — do not register them into any page; they may be summarized later into the archived `feasibility.html` by the design stage.
- 过程性内容不进入任何页面：待确认事项、agent 提醒、对话记录只留在对话里，解决后才以结论形式落文档。
- 同一信息只描述一次：文字、表格、mermaid 图可以组合使用，但不得用多种方式重复表达同一内容；需要引用时链接到单一事实来源。

## 认知象限确认（Johari）

澄清问题按 Johari 四象限设计与标注：

| 象限 | 问题风格 |
|------|----------|
| 知道自己知道 | 复述确认题：用你的话复述需求，防止会错意 |
| 知道自己不知道 | 直接回答 + coach：先给背景与选项，不反问 |
| 不知道自己知道 | 展示已有资产：引用 knowledge/、issues、既有文档中已有的答案 |
| 不知道自己不知道 | 探查题：用具体场景暴露用户未意识到的风险与缺失 |

出口条件（两条都满足才允许进入下一阶段）：

1. 每个开放问题都有明确的验收标准答案（用户认可的"怎样算完成"）。
2. 执行路径已确定（下一步产物、负责角色、进入哪个阶段）。

## Output Artifacts

- `{process_slug}/pages/docs/requirements.html`
- `{process_slug}/pages/docs/stakeholders.html`
- `{process_slug}/pages/docs/user-stories.html`
- `{process_slug}/pages/docs/prd.html` (root-level PRD, versioned)
- `{process_slug}/pages/docs/snapshots/prd-v1.0.html` (immutable snapshot after approval)
- `{process_slug}/pages/docs/prd-traceability.yaml` (required for core-v2, optional for legacy)

## Traceability

Every requirement must reference the transcript timestamp where it originated, e.g., `(来源: 00:03:22)`.

## Next Step

After confirmation and snapshot freeze, tell the user the clarify stage is complete and the next stage is `product-design-docs`.
