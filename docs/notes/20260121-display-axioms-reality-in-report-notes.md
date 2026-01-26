# Notes: Display Axioms and Reality Items Text in Final Report

Plan: [20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md)

## Phase 1: Data Model Updates (Completed 2026-01-26)

### Summary

Implemented data model extensions to support storing axiom and reality definitions in evaluation
results:

1. **New Pydantic Models** - Added `AxiomItem` and `RealityItem` models in [src/eval/models.py](../../src/eval/models.py):
   - Both models have `id` (str) and `description` (str) fields with Field descriptions
   - Include comprehensive docstrings explaining their purpose

2. **Extended `EvaluationResult` Model** - Added two optional fields:
   - `axiom_definitions: list[AxiomItem] | None` - defaults to `None` for backward compatibility
   - `reality_definitions: list[RealityItem] | None` - defaults to `None` for backward compatibility

3. **TypeScript Type Definitions** - Checked for separate `.d.ts` files; only
   `src/ui/vite-env.d.ts` exists which is unrelated (contains Vite environment types)

4. **Unit Tests** - Created [tests/eval/test_models.py](../../tests/eval/test_models.py) with 28
   tests covering:
   - `AxiomItem`: creation, serialization (dict/JSON), validation errors, equality, JSON roundtrip
   - `RealityItem`: same coverage as AxiomItem
   - `EvaluationResult` with definitions: backward compatibility (without definitions), with axiom
     only, with reality only, with both, with empty lists, serialization, JSON roundtrip

5. **Backward Compatibility** - Updated existing tests in
   [tests/eval/test_report_generation.py](../../tests/eval/test_report_generation.py) to handle the
   new optional fields being populated with `None` values when the model validates data that
   doesn't include them. The Pydantic model adds these default values during `model_dump()`.

### Test Results

All 175 tests pass (28 new + 147 existing, with 5 existing tests updated for compatibility).

