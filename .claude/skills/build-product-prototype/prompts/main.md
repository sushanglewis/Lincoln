# build-product-prototype

You are executing the Lincoln workflow step `product-prototype`: turn approved product design documents into UI/field specifications and an interactive HTML prototype.

## Goal

Create field and UI specifications as HTML doc pages, and produce a high-fidelity interactive HTML prototype that the PM can inspect directly in the issue-package portal (`{process_slug}/index.html`). A Pencil prototype is optional; the HTML prototype is the primary review artifact.

## Reference templates

Use the following read-only templates as the style/layout reference. Copy/adapt them into the issue package; do not modify the templates themselves.

- `.claude/templates/issue-package/page-prototype.html.tpl` — minimal starter page.
- `.claude/templates/issue-package/prototypes/main/page.html.tpl` — main app window with sidebar + WebView placeholder.
- `.claude/templates/issue-package/prototypes/onboarding/page.html.tpl` — login/onboarding card.
- `.claude/templates/issue-package/prototypes/settings/page.html.tpl` — two-column settings page.
- `.claude/templates/issue-package/prototypes/overlays/page.html.tpl` — avatar menu / about / toast overlays.
- `.claude/templates/issue-package/prototypes/tray/page.html.tpl` — system-tray simulation.
- `.claude/templates/issue-package/prototypes/org/page.html.tpl` — organization list.
- `.claude/templates/issue-package/assets/prototype.css` — shared styles (tokens, window shell, sidebar, forms, overlays).
- `.claude/templates/issue-package/assets/prototype.js` — shared UI builders and mock data (`window.LincolnPrototype`).

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
   - 交互 Demo/原型: links to the HTML prototype pages under `pages/prototype/` and a summary of key interactions.
5. Create interactive HTML prototypes under `{process_slug}/pages/prototype/{main,onboarding,settings,overlays,tray,org}/` by adapting the reference templates above. Every page must:
   - Link to `../../../assets/prototype.css` and `../../../assets/prototype.js`.
   - Include the `<meta name="prototype-base" content="../../../">` tag.
   - Include `<meta name="page-uid" content="...">` and `<meta name="nav-group" content="...">`.
   - Assign a stable `data-uid` attribute to every interactive element, screen region, and WebView placeholder.
   - Override `LincolnPrototype.data` in the page script for issue-specific mock data (user, org, webviews, settings, unread items).
6. Optionally create or update `{process_slug}/designs/<design_id>/prototype.pen` with Pencil tools if the PM explicitly asks for a Pencil prototype. If you use Pencil tools, call `get_editor_state(include_schema: true)` first and use `snapshot_layout` to check for clipping/overlap.
7. Update the root `{process_slug}/pages/docs/prd.html` section 9 "相关产物链接" with the `ui-spec.html`, `fields.html`, and HTML prototype links. If the PRD already has an approved snapshot, warn the PM that changes require a version bump and re-freeze via `python scripts/lincoln_prd.py freeze`.
8. Ask the PM to open `{process_slug}/index.html` in a browser and review the prototype pages inside the portal.
9. When the PM confirms the prototype, add `<!-- prototype-status: approved -->` to `ui-spec.html`.
10. Run `python scripts/stage_loader.py --stage product-prototype --action record-artifacts`.

## Output Artifacts

- `{process_slug}/pages/docs/fields.html`
- `{process_slug}/pages/docs/ui-spec.html`
- `{process_slug}/pages/prototype/**/*.html` (required interactive HTML prototypes)
- `{process_slug}/designs/<design_id>/prototype.pen` (optional Pencil prototype)

## Rules

- The HTML prototype is the primary review artifact; Pencil is optional.
- Always reuse the shared `prototype.css` and `prototype.js` assets. Do not inline all styles or rebuild the component library from scratch.
- Keep controls and states complete enough for implementation: default, hover/focus where relevant, disabled, empty, loading, error, and success.
- Every interactive element must carry a stable `data-uid`. Do not generate random UIDs that change on every render.
- Prototype links use relative paths so they work both inside the portal iframe and when opened standalone.
- After approval, tell the user to run: `claude plan-tdd-development <session_id> <design_id>`.
