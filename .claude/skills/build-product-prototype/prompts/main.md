# build-product-prototype

You are executing the Lincoln workflow step `product-prototype`: turn approved product design documents into UI/field specifications and an interactive HTML prototype.

## Goal

Create field and UI specifications as HTML doc pages, and produce a high-fidelity interactive HTML prototype that the PM can inspect directly in the issue-package portal (`{process_slug}/index.html`). A Pencil prototype is optional; the HTML prototype is the primary review artifact.

## Reference templates

Use the following read-only templates as the style/layout reference. Copy/adapt them into the issue package; do not modify the templates themselves.

- `.claude/templates/issue-package/page-prototype.html.tpl` — minimal starter page with theme sync support.
- `.claude/templates/issue-package/prototypes/app/main/page.html.tpl` — main app window with sidebar + WebView placeholder.
- `.claude/templates/issue-package/prototypes/app/onboarding/page.html.tpl` — login/onboarding card.
- `.claude/templates/issue-package/prototypes/app/settings/page.html.tpl` — two-column settings page.
- `.claude/templates/issue-package/prototypes/app/overlays/page.html.tpl` — avatar menu / about / toast overlays.
- `.claude/templates/issue-package/prototypes/app/tray/page.html.tpl` — system-tray scenario controller. When the product has a macOS menubar presence, create thin scenario pages under `pages/prototype/app/tray/` showing at minimum: default state, unread-badge state, and menu-open state. These pages must **not** redraw the tray inside the app prototype; instead they send `postMessage({type:'lincoln-tray-state', unread:<int>, open:<bool>}, '*')` to the portal so the portal-level macOS tray updates. See the tray template for the exact snippet.
- `.claude/templates/issue-package/prototypes/app/org/page.html.tpl` — organization list.
- `.claude/templates/issue-package/prototypes/web/dashboard/page.html.tpl` — web dashboard shell.
- `.claude/templates/issue-package/prototypes/web/list/page.html.tpl` — web list view shell.
- `.claude/templates/issue-package/prototypes/web/form/page.html.tpl` — web form shell.
- `.claude/templates/issue-package/prototypes/web/detail/page.html.tpl` — web detail shell.
- `.claude/templates/issue-package/prototypes/mobile/home/page.html.tpl` — mobile home feed shell.
- `.claude/templates/issue-package/prototypes/mobile/chat/page.html.tpl` — mobile chat shell.
- `.claude/templates/issue-package/prototypes/mobile/settings/page.html.tpl` — mobile settings list shell.
- `.claude/templates/issue-package/prototypes/mobile/profile/page.html.tpl` — mobile profile shell.
- `.claude/templates/issue-package/assets/prototype.css` — shared styles (tokens, dark mode, window shell, sidebar, forms, overlays, web/mobile shells).
- `.claude/templates/issue-package/assets/prototype.js` — shared UI builders and mock data (`window.LincolnPrototype`), including `frameApp`, `frameWeb`, `frameMobile`.

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
5. **Plan prototype generation granularity.** Before writing prototype pages, list every screen from `flows.html` and `page-map.html`. Group them into cohesive clusters (e.g. onboarding, main shell, settings, overlays, tray). Generate one cluster at a time. After each cluster, verify that every page in the cluster has complete annotation meta tags before starting the next cluster. This prevents agent context exhaustion and keeps each page's documentation and interactions complete.
6. Create interactive HTML prototypes under `{process_slug}/pages/prototype/{app,web,mobile}/` by adapting the reference templates above. Pick the right shell (`frameApp`, `frameWeb`, or `frameMobile`) from `LincolnPrototype.ui` for the product form-factor. Every page must:
   - Link to `../../../assets/prototype.css` and `../../../assets/prototype.js` (depth 3) or `../../../../assets/...` (depth 4) depending on its path.
   - Include the theme sync IIFE shown in the starter template.
   - Include `<meta name="prototype-base" content="../../../">` (or `../../../../` for depth 4).
   - Include `<meta name="page-uid" content="...">`, `<meta name="nav-group" content="...">`, and `<meta name="nav-label" content="...">` with a short Chinese label for the left nav.
   - Include the annotation meta tags `doc-purpose`, `doc-layout`, `doc-fields`, `doc-boundaries`, `doc-exceptions`. Also include `doc-stories`, `doc-rules`, `doc-refs` when they add clarity, so the portal right panel explains functionality, layout, fields, boundary cases, and exception flows.
   - Use `LincolnPrototype.ui` builders and `prototype.css` tokens for every visual element so both light and dark themes render correctly; verify both themes by toggling the portal theme switch.
   - Assign a stable `data-uid` attribute to every interactive element, screen region, and WebView placeholder.
   - Override `LincolnPrototype.data` in the page script for issue-specific mock data (user, org, webviews, settings, unread items).
7. Optionally create or update `{process_slug}/designs/<design_id>/prototype.pen` with Pencil tools if the PM explicitly asks for a Pencil prototype. If you use Pencil tools, call `get_editor_state(include_schema: true)` first and use `snapshot_layout` to check for clipping/overlap.
8. Update the root `{process_slug}/pages/docs/prd.html` section 9 "相关产物链接" with the `ui-spec.html`, `fields.html`, and HTML prototype links. If the PRD already has an approved snapshot, warn the PM that changes require a version bump and re-freeze via `python scripts/lincoln_prd.py freeze`.
9. Ask the PM to open `{process_slug}/index.html` in a browser, toggle the theme switch in the macOS menubar, and review both light and dark renderings of each prototype page inside the portal.
10. When the PM confirms the prototype, add `<!-- prototype-status: approved -->` to `ui-spec.html`.
11. Run `python scripts/stage_loader.py --stage product-prototype --action record-artifacts`.

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
- Do not add collapse toggles or custom panel chrome to the portal; the right annotation panel is always visible.
- The system tray is portal-level chrome. Never redraw the tray inside an app prototype page with `.menubar`, `.tray-icon`, `.tray-panel`, `bindTray`, or `trayMenu`. Tray scenario pages must be thin controllers that post `lincoln-tray-state` messages to the portal.
- After approval, tell the user to run: `claude plan-tdd-development <session_id> <design_id>`.
