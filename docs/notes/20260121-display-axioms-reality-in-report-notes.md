# Notes: Display Axioms and Reality Items Text in Final Report

Plan:
[20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md)

## Phase 1: Data Model Updates (Completed 2026-01-26)

### Summary

Implemented data model extensions to support storing axiom and reality
definitions in evaluation results:

1. **New Pydantic Models** - Added `AxiomItem` and `RealityItem` models in
   [src/eval/models.py](../../src/eval/models.py):
   - Both models have `id` (str) and `description` (str) fields with Field
     descriptions
   - Include comprehensive docstrings explaining their purpose

2. **Extended `EvaluationResult` Model** - Added two optional fields:
   - `axiom_definitions: list[AxiomItem] | None` - defaults to `None` for
   backward compatibility - `reality_definitions: list[RealityItem] | None` -
   defaults to `None` for backward compatibility

3. **TypeScript Type Definitions** - Checked for separate `.d.ts` files; only
   `src/ui/vite-env.d.ts` exists which is unrelated (contains Vite environment
   types)

4. **Unit Tests** - Created
   [tests/eval/test_models.py](../../tests/eval/test_models.py) with 28 tests
   covering:
   - `AxiomItem`: creation, serialization (dict/JSON), validation errors,
     equality, JSON roundtrip
   - `RealityItem`: same coverage as AxiomItem
   - `EvaluationResult` with definitions: backward compatibility (without
     definitions), with axiom only, with reality only, with both, with empty
     lists, serialization, JSON roundtrip

5. **Backward Compatibility** - Updated existing tests in
   [tests/eval/test_report_generation.py](../../tests/eval/test_report_generation.py)
   to handle the new optional fields being populated with `None` values when
   the model validates data that doesn't include them. The Pydantic model adds
   these default values during `model_dump()`.

### Test Results

All 175 tests pass (28 new + 147 existing, with 5 existing tests updated for
compatibility).


## Phase 2: Evaluation Pipeline Updates (Completed 2026-01-26)

### Summary

Implemented functions to load axiom and reality definitions during evaluation
and include them in the output JSON:

1. **Loading Functions** - Added in [src/eval/eval.py](../../src/eval/eval.py):
   - `load_axiom_definitions(file_path: Path | None = None) ->
     list[AxiomItem]`: Loads axioms from `data/constitution.json` (or custom
     path)
   - `load_reality_definitions(file_path: Path | None = None) ->
     list[RealityItem]`: Loads reality items from `data/reality.json` (or
     custom path)
   - Both functions include comprehensive docstrings and error handling for
     missing files, invalid JSON, and validation errors

2. **Updated `EvaluationResult` in eval.py** - Added optional fields to match
   models.py:
   - `axiom_definitions: list[AxiomItem] | None = None` - `reality_definitions:
   list[RealityItem] | None = None`

3. **Updated `calculate_stats` function** - Modified signature to accept
   definitions:
   - Added `axiom_definitions` and `reality_definitions` optional parameters
   - Includes definitions in returned `EvaluationResult` object
   - Maintains backward compatibility when definitions are not provided

4. **Updated `run_evaluation` function**:
   - Loads axiom and reality definitions at the start of evaluation
   - Passes definitions to `calculate_stats` for inclusion in output JSON

5. **Unit Tests** - Created
   [tests/eval/test_definition_loading.py](../../tests/eval/test_definition_loading.py)
   with 22 tests covering:
   - `load_axiom_definitions`: valid file, missing file, invalid JSON,
     missing/empty fields, empty array, default path, structure validation
   - `load_reality_definitions`: same coverage as axiom loading
   - `calculate_stats` with definitions: axiom only, reality only, both,
     without definitions (backward compat), empty results with definitions,
     JSON serialization

### Test Results

All 205 tests pass (22 new + 183 existing).

### Files Modified

| File | Changes |
| ---- | ------- |
| [src/eval/eval.py](../../src/eval/eval.py) | Added `load_axiom_definitions`, `load_reality_definitions`, updated `EvaluationResult`, `calculate_stats`, and `run_evaluation` |
| [tests/eval/test_definition_loading.py](../../tests/eval/test_definition_loading.py) | New test file with 22 tests |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 2 as complete |


