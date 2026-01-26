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


## Phase 2: Evaluation Pipeline Updates (Completed 2026-01-26)

### Summary

Implemented functions to load axiom and reality definitions during evaluation and include them in
the output JSON:

1. **Loading Functions** - Added in [src/eval/eval.py](../../src/eval/eval.py):
   - `load_axiom_definitions(file_path: Path | None = None) -> list[AxiomItem]`: Loads axioms from
     `data/constitution.json` (or custom path)
   - `load_reality_definitions(file_path: Path | None = None) -> list[RealityItem]`: Loads reality
     items from `data/reality.json` (or custom path)
   - Both functions include comprehensive docstrings and error handling for missing files,
     invalid JSON, and validation errors

2. **Updated `EvaluationResult` in eval.py** - Added optional fields to match models.py:
   - `axiom_definitions: list[AxiomItem] | None = None`
   - `reality_definitions: list[RealityItem] | None = None`

3. **Updated `calculate_stats` function** - Modified signature to accept definitions:
   - Added `axiom_definitions` and `reality_definitions` optional parameters
   - Includes definitions in returned `EvaluationResult` object
   - Maintains backward compatibility when definitions are not provided

4. **Updated `run_evaluation` function**:
   - Loads axiom and reality definitions at the start of evaluation
   - Passes definitions to `calculate_stats` for inclusion in output JSON

5. **Unit Tests** - Created [tests/eval/test_definition_loading.py](../../tests/eval/test_definition_loading.py)
   with 22 tests covering:
   - `load_axiom_definitions`: valid file, missing file, invalid JSON, missing/empty fields,
     empty array, default path, structure validation
   - `load_reality_definitions`: same coverage as axiom loading
   - `calculate_stats` with definitions: axiom only, reality only, both, without definitions
     (backward compat), empty results with definitions, JSON serialization

### Test Results

All 205 tests pass (22 new + 183 existing).

### Files Modified

| File | Changes |
| ---- | ------- |
| [src/eval/eval.py](../../src/eval/eval.py) | Added `load_axiom_definitions`, `load_reality_definitions`, updated `EvaluationResult`, `calculate_stats`, and `run_evaluation` |
| [tests/eval/test_definition_loading.py](../../tests/eval/test_definition_loading.py) | New test file with 22 tests |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 2 as complete |

