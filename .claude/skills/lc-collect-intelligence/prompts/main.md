# lc-collect-intelligence prompt

You are executing the Lincoln workflow step `lc-collect-intelligence`: systematically gather authoritative information for the research.

## Goal

Produce `{process_slug}/research/{session_id}/collected-intelligence.md` that compiles evidence from authoritative sources, organized by research question and analysis framework.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/analysis-frameworks.md`
- Any prior research documents

## Steps

1. Read the scope and selected analysis frameworks.
2. For each research question and framework, derive an information checklist.
3. Gather information from authoritative sources:
   - Industry reports (Gartner, IDC, McKinsey, etc.)
   - Official product docs, blogs, release notes
   - Open API docs and changelogs
   - Public financial reports, investor decks
   - Reputable news and analysis sites
4. For each piece of evidence, record:
   - Claim / fact
   - Source URL
   - Source type
   - Confidence (high / medium / low)
   - Relevant research question
5. Write `collected-intelligence.md` using the template below.

## Output template

```markdown
# Collected Intelligence: <Title>

## Research Questions → Evidence

### Q1: <question>

| Claim | Source | Type | Confidence | Notes |
|-------|--------|------|------------|-------|
| ...   | ...    | ...  | ...        | ...   |

## Framework-Specific Evidence

### SWOT
- **Strengths evidence:** ...
- **Weaknesses evidence:** ...

## Information Gaps

- <what we still need to know>

## Source Index

1. <source 1>
2. <source 2>
```

## Rules

- Prioritize authoritative sources over anonymous opinions.
- Quote or paraphrase accurately; never fabricate sources.
- Mark low-confidence information explicitly.

## Exit Criteria

- `collected-intelligence.md` has evidence mapped to research questions.
- Every claim has a source and confidence rating.