## Phase 3: Report UI - Add Axioms/Reality Summary Section (Completed 2026-01-26)

### Summary

Implemented the UI sections to display axiom and reality definitions in the
evaluation report:

1. **HTML Template Updates** - Modified
   [index.html](../../src/eval/report_generation/templates/index.html):
   - Added `definitions-container` div with two-column grid layout
   - Created `axiom-definitions-section` with heading and
     `axiom-definitions-list` placeholder
   - Created `reality-definitions-section` with heading and
     `reality-definitions-list` placeholder
   - Positioned after summary stats and before evaluations container

2. **CSS Styling** - Added to
   [styles.css](../../src/eval/report_generation/templates/styles.css):
   - `.definitions-container`: Two-column responsive grid layout
   - `.definitions-section`: Card-style container with shadow and padding
   - `.definitions-section h3`: Section heading with bottom border
   - `.definitions-list`: Scrollable list with max-height for large datasets
   - `.definition-item`: Flex container with gap between ID and description
   - `.definition-id`: Styled ID badge (blue background, monospace font)
   - `.definition-text`: Text styling with light background
   - `.no-definitions`: Styled message for empty states
   - Responsive breakpoint for single-column on narrow screens

3. **JavaScript Render Functions** - Added to
   [script.js](../../src/eval/report_generation/templates/script.js):
   - Added JSDoc type definitions: `AxiomItem`, `RealityItem`
   - Updated `EvaluationData` typedef with optional `axiom_definitions` and
     `reality_definitions`
   - `renderAxiomDefinitions()`: Renders axiom list or "no definitions" message
   - `renderRealityDefinitions()`: Renders reality list or "no definitions"
     message
   - Both functions handle empty/undefined arrays gracefully
   - Added calls to both functions in main initialization

4. **Unit Tests** - Created
   [tests/ui/report-script.spec.ts](../../tests/ui/report-script.spec.ts):
   - Uses `@vitest-environment jsdom` for DOM testing
   - 8 tests covering both render functions:
     - Empty definitions message when undefined
     - Empty definitions message when empty array
     - Correct rendering of definition items
     - Error logging when container element is missing
   - Installed `jsdom` package as dev dependency

### Test Results

- All 30 JavaScript/TypeScript tests pass (8 new + 22 existing)
- All 209 Python tests pass
- All lint checks pass (ESLint, Prettier, Ruff)

### Files Modified

| File | Changes |
| ---- | ------- |
| [index.html](../../src/eval/report_generation/templates/index.html) | Added definitions container with axiom and reality sections |
| [styles.css](../../src/eval/report_generation/templates/styles.css) | Added ~80 lines of CSS for definitions styling |
| [script.js](../../src/eval/report_generation/templates/script.js) | Added JSDoc types, `renderAxiomDefinitions()`, `renderRealityDefinitions()`, initialization calls |
| [tests/ui/report-script.spec.ts](../../tests/ui/report-script.spec.ts) | New test file with 8 tests for render functions |
| [package.json](../../package.json) | Added `jsdom` as dev dependency |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 3 as complete |


## Phase 4: Report UI - Enhance Reference Display (Completed 2026-01-26)

### Summary

Enhanced the reference tags in evaluation items to show tooltips with
descriptions when hovering:

1. **New Helper Functions** - Added to
   [script.js](../../src/eval/report_generation/templates/script.js):
   - `buildDefinitionsMap(definitions)`: Builds a lookup map from definitions
     array for quick ID-to-description lookup. Works with both axiom (axiom_id)
     and reality (reality_id) items.
   - `renderReferenceTag(refId, tagClass, definitionsMap)`: Renders a single
     reference tag with optional tooltip. Escapes HTML entities in descriptions
     for safe attribute values.

2. **Updated `renderReferences()` Function**:
   - Added optional `definitionsMap` parameter to accept ID-to-description
     lookup map
   - Now uses `renderReferenceTag()` helper for consistent tag rendering with
     tooltips
   - Backward compatible - works without definitions map (no tooltips shown)

3. **Updated `renderEvaluation()` Function**:
   - Added `axiomDefinitionsMap` and `realityDefinitionsMap` parameters
   - Passes appropriate definitions map to each `renderReferences()` call

