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

   Write `{process_slug}/pages/docs/prd.md` following this progressive skeleton. Keep all thirteen chapters in this order as the default narrative; you may insert additional business chapters inside the skeleton when this requirement's shape calls for it. Section headings are matched by name — numbering is cosmetic, not part of the contract:

   - `## 1. 版本说明` — 当前版本、文档状态、决策人（最终谁拍板）。
   - `## 2. 修订记录` — 版本/日期/作者/变更摘要 表格。
   - `## 3. 功能列表` — 功能/优先级/状态/对应用户故事 表格。
   - `## 4. 需求背景`
   - `## 5. 用户故事`
   - `## 6. 功能拆解`
   - `## 7. 业务流程图` (use ` ```mermaid ` diagrams)
   - `## 8. 验收标准`
   - `## 9. 业务规则`（边界与异常处理）
   - `## 10. 非功能需求`（含体验要求）
   - `## 11. 关联系统/接口`
   - `## 12. 相关产物链接`
   - `## 13. 风险与开放问题`

   PRD 正文禁则（读者是研发团队，文档只讲业务场景）：
   - 不写技术调研、技术方案、架构设计、接口设计、数据库设计等内容——这类内容只进 design 阶段维护的归档页 `feasibility.html`。
   - 不写任何过程性提醒（"待确认""待人类 PM 确认""TODO"、agent 注等）——疑问在对话中解决，解决后才落文档。
   - 同一信息只用一种方式描述：文字、表格、mermaid 图组合使用，但不重复表达同一内容。

   It must also carry:
   - `<!-- version: v1.0 -->` marker (added automatically by the renderer from the Markdown file or `--version`).
   - Meta tags: `doc-title`, `nav-group="Docs"`, `doc-version="v1.0"`, and a stable `doc-uid` (all injected by the renderer).
11. When the PM confirms, add an approval marker inside `requirements.html`: `<!-- status: approved -->`.
12. After human approval, run `python scripts/lincoln_prd.py freeze` to create the immutable snapshot `{process_slug}/pages/docs/snapshots/prd-v1.0.html`.
13. Run `python scripts/stage_loader.py --stage clarify --action record-artifacts` to persist the artifact paths and refresh `{process_slug}/assets/js/package-data.js`.

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

## Traceability

Every requirement must reference the transcript timestamp where it originated, e.g., `(来源: 00:03:22)`.

## Next Step

After confirmation and snapshot freeze, tell the user the clarify stage is complete and the next stage is `product-design-docs`.
