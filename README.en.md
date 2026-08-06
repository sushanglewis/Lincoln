# Lincoln — AI-Native R&D Workflow & Product-Engineering Collaboration System

> [中文](README.md) | English

Lincoln is an AI-Native R&D workflow system spanning **IDEs, agent harnesses, code hosting, knowledge management, skills, plugins, and automation**. It runs on **stages** for rhythm, **gates** for quality, and **repeatable SOPs** as its backbone, chaining requirements clarification, product design, prototyping, TDD planning, OpenSpec proposals, task splitting, implementation, and knowledge-base distillation into one human-AI collaborative pipeline.

- **Whole lifecycle, not a point tool**: every stage has explicit role, skill, and artifact contracts — agents step in at the right moments instead of replacing human judgment.
- **Disciplined, not bureaucratic**: stage gates, human gates, branch hygiene, and the dual-track knowledge model keep collaboration traceable, handoff-ready, and auditable.
- **Low-invasion and pluggable**: Lincoln blends into your project as a harness plugin — skills, hooks, workflow templates, and multi-harness adapters all extend along one meta-model.

## Latest Release

[![Release](https://img.shields.io/badge/release-v1.6.0-blue)](RELEASE.md)

**v1.6.0** is released: Lincoln switches to a global npm plugin model. Install with `npm install -g @sushanglewis/lincoln`; projects opt in via `.lincoln.yaml`.

See the full release notes in [RELEASE.md](RELEASE.md).

## Quick Start

Open the repo and tell the Agent what you want in plain language. Lincoln will route to the right workflow automatically:

- **Start working on issue 55** → initializes the `issue-55` branch and work package, entering the `interview-to-knowledge` team workflow
- **Use existing-project-iteration to understand this codebase** → scans source code, builds the `knowledge/` function library, and plans the next iteration
- **Use design-spike to explore this idea** → clarifies requirements and produces a design review plus an interactive prototype
- **What's the current status?** → reports current stage, blocker, recommended skills, and next action

## Installation

### Prerequisites

- Node.js ≥ 20
- Python 3.10+ (`lincoln install` will auto-detect `python3.12 / 3.11 / 3.10` and create a virtual environment)
- At least one agent harness installed: `Claude Code`, `Codex`, or `OpenCode`

### Install Lincoln

```bash
npm install -g @sushanglewis/lincoln
```

`npm install -g` installs the CLI and bundled framework payload. After installation, an interactive bootstrap starts and lets you choose which agent harnesses to install Lincoln into (`Claude Code`, `Codex`, `OpenCode`).

For a non-interactive install, run:

```bash
lincoln install --yes
```

You can also target specific harnesses:

```bash
lincoln install --yes --harnesses claude-code,opencode
```

> **Note**: `npm install -g` only installs the CLI and bundled framework payload; **you must run `lincoln install`** to sync hooks, agents, skills, scripts, and the full runtime framework to `~/.claude/`, `~/.codex/`, and `~/.opencode/`.

If you previously installed the legacy `lincoln-install` package, uninstall it first (its bin names conflict with the new package):

```bash
npm uninstall -g lincoln-install
npm install -g @sushanglewis/lincoln
lincoln install --yes
```

To force a reinstall:

```bash
npm install -g @sushanglewis/lincoln --force
lincoln install --yes
```

### Verify the installation

```bash
lincoln --version
lincoln doctor --json
```

`lincoln doctor --json` checks Node, Python, PyYAML, npm, the global marker, payload hooks, venv, and project marker.

### Enable Lincoln in a project

Lincoln hooks are **off by default** in directories without a marker. In your project root run:

```bash
cd your-project
lincoln init-project
```

This creates a `.lincoln.yaml` marker file. After that, opening Claude Code in this directory will load the `/lc-*` commands.

### Update Lincoln

```bash
lincoln update
```

### Migrate from the old vendored model

If your project previously committed the Lincoln framework source directly into the repo:

```bash
lincoln migrate-project --dry-run   # preview files to remove
lincoln migrate-project --yes       # confirm migration
```

The legacy `npx lincoln-install` / `npx lincoln-update` wrappers are still present but deprecated; migrate to the global CLI.

First time? Read [USAGE.md](USAGE.md) for the full installation and usage guide.

## What Lincoln Can Do

### Stage-Driven Workflow Engine

Each stage is defined in `.claude/stages/<stage-id>.yaml` with its role, skills, gates, and artifacts. The `workflow-stage.yaml` runtime state drives agent context injection, while Lincoln's stage loader handles stage validation, artifact recording, and gate advancement.

### Preset SOP Workflow Templates

| Workflow | Scenario | Mode |
|----------|----------|------|
| `interview-to-knowledge` | From interview recordings to GitHub Issues to Obsidian knowledge distillation | team |
| `existing-project-iteration` | Existing source code: build knowledge first, then iterate | solo |
| `bug-fix` | Clear bug: lightweight design, fast fix | solo |
| `design-spike` | Requirements unclear: explore solutions and prototypes | solo |
| `oss-first-design` | Heavily reliant on open-source solutions: research first, then design | solo |
| `pm-research` | Systematic competitive/market/user/stakeholder research | solo |

See [`.claude/workflows/README.md`](.claude/workflows/README.md) for the full template catalog.

### Issue Work Packages (HTML Portal)

Every requirement maps to one GitHub issue and one Lincoln feature branch. The `issue-<N>/` work package contains:

- `index.html` — human-facing portal aggregating stage status, navigation, and artifacts
- `workflow-stage.yaml` — machine-readable state and handoff protocol
- `documents.yaml` — artifact index and human-approval status
- `pages/docs/` — HTML pages for requirements, PRDs, designs, TDD plans
- `pages/prototype/` — interactive HTML prototypes
- `handoffs/` — stage handoff documents

## Natural-Language Interaction

Lincoln is AI-Native — **you don't need to type terminal commands**. Describe your intent in plain language and the Agent translates and executes the right scripts for you.

| You say | Agent does |
|---------|------------|
| Start working on issue 55 | Initializes branch and work package, enters `interview-to-knowledge` |
| What's the current status? | Reports current stage, blocker, and next action |
| Record this stage's artifacts | Records artifacts and refreshes `documents.yaml` |
| Confirm and proceed | Marks the current gate as approved after explicit human confirmation |
| Generate handoff | Generates a handoff document |
| Check the Lincoln environment | Detects dependencies and lists missing items |
| List all active Lincoln branches | Lists stage status and blockers for every issue branch |
| Run benchmark | Generates a Lincoln session benchmark report |
| Start the PM research workflow | Enters the `pm-research` research chain |

More commands and usage details are in [USAGE.md](USAGE.md).

## Two Usage Modes

### Lightweight Solo Path (vibe-coding / indie maker)

Best for local projects and quick personal iteration. No GitHub issue required — just pick a workflow template and start. Artifacts land in the work-package directory, and you can upgrade to the team flow at any time.

### Team Issue Path (product / design / engineering / QA)

Every requirement uses a dedicated Lincoln feature branch named `issue-<N>`. Stage state travels with the branch; downstream roles check out the same branch and continue. Process documents stay on the feature branch and are **not merged to `main`** — only final code artifacts go through the PR.

Detailed walkthroughs are in [USAGE.md](USAGE.md).

## Tools

- `@sushanglewis/lincoln` — global CLI: `lincoln install`, `lincoln update`, `lincoln use`, `lincoln doctor`, `lincoln init-project`, `lincoln migrate-project`, `lincoln record`
- `tools/lincoln/` — Ink/React TUI for recording interviews (`lincoln-record` CLI)
- `tools/lincoln-record/` — Rust local recording & transcription CLI (whisper-rs + Metal, speaker diarization)
- `tools/lincoln-installer/` — legacy terminal TUI installer and updater (deprecated, kept for backward compatibility)

## Multi-harness Support

Lincoln's end-to-end logic — role contracts, stage workflows, and `lc-*` commands — can be derived for codex and opencode. `.claude/` is the single source of truth; harness artifacts are auto-generated by the adapter. **Never edit generated artifacts by hand.**

Tell the Agent "generate codex adapter" or "generate opencode adapter". Generated artifacts are gitignored (`AGENTS.md`, `.codex-plugin/`, `.opencode/`). CI validates that manifests can be generated and that local artifacts have not drifted.

## Extending and Contributing

Lincoln's `.claude/` is an open system-prompt layer. Contributions of new agent roles, skills, hooks, or workflow templates are welcome.

Before submitting a PR, please read:

- [CONTRIBUTING.md](CONTRIBUTING.md) — contributor guardrails, core vs. domain boundaries, test layers, and eval gates
- [CLAUDE.md](CLAUDE.md) — agent contract, human-gate rules, and artifact conventions
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — steps for adding new workflow templates

## Learn More

- [USAGE.md](USAGE.md) — complete user manual
- [CONTRIBUTING.md](CONTRIBUTING.md) — contributor guide
- [RELEASE.md](RELEASE.md) — release notes and changelog
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — workflow template catalog
- [OpenSpec docs](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)

## License

Lincoln is released under the [MIT License](LICENSE), Copyright (c) 2026 苏尚lewis (sushanglewis).

External skill, CLI, and plugin licenses are declared in [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml) and [`.claude/agents/external/NOTICES.md`](.claude/agents/external/NOTICES.md).
