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

9. Generate the root-level PRD at `{process_slug}/pages/docs/prd.html` using the Markdown-first renderer:

   ```bash
   python scripts/lincoln_render.py \
     --stage clarify \
     --target {process_slug}/pages/docs/prd.html \
     --title "产品需求文档" \
     --markdown {process_slug}/pages/docs/prd.md
   ```

   Write `{process_slug}/pages/docs/prd.md` with at least these H2 chapters, but feel free to add, merge, or reorder them to best tell the story:

   - `## 1. 需求背景`
   - `## 2. 用户故事`
   - `## 3. 功能拆解`
   - `## 4. 业务流程图` (use ` ```mermaid ` diagrams)
   - `## 5. 验收标准`
   - `## 6. 业务规则`
   - `## 7. 非功能需求`
   - `## 8. 关联系统/接口`
   - `## 9. 相关产物链接`
   - `## 10. 风险与开放问题`

   It must also carry:
   - `<!-- version: v1.0 -->` marker (added automatically by the renderer from the Markdown file or `--version`).
   - Meta tags: `doc-title`, `nav-group="Docs"`, `doc-version="v1.0"`, and a stable `doc-uid` (all injected by the renderer).
10. When the PM confirms, add an approval marker inside `requirements.html`: `<!-- status: approved -->`.
11. After human approval, run `python scripts/lincoln_prd.py freeze` to create the immutable snapshot `{process_slug}/pages/docs/snapshots/prd-v1.0.html`.
12. Run `python scripts/stage_loader.py --stage clarify --action record-artifacts` to persist the artifact paths and refresh `{process_slug}/assets/js/package-data.js`.

## Human Interaction Rules

- Ask at most 3 questions per turn.
- After each answer, update the document and show the changed sections.
- If the PM edits `requirements.html`, `stakeholders.html`, or `prd.html` directly and runs `workflow-continue`, re-read the file and continue from there.
- Do not proceed to the next step until the PM explicitly confirms (e.g., says "confirm" or "确认").

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
