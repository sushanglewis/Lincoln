# build-product-prototype

You are executing the Lincoln workflow step `product-prototype`: turn approved product design documents into UI/field specifications and an interactive HTML prototype.

## Goal

Create field and UI specifications as HTML doc pages, and produce a high-fidelity interactive HTML prototype that the PM can inspect directly in the issue-package portal (`{process_slug}/index.html`). The HTML prototype is the primary review artifact; a Pencil prototype is optional and produced only if the PM explicitly asks for it.

## Reference templates

The default rendering templates are:

- `.claude/templates/issue-package/page-doc-structured.html.tpl` — structured doc page used for `fields.html` and `ui-spec.html`.
- `.claude/templates/issue-package/page-prototype-structured.html.tpl` — data-driven prototype page used for all `pages/prototype/**/*.html`.

You may still read the categorized example templates under `.claude/templates/issue-package/prototypes/` for layout inspiration, but generate pages through `python scripts/lincoln_render.py` rather than copying templates by hand.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier

## Steps

1. Verify `{process_slug}/pages/docs/design-review.html` contains `<!-- status: approved -->` or `[x] PM 已确认设计文档`.
2. Read the approved design package under `{process_slug}/pages/docs/`, including `flows.html` and `page-map.html`.
3. Write `{process_slug}/pages/docs/fields.html` using the structured renderer:

   ```bash
   python scripts/lincoln_render.py \
     --stage product-prototype \
     --target {process_slug}/pages/docs/fields.html \
     --title "字段说明" --nav-label "字段" --version v1.0 --uid fields \
     --data {process_slug}/pages/docs/fields.yaml
   ```

   The YAML should contain a `fields` array (optionally grouped under `groups`):

   ```yaml
   intro: "本页面列出所有 screen/form 字段规格。"
   annotations:
     doc-purpose: "字段规格"
     doc-fields: "字段名 — 类型 — 必填 — 说明"
   fields:
     - name: "手机号"
       type: "string"
       required: true
       validation: "大陆手机号正则"
       default: ""
       copy: "请输入手机号"
       error: "手机号格式不正确"
       source: "model/user"
   ```

4. Write `{process_slug}/pages/docs/ui-spec.html` covering the interaction-document delivery standards:
   - 用户场景与流程: who, when, goal, trigger, completion criteria.
   - 界面流转图: screen-to-screen flow mapped to the business flow in `flows.html`.
   - 页面交互说明: per-screen layout elements, interaction rules (events, responses, navigation), and field validation/error handling.
   - 交互 Demo/原型: links to the HTML prototype pages under `pages/prototype/` and a summary of key interactions.

   Use the structured renderer with `--data` containing `sections`, `pages`, and `interactions` as appropriate.

5. **Plan prototype generation granularity.** Before writing prototype pages, list every screen from `flows.html` and `page-map.html`. Group them into cohesive clusters (e.g. onboarding, main shell, settings, overlays, tray). Generate one cluster at a time. After each cluster, verify that every page has complete annotation meta tags before starting the next cluster.

6. Create interactive HTML prototypes under `{process_slug}/pages/prototype/{app,web,mobile}/` using the structured prototype renderer:

   ```bash
   python scripts/lincoln_render.py \
     --stage product-prototype \
     --target {process_slug}/pages/prototype/web/dashboard/page.html \
     --title "仪表盘" --nav-label "仪表盘" --nav-group "Prototype" --uid page-dashboard \
     --data {process_slug}/pages/prototype/web/dashboard/page.yaml
   ```

   Prototype YAML schema:

   ```yaml
   layout:
     type: web          # web | app | mobile
     shell: dashboard   # dashboard | list | form | detail | main | onboarding | settings | overlays | tray | org
     title: "仪表盘"
     active: dashboard
     navItems:
       - {id: dashboard, label: 概览, href: ./dashboard/page.html}
       - {id: list, label: 列表, href: ./list/page.html}
   annotations:
     doc-purpose: "展示核心指标与快捷入口"
     doc-layout: "顶部导航 | 指标卡片网格 | 列表区"
     doc-fields: "..."
     doc-stories: "..."
     doc-rules: "..."
     doc-boundaries: "..."
     doc-exceptions: "..."
     doc-refs: "flows.html | page-map.html"
   components:
     - type: html
       uid: dashboard-metrics
       props:
         html: '<div class="metric-grid">...'>
     - type: wv
       props:
         kind: chat
   interactions:
     - trigger: "点击指标卡片"
       action: "跳转到详情页"
       target: "detail/page.html"
   ```

   Every page must:
   - Link to `../../../assets/prototype.css` and `../../../assets/prototype.js` (depth 3) or `../../../../assets/...` (depth 4) depending on its path.
   - Include theme sync support (built into the structured template).
   - Include `<meta name="prototype-base" content="../../../">` (or `../../../../` for depth 4).
   - Include `<meta name="page-uid" content="...">`, `<meta name="nav-group" content="...">`, and `<meta name="nav-label" content="...">` (injected by the renderer from CLI args; annotations come from the YAML `annotations` block).
   - Provide the full annotation meta tags so the portal right panel explains functionality, layout, fields, boundary cases, and exception flows.
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
