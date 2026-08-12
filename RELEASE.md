# Lincoln v1.6.2 Release Notes

**Release date:** 2026-08-12

## Highlights

- **全局插件模式下 `lc-init-branch` 使用全局模板** — 修复 `lc-init-branch` 命令映射指向项目本地 `scripts/init-lincoln-branch.sh` 的问题。现在它会调用 `"$LINCOLN_ROOT/scripts/init-lincoln-branch.sh"`，确保新建 issue 工作包读取 `~/.lincoln/current/` 下的最新模板，而不是项目里遗留的旧版本 `.claude/templates/issue-package/`。
- **迁移提示更新** — `lc-init-branch` skill 文档的示例命令改为使用 `$LINCOLN_ROOT`，与全局插件模型保持一致。

## Migration Notes

- 已使用全局插件模式的项目，运行 `lincoln migrate-project --yes` 清理本地旧 `.claude/` 文件后，再通过 `lc-init-branch` 初始化工作包即可生效。
- 如果已手动安装 Lincoln 1.6.1，可编辑 `~/.claude/harnesses/command-map.yaml` 中 `lc-init-branch` 的 action 为 `bash "$LINCOLN_ROOT/scripts/init-lincoln-branch.sh"`，或升级到 1.6.2 后重新 `lincoln install`。

---

# Lincoln v1.6.1 Release Notes

**Release date:** 2026-08-11

## Highlights

- **lc-one-id skill** — Agent 现在可通过工具描述学习 one-id 查询，按 `feature/*`、`page/*`、`field/*`、`doc/*` 稳定 ID 追溯上游产物，避免 downstream 阶段凭路径猜测。
- **Agent one-id 约束** — `.claude/agents/default.md` 明确要求：需要按 ID 追溯产物时调用 `lc-one-id` skill。
- **Portal 注解对齐** — 修复 `lincoln_render.py` 把 HTML 注释内的占位 `<meta>` 误当作已存在标签的 bug，结构化数据里的 `annotations` 现在会正确注入为独立 `<meta>` 标签，被 portal 索引扫描到。
- **command-map 刷新** — 自动注册 `lc-skill-one-id` 命令入口。

## Tooling

- `scripts/lincoln_id.py` 增加可执行权限，配合 skill prompt 直接调用。

## Migration Notes

- 无需迁移；已有 issue package 的 `index.html` portal 会在下次 `record-artifacts` 或 `lincoln_index.py` 刷新后自动获得完整注解。

---

# Lincoln v1.6.0 Release Notes

**Release date:** 2026-08-06

## Release Automation Contract

Starting from this release, every PR merged into `main` automatically triggers a patch release:

1. `.github/workflows/release-on-merge.yml` bumps the patch version in `.version-bump.json` and all linked manifests.
2. The workflow updates the version badge and callout in `README.md` and `README.en.md`.
3. The workflow commits the version bump, pushes it to `main`, and pushes a `lincoln-vX.Y.Z` tag.
4. `.github/workflows/publish-lincoln.yml` publishes the npm package and creates a GitHub Release using the matching section from this file.

To include curated release notes for a version, add a new section to this file before merging the release-triggering PR.

## Highlights

Lincoln v1.6.0 moves the framework from a vendored-per-project model to a global npm plugin. Users now install `@sushanglewis/lincoln` once and run `lincoln install` to sync the framework to `~/.claude/`, `~/.codex/`, and `~/.opencode/`. Projects opt in with a single `.lincoln.yaml` marker; unmarked projects keep Lincoln inactive by default.

## New Features

