# Lincoln — AI-Native R&D Workflow & Product-Engineering Collaboration System

> [中文](README.md) | English

> **What is Lincoln?** Lincoln is an AI-Native R&D workflow system spanning **IDEs, agent harnesses, code hosting, knowledge management, skills, plugins, and automation** — dedicated to serving indie developers and product-engineering teams, helping them use agents, skills, and plugins more appropriately at every stage of the product R&D lifecycle, while following more disciplined development processes, code management, and knowledge distillation. It runs on **stages** for rhythm, **gates** for quality, and **repeatable SOPs** as its backbone, chaining requirements clarification, product design, prototyping, TDD planning, OpenSpec proposals, task splitting, implementation, and knowledge-base distillation into one human-AI collaborative pipeline; it works for **vibe-coding developers and indie makers** iterating with an Agent on local projects, and for **product, design, engineering, and QA teams** collaborating across roles with GitHub issues as the unit of work. **Conductor** is the recommended environment (other IDEs/CLIs work too), and role contracts, `lc-*` commands, and stage workflows can be derived for **codex / opencode** via multi-harness adaptation.

- **Whole lifecycle, not a point tool**: from requirements clarification, product design, prototyping, and TDD planning to implementation and acceptance, every stage has explicit role, skill, and artifact contracts — agents step in at the right moments instead of replacing human judgment.
- **Disciplined, not bureaucratic**: stage gates, human gates, branch hygiene, and the dual-track knowledge model (process documents stay on the branch, durable knowledge merges to the vault) keep collaboration traceable, handoff-ready, and auditable.
- **Low-invasion and pluggable**: Lincoln blends into your project as a harness plugin — skills, hooks, workflow templates, and multi-harness adapters all extend along one meta-model, without asking you to reshape your project around it.

## First time here? Let Claude install it for you

Lincoln's hooks usually trigger installation automatically when you first open the repo. If Claude doesn't start on its own, copy this prompt and send it to Claude:

> Please help me complete the Lincoln initial setup:
> 1. Ask me two questions first and decide the install scope based on my answers:
>    - Do I need **recording transcription** (interview audio → transcript)? Only install ffmpeg and the transcription CLI if yes.
>    - Do I need to run the **benchmark** (Lincoln benchmark evaluation)?
> 2. Check the Lincoln environment in this repo and list all missing dependencies.
> 3. Install external skills: superpowers, gsd (both tracking upstream main) into `~/.claude/skills/`, ensuring correct refs.
> 4. Install CLI tools: openspec, gh; only if I need recording transcription, also install ffmpeg and build `tools/lincoln-record/` (the Rust local recording & transcription CLI).
> 5. Install the oh-my-claudecode plugin.
> 6. Interactively configure `.github/openspec-config.yml` (ask me for the GitHub owner and repo name).
> 7. Run `scripts/init-project.sh` to finish project initialization.
> 8. If I need the benchmark, explain how to use `scripts/lincoln_benchmark.py`.
> 9. Report status when done.
>
> Ask for my confirmation before installing any global tool or writing config.

