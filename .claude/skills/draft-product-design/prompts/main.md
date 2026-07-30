# draft-product-design

You are executing the Lincoln workflow step `product-design-docs`: turn approved requirements into a concise product design review package for the human PM.

## Goal

Create `{process_slug}/pages/docs/` HTML design documents with enough product, data, flow, feasibility, and technical framing for PM review and later development planning, without creating unnecessary review burden.

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
3. Produce the design package under `{process_slug}/pages/docs/` using `.claude/templates/issue-package/page-doc.html.tpl`. Each page embeds Markdown in `<script type="text/markdown" id="docSource">` with a `<!-- version: v1.0 -->` marker and meta tags (`doc-title`, `nav-group`, `doc-version`, `doc-uid`):
   - `design-review.html`: PM-facing entry point with decision summary, scope, links to all design docs, open questions, and approval checklist.
   - `scenarios.html`: target users, primary scenarios, boundary scenarios, and non-goals.
   - `feature-catalog.html`: concise feature list, priority, acceptance mapping, and source requirement links.
   - `data-model.html`: core entities, fields, constraints, validation rules, and state transitions.
   - `flows.html`: Mermaid user flow, business flow, screen flow, sequence diagram, and architecture diagram.
   - `page-map.html`: page inventory, page relationships, navigation, and routing/state notes.
   - `feasibility.html`: business feasibility, technical feasibility, current official framework/library options, usable open-source projects, risks, and recommended stack.
   - `version-log.html`: design decision version history and rationale.
   - `api-list.html`: internal and external APIs/data contracts the feature depends on.
4. Create the PM→UX handoff contract at `{process_slug}/handoffs/pm-to-ux/pm-to-ux.handoff.yaml` referencing the approved design docs and PRD versions.
5. Keep all documents traceable to the approved requirement and transcript timestamps where available.
6. Update the root `{process_slug}/pages/docs/prd.html` section 9 "相关产物链接" with links to the new design documents. If the PRD already has an approved snapshot (`pages/docs/snapshots/prd-v*.html`), warn the PM that any content change requires bumping the version marker and re-freezing via `python scripts/lincoln_prd.py freeze`.
7. Ask the PM to review `design-review.html` and linked docs (they can open `{process_slug}/index.html` in a browser).
8. When the PM confirms, add `<!-- status: approved -->` to `design-review.html`.
9. Run `python scripts/stage_loader.py --stage product-design-docs --action record-artifacts`.

## Rules

- Use Chinese for PM-facing content unless the requirements are in English.
- Keep documents short and reviewable; prefer tables and Mermaid diagrams over long prose.
- For technical frameworks and open-source projects, check current official docs or primary repositories before recommending.
- Do not create a Pencil prototype in this step.
- After approval, tell the user to run: `claude build-product-prototype <session_id> <design_id>`.
