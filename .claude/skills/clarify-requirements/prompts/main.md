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
2. Draft an initial `{process_slug}/pages/docs/requirements.html` using `python scripts/lincoln_render.py --stage clarify --target {process_slug}/pages/docs/requirements.html --title "需求文档" --nav-label "需求" --version v1.0 --uid requirements --data {process_slug}/pages/docs/requirements.yaml`. The YAML data file should follow this schema:

   ```yaml
   intro: "一句话概括本需求。"
   annotations:
     doc-purpose: "说明本次需求要解决的核心问题"
     doc-layout: "单页文档"
     doc-stories: "作为 <角色> 我想要 <目标> 以便 <价值>"
     doc-rules: "列出关键业务规则"
     doc-boundaries: "列出边界情况"
     doc-exceptions: "列出异常流"
   sections:
     - title: "背景"
       content: "..."
     - title: "问题"
       content: "..."
     - title: "用户"
       content: "..."
     - title: "方案"
       content: "..."
     - title: "验收标准"
       content: "..."
     - title: "非目标"
       content: "..."
     - title: "开放问题"
       content: "..."
   ```

   The renderer will inject the YAML as `pageData` and render structured sections automatically. You may also pass `--markdown` for a free-form supplement.
3. Identify 1-3 ambiguities or missing details, and tag each with its Johari quadrant (认知象限): 知道自己知道 → 复述确认题; 知道自己不知道 → 直接回答 + coach; 不知道自己知道 → 展示已有资产; 不知道自己不知道 → 探查题.
4. Ask the human PM these questions one batch at a time in the terminal, using the quadrant-appropriate style.
5. Update `requirements.html` based on the answers (always rewrite the full file; do not mutate in-place).
6. Repeat until the PM confirms the requirements are clear.
7. Also generate `{process_slug}/pages/docs/user-stories.html` from the finalized requirements using the structured renderer with `--data` containing a `stories` array:

   ```yaml
   intro: "基于已确认需求提炼的用户故事清单。"
   annotations:
     doc-purpose: "用户故事全景"
   stories:
     - who: "作为 访客用户"
       want: "我想要 通过微信扫码登录"
       so: "以便 不用注册密码"
       acceptance: "扫码后 3 秒内完成登录"
       source: "prd#section-2"
   ```

8. Generate the root-level PRD at `{process_slug}/pages/docs/prd.html` using the structured renderer with `--stage clarify --uid prd`. The data YAML must include `intro`, `annotations`, and `sections` for the 10 required PRD sections:

   ```yaml
   intro: "一句话 PRD 概述。"
   annotations:
     doc-purpose: "XXX 产品需求文档"
     doc-stories: "..."
     doc-rules: "..."
     doc-boundaries: "..."
     doc-exceptions: "..."
     doc-refs: "requirements.html | user-stories.html"
   sections:
     - title: "1. 需求背景"
       content: "..."
     - title: "2. 用户故事"
       content: "..."
     - title: "3. 功能拆解"
       content: "..."
     - title: "4. 业务流程图"
       content: "..."
     - title: "5. 验收标准"
       content: "..."
     - title: "6. 业务规则"
       content: "..."
     - title: "7. 非功能需求"
       content: "..."
     - title: "8. 关联系统/接口"
       content: "..."
     - title: "9. 相关产物链接"
       content: "| 产物 | 路径 | 状态 |"
     - title: "10. 风险与开放问题"
       content: "..."
   ```

   It must also carry:
   - `<!-- version: v1.0 -->` marker (added automatically by the renderer from `--version`).
   - Meta tags: `doc-title`, `nav-group="Docs"`, `doc-version="v1.0"`, and a stable `doc-uid` (all injected by the renderer).
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
