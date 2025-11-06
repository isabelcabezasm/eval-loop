# ADR-001: Migration from Health Insurance to Banking Domain with Schema Simplification

## Status
Proposed

## Date
2025-11-06

## Context
The Constitutional Q&A Agent was originally built for health insurance but needs to
change domains for better architectural fit:

**Why Change from Health Insurance?**
- Health insurance rules rarely change, making the "constitutional vs. reality"
  distinction unclear
- The domain doesn't showcase the system's core value of handling both stable rules and
  dynamic data

**Why Banking Works Better**
- Banking was the original intended domain
- Banking reality changes frequently (rates, inflation, political changes that
  influence the economy)
- Clear split between stable policies and changing operational data
- Better demonstrates the constitutional framework concept

**Why Simplify the Schema?**
- Current schema has too many overlapping fields (subject, entity, trigger, conditions)
- Simpler structure is easier to understand, maintain and access
- Reduces complexity for demonstration purposes
- We start with the bare minimum in both schemas: id and description for the first
  iteration, and will add complexity only if data-driven experiments show it improves
  performance or helps the LLM


## Decision

We will migrate the project from the health insurance domain to the banking domain and
simultaneously simplify the constitutional schema.

### New Simplified Constitution Schema

```json
{
  "id": "string",           // Unique identifier for the axiom (e.g., "A001")
  "description": "string"   // Explanation of the rule
}
```

eg.

```json
  {
    "id": "A001",
    "description": "Instability often disrupts markets and investor confidence,
    leading to downturns."
  },
```

### New Simplified Reality Schema

```json
{
  "id": "string",           // Unique identifier for the reality (e.g., "R001")
  "description":  "string"  // Explanation of the reality
}
```

eg.

```json
{
  "id": "R001",
  "description":  "Current inflation in Switzerland is elevated at 7.5%."
},
{
  "id": "R002",
  "description": "Unemployment rate in Switzerland is 5%."
}
```