If you only need the [lightweight solo path](#quick-start), you can skip `gh`, `ffmpeg`, the transcription CLI, and `.github/openspec-config.yml` — keeping just `python3`, a Claude Code environment, and Lincoln's own hooks.

> **Where do I start?**
> - **Vibe-coding / indie maker** (personal projects, AI pair programming): jump to the lightweight solo path in [Quick Start](#quick-start).
> - **Team collaborator** (product, design, engineering, QA, driven by GitHub issues): jump to the team issue path in [Quick Start](#quick-start).
> - **Framework developer / contributor** (extending agents, skills, hooks, workflow templates): read [Framework Docs](#framework-docs), [`CLAUDE.md`](CLAUDE.md), and [Extending & Contributing to Lincoln](#extending--contributing-to-lincoln).

## Quick Start

Lincoln offers two entry paths — pick whichever fits you.

### Just open it and say what you need

When you open the repo in Conductor / Claude Code, if Lincoln has no drivable work state (fresh repo, or a work package that hasn't started), the Agent automatically enters opening guidance:

1. **Recon**: the Agent does an overview-level sweep of the repo (top-level structure, README, knowledge index, open issues) — no source reading, no deep scans.
2. **Judgment**: the Agent assesses your situation — role, position in the process, most likely problem and goal — with a confidence level.
3. **Ask & confirm**: the Agent designs confirmation moves around the Johari window, at most 3 questions per round: for known-knowns it paraphrases to confirm; for known-unknowns it supplies background directly; for unknown-knowns it shows you artifacts already in the repo; for unknown-unknowns it probes with concrete scenarios.
4. **Strategic execution**: only when every goal has explicit acceptance criteria and a determined execution path does the Agent start real work.

It won't interrupt work already in progress — the Agent simply continues the current stage. The two paths below describe the full first-time flow.

### Path A: Lightweight solo path (vibe-coding / indie maker)

If you already have a local project, or just an idea you want to iterate on quickly with an Agent, you can start directly from a workflow template — no GitHub issue required.

1. Open the project repo in Conductor.
2. Tell Claude "check the Lincoln environment" — the Agent runs the environment check and lists missing dependencies.
3. Pick a template for your scenario:
   - **Existing source code, want the Agent to understand it before iterating**: use `existing-project-iteration`
   - **Just an idea, want to explore a solution/prototype first**: use `design-spike`
4. Tell Claude:
   - If you chose `existing-project-iteration`:
     > Please use Lincoln's `existing-project-iteration` template to help me understand the current codebase and plan the next feature iteration.
   - If you chose `design-spike`:
     > Please use Lincoln's `design-spike` template to help me clarify this idea and produce a design review and prototype.
5. If you later decide to adopt the team flow or need GitHub issue tracking, tell the Agent "start working on issue <N>" — it creates a new issue work package, and you hand the confirmed requirements/design artifacts from your solo path to it for filing into the new `issue-<number>/` directory.

> Solo-path artifacts land in the work-package directory chosen automatically by the template (e.g. workspace name or repo name): codebase-knowledge artifacts go to `knowledge/`, while design, requirements, and research artifacts go to `<process_slug>/designs/`, `<process_slug>/requirements/`, and `<process_slug>/docs/research/` respectively.

### Path B: Team issue path (default)

On GitHub, click **Use this template** to create your project repo, then clone it into a local Conductor workspace.

#### Initialize an issue work package

Every requirement maps to one GitHub issue and one Lincoln feature branch. Tell the Agent "start working on issue <N>" — it creates a branch from the issue number and generates the issue-specific work-package directory (initializing `workflow-stage.yaml` and the document index `documents.yaml`; the `.tpl` templates under `.claude/templates/issue-package/` stay read-only and are no longer copied into the package — agents consult them for format and author documents directly).

You can also provide finer preferences, and the Agent translates them into the corresponding init parameters:

- Interview/requirements session ID (format `YYYY-MM-DD-descriptive-name`; auto-generated if omitted)
- Design topic ID (kebab-case; auto-generated if omitted)
- Work-package directory name (defaults to `issue-<number>`)
- Workflow template (under `.claude/workflows/`; defaults to `interview-to-knowledge`)
- Whether to push the branch to remote after initialization

> You can also start workflows via `lc-wf-*` skills: tell the Agent "list all workflows" or "start issue <N> with interview-to-knowledge". Team workflows are equivalent to initializing an issue work package, while solo workflows create session-scoped instances under `.context/workflow/` (gitignored, not shared across members). See [`.claude/workflows/README.md`](.claude/workflows/README.md).

After running, the branch contains:

```
issue-<N>/
├── workflow-stage.yaml          # issue runtime state & handoff protocol
├── documents.yaml               # document index: per-stage artifacts & human-approval status (auto-generated)
├── recordings/                  # raw recordings (gitignored)
├── interviews/<session-id>/     # transcripts, summaries, raw insights
├── requirements/<session-id>/   # requirements docs, user stories, PRD
├── designs/<design-id>/         # design review, scenarios, data model, flows, prototype, TDD plan
├── openspec/changes/            # OpenSpec change proposals
├── docs/research/               # OSS research notes, decision records
└── handoffs/                    # stage handoff documents
```

`issue-<N>/workflow-stage.yaml` is the stage handoff protocol shared between humans and Agents; `.claude/templates/issue-package/workflow-stage.yaml` is only the template used to generate it. `issue-<N>/documents.yaml` is the package document index, refreshed automatically on every state save, recording each artifact's stage, gate, and human-confirmation status — an Agent reads it first to learn which documents already exist in the package.

**Cross-member, cross-Agent collaboration**: branch names must strictly follow the `issue-<number>` convention. When any member or Agent receives a handoff from an upstream node, the branch name alone locates the issue and its work package (`{process_slug}/workflow-stage.yaml`), keeping issue, branch, and PR in end-to-end one-to-one correspondence from requirements to final acceptance. Tell the Agent "list all active Lincoln branches" to view the stage status and waiting-on of all active issue branches.

> Full template documentation lives in [`.claude/workflows/README.md`](.claude/workflows/README.md). Workflow templates are scenario references: a human may ask the Agent to follow a specific workflow for the current scenario — automatic routing is not enforced.

---

## Natural-Language Interaction

Lincoln is an AI-Native workflow — **you never need to type commands in a terminal**. Describe your intent in plain language and the Agent translates it into the right script and runs it for you; you can also invoke skills explicitly with `/lc-*` in your agent harness:

| You say | Agent does |
|---------|------------|
| "Start working on issue 55" | `/lc-wf-interview-to-knowledge` (or `/lc-init-branch`) sets up the branch and work package |
| "What's the status?" | `/lc-status` reports current stage, waiting-on, and next step |
| "Submit this stage's artifacts" | `/lc-stage` records artifacts and refreshes `documents.yaml` |
| "Approved" | `/lc-stage` marks the current gate after explicit human-PM approval |
| "Generate the handoff" | `/lc-handoff` writes the handoff document |
| "Move to the next stage" | Agent checks the gate, then transitions |
| "Check the Lincoln environment" | `/lc-setup` checks dependencies and lists what's missing |
| "List all active branches" | Agent lists the stage status and waiting-on of all issue branches |
| "Audit workflow health" | Agent outputs a PASS/WARN/FAIL health report |

The `/lc-stage` skill covers the full stage-lifecycle intent mapping. Underlying scripts are always executed by the Agent — users never need to know them.

## What's New (v1.2.0)

- **Issue-driven work packages**: `scripts/init-lincoln-branch.sh --issue-number ...` creates an issue-specific branch and `{process_slug}/` work package, so process documents no longer pollute `main`.
- **Templated work packages**: `.claude/templates/issue-package/` provides a unified directory structure and read-only `.tpl` reference templates (no longer copied into the package at init; agents consult them on demand).
- **Package document index**: `{process_slug}/documents.yaml` is refreshed automatically by `scripts/lincoln_documents.py` on every state save, recording per-stage artifacts and their gate / human-confirmation status.
- **Main merge-hygiene check**: `scripts/check-main-merge-hygiene.py` (the CI gate for PRs → main) rejects every file under any directory containing `workflow-stage.yaml`, preventing issue work packages from being merged into main by mistake.
- **Instantiated state files**: runtime state lives in `{process_slug}/workflow-stage.yaml`, not `.claude/workflow-stage.yaml`.
- **Unified workflow entry `lc-wf-*`**: [`.claude/workflows/README.md`](.claude/workflows/README.md) maintains all SOP templates; `lc-wf-*` commands (backed by `scripts/lincoln_workflow.py`) unify how solo / team `execution_mode` workflows start.
- **Local recording & transcription CLI**: `tools/lincoln-record/` (Rust + whisper-rs/Metal + speaker diarization) provides local recording and transcription, alongside the redesigned `tools/lincoln/` TUI.
- **Multi-harness adaptation**: role contracts, `lc-*` commands, and stage workflows can be derived for codex / opencode — see [Multi-harness support](#multi-harness-support-codex--opencode) below.
- **Claude Code plugin packaging**: a new `.claude-plugin/` manifest allows installing Lincoln as a Claude Code plugin.

## What's New (Unreleased)

- **Session opening guidance**: when Lincoln has no drivable work state (fresh repo or a work package that hasn't started), the session-start hook injects opening guidance — the Agent does an overview-level recon first (≤ 8 read-only operations, no source reading), presents a situation judgment (role / process position / problem / goal + confidence), confirms via the Johari window (≤ 3 questions per round), and starts work only once every goal has explicit acceptance criteria and a determined execution path; the README has switched to natural-language-only entry points to match.

---

## Workflow Status & Handoff

### Check the current branch status

Tell the Agent "what's the status" — it reports: current stage, waiting-on, loaded context, recommended skills, artifact status, next action. When you need machine-readable output, ask for JSON or Markdown format.

### Generate a handoff document

When pausing or switching collaborators, tell the Agent "generate the handoff" — it produces `.context/lc-handoff-<stage>.md` or `{process_slug}/handoffs/` documents containing the current stage, confirmed artifacts, open questions, next role, and recommended skills.

After a stage passes human confirmation, tell the Agent "approved" — it marks that stage's gate as approved.

### List all in-flight Lincoln branches

Tell the Agent "list all active Lincoln branches"; to see only the branches waiting on you, say "which branches are waiting on me".

### Audit workflow health

Tell the Agent "audit workflow health" — it outputs a PASS/WARN/FAIL report covering state consistency, artifact completeness, gate compliance, skill coverage, and anomaly detection.

---

## Framework Docs

Lincoln's core definitions are inlined in `.claude/`:

- [`.claude/stages/`](.claude/stages/) — registry and capability boundaries for Stages, Gates, Artifacts, and Roles: one `<stage-id>.yaml` per stage, whose `skills` field derives the stage-to-skill mapping.
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — index and routing notes for all SOP workflow templates.
- [`.claude/schemas/`](.claude/schemas/) — JSON Schemas for `workflow-stage`, `stage-definition`, and `workflow-template`.
- [`CLAUDE.md`](CLAUDE.md) — Agent startup self-check, human-gate rules, handoff protocol, skill invocation rules.

---

## Branch-Level Workflow & Stage State

- Each requirement uses its own Lincoln feature branch (named `issue-<N>`, where N is the GitHub issue number).
- Stage state is committed with the branch, stored in `{process_slug}/workflow-stage.yaml`.
- Process documents (`recordings/`, `interviews/`, `requirements/`, `designs/`, `openspec/`, `docs/research/`) travel with the feature branch and are **never merged to `main`**.
- The current owner pushes the feature branch after advancing stages locally; downstream roles check out the same branch to continue.
- Every stage's context is defined in `.claude/stages/<stage-id>.yaml` (role, skills, gates, and artifact contracts inlined).

At Agent startup, `.claude/hooks/on-session-start.sh` automatically resolves `{process_slug}/workflow-stage.yaml`, loads the current stage context, reads handoff documents, and injects recommended skills — no need to manually read README then CLAUDE.md.

---

## Workflow Overview

### Full team pipeline

```
Interview recording → Transcript & summary → Requirements clarification → Product design → Pencil prototype → TDD development plan → OpenSpec proposal → GitHub Issues → Implementation → PR merge → Obsidian knowledge base
```

### Lightweight solo pipeline (vibe-coding)

```
Idea / local code → Requirements clarification → Design review → TDD plan → Implementation → Local verification → Knowledge sync
```

The solo path can skip interview recordings, OpenSpec proposals, and GitHub issue splitting, iterating directly with the Agent on the project at hand; when upgrading to team collaboration, fill in the intermediate stages.

For template selection details see [`.claude/workflows/README.md`](.claude/workflows/README.md).

---

## Tools

Lincoln ships two companion tools:

- `tools/lincoln/` — Ink/React-based TUI recording frontend (the `lincoln` CLI).
- `tools/lincoln-record/` — Rust local recording & transcription CLI (whisper-rs + Metal acceleration, speaker diarization); recommended for local interview transcription. Models are downloaded via the hf-mirror.com mirror.

Install and usage instructions live in each directory's README or `--help`.

---

## Directory Structure

```
.
├── issue-<number>/                     # issue work package (team/collaboration; solo vibe-coding may start with the template-chosen package directory and migrate later)
│   ├── workflow-stage.yaml             # issue runtime state & handoff protocol
│   ├── documents.yaml                  # document index: per-stage artifacts & human-approval status (auto-generated)
│   ├── recordings/                     # raw audio (gitignored)
│   ├── interviews/<session-id>/        # transcripts & summaries
│   ├── requirements/<session-id>/      # requirements documents
│   ├── designs/<design-id>/            # design docs, Pencil prototype, TDD plan
│   ├── openspec/changes/               # OpenSpec change proposals
│   ├── docs/research/                  # research & decision records
│   └── handoffs/                       # stage handoff documents
├── knowledge/                          # project-level Obsidian vault (merged to main)
├── products/                           # product code placeholder
├── oss/                                # open-source candidate tracking
├── .claude/                            # Claude Code system-prompt layer (auto-loaded)
│   ├── agents/                         # Agent role templates
│   ├── hooks/                          # lifecycle hooks (wired by settings.json)
│   ├── schemas/                        # JSON Schema validation
│   ├── skills/                         # native skills (incl. dependencies.yaml)
│   ├── stages/                         # stage contexts
│   ├── templates/issue-package/        # issue work-package templates
│   ├── workflows/                      # SOP workflow templates
│   │   └── README.md (workflow index)   # ← route here for all templates
│   ├── settings.json                   # Claude Code project settings
├── .context/                           # session-scoped temp files (gitignored), incl. solo workflow instances .context/workflow/<name>.yaml
├── .github/                            # issue templates, Actions, OpenSpec config
├── scripts/                            # initialization, status, audit tools
├── tests/                              # pytest test suite
└── tools/                              # lincoln TUI + lincoln-record (Rust)
```

---

## Dependencies

- `python3` (≥3.10 recommended)
- `node` ≥ 20 (for `tools/lincoln/`)
- `gh` CLI (authenticated)
- `openspec` CLI: `npm install -g @fission-ai/openspec`
- `ffmpeg` (optional, only for recording transcription)
- Rust toolchain (`cargo`, optional, only to build the `tools/lincoln-record/` local transcription CLI; local transcription is provided by the bundled whisper-rs — no Python Whisper dependency needed)
- Pencil app or Pencil MCP (for `.pen` prototypes)
- `ecc` CLI (from everything-claude-code)
- Obsidian (optional, for browsing the vault visually)

Benchmark (optional): Lincoln ships a workflow-benchmarking entry point — when you need it, tell the Agent "run the benchmark" to learn the usage.

Lincoln also depends on several external skills/CLIs — see `.claude/skills/dependencies.yaml`. After installing or upgrading, tell the Agent "check the Lincoln environment".

---

## Installing as a Claude Code Plugin

Lincoln can be installed as a Claude Code plugin. Manifests live in `.claude-plugin/`:

- `.claude-plugin/plugin.json` — plugin metadata and skill entry points.
- `.claude-plugin/marketplace.json` — marketplace registration info.

The install method depends on your Claude Code plugin manager (e.g. oh-my-claudecode). Usually, referencing this repo as a plugin source is enough.

---

## Multi-harness support (codex / opencode)

Lincoln's end-to-end logic (role contracts, stage workflows, `lc-*` commands) can be adapted to codex and opencode. `.claude/` is the single source of truth; harness artifacts are derived by the adapter from `.claude/harnesses/<name>.yaml` manifests — **never edit generated artifacts by hand**.

Tell the Agent "generate the codex adaptation" or "generate the opencode adaptation" (or say "generate both harness adaptations at install time" to do it in one step). Generated artifacts: for codex, `AGENTS.md` and `~/.codex/prompts/lc-*.md`; for opencode, `.opencode/agent/*.md` and `.opencode/command/lc-*.md`.

Generated artifacts are not committed to git (`.opencode/` and `AGENTS.md` are in `.gitignore`). CI verifies that manifests can be generated and local artifacts haven't drifted.

Gates and CI stay lightweight: stage progression is always performed by the Agent through stage validation, already written into each harness's command templates; human_gate stages still require explicit human PM confirmation.

### Command naming migration: `lincoln-*` → `lc-*` (breaking)

Skill/command entry points have been renamed from `lincoln-*` to `lc-*` (e.g. `lincoln-status` → `lc-status`). The environment check (tell the Agent "check the Lincoln environment") scans for old directories under `~/.claude/skills/` and prints a migration hint; after confirming there are no local changes, delete the old directories manually. Underlying script file names are unchanged and transparent to the Agent.

---

## Conventions & Constraints

- At Agent startup, `.claude/hooks/on-session-start.sh` automatically loads the current stage context — no need to traverse every file manually.
- Behavioral contracts live in [`CLAUDE.md`](CLAUDE.md); stage-level context lives in `.claude/stages/<stage-id>.yaml`.
- `human_gate: true` stages require explicit final human confirmation before proceeding.
- Stage exit validation runs via `scripts/validate_stage.py`.

---

## Extending & Contributing to Lincoln

Lincoln's `.claude/` is an open system-prompt layer — contributions built on the same meta-model are welcome:

- **Agent role templates** (`.claude/agents/`): define new role behaviors and contexts for specific scenarios.
- **Skills** (`.claude/skills/`): package methodology sub-skills or Lincoln-native skills.
- **Hooks lifecycle extensions** (`.claude/hooks/`): inject custom logic at session start, before/after tool calls, etc.
- **Workflow templates** (`.claude/workflows/`): define complete stage sequences from requirements input to knowledge distillation for different scenarios.

Before submitting a PR, please consult:

- [`CLAUDE.md`](CLAUDE.md) — Agent contract, human-gate rules, and artifact conventions.
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — steps for adding a workflow template.
- [`.claude/stages/`](.claude/stages/) — registry of stages, gates, artifacts, and roles; each `<stage-id>.yaml`'s `skills` field derives the stage-to-skill mapping.
- [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml) — external skill and CLI dependency manifest.

> Tip: when adding a workflow template, also update the quick-routing table and template details in `.claude/workflows/README.md`; when adding skills or hooks, ensure compatibility with `.claude/settings.json` and `dependencies.yaml`, and add the necessary validation and tests.

---

## License & Third-Party Acknowledgments

Lincoln itself is released under the [MIT License](LICENSE), Copyright (c) 2026 苏尚lewis (sushanglewis).

Lincoln references the following open-source projects as external skills, plugins, and CLI dependencies (declared in [`.claude/skills/dependencies.yaml`](.claude/skills/dependencies.yaml), each used under its own license):

| Project | Source | Purpose | License |
|---|---|---|---|
| superpowers | [obra/superpowers](https://github.com/obra/superpowers) | general skills (brainstorming, TDD, etc.) | MIT |
| gsd | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | process skills (import, docs-update, etc.) | MIT |
| oh-my-claudecode | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | optional multi-agent orchestration plugin | MIT |
| openspec | [Fission-AI/openspec](https://github.com/Fission-AI/openspec) | change proposal CLI | MIT |
| gh | [cli/cli](https://github.com/cli/cli) | GitHub CLI | MIT |
| ffmpeg | [FFmpeg](https://ffmpeg.org/) | optional, recording transcription | LGPL/GPL (see website) |
| whisper-rs | [tazz4843/whisper-rs](https://github.com/tazz4843/whisper-rs) | optional, local speech transcription for `tools/lincoln-record/` (whisper.cpp bindings) | MIT |

External agent definitions are synced by `scripts/sync-external-agents.sh` per manifest; sources and licenses are listed in [`.claude/agents/external/NOTICES.md`](.claude/agents/external/NOTICES.md) (everything-claude-code, oh-my-claudecode, wshobson/agents — all MIT).

---

## Learn More

- [OpenSpec docs](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
- [`.claude/workflows/README.md`](.claude/workflows/README.md) — overview of Lincoln workflow templates
