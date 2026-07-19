---
name: lc-workflow-router
description: Use at the start of a Lincoln session to run session intake (recon, situation judgment, Johari confirmation) and select the most appropriate workflow template.
version: 1.1.0
---

# Lincoln Workflow Router

## Purpose

Using [lc-workflow-router] to run session intake and select the most appropriate workflow template.

Runs session intake on a cold start — overview recon (摸排), five-element situation judgment, Johari confirmation — then inspects the confirmed context and chooses a workflow template from `.claude/workflows/`.

## When to Use

- At session start when the hook injects 「=== Lincoln 开场引导 ===」(no state file, or `current_stage: not_started`).
- At session start when `<process_slug>/workflow-stage.yaml` has no `workflow.template`.
- When the human PM says "重新评估工作流" or asks to switch templates.

## Inputs

- `prompts/intake-prompt.md` — the intake procedure to run first on a cold start
- Repository root contents (overview recon only, ≤ 8 read-only operations)
- `<process_slug>/workflow-stage.yaml`
- Human's stated intent (interview, bug fix, design spike, existing project, etc.)

## Outputs

- `.context/lc-intake.md` — recon summary, situation judgment, confirmation record (session-level, gitignored)
- Recommended `workflow.template` name
- Recommended `current_run.current_stage`
- Confidence score and 1-3 confirmation questions if needed

## Rules

- On a cold start (hook guidance block or `current_stage: not_started`), follow `prompts/intake-prompt.md` BEFORE selecting a template; then continue with `prompts/router-prompt.md`.
- Do not proceed with any implementation until the PM confirms or overrides the recommended template.
- If context is ambiguous, prefer the simplest template that matches the stated intent.
- Document the reasoning in `current_run.context_assessment`.
- When reporting the routing decision to the PM, declare: `Using lc-workflow-router to select workflow: <name> because <reason>`, and record it in `.context/lc-intake.md`.
