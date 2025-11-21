# Implementation Plan: Domain Migration to Banking

**Created:** 2025-11-06  
**Status:** In Progress  
**Related ADR:** [ADR-001: Migration from Health Insurance to Banking
Domain](../ADR01-domain-change.md)

## Overview

This plan covers the migration from health insurance domain to banking domain
with simplified schemas for both constitution and reality data structures.

---

## Phase 1: Constitution Code Changes

### - [x] Task 1.1: Update Constitution Schema
- Simplify constitution schema to only include `id` and `description` fields
- Remove fields: `subject`, `entity`, `trigger`, `conditions`, and any other
  fields
- Update data models in `src/core/models.py` or equivalent
- Update type definitions and validation logic

### - [x] Task 1.2: Update Constitution Loading Logic
- Update parsers/loaders in `src/core/` to handle simplified constitution
  schema
- Remove logic handling old complex fields
- Ensure backward compatibility is cleanly removed

### - [x] Task 1.3: Update Constitution Query Processing
- Review query processing logic in `src/core/` related to constitution
- Ensure prompts and context building work with simplified constitution schema
- Update any field references in prompts or retrieval logic

### - [x] Task 1.4: Update Constitution Retrieval Logic
- Review retrieval/search mechanisms for constitution data
- Ensure they work effectively with description-only content
- Update any indexing or embedding logic if needed

### - [x] Task 1.5: Update API Constitution Response Models
- Update `AxiomCitationResponse` in `src/api/generate.py`
- Remove fields: `subject`, `entity`, `trigger`, `conditions`, `category`
- Keep only `id` and `description` fields
- Update the response mapping in the `generate()` endpoint

### - [x] Task 1.6: Update Constitution Test Fixtures
- Update test fixtures in `tests/` to use simplified constitution schema
- Keep health insurance domain content for now (domain change comes later)
- Ensure tests still pass with schema changes

### - [x] Task 1.7: Run Tests for Phase 1
- Run all tests to identify broken functionality
- Fix any test failures related to constitution schema changes
- Verify constitution-related functionality works with new schema
- Ensure API tests pass with updated response models

---

## Phase 2: Reality Code Changes

### - [x] Task 2.1: Update Reality Schema
- Simplify reality schema to only include `id` and `description` fields
- Remove any other complex fields
- Update data models for reality data
- Update type definitions and validation logic

### - [x] Task 2.2: Update Reality Data Loading Logic
- Update reality data parsers/loaders
- Simplify extraction logic to work with new schema
- Remove any field mapping logic for deprecated fields

### - [x] Task 2.3: Update Reality Query Processing
- Review query processing logic in `src/core/` related to reality data
- Ensure prompts and context building work with simplified reality schema
- Update any field references in prompts or retrieval logic

### - [x] Task 2.4: Update Reality Retrieval Logic
- Review retrieval/search mechanisms for reality data
- Ensure they work effectively with description-only content
- Update any indexing or embedding logic if needed

### - [x] Task 2.5: Update API Reality Response Models
- Update `RealityCitationResponse` in `src/api/generate.py`
- Remove fields: `entity`, `attribute`, `value`, `number`
- Keep only `id` and `description` fields
- Update the response mapping in the `generate()` endpoint

### - [x] Task 2.6: Update Reality Test Fixtures
- Update test fixtures in `tests/` to use simplified reality schema
- Keep health insurance domain content for now (domain change comes later)
- Ensure tests still pass with schema changes

### - [x] Task 2.7: Run Tests for Phase 2
- Run all tests to verify reality-related changes
- Fix any broken tests
- Verify both constitution and reality functionality work together running
  `samples/qa_with_reality.py`
- Ensure API tests pass with updated response models

---

## Phase 3: Data Migration to Banking Domain

### - [x] Task 3.1: Create Banking Domain Constitution Data
- Create new `data/constitution.json` with banking axioms
- Include examples like market stability, investor confidence, economic
  principles
- Ensure each axiom has unique `id` (e.g., "A-001", "A-002") and `description`
- Use simplified schema (id + description only)

### - [x] Task 3.2: Create Banking Domain Reality Data
- Create or update reality data file with banking realities
- Include banking realities like inflation rates, unemployment, political
  changes
- Ensure each reality has unique `id` (e.g., "R-001", "R-002") and `description`
- Use Switzerland as the example country per ADR

### - [x] Task 3.3: Update Evaluation Dataset
- Review `data/eval_dataset.json`
- Replace health insurance questions with banking domain questions
- Ensure questions test both constitutional axioms and reality data
- Maintain similar difficulty distribution

