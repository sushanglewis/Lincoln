# lc-research-scope prompt

You are executing the Lincoln workflow step `lc-research-scope`: define the research brief for a PM-led research workflow.

## Goal

Produce `{process_slug}/research/{session_id}/scope.md` that becomes the single source of truth for all subsequent research stages.

## Inputs

- `session_id`: the research session identifier
- Optional topic, questions, or context provided by the human PM
- Any existing requirements, interviews, designs, or knowledge documents in `{process_slug}/`

## Steps

1. Create `{process_slug}/research/{session_id}/` if it does not exist.
2. Read any existing context that could shape the research (requirements, interview summaries, knowledge notes).
3. Draft `scope.md` using the template below.
4. Identify 1-3 ambiguities and tag each with its Johari quadrant:
   - 知道自己知道 → confirm with the PM
   - 知道自己不知道 → ask directly and coach
   - 不知道自己知道 → surface existing assets
   - 不知道自己不知道 → probe with concrete scenarios
5. Ask the human PM at most 3 questions per turn to converge on scope.
6. Update `scope.md` after each answer.
7. Repeat until the PM confirms the scope is ready.
8. When confirmed, append `<!-- status: approved -->` to `scope.md`.

## Output template

```markdown
# Research Scope: <Title>

## Background

<决策背景与研究动机>

## Research Questions

1. <问题 1>
2. <问题 2>
3. <问题 3>

## Scope Inclusions

- <明确包含的内容>

## Scope Exclusions

- <明确不包含的内容，避免范围蔓延>

## Stakeholders

- <谁使用、谁买单、谁建设、谁维护（初步）>

## Analysis Frameworks

- <初步建议使用的分析框架>

## Acceptance Criteria

1. <怎样算研究完成>
2. <需要产出哪些 artifact>
3. <决策点是什么>

## Risks & Assumptions

- <关键假设>
- <可能风险>
```

## Human Interaction Rules

- Ask at most 3 questions per turn.
- After each answer, update the document and show the changed sections.
- Do not proceed to the next step until the PM explicitly confirms (e.g., says "confirm" or "确认").

## Exit Criteria

- `scope.md` is approved by the human PM.
- Research questions and acceptance criteria are explicit and decision-oriented.
