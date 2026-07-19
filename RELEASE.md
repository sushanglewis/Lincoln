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