4. **Updated `renderEvaluations()` Function**:
   - Builds axiom and reality definitions maps from `window.evaluationData`
   - Passes maps to `renderEvaluation()` for each evaluation item

5. **CSS Tooltip Styling** - Added to
   [styles.css](../../src/eval/report_generation/templates/styles.css):
   - Pure CSS tooltips using `::after` pseudo-element with `data-tooltip`
     attribute
   - Dark tooltip bubble with arrow pointing down
   - Smooth fade-in transition on hover
   - Focus state support for keyboard accessibility
   - Max-width constraint with text wrapping for long descriptions

6. **Unit Tests** - Updated
   [tests/ui/report-script.spec.ts](../../tests/ui/report-script.spec.ts):
   - 17 new tests added (25 total, up from 8):
     - `buildDefinitionsMap`: 5 tests for empty, axiom, reality, and edge cases
     - `renderReferenceTag`: 4 tests for no tooltip, with tooltip, HTML
       escaping, tag classes
     - `renderReferences`: 8 tests for null/undefined, with/without
       definitions, empty states, tag classes, and partial definitions

### Test Results

- All 47 JavaScript/TypeScript tests pass (25 report-script + 22 existing)
- All 209 Python tests pass
- All lint checks pass (ESLint, Prettier, Ruff)

### Files Modified

| File | Changes |
| ---- | ------- |
| [src/eval/report_generation/templates/script.js](../../src/eval/report_generation/templates/script.js) | Added `buildDefinitionsMap()`, `renderReferenceTag()`, updated `renderReferences()`, `renderEvaluation()`, `renderEvaluations()` |
| [src/eval/report_generation/templates/styles.css](../../src/eval/report_generation/templates/styles.css) | Added ~70 lines of CSS for tooltip styling |
| [tests/ui/report-script.spec.ts](../../tests/ui/report-script.spec.ts) | Added 17 new tests for reference tag and tooltip functionality |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 4 as complete |


## Phase 5: Edge Cases and Polish (Completed 2026-01-26)

### Summary

Implemented edge case handling and UI polish including collapsible sections and
responsive layouts:

1. **Task 5.2: Handle Missing ID in Definitions**
   - Already implemented in Phase 4: `renderReferenceTag()` renders tags
     without tooltips when ID is not found in definitions map
   - Verified by existing tests: "should render tag without tooltip when no
     definition exists"

2. **Task 5.3: Collapsible Definitions Sections**
   - Updated
     [index.html](../../src/eval/report_generation/templates/index.html) to use
     new collapsible structure with headers and content divs
   - Added `toggleDefinitionsSection()` function to
     [script.js](../../src/eval/report_generation/templates/script.js) for
     toggle behavior
   - Added `setupDefinitionsKeyboardHandlers()` for keyboard accessibility
     (Enter/Space)
   - Added CSS styling for collapsible headers with toggle icons in
     [styles.css](../../src/eval/report_generation/templates/styles.css)

3. **Task 5.4: Responsive Layout**
   - Added responsive breakpoint at 600px for definitions sections
   - Adjusted padding, gaps, and definition item layout for smaller screens
   - Definition items stack vertically on narrow screens

4. **Task 5.5: Python Integration Tests**
   - Added 5 new tests to
     [test_report_generation.py](../../tests/eval/test_report_generation.py):
     - `test_report_generation_with_empty_definitions`
     - `test_report_generation_with_definitions`
     - `test_report_generation_missing_definitions_defaults_to_none`
     - `test_report_generation_with_axiom_only_definitions`
     - `test_report_generation_with_reality_only_definitions`
   - Added 2 new fixtures for test data with definitions

5. **Task 5.6: JavaScript Unit Tests for Edge Cases**
   - Added 19 new tests to
     [report-script.spec.ts](../../tests/ui/report-script.spec.ts):
     - Edge Cases - buildDefinitionsMap: null, non-array, null id, null
       description, undefined fields
     - Edge Cases - renderReferenceTag: empty refId, empty map, special chars,
       newlines
     - Edge Cases - renderReferences: empty arrays, zero precision/recall,
       decimal values
     - toggleDefinitionsSection: collapse, expand, aria-expanded toggling
     - Edge Cases - renderAxiomDefinitions: null, special characters
     - Edge Cases - renderRealityDefinitions: null, long descriptions

