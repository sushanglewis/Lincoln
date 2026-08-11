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
3. Produce the design package under `{process_slug}/pages/docs/` using `python scripts/lincoln_render.py --stage product-design-docs --target <path> --data <yaml>`. Each page uses the structured doc template; provide a YAML data file with `intro`, `annotations`, and the domain-specific keys below. The renderer injects the annotation metas (`doc-purpose`, `doc-layout`, `doc-fields`, `doc-boundaries`, `doc-exceptions`, plus `doc-stories`, `doc-rules`, `doc-refs` when useful) so the portal right panel explains functionality, layout, fields, boundary cases, and exception flows.

   Common command pattern:
   ```bash
   python scripts/lincoln_render.py \
     --stage product-design-docs \
     --target issue-<N>/pages/docs/<page>.html \
     --title "<标题>" --nav-label "<导航标签>" --version v1.0 --uid <uid> \
     --data issue-<N>/pages/docs/<page>.yaml
   ```

   Page-specific data keys:
   - `design-review.html`: `sections` (decision summary, scope, links, open questions, approval checklist).
   - `scenarios.html`: `sections` plus optional `personas`, `primary`, `boundary`, `non_goals` arrays.
   - `feature-catalog.html`: `features` array (`id`, `title`, `priority`, `acceptance`, `source`).
   - `data-model.html`: `entities` array (`name`, `fields`, `constraints`, `states`).
   - `flows.html`: `flows` array (`name`, `type`, `mermaid`, `steps`).
   - `page-map.html`: `pages` array (`id`, `title`, `path`, `links`, `notes`).
   - `feasibility.html`: `sections` plus `risks` and `options` arrays.
   - `version-log.html`: `sections` plus `entries` array (`version`, `date`, `author`, `changes`, `rationale`).
   - `api-list.html`: `apis` array (`name`, `method`, `endpoint`, `purpose`, `contract`).
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
