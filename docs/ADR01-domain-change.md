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
  influences to economy)
- Clear split between stable policies and changing operational data
- Better demonstrates the constitutional framework concept

**Why Simplify the Schema?**
- Current schema has too many overlapping fields (subject, entity, trigger, conditions)
- Simpler structure is easier to understand, maintain and access
- Reduces complexity for demonstration purposes


## Decision

We will migrate the project from the health insurance domain to the banking domain and
simultaneously simplify the constitutional schema.

### New Simplified Constitution Schema

```json
{
  "id": "string",           // Unique identifier (e.g., "RULE-001")
  "condition": "string",    // When this rule applies (trigger + conditions)
  "consequence": "string",  // What happens when the condition is met
  "description": "string"   // Human-readable explanation of the rule
}
```

eg.

```json
  {
    "id": "A001",
    "condition": "Political instability in a country",
    "consequence": "Economic recession",
    "description": "Instability often disrupts markets and investor confidence, leading to downturns."
  },
```

### New Simplified Reality Schema

```json
{
  "id": "string",
  "title": "string",
  "description":  "string"
},
```

eg.

```json

{
  "id": "S001",
  "title": "Inflation",
  "description":  "Current inflation in Switzerland is elevated at 7.5%."
},
{
  "id": "S002",
  "title": "Employment rate",
  "description": "Unemployment rate in Switzerland is 5%."
}
```