6. **Task 5.7: Full Test Suite Run**
   - All 214 Python tests pass
   - All 66 JavaScript tests pass (increased from 47)
   - Linting and formatting checks pass (Ruff, ESLint, Prettier)

### Test Results

- Python tests: 214 passed (5 new integration tests)
- JavaScript tests: 66 passed (19 new edge case tests)
- All lint checks pass

### Files Modified

| File | Changes |
| ---- | ------- |
| [src/eval/report_generation/templates/index.html](../../src/eval/report_generation/templates/index.html) | Added collapsible structure with headers and toggle icons |
| [src/eval/report_generation/templates/script.js](../../src/eval/report_generation/templates/script.js) | Added `toggleDefinitionsSection()`, `setupDefinitionsKeyboardHandlers()` |
| [src/eval/report_generation/templates/styles.css](../../src/eval/report_generation/templates/styles.css) | Added collapsible styling, responsive breakpoints for 600px |
| [tests/eval/test_report_generation.py](../../tests/eval/test_report_generation.py) | Added 5 integration tests + 2 fixtures for definitions edge cases |
| [tests/ui/report-script.spec.ts](../../tests/ui/report-script.spec.ts) | Added 19 edge case tests for definitions and collapsible sections |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 5 as complete |


### Bug Fixes During Phase 5

#### Bug 1: Axiom/Reality IDs Showing "undefined"

**Issue**: Reference tags displayed `undefined` instead of actual IDs (e.g.,
"A-001").

**Root Cause**: Field name mismatch between Python models and JavaScript code:
- Python `AxiomItem` and `RealityItem` models use `id` field
- JavaScript code incorrectly expected `axiom_id` and `reality_id` fields

**Fix**: Updated JavaScript code to use `item.id` instead of
`item.axiom_id`/`item.reality_id`:
- [script.js](../../src/eval/report_generation/templates/script.js): Fixed
  `buildDefinitionsMap()`, `renderAxiomDefinitions()`, and
  `renderRealityDefinitions()` functions
- [report-script.spec.ts](../../tests/ui/report-script.spec.ts): Updated all
  TypeScript interfaces and test data to use `id` field

#### Bug 2: Tooltips Cut Off by Container

**Issue**: Tooltips on axiom/reality reference tags were being cut off
(clipped) at the container boundary.

**Root Cause**: The `.container` element had `overflow: hidden` CSS rule which
clipped any content extending beyond its bounds, including tooltips positioned
above reference tags.

**Fix**: Removed `overflow: hidden` from `.container` in
[styles.css](../../src/eval/report_generation/templates/styles.css). Added
`border-radius` to `.header` to maintain rounded corner appearance at the top.


## Phase 6: Documentation and Cleanup (Completed 2026-01-26)

### Summary

Completed final documentation and cleanup tasks:

1. **Task 6.1: Update README with Report Features**
   - Added "Report Features" section to README documenting:
     - Axiom and Reality definitions sections with descriptions
     - Collapsible definitions sections
     - Reference tag tooltips showing full descriptions
     - Responsive layout for mobile devices

2. **Task 6.2: JSDoc Comments** - ALREADY COMPLETE
   - Verified comprehensive JSDoc comments exist for all JavaScript functions
   - All functions have `@param`, `@returns`, and type documentation

3. **Task 6.3: Python Docstrings** - ALREADY COMPLETE
   - Verified complete docstrings exist for:
     - `AxiomItem` and `RealityItem` models in `models.py`
     - `load_axiom_definitions()` and `load_reality_definitions()` in `eval.py`
   - All docstrings include Args, Returns, Raises, and Examples sections

4. **Task 6.4: Test Coverage Review**
   - Confirmed comprehensive test coverage across all features:
     - 214 Python tests (including 5 report generation integration tests)
     - 66 JavaScript tests (including edge cases for definitions and tooltips)

5. **Task 6.5: Final Test Run**
   - All Python tests pass
   - All JavaScript tests pass
   - All lint checks pass (Ruff, ESLint, Prettier)

### Files Modified

| File | Changes |
| ---- | ------- |
| [README.md](../../README.md) | Added Report Features section |
| [docs/plans/20260121-display-axioms-reality-in-report.md](../plans/20260121-display-axioms-reality-in-report.md) | Marked Phase 6 as complete |