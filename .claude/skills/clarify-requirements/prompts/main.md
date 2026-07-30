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
2. Draft an initial `{process_slug}/pages/docs/requirements.html` using `.claude/templates/issue-package/page-doc.html.tpl`. Embed the Markdown source in the `<script type="text/markdown" id="docSource">` block and include a `<!-- version: v1.0 -->` marker. Required sections:
   - `背景`
   - `问题`
   - `用户`
   - `方案`
   - `验收标准`
   - `非目标`
   - `开放问题`
3. Identify 1-3 ambiguities or missing details, and tag each with its Johari quadrant (认知象限): 知道自己知道 → 复述确认题; 知道自己不知道 → 直接回答 + coach; 不知道自己知道 → 展示已有资产; 不知道自己不知道 → 探查题.
4. Ask the human PM these questions one batch at a time in the terminal, using the quadrant-appropriate style.
5. Update `requirements.html` based on the answers (always rewrite the full file; do not mutate in-place).
6. Repeat until the PM confirms the requirements are clear.
7. Also generate `{process_slug}/pages/docs/user-stories.html` from the finalized requirements using the same doc-page template.
8. Generate the root-level PRD at `{process_slug}/pages/docs/prd.html` using `.claude/templates/issue-package/page-doc.html.tpl`. It must include:
   - `<!-- version: v1.0 -->` marker inside the `docSource` block.
   - Meta tags: `doc-title`, `nav-group="Docs"`, `doc-version="v1.0"`, and a stable `doc-uid`.
   - All required sections: 1.需求背景, 2.用户故事, 3.功能拆解, 4.业务流程图, 5.验收标准, 6.业务规则, 7.非功能需求, 8.关联系统/接口, 9.相关产物链接, 10.风险与开放问题.
   - A links table in section 9 pointing to interviews, requirements.html, user-stories.html, and downstream design/prototype/OpenSpec artifacts.
9. When the PM confirms, add an approval marker inside `requirements.html`: `<!-- status: approved -->`.
10. After human approval, run `python scripts/lincoln_prd.py freeze` to create the immutable snapshot `{process_slug}/pages/docs/snapshots/prd-v1.0.html`.
11. Run `python scripts/stage_loader.py --stage clarify --action record-artifacts` to persist the artifact paths and refresh `{process_slug}/assets/js/package-data.js`.

## Human Interaction Rules

- Ask at most 3 questions per turn.
- After each answer, update the document and show the changed sections.
- If the PM edits `requirements.html` or `prd.html` directly and runs `workflow-continue`, re-read the file and continue from there.
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
- `{process_slug}/pages/docs/user-stories.html`
- `{process_slug}/pages/docs/prd.html` (root-level PRD, versioned)
- `{process_slug}/pages/docs/snapshots/prd-v1.0.html` (immutable snapshot after approval)

## Traceability

Every requirement must reference the transcript timestamp where it originated, e.g., `(来源: 00:03:22)`.

## Next Step

After confirmation and snapshot freeze, tell the user the clarify stage is complete and the next stage is `product-design-docs`.
