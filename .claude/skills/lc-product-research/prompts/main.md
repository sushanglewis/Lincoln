# lc-product-research prompt

You are executing the Lincoln workflow step `lc-product-research`: research existing products and solutions relevant to the decision.

## Goal

Produce `{process_slug}/research/{session_id}/product.md` analyzing relevant products' capabilities, value propositions, and use cases.

## Inputs

- `session_id`: the research session identifier
- `{process_slug}/research/{session_id}/scope.md`
- `{process_slug}/research/{session_id}/first-principles.md`
- `{process_slug}/research/{session_id}/stakeholders.md`

## Steps

1. Read prior research documents.
2. Identify 3-7 relevant products or solution categories.
3. For each product, research:
   - Positioning and value proposition
   - Core capabilities and features
   - Target users and use cases
   - Pricing model (if public)
   - API / integration surface (if relevant)
4. Use WebSearch / WebFetch / GitHub MCP to gather official information.
5. Write `product.md` using the template below.

## Output template

```markdown
# Product Research: <Title>

## Products Analyzed

| Product | Category | Positioning | Target Users | Pricing |
|---------|----------|-------------|--------------|---------|
| ...     | ...      | ...         | ...          | ...     |

## Product Profiles

### 1. <Product A>

- **Value proposition:** ...
- **Core capabilities:** ...
- **Use cases:** ...
- **API / integration:** ...
- **Strengths:** ...
- **Weaknesses:** ...

### 2. <Product B>

...

## Capability Comparison

| Capability | Product A | Product B | Product C |
|------------|-----------|-----------|-----------|
| ...        | ...       | ...       | ...       |

## Sources

- <source 1>
- <source 2>

## Implications

- <what this means for our product>
```

## Rules

- Rely on official sources (product websites, docs, API references, pricing pages).
- Distinguish facts from marketing claims.
- Note information gaps.

## Exit Criteria

- `product.md` covers at least 3 relevant products.
- Each product has capabilities and use cases documented with sources.
