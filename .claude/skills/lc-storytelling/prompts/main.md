# lc-storytelling prompt

You are executing the Lincoln workflow step `lc-storytelling`: structure the research findings into a compelling, evidence-based narrative.

## Goal

Produce `{process_slug}/research/{session_id}/narrative.md` that presents the research as a clear story using pyramid principle reasoning (thesis → sub-theses → evidence).

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/first-principles.md`
- `{process_slug}/research/{session_id}/analysis-frameworks.md`
- `{process_slug}/research/{session_id}/collected-intelligence.md`

## Steps

1. Read all prior research artifacts.
2. Identify the single core thesis (the answer to the research question).
3. Derive 3-5 supporting sub-theses. Each sub-thesis must be backed by evidence.
4. For each sub-thesis, list 2-4 pieces of evidence (data, quotes, analysis).
5. Arrange the narrative using one of these structures:
   - SCQA (Situation, Complication, Question, Answer)
   - Thesis → Sub-thesis → Evidence
   - Major premise → Minor premise → Conclusion
6. Add a story arc: setup → tension → turning point → resolution → call to action.
7. Write `narrative.md` using the template below.
8. Present the narrative to the PM for confirmation before writing the final report.

## Output template

```markdown
# Research Narrative: <Title>

## Core Thesis

<one-sentence conclusion>

## Story Arc

- **Setup:** ...
- **Tension:** ...
- **Turning point:** ...
- **Resolution:** ...
- **Call to action:** ...

## Supporting Sub-theses

### Sub-thesis 1: <statement>
- Evidence: ...
- Evidence: ...

### Sub-thesis 2: ...

## Logical Structure

- **Major premise:** ...
- **Minor premise:** ...
- **Conclusion:** ...

## PM Confirmation Questions

1. <Is this the right thesis?>
2. <Is the evidence sufficient?>
3. <What would make this story more convincing?>
```

## Human Interaction Rules

- Present the narrative and ask for PM confirmation.
- Do not proceed to the final report until the PM confirms the narrative.
- If the PM challenges a sub-thesis, return to the evidence and revise.

## Exit Criteria

- `narrative.md` has a confirmed core thesis and evidence-backed sub-theses.