### - [x] Task 3.4: Update API Test Data
- Update test files in `tests/api/` to use banking domain data
- Update `tests/api/test_generate.py` with banking examples
- Replace health insurance questions with banking questions
- Update test assertions for banking domain

### - [x] Task 3.5: Update Test Data
- Update all test files in `tests/` to use banking domain data
- Replace health insurance examples with banking examples
- Update assertions and expected outputs for banking domain

### - [x] Task 3.6: Run Tests for Phase 3
- Run all tests to verify data migration
- Fix any test failures related to domain change
- Verify system works end-to-end with banking data
- Test API endpoints with banking domain questions

---

## Phase 4: Documentation and Examples Updates

### - [x] Task 4.1: Update README
- Replace health insurance examples with banking examples
- Update domain description throughout
- Update sample questions and outputs

### - [x] Task 4.2: Update Sample Scripts
- Review and update `samples/basic_qa.py`
- Review and update `samples/basic_qa_streaming.py`
- Review and update `samples/qa_with_reality.py`
- Update any hardcoded questions to banking domain

### - [x] Task 4.3: Update Code Comments
- Search codebase for health insurance references
- Update inline comments and docstrings
- Ensure examples in code use banking domain

### - [x] Task 4.4: Update API Documentation
- Update API endpoint documentation in `src/api/generate.py`
- Update docstrings to reflect banking domain
- Ensure example requests/responses use banking examples
- Update any API-related comments with banking context

### - [x] Task 4.5: Run Tests for Phase 4
- Run all tests to verify documentation examples work
- Fix any broken tests
- Verify all sample scripts execute successfully
- Test API endpoints manually with banking questions

---

## Phase 5: Validation and Cleanup

### - [x] Task 5.1: Run Complete Test Suite
- Execute: `uv run pytest tests/`
- Verify all tests pass
- Check test coverage hasn't decreased significantly

### - [x] Task 5.2: Run All Sample Scripts
- Execute `samples/run_all_samples.py` or run each individually
- Verify outputs are sensible for banking domain
- Check for any lingering health insurance references

### - [x] Task 5.3: Run Evaluation
- Execute evaluation task: `uv run python -m eval.main`
- Review evaluation results for banking domain
- Ensure results make sense for new domain

### - [x] Task 5.4: Code Quality Checks
- Run linter: `uv run ruff check src/ tests/`
- Run formatter: `uv run ruff format src/ tests/`
- Run type checker: `uv run pyright`
- Fix any issues identified

### - [x] Task 5.5: Manual Testing
- Test the system with various banking questions
- Verify constitutional axioms are properly applied
- Verify reality data is correctly integrated
- Test edge cases and error handling
- Test API endpoints with various banking questions
- Verify API response format with simplified schemas

### - [x] Task 5.6: API Integration Testing
- Start the API server and test `/api/generate` endpoint
- Send requests with banking domain questions
- Verify streaming responses work correctly
- Test with and without reality data
- Validate response format matches simplified schema

### - [x] Task 5.7: Clean Up Old Artifacts
- Remove any health insurance specific files
- Clean up old run results if needed
- Remove any deprecated code or comments
- Remove any old API examples or documentation

---

## Success Criteria

The migration is complete when:

1. ✅ All constitution and reality data uses simplified schema (id + description
   only)
2. ✅ All data files contain banking domain content (no health insurance
   references)
3. ✅ All tests pass with banking domain data
4. ✅ All sample scripts execute successfully with banking examples
5. ✅ Code quality checks (lint, format, type check) pass
6. ✅ Evaluation runs successfully and produces sensible results
7. ✅ Documentation accurately reflects banking domain
8. ✅ No health insurance references remain in code or documentation
9. ✅ System correctly handles both constitutional axioms and reality data for
   banking questions
10. ✅ API endpoints work correctly with simplified schemas
11. ✅ API response models only contain `id` and `description` fields
12. ✅ API tests pass with banking domain data

---

## Notes

- Phase 1: Focus on constitution schema and code changes (including API)
- Phase 2: Focus on reality schema and code changes (including API)
- Phase 3: Migrate all data from health insurance to banking domain
- Phase 4: Update documentation and examples
- Phase 5: Comprehensive validation and cleanup
- Each phase ends with testing to catch issues early
- Schema changes may have cascading effects - be thorough in searching for
  dependencies
- Keep commits atomic and well-described for easy rollback if needed
- Test frequently during implementation to catch issues early
- API response models must be updated in sync with core data models
- API tests require updates to reflect both schema and domain changes
