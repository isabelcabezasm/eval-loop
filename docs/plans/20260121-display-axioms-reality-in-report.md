# Plan: Display Axioms and Reality Items Text in Final Report

## Overview

The final report currently shows axiom and reality references by their IDs (e.g., `A-001`, `R-001`)
but does not display the actual text content (descriptions) of these items. This plan outlines the
implementation needed to display the full text of constitutional axioms and reality item
descriptions in the final HTML report.

### Current State

- **Axioms** are stored in `data/constitution.json` as objects with `id` and `description` fields
- **Reality items** are stored in `data/reality.json` as objects with `id` and `description` fields
- The report template (`src/eval/report_generation/templates/`) renders axiom/reality references
  as ID tags only
- The `renderReferences()` function in `script.js` displays expected and found references as tags
  without descriptions
- The evaluation data (`EvaluationResult` model in `src/eval/models.py`) contains reference IDs
  but not descriptions

## Phase 1: Data Model Updates ✅

- [x] Task 1.1: Create new Pydantic models for axiom and reality items with full content
  (`AxiomItem`, `RealityItem`)
- [x] Task 1.2: Add optional `axiom_definitions` list to `EvaluationResult` model to store all
  axiom items with text
- [x] Task 1.3: Add optional `reality_definitions` list to `EvaluationResult` model to store all
  reality items with text
- [x] Task 1.4: Update any TypeScript type definitions if separate `.d.ts` files exist
  (N/A - no separate TypeScript type definitions for these models)
- [x] Task 1.5: Create unit tests for new `AxiomItem` and `RealityItem` models
  (validation, serialization)
- [x] Task 1.6: Create unit tests for `EvaluationResult` with axiom/reality definitions
  (with and without definitions for backward compatibility)
- [x] Task 1.7: Testing - Run existing tests to ensure data model changes maintain backward
  compatibility

## Phase 2: Evaluation Pipeline Updates ✅

- [x] Task 2.1: Identify where the evaluation result JSON is generated
  (likely in `src/eval/eval.py` or `src/eval/main.py`)
- [x] Task 2.2: Load axiom definitions from `data/constitution.json` during evaluation
- [x] Task 2.3: Load reality definitions from `data/reality.json` during evaluation
- [x] Task 2.4: Include axiom and reality definitions in the evaluation result output JSON
- [x] Task 2.5: Create unit tests for axiom loading function (valid file, missing file, invalid JSON)
- [x] Task 2.6: Create unit tests for reality loading function (valid file, missing file, invalid JSON)
- [x] Task 2.7: Modify existing evaluation pipeline tests to verify definitions are included in output
- [x] Task 2.8: Testing - Verify the generated `evaluation_data.json` includes axiom and reality
  definitions

## Phase 3: Report UI - Add Axioms/Reality Summary Section

- [x] Task 3.1: Add a new summary section to `templates/index.html` for displaying axiom definitions
- [x] Task 3.2: Add a new summary section to `templates/index.html` for displaying reality definitions
- [x] Task 3.3: Add CSS styles for the new definitions sections in `templates/styles.css`
- [x] Task 3.4: Create `renderAxiomDefinitions()` function in `script.js` to render axiom list
  with ID and description
- [x] Task 3.5: Create `renderRealityDefinitions()` function in `script.js` to render reality item
  list with ID and description
- [x] Task 3.6: Call the new render functions from the main initialization in `script.js`
- [x] Task 3.7: Create JavaScript unit tests for `renderAxiomDefinitions()` function
  (empty list, valid list, missing data)
- [x] Task 3.8: Create JavaScript unit tests for `renderRealityDefinitions()` function
  (empty list, valid list, missing data)
- [x] Task 3.9: Testing - Verify new sections appear correctly in generated report

## Phase 4: Report UI - Enhance Reference Display

- [x] Task 4.1: Update `renderReferences()` function to accept definitions lookup map as parameter
- [x] Task 4.2: Modify axiom reference tags to show tooltip or inline description text
- [x] Task 4.3: Modify reality reference tags to show tooltip or inline description text
- [x] Task 4.4: Add CSS for tooltips or expandable descriptions on reference tags
- [x] Task 4.5: Update existing `renderReferences()` JavaScript tests to cover new definitions
  parameter
- [x] Task 4.6: Create JavaScript unit tests for tooltip/description display
  (with definitions, without definitions, missing ID)
- [x] Task 4.7: Testing - Verify reference tags show descriptions correctly

## Phase 5: Edge Cases and Polish

- [x] Task 5.2: Handle case where a referenced ID is not found in definitions (show ID only)
- [x] Task 5.3: Add collapsible/expandable behavior for definitions sections if they become too long
- [x] Task 5.4: Ensure responsive layout works on different screen sizes
- [x] Task 5.5: Create Python integration tests for report generation with missing/empty definitions
- [x] Task 5.6: Create JavaScript unit tests for edge cases
  (null definitions, undefined fields, empty arrays)
- [x] Task 5.7: Testing - Run full test suite and manually verify report with various edge cases

## Phase 6: Documentation and Cleanup ✅

- [x] Task 6.1: Update README or docs with information about new report features
- [x] Task 6.2: Add JSDoc comments for new JavaScript functions
- [x] Task 6.3: Add docstrings for new Python models/functions
- [x] Task 6.4: Review test coverage and add any missing test cases
- [x] Task 6.5: Testing - Final test run to ensure all tests pass (Python and JavaScript)

## Files to Modify

| File                                              | Changes                                                          |
| ------------------------------------------------- | ---------------------------------------------------------------- |
| `src/eval/models.py`                              | Add `AxiomItem`, `RealityItem` models; extend `EvaluationResult` |
| `src/eval/eval.py` or `src/eval/main.py`          | Load and include axiom/reality definitions in output             |
| `src/eval/report_generation/templates/index.html` | Add sections for axiom/reality definitions                       |
| `src/eval/report_generation/templates/script.js`  | Add render functions and enhance reference display               |
| `src/eval/report_generation/templates/styles.css` | Add styles for new sections and tooltips                         |

## Success Criteria

1. The final HTML report displays a "Constitutional Axioms" section listing all axioms with their
   IDs and full descriptions
2. The final HTML report displays a "Reality Items" section listing all reality items with their
   IDs and full descriptions
3. Axiom reference tags in evaluation items show or link to the full description text
4. Reality reference tags in evaluation items show or link to the full description text
5. All existing tests continue to pass
6. The report gracefully handles missing or incomplete data (backward compatibility)
7. The new sections are visually consistent with the existing report styling
8. The report remains usable and readable with the additional content