- **Global npm plugin distribution** (#100)
  - New `@sushanglewis/lincoln` package provides the `lincoln` CLI.
  - `lincoln install` performs one-time global setup and syncs framework files.
  - `lincoln update` pulls the latest release and re-syncs globally.
  - `lincoln use <version>` switches the active global version.
  - `lincoln doctor` diagnoses harness integration.
  - `lincoln init-project` creates `.lincoln.yaml` in a project.
  - `lincoln migrate-project` removes unmodified vendored framework files and generates `.lincoln.yaml`.
  - `lincoln record` launches the interview recorder TUI.

- **Hooks globalize and default-off** (#100)
  - `.claude/hooks/*.sh` now resolve `CLAUDE_PLUGIN_ROOT` / `LINCOLN_HOME` / `~/.lincoln/current` before falling back to the local repo.
  - When running in global mode, hooks exit quietly unless `.lincoln.yaml`, legacy `.claude/workflow-state.yaml`, or `LINCOLN_ALWAYS_ON` is present.

- **Marketplace plugin hooks manifest** (#100)
  - Adds `.claude-plugin/hooks.json` and references it from `.claude-plugin/plugin.json`.

## Tooling

- `packages/lincoln` — global CLI package `@sushanglewis/lincoln` (version aligned to `1.6.0`).
- `tools/lincoln` — Ink/React TUI for interview recording, now packaged as `@sushanglewis/lincoln-recorder` (`lincoln-record` CLI).
- `tools/lincoln-installer` — legacy terminal TUI installer and updater (deprecated, kept for backward compatibility).

## Dependencies

- `superpowers` v1.2.0
- `gsd` v2.0.1
- `openspec` v0.5.0

## Migration Notes

- Install the new global CLI with `npm install -g @sushanglewis/lincoln` and run `lincoln install`.
- Existing projects with vendored framework files can use `lincoln migrate-project --dry-run` / `--yes` to switch to the global model.
- Legacy `npx lincoln-install` / `npx lincoln-update` still work but print a deprecation notice; migrate to the global CLI.

## Full Changelog

Compare: https://github.com/sushanglewis/Lincoln/compare/v1.5.0...v1.6.0

Merged PRs since v1.5.0:

- #100 feat(#100): implement global Lincoln plugin distribution

---

# Lincoln v1.5.0 Release Notes

**Release date:** 2026-08-05

## Highlights

Lincoln v1.5.0 strengthens the HTML prototype framework with an annotation contract and a portal tray, making issue work packages more interactive and easier to navigate.

## New Features

- **HTML prototype framework enhancements** (#97)
  - Adds an annotation contract for structured notes and comments on HTML prototypes.
  - Introduces a portal tray for quick navigation and contextual actions within the issue portal.
  - Extends the HTML-centric issue work package experience introduced in v1.4.0.

## Tooling

- `tools/lincoln` — Ink/React TUI for interview recording (version aligned to `1.5.0`).
- `tools/lincoln-record` — Rust local recording & transcription CLI (version aligned to `1.5.0`).
- `tools/lincoln-installer` — terminal TUI installer and updater for Lincoln (version aligned to `1.5.0`).

## Dependencies

- `superpowers` v1.2.0
- `gsd` v2.0.1
- `openspec` v0.5.0

## Migration Notes

- Users upgrading from v1.4.0 should run `python3 scripts/bump_version.py --check` to verify all manifests are lockstep-aligned.
- Issue work packages created before v1.5.0 continue to work; new packages can leverage the annotation contract and portal tray.

## Full Changelog

Compare: https://github.com/sushanglewis/Lincoln/compare/v1.4.0...v1.5.0

Merged PRs since v1.4.0:

- #98 feat(#97): strengthen HTML prototype framework with annotation contract and portal tray

---

# Lincoln v1.4.0 Release Notes

**Release date:** 2026-08-04

## Highlights

Lincoln v1.4.0 ships an HTML-centric issue work package experience, a terminal-based installer/updater, and root-level PRD standards. The README is now a slim entry point, with detailed user and contributor guidance moved to `USAGE.md` and `CONTRIBUTING.md`.

## New Features

- **HTML-centric issue work packages** (#90 / #91 / #96)
  - Refactors `issue-<N>/` process packages from Markdown/YAML-centric artifacts to an HTML portal (`issue-<N>/index.html`) as the human-readable entry point.
  - `workflow-stage.yaml` remains the machine-readable state; `documents.yaml` remains the artifact index.
  - Strengthens the HTML prototype kit with categorized shell templates and theme synchronization.
  - Auto-generates `assets/js/package-data.js` to drive portal navigation and status panels.

- **Terminal installer and updater** (#88 / #89)
  - `npx lincoln-install` provides a TUI installer for first-time setup, selecting harness, optional dependencies, and install scope.
  - `npx lincoln-update` downloads the latest Lincoln release and merges framework files by allowlist while preserving user data.
  - Both support `--no-tui --format json` for scripting and `--dry-run` for safe preview.

- **Root-level PRD and interaction-doc standards** (#85 / #86)
  - Introduces a root-level PRD format with version management and interaction-document standards.
  - Aligns design and implementation artifacts around a single source of truth at the repository root.

## Tooling

- `tools/lincoln` — Ink/React TUI for interview recording (version aligned to `1.4.0`).
- `tools/lincoln-record` — Rust local recording & transcription CLI (version aligned to `1.4.0`).
- `tools/lincoln-installer` — terminal TUI installer and updater for Lincoln (version aligned to `1.4.0`).
- `scripts/lincoln_index.py` — generates portal navigation data for HTML issue packages.
- `scripts/lincoln_documents.py` — refreshes `documents.yaml` artifact index.

## Dependencies

- `superpowers` v1.2.0
- `gsd` v2.0.1
- `openspec` v0.5.0

## Migration Notes

- Users upgrading from v1.3.0 should run `python3 scripts/bump_version.py --check` to verify all manifests are lockstep-aligned.
- Issue work packages created before v1.4.0 continue to work; new packages are initialized with the HTML portal layout.
- The README no longer contains detailed installation or contribution instructions; see `USAGE.md` and `CONTRIBUTING.md`.

## Full Changelog

Compare: https://github.com/sushanglewis/Lincoln/compare/v1.3.0...v1.4.0

Merged PRs since v1.3.0:

- #96 feat(#90): strengthen HTML prototype kit with categorized shells and theme sync
- #91 feat(#90): refactor issue-package to HTML-centric artifacts
- #89 feat(#88): add lincoln-install terminal TUI installer and npx lincoln-update updater
- #86 feat(#85): root-level PRD with version management and interaction-doc standards

---

# Lincoln v1.3.0 Release Notes

**Release date:** 2026-07-22

## Highlights

Lincoln v1.3.0 ships a unified `/lc-*` command surface, introduces the `pm-research` solo workflow for product research, hardens infrastructure with explicit opt-in benchmark and lockstep version bumping, and codifies agent-agent handoff and sub-agent dispatch rules.

## New Features

- **Unified `/lc-*` command surface** (#78 / #79 / #81 / #82)
  - Adds `lc-agent-*`, `lc-skill-*`, `lc-scenario-*`, and `lc-wf-*` command families covering all roles, skills, scenarios, and workflows.
  - Command map is auto-generated by `scripts/lincoln_command_map.py --refresh` from `.claude/workflows/`, `.claude/agents/`, `.claude/skills/`, and `.claude/harnesses/scenarios.yaml`.

- **PM research solo workflow `pm-research`** (#79 / #81)
  - Complete chain from scope definition, first-principles thinking, stakeholder research, market/product/competitor research, intelligence collection, framework analysis, storytelling, to final research report.
  - Adds 10 research skills/stages: `lc-research-scope`, `lc-first-principles`, `lc-stakeholder-research`, `lc-market-research`, `lc-product-research`, `lc-competitive-analysis`, `lc-collect-intelligence`, `lc-analyze-frameworks`, `lc-storytelling`, `lc-research-report`.

- **Session opening guidance** (#59 / #70)
  - Session-start hook injects overview-level recon, situation judgment with confidence, and Johari-window confirmation when no work state exists.
  - README switches to natural-language-only entry points.

- **Sub-Agent dispatch principles** (#75 / #80)
  - Agent contract adds Red Flags and explicit-PM-permission rules before fanning out sub-agents.
  - Main session must verify and integrate sub-agent output; sub-agents cannot replace human confirmation.

- **PM→UX handoff docs and gate** (#76 / #77)
  - `product-design-docs` stage produces `handoffs/pm-to-ux/master-handoff-pm-to-ux-v*.md` and `pm-to-ux.handoff.yaml`.
  - Defines machine-readable context-pack order and validation items for UX Agent takeover.

- **Infrastructure hardening** (#58 / #63 / #65 / #67 / #68 / #72 / #73 / #74)
  - Benchmark is explicit opt-in via `lc-benchmark` / `scripts/lc-benchmark-cli.py`; no longer auto-triggered.
  - Behavioral-shaping writing mode (Red Flags / SUBAGENT-STOP / announce skill use).
  - Infrastructure test layer: `scripts/run-infrastructure-tests.py`.
  - Lockstep multi-manifest version bump: `scripts/bump_version.py` + `.version-bump.json`.
  - Session-start trimmed and exposes token-cost metrics.

- **Multi-harness default-off acceptance tests** (#64 / #71)
  - Codex-derived plugin manifest explicitly declares `"hooks": {}`.
  - Default-off acceptance tests for codex / opencode prevent harness fallback traps.

- **Installation and dependency compliance** (#39 / #41 / #42 / #43 / #44 / #45 / #46)
  - Setup asks whether recording transcription and benchmark are needed.
  - External skills pinned to known-good refs; license compliance centralized.

## Tooling

- `tools/lincoln` — Ink/React TUI for recording interviews (version aligned to `1.3.0`).
- `tools/lincoln-record` — Rust local recording & transcription CLI (version aligned to `1.3.0`).
- `scripts/lincoln_role.py`, `scripts/lincoln_skill_prompt.py`, `scripts/lincoln_scenario.py` — helper scripts for role templates, skill prompts, and scenario compositions (#81).

## Dependencies

- `superpowers` v1.2.0
- `gsd` v2.0.1
- `openspec` v0.5.0

## Migration Notes

- Users upgrading from v1.2.0 should run `python3 scripts/bump_version.py --check` to verify all manifests are lockstep-aligned.
- Benchmark is no longer auto-triggered; invoke `/lc-benchmark` or `python3 scripts/lc-benchmark-cli.py` explicitly when needed.

## Full Changelog

Compare: https://github.com/sushanglewis/Lincoln/compare/v1.2.0...v1.3.0

Merged PRs since v1.2.0:

- #82 fix(#78 #79): address review findings in command-map, helper scripts and tests
- #81 feat(#78,#79): comprehensive lc-* command surface and pm-research workflow
- #80 feat(#75): sub-Agent dispatch principles in agent contract
- #77 feat(#76): PM→UX handoff docs, agent contract and stage gates
- #74 feat: 补完 #63 session-start token cost metric
- #73 feat: Lincoln 基础设施加固 (#63 #65 #67 #68 #72)
- #71 feat: codex 派生 manifest 显式声明 hooks:{} + 缺省关闭验收测试 (#64)
- #70 feat: 会话开场引导 + README 全自然语言化 (#59)
- #58 fix: 文档与实现对齐 + benchmark 主 agent 映射改读实际阶段文件
- #57 feat: 工作包合并卫生修复 + 自然语言交互入口 (#55 #56 #54)
- #51 feat: 统一 workflow 目录与 lc-wf-* bundle 注册 (#48)
- #50 feat: 多 harness 适配（codex/opencode)+ lc-* 命令统一 (#47)
- #49 feat(LEW-17): local Whisper recording CLI and redesigned Lincoln TUI
- #46 fix: 依赖指向上游 main + 许可合规 + 安装询问 + 分支命名对齐

---

# Lincoln v1.2.0 Release Notes

**Release date:** 2026-07-12

## Highlights

Lincoln v1.2.0 reframes the project as an AI-Native product R&D collaboration system. It introduces issue-driven process packages, ships a single-YAML stage framework, adds a benchmark system for evaluating Lincoln sessions, automates first-run dependency setup, and packages Lincoln as a Claude Code plugin.

## New Features

- **Issue-driven process packages** (#22)
  - `scripts/init-lincoln-branch.sh --issue-number ...` scaffolds a per-issue workspace.
  - Per-branch `{process_slug}/workflow-stage.yaml` keeps runtime state out of `main`.
  - Branch-only process artifacts (`recordings/`, `interviews/`, `designs/`, etc.) are protected from merging to `main` by `scripts/check-main-merge-hygiene.py`.

- **Single-YAML stage framework** (#38 / #33)
  - Stage definitions moved from folder-based metadata to `.claude/stages/<stage>.yaml`.
  - Unified `workflow-stage.yaml` schema drives agent context injection via `.claude/hooks/on-session-start.sh`.
  - Routing and skill dependencies are now declared in `.claude/skills/routing.yaml` and `.claude/skills/dependencies.yaml`.

- **Lincoln benchmark system** (#37 / LEW-18, #27)
  - `scripts/lincoln_benchmark*.py` generate benchmark runs from session traces.
  - Evaluates gate compliance, artifact completeness, and skill coverage.
  - Results are written as structured JSON for CI consumption.

- **Automated first-run dependency setup** (#34 / #32)
  - `lincoln-setup` detects missing external skills (`superpowers`, `gsd`, etc.) and guides installation on first launch.

- **External agent imports** (#26 / #23)
  - High-star external agents are imported into `.claude/agents/external/` and validated by tests.

## Documentation

- README reframed as an AI-Native product R&D collaboration system (#29).
- README simplified and scenario sections removed (#30).
- README, `CLAUDE.md`, workflow index, and plugin manifest refreshed (#28).
- README expanded for vibe-coding users with a contribution section (#36).

## Tooling

- `tools/lincoln` — Ink/React TUI for recording interviews (version aligned to `1.2.0`).
- `tools/record-interview` — Python recording backend (version aligned to `1.2.0`).

## Dependencies

- `superpowers` v1.2.0
- `gsd` v2.0.1
- `openspec` v0.5.0

## Migration Notes

- Users upgrading from v1.1.0 should delete any legacy `.claude/workflow-stage.yaml` at repo root and let the next session recreate a per-branch state file.
- External skill installation is now checked at session start; follow the prompts if any skill is missing.

## Release Checklist

Before tagging a new Lincoln release, run the deterministic packaging pipeline:

1. Bump version and regenerate harness artifacts:
   ```bash
   python3 scripts/bump_version.py bump X.Y.Z
   python3 scripts/bump_version.py --audit X.Y.Z-1
   ```
2. Dry-run the package to validate the allowlist/denylist:
   ```bash
   python3 scripts/package-lincoln-plugin.py check --check-dirty
   ```
3. Build the distribution archive on a clean working tree:
   ```bash
   python3 scripts/package-lincoln-plugin.py package
   ```
4. Verify the checksum and archive contents:
   ```bash
   cat dist/lincoln-X.Y.Z.tar.gz.sha256
   tar -tzf dist/lincoln-X.Y.Z.tar.gz | head
   ```
5. Create a GitHub Release manually and attach `dist/lincoln-X.Y.Z.tar.gz`.
   Automated marketplace/portal upload is not yet enabled.

## Full Changelog

Compare: https://github.com/sushanglewis/Lincoln/compare/v1.1.0...v1.2.0

Merged PRs since v1.1.0:

- #38 refactor: P0 Lincoln overall framework with single-YAML stages (#33)
- #37 feat: Lincoln benchmark system from session trace (LEW-18 / #27)
- #36 docs: expand README audience to vibe-coding users and add contribution section
- #34 feat: automate Lincoln dependency setup for first-run users (#32)
- #30 docs: simplify README constraints and remove scenario sections
- #29 docs: reframe Lincoln as AI-Native product R&D collaboration system
- #28 docs: refresh README, CLAUDE.md, workflow index, and plugin manifest
- #26 feat: import high-star external agents into Lincoln (#23)
- #22 feat: issue-driven process package with artifact state recording
