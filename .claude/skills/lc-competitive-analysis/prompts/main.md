# lc-competitive-analysis prompt

You are executing the Lincoln workflow step `lc-competitive-analysis`: analyze the competitive landscape.

## Goal

Produce `{process_slug}/research/{session_id}/competitive.md` with a structured competitive analysis, including positioning, SWOT, and differentiation opportunities.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/market.md`
- `{process_slug}/research/{session_id}/product.md`

## Steps

1. Read prior research documents.
2. Identify direct and indirect competitors.
3. For each competitor, summarize positioning, target segment, key strengths, and key weaknesses.
4. Build a SWOT for our product (or proposed product) in this competitive context.
5. Identify 2-4 differentiation opportunities.
6. Use WebSearch / WebFetch to verify claims.
7. Write `competitive.md` using the template below.

## Output template

```markdown
# Competitive Analysis: <Title>

## Competitor Landscape

| Competitor | Type | Positioning | Target Segment | Key Strengths | Key Weaknesses |
|------------|------|-------------|----------------|---------------|----------------|
| ...        | ...  | ...         | ...            | ...           | ...            |

## SWOT (Our Product)

### Strengths
- ...

### Weaknesses
- ...

### Opportunities
- ...

### Threats
- ...

## Differentiation Opportunities

1. **<Opportunity 1>**
   - Evidence: ...
   - How to exploit: ...

## Strategic Implications

- <what this means for positioning>
```

## Rules

- Be specific: avoid generic claims like "better UX" without evidence.
- Cite sources for competitor facts.
- Distinguish current state from future threats.

## Exit Criteria

- `competitive.md` includes a competitor table, SWOT, and at least two differentiation opportunities.
