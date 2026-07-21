# lc-stakeholder-research prompt

You are executing the Lincoln workflow step `lc-stakeholder-research`: identify and analyze the stakeholders surrounding the product decision.

## Goal

Produce `{process_slug}/research/{session_id}/stakeholders.md` that maps who uses, pays for, builds, and maintains the product, where they speak, and what they need.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/first-principles.md`

## Steps

1. Read the scope and first-principles documents.
2. List stakeholder categories:
   - End users (primary, secondary)
   - Economic buyers / budget owners
   - Builders / implementers
   - Maintainers / operators
   - Influencers / gatekeepers
3. For each stakeholder, identify:
   - Goals and pains
   - Where they publicly voice opinions (forums, Slack, X/Twitter, Reddit, GitHub, app stores, review sites, interviews)
   - Evidence of their voice (quotes, metrics, behavioral signals)
4. Use WebSearch / WebFetch / GitHub MCP to collect representative quotes and data points.
5. Write `stakeholders.md` using the template below.

## Output template

```markdown
# Stakeholder Research: <Title>

## Stakeholder Map

| Role | Who | Goals | Pains | Voice Channels | Evidence |
|------|-----|-------|-------|----------------|----------|
| ...  | ... | ...   | ...   | ...            | ...      |

## Key Quotes

> "..." — source, channel, date

## Insight Summary

- <stakeholder tension 1>
- <stakeholder tension 2>

## Implications for Research

- <what this means for the product decision>
```

## Rules

- Every claim about a stakeholder must have a source.
- Distinguish observed behavior from inferred needs.
- Respect privacy: do not scrape private communities without authorization.

## Exit Criteria

- `stakeholders.md` covers all relevant stakeholder categories.
- Each category links to at least one voice channel and one piece of evidence.
