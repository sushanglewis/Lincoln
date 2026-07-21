# lc-first-principles prompt

You are executing the Lincoln workflow step `lc-first-principles`: explore the first principles behind the research topic.

## Goal

Produce `{process_slug}/research/{session_id}/first-principles.md` that captures the fundamental truths, unstated assumptions, and root causes beneath the research topic.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`

## Steps

1. Read the approved `scope.md`.
2. Ask: "What are we actually trying to decide?" "Why does this problem exist?" "What must be true for any solution to matter?"
3. List the explicit and implicit assumptions held by the PM, users, and team.
4. For each assumption, ask "Is this always true?" and "What would happen if it were false?"
5. Trace each assumption down to a first principle: a statement that cannot be reduced further within this context.
6. Identify 1-3 root causes or fundamental truths that reshape how the research should be framed.
7. Write `first-principles.md` using the template below.

## Output template

```markdown
# First-Principles Analysis: <Title>

## Decision Context

<复述 scope 中的决策背景>

## Explicit Assumptions

| Assumption | Why it is held | Evidence | Risk if false |
|------------|----------------|----------|---------------|
| ...        | ...            | ...      | ...           |

## Implicit Assumptions

- <unspoken beliefs that need surfacing>

## First Principles

1. **<Principle 1>**
   - Reasoning: <why it is fundamental>
   - Implication: <how it reframes the research>

## Root Causes

1. <Root cause 1>
2. <Root cause 2>

## Reframed Research Questions

1. <问题 1，基于第一性原理>
2. <问题 2>

## Questions for PM Confirmation

- <1-2 questions to confirm the reframing>
```

## Human Interaction Rules

- Present the reframed questions to the PM.
- Do not proceed until the PM confirms or refines the first-principles framing.
- If the PM disagrees with an assumption, capture the revised view and update the document.

## Exit Criteria

- `first-principles.md` is complete and confirmed by the PM.
- At least one implicit assumption has been surfaced and validated.
