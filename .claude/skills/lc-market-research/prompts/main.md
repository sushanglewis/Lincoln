# lc-market-research prompt

You are executing the Lincoln workflow step `lc-market-research`: analyze the market context for the product decision.

## Goal

Produce `{process_slug}/research/{session_id}/market.md` describing market size, trends, segments, and dynamics.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/first-principles.md`
- `{process_slug}/research/{session_id}/stakeholders.md`

## Steps

1. Read prior research documents.
2. Define the addressable market:
   - TAM / SAM / SOM if data is available
   - Key segments and their growth rates
3. Identify macro trends (technology, regulation, behavior, economics) that affect the market.
4. Map the value chain and key players.
5. Use WebSearch / WebFetch to find authoritative reports and data sources.
6. Write `market.md` using the template below.

## Output template

```markdown
# Market Research: <Title>

## Market Definition

<what market are we in and why>

## Market Size

| Metric | Value | Source | Year |
|--------|-------|--------|------|
| TAM    | ...   | ...    | ...  |
| SAM    | ...   | ...    | ...  |
| SOM    | ...   | ...    | ...  |

## Trends

1. **<Trend 1>** — implication: ...
2. **<Trend 2>** — implication: ...

## Segments

| Segment | Description | Size | Growth | Key Needs |
|---------|-------------|------|--------|-----------|
| ...     | ...         | ...  | ...    | ...       |

## Value Chain

- <step 1>
- <step 2>

## Sources

- <source 1>
- <source 2>

## Implications

- <what this means for the product>
```

## Rules

- Prefer primary or well-known secondary sources (industry reports, official statistics, reputable publications).
- Flag low-confidence numbers and assumptions.
- Cite all data points.

## Exit Criteria

- `market.md` is complete with cited sources.
- At least one trend and one segment are analyzed.
