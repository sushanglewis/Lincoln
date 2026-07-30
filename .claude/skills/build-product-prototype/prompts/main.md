# build-product-prototype

You are executing the Lincoln workflow step `product-prototype`: turn approved product design documents into UI/field specifications and a prototype.

## Goal

Create field and UI specifications as HTML doc pages, and produce a Pencil prototype (and optional interactive HTML prototype) that the PM can inspect and developers can use later.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier

## Steps

1. Verify `{process_slug}/pages/docs/design-review.html` contains `<!-- status: approved -->` or `[x] PM 已确认设计文档`.
2. Read the approved design package under `{process_slug}/pages/docs/`, including `flows.html` and `page-map.html`.
3. Write `{process_slug}/pages/docs/fields.html` using `.claude/templates/issue-package/page-doc.html.tpl` with screen/form fields, data type, required/optional status, validation, default value, copy, error state, and source data object.
4. Write `{process_slug}/pages/docs/ui-spec.html` covering the interaction-document delivery standards:
   - 用户场景与流程: who, when, goal, trigger, completion criteria.
   - 界面流转图: screen-to-screen flow mapped to the business flow in `flows.html`.
   - 页面交互说明: per-screen layout elements, interaction rules (events, responses, navigation), and field validation/error handling.
   - 交互 Demo/原型: link to `prototype.pen` and summarize key interactions.
5. Optionally create interactive HTML prototypes under `{process_slug}/pages/prototype/{web,mobile,overlays}/` using `.claude/templates/issue-package/page-prototype.html.tpl`. Every interactive element must carry a stable `data-uid`.
6. Use Pencil tools to create or update `{process_slug}/designs/<design_id>/prototype.pen` as a clickable prototype that realizes the screen flow and key interactions.
7. Before using Pencil tools, call `get_editor_state(include_schema: true)` if the current `.pen` schema is not already known.
8. After generating the prototype, use `snapshot_layout` to check for clipped or overlapping elements. Fix layout issues before asking for review.
9. Update the root `{process_slug}/pages/docs/prd.html` section 9 "相关产物链接" with the `ui-spec.html`, `fields.html`, and `prototype.pen` links. If the PRD already has an approved snapshot, warn the PM that changes require a version bump and re-freeze via `python scripts/lincoln_prd.py freeze`.
10. Ask the PM to open and edit `{process_slug}/designs/<design_id>/prototype.pen` in Pencil. Treat the saved `.pen` as the final development reference.
11. When the PM confirms the prototype, add `<!-- prototype-status: approved -->` to `ui-spec.html`.
12. Run `python scripts/stage_loader.py --stage product-prototype --action record-artifacts`.

## Output Artifacts

- `{process_slug}/pages/docs/fields.html`
- `{process_slug}/pages/docs/ui-spec.html`
- `{process_slug}/designs/<design_id>/prototype.pen`
- `{process_slug}/pages/prototype/**/*.html` (optional interactive prototypes)

## Rules

- Never read or modify `.pen` files with normal file tools; use Pencil tools or the Pencil application only.
- Do not rely on screenshots or static HTML as the main approval artifact. They are optional review aids only.
- Keep controls and states complete enough for implementation: default, hover/focus where relevant, disabled, empty, loading, error, and success.
- After approval, tell the user to run: `claude plan-tdd-development <session_id> <design_id>`.
