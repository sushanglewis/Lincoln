# draft-product-design

You are executing the Lincoln workflow step `product-design-docs`: turn approved requirements into a concise product design review package (a set of HTML documents) for the human PM.

## Goal

Create `{process_slug}/pages/docs/` HTML design documents with enough product, data, flow, feasibility, and technical framing for PM review and later development planning, without creating unnecessary review burden. This step does **not** produce UI specs, field specs, or prototypes — those belong to the next stage `product-prototype`.

## Input

- `session_id`: the interview session identifier
- `design_id`: a kebab-case product design identifier

## 子技能准备

在执行本 prompt 前：
1. 调用 `superpowers:brainstorming` 探索 ≥2 种设计方向并说明 trade-offs，等待 PM 确认。
2. PM 确认后，调用 `superpowers:writing-plans` 规划文档文件结构与每份文档的职责。

## Steps

1. Validate that `{process_slug}/pages/docs/requirements.html` is approved (contains `<!-- status: approved -->`).
2. Read `{process_slug}/pages/docs/requirements.html`, `user-stories.html`, and the root-level `{process_slug}/pages/docs/prd.html`.
3. Produce the design package under `{process_slug}/pages/docs/`. Use the Markdown-first template for narrative documents and the structured template only when a fixed table is clearer.

   Default to Markdown for: `design-review`, `scenarios`, `feasibility`, `version-log`.
   Use structured data (`--data`) only when a rigid table is genuinely better: `feature-catalog`, `data-model`, `page-map`, `api-list`.
   For `flows`, prefer a Markdown file with ` ```mermaid ` diagrams.

   Simplified single-page command:
   ```bash
   python scripts/lincoln_render.py \
     --stage product-design-docs \
     --target issue-<N>/pages/docs/<page>.html \
     --title "<标题>" \
     --markdown issue-<N>/pages/docs/<page>.md
   ```

   You can also render the whole missing package in one call:
   ```bash
   python scripts/lincoln_render.py \
     --render-stage \
     --stage product-design-docs \
     --state-file issue-<N>/workflow-stage.yaml
   ```
   This creates only the pages that do not yet exist. If a matching `.md` file exists, it is used automatically; otherwise the page is created empty for you to fill afterwards.

   Page-specific guidance:
   - `design-review.md`: H2 chapters such as `## 决策摘要`, `## 范围`, `## 链接`, `## 开放问题`, `## 审批清单`.
   - `scenarios.md`: `## 主要场景`, `## 边界场景`, `## 非目标`, plus persona descriptions and Mermaid flowcharts.
   - `feature-catalog.md`: either a Markdown table or a YAML `features` array.
   - `data-model.md`: either Markdown entity sections or a YAML `entities` array.
   - `flows.md`: Markdown with ` ```mermaid ` flowcharts and numbered step lists.
   - `page-map.md`: either a Markdown table or a YAML `pages` array.
   - `feasibility.md`: H2 chapters such as `## 风险`, `## 方案对比`, `## 建议`.
   - `version-log.md`: H2 chapters plus a Markdown table of version entries.
   - `api-list.md`: either a Markdown table or a YAML `apis` array.
4. Create the PM→UX handoff contract at `{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml` referencing the approved design docs and PRD versions.
5. Create the human-readable PM→UX handoff portal page at `{process_slug}/pages/docs/handoff-pm-to-ux-v1.0.html` and the narrative master handoff document at `{process_slug}/handoffs/pm-to-ux/master-handoff-pm-to-ux-v1.0.md`. These summarize core decisions, scope, open questions, and the context pack for the receiving UX Agent.
6. Keep all documents traceable to the approved requirement and transcript timestamps where available.
7. Update the root `{process_slug}/pages/docs/prd.html` section 9 "相关产物链接" with links to the new design documents and handoff artifacts. If the PRD already has an approved snapshot (`pages/docs/snapshots/prd-v*.html`), warn the PM that any content change requires bumping the version marker and re-freezing via `python scripts/lincoln_prd.py freeze`.
8. Ask the PM to review `design-review.html` and linked docs (they can open `{process_slug}/index.html` in a browser).
9. When the PM confirms, add `<!-- status: approved -->` to `design-review.html`.
10. Run `python scripts/stage_loader.py --stage product-design-docs --action record-artifacts`.

## Rules

- Use Chinese for PM-facing content unless the requirements are in English.
- Keep documents short and reviewable; prefer tables and Mermaid diagrams over long prose.
- For technical frameworks and open-source projects, check current official docs or primary repositories before recommending.
- Do not create UI specs, field specs, or prototypes in this step. Those are produced in the next stage `product-prototype`.
- Do not create a Pencil prototype in this step.
- After approval, tell the user to run: `claude build-product-prototype <session_id> <design_id>`.
