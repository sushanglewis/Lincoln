# lc-analyze-frameworks prompt

You are executing the Lincoln workflow step `lc-analyze-frameworks`: select and apply analysis frameworks to the research.

## Goal

Produce `{process_slug}/research/{session_id}/analysis-frameworks.md` that selects the right frameworks, applies them, and specifies how to visualize the results (ECharts or HTML).

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/first-principles.md`
- `{process_slug}/research/{session_id}/stakeholders.md`

## Steps

1. Read prior documents.
2. From the framework catalog, select 2-4 frameworks suited to the decision:
   - SWOT — for strategic positioning
   - Porter's Five Forces — for market attractiveness
   - Business Model Canvas — for value creation logic
   - PEST — for macro context
   - User Analysis (jobs-to-be-done, personas) — for demand side
   - Custom multi-dimensional framework — when none of the above fit
3. Justify each selection in one sentence.
4. Apply each framework using the evidence collected so far; note gaps.
5. For each framework, specify the best visualization:
   - SWOT → quadrant matrix (HTML/CSS grid or ECharts custom series)
   - Porter's Five Forces → radar chart or horizontal bar (ECharts)
   - Business Model Canvas → HTML table/grid
   - PEST → 2x2 matrix or quadrant chart
   - User Analysis → persona cards or journey flow (HTML)
   - Custom → choose the most intuitive ECharts/HTML rendering
6. Optionally generate the actual HTML/ECharts file in `{process_slug}/research/{session_id}/visualizations/`.
7. Write `analysis-frameworks.md` using the template below.

## Output template

```markdown
# Analysis Frameworks: <Title>

## Selected Frameworks

| Framework | Why Selected | Key Dimensions | Visualization |
|-----------|--------------|----------------|---------------|
| SWOT      | ...          | ...            | quadrant matrix |
| ...       | ...          | ...            | ...           |

## Framework Applications

### SWOT

#### Strengths
- ...

#### Weaknesses
- ...

#### Opportunities
- ...

#### Threats
- ...

### Porter's Five Forces

| Force | Intensity | Evidence |
|-------|-----------|----------|
| ...   | ...       | ...      |

## Visualization Plan

- <file path and chart type for each framework>

## Generated Visualizations

- `{process_slug}/research/{session_id}/visualizations/swot.html`
- ...

## Implications

- <what the frameworks reveal>
```

## Rules

- Match the framework to the decision, not the other way around.
- Visualizations should be renderable in a browser (HTML/ECharts); embed data inline so they work offline.
- If generating HTML, include a concise title and legend.

## Exit Criteria

- `analysis-frameworks.md` selects and applies at least two frameworks.
- Each framework has a specified visualization format.
