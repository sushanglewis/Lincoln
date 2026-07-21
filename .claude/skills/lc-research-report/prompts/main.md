# lc-research-report prompt

You are executing the Lincoln workflow step `lc-research-report`: synthesize all research artifacts into a final report.

## Goal

Produce `{process_slug}/research/{session_id}/report.md` that integrates the research scope, first principles, stakeholder map, market, product, competitive, framework, intelligence, and narrative into a decision-ready document.

## Inputs

- `session_id`: the research session identifier
- All prior research artifacts in `{process_slug}/research/{session_id}/`

## Steps

1. Read all prior research artifacts.
2. Write an executive summary with:
   - Core thesis
   - Key findings
   - Recommended decision
   - Key risks
3. Include sections for each research domain (scope, first principles, stakeholders, market, product, competitive, frameworks, intelligence, narrative).
4. Link every claim to evidence in the prior artifacts.
5. Add an appendix with all sources.
6. Write `report.md` using the template below.
7. Present the report to the PM for final approval.

## Output template

```markdown
# Research Report: <Title>

## Executive Summary

### Core Thesis
...

### Key Findings
1. ...
2. ...

### Recommendation
...

### Risks
- ...

## Background
...

## First Principles
...

## Stakeholder Insights
...

## Market Analysis
...

## Product Analysis
...

## Competitive Analysis
...

## Applied Frameworks
...

## Evidence Summary
...

## Narrative
...

## Next Steps
1. ...

## Appendix: Sources
- ...
```

## Human Interaction Rules

- Present the report to the PM for approval.
- Do not mark the stage complete until the PM explicitly confirms.

## Exit Criteria

- `report.md` is complete and approved by the human PM.
- Every recommendation links to evidence.
