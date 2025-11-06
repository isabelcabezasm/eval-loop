# ADR-002: Migration from Health Insurance to Banking Domain with Schema Simplification

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


## Implementation Plan

For detailed step-by-step instructions, see:
- **Implementation Checklist**: `MIGRATION_CHECKLIST.md` - Complete task-by-task guide
- **Sample Data**: `BANKING_DOMAIN_EXAMPLES.md` - 20 example rules and 12 evaluation questions
- **Migration Overview**: `README_MIGRATION.md` - Quick reference and navigation guide

### Phase 1: Schema Migration (Priority: High)
**Goal**: Update code to support new simplified schemas

#### 1.1 Constitution Schema - Update Axiom Data Model
File: `src/core/axiom_store.py`

- Modify `Axiom` dataclass to new schema (id, condition, consequence, description)
- Update `RawAxiom` Pydantic model
- Remove old fields: subject, entity, trigger, conditions, category
- Add new fields: condition, consequence
- Keep fields: id, description
- Update type hints referencing old schema fields
- Ensure Pydantic validation works with new schema

**Verification**: `uv run pytest tests/core/test_axiom_store.py -v`

#### 1.2 Reality Schema - Update Reality Module
File: `src/core/reality.py`

- Update reality data structure to new schema (id, title, description)
- Simplify from current complex structure
- Update any reality-related type definitions
- Update reality loading and validation logic

**Verification**: Test reality module independently

### Phase 2: Constitution and Reality Data (Priority: High)
**Goal**: Create new banking domain data files

#### 2.1 Archive Old Data
```bash
mkdir -p data/archive/
mv data/constitution.json data/archive/constitution_health_insurance_$(date +%Y%m%d).json
mv data/reality.json data/archive/reality_health_insurance_$(date +%Y%m%d).json  # if exists
```

#### 2.2 Create New Banking Constitution
File: `data/constitution.json`

Create 20-30 banking rules covering:
- **Account management** (5-7 rules): minimum balance, overdraft, dormancy, tier changes
- **Transaction policies** (5-7 rules): daily limits, fraud detection, international transactions
- **Lending and credit** (5-7 rules): credit scoring, loan approval, interest rates, utilization
- **Compliance and risk** (5-7 rules): KYC, AML, suspicious activity, regulatory requirements

**Reference**: See `BANKING_DOMAIN_EXAMPLES.md` for 20 ready-to-use example rules

**Validation**:
```bash
python -m json.tool data/constitution.json > /dev/null
python -c "from core.dependencies import axiom_store; store = axiom_store(); print(f'Loaded {len(store.list())} axioms')"
```

#### 2.3 Create New Banking Reality Data
File: `data/reality.json` (if used)

Create reality data with simplified schema:
- Economic indicators (inflation, unemployment, interest rates)
- Market conditions (stock indices, currency rates)
- Regulatory environment (recent policy changes)
- Current events affecting banking

Example entries: inflation rates, employment statistics, policy announcements

### Phase 3: Prompts and Engine (Priority: High)
**Goal**: Update system prompts and ensure domain-agnostic engine

#### 3.1 Update System Prompts
Directory: `src/core/prompts/`

For each prompt file:
- Replace "health insurance" → "banking"
- Replace "policyholder" → "customer" or "account holder"
- Replace "claims" → "transactions" or appropriate banking term
- Replace "premiums" → "fees", "interest", "charges"
- Update examples to banking scenarios (account management, transactions, loans)
- Update schema references in prompts:
  - Old: subject, entity, trigger, conditions, category
  - New: condition, consequence
- Update few-shot examples with banking use cases

#### 3.2 Review QA Engine
File: `src/core/qa_engine.py`

- Verify no domain-specific hardcoding
- Update any domain references in comments
- Ensure engine is fully domain-agnostic
- Review reality integration logic

**Verification**: `uv run python samples/basic_qa.py` with banking question

### Phase 4: Evaluation Dataset (Priority: High)
**Goal**: Create comprehensive banking domain evaluation dataset

#### 4.1 Archive Old Dataset
```bash
mv data/eval_dataset.json data/archive/eval_dataset_health_insurance_$(date +%Y%m%d).json
```

#### 4.2 Create New Evaluation Dataset
File: `data/eval_dataset.json`

Create 20-30 test questions with diversity:
- **Factual questions** (8-10): Direct rule lookups, single-axiom questions
- **Analytical questions** (8-10): Multi-rule scenarios, trade-off analysis
- **Hypothetical questions** (4-6): "What if" scenarios, policy changes
- **Edge cases** (2-4): Boundary conditions, threshold testing

Each question must include:
- `id`: Unique identifier
- `query`: Question text
- `context`: Relevant background (optional)
- `expected_answer`: Desired response
- `reasoning`: Step-by-step reasoning array
- `axioms_used`: Referenced rule IDs array

**Reference**: See `BANKING_DOMAIN_EXAMPLES.md` for 12 example questions across all types

**Validation**:
```bash
python -m json.tool data/eval_dataset.json > /dev/null
# Verify all axiom IDs exist in constitution
```

### Phase 5: Tests (Priority: Medium)
**Goal**: Update all test suites for banking domain

#### 5.1 Update Unit Tests - Core
Directory: `tests/core/`

Files to update:
- `test_axiom_store.py`:
  - Update test fixtures with new schema
  - Update assertions for new field names (condition, consequence)
  - Add tests for new fields
  - Remove tests for deprecated fields
  
- Other core tests:
  - Replace health insurance test data with banking examples
  - Update mock data to match new schemas
  - Fix any broken assertions

**Verification**: `uv run pytest tests/core/ -v`

#### 5.2 Update Evaluation Tests
Directory: `tests/eval/`

- Update test scenarios with banking examples
- Verify metric calculations still work with new data
- Update any domain-specific test assertions
- Ensure evaluation pipeline works end-to-end

**Verification**: `uv run pytest tests/eval/ -v`

#### 5.3 Full Test Suite
**Verification**: `uv run pytest tests/ -v` - Achieve 100% pass rate

### Phase 6: Samples and Documentation (Priority: Medium)
**Goal**: Update all examples and user-facing documentation

#### 6.1 Update Sample Scripts
Directory: `samples/`

- `basic_qa.py`: Replace with banking query (e.g., "What happens if my account balance falls below $1,500?")
- `basic_qa_streaming.py`: Replace with banking query about transactions or fees
- `qa_with_reality.py`: Replace with banking scenario using reality context (inflation impact on rates)
- `run_all_samples.py`: Verify still executes all samples

**Test each sample**: Verify outputs are realistic and relevant

#### 6.2 Update README
File: `README.md`

- **Title/Description**: Change "health insurance" to "banking"
- **Introduction**: Update domain description and use cases
- **Quick Start**: Replace example query with banking question
- **Project Structure**: Keep (domain-agnostic)
- **Examples**: Update any code snippets with banking scenarios

#### 6.3 Update Additional Documentation
- `pyproject.toml`: Update project description if domain-specific
- Any API documentation: Replace examples
- Add migration completion note to changelog
- Update ADR status to "Accepted"

### Phase 7: Validation and Cleanup (Priority: Low)
**Goal**: Comprehensive validation and cleanup

#### 7.1 Code Quality Checks
```bash
uv run ruff check src/ tests/          # Linting
uv run ruff format src/ tests/         # Formatting
uv run pyright                          # Type checking
```
Fix any issues found.

#### 7.2 End-to-End Testing
```bash
uv run pytest tests/                   # Full test suite
uv run python -m eval.main             # Evaluation run
uv run python samples/run_all_samples.py  # All samples
```

Review outputs:
- Evaluation results make sense for banking domain
- Sample outputs are realistic
- No errors or warnings

#### 7.3 Archive Old Runs
```bash
mkdir -p runs/archive/
mv runs/202* runs/archive/  # Excluding new runs
echo "These runs used health insurance domain data" > runs/archive/README.md
```

#### 7.4 Final Verification
- [ ] All tests pass (100%)
- [ ] All samples run successfully
- [ ] Evaluation produces results
- [ ] No health insurance references remain (except in archives)
- [ ] Code quality checks pass
- [ ] Git status clean (all changes committed)
- [ ] Documentation is consistent

### Phase 8: Completion (Priority: Low)
**Goal**: Finalize and document the migration

#### 8.1 Git and Version Control
```bash
git add -A
git commit -m "feat: migrate from health insurance to banking domain with simplified schema

- Updated constitution schema (id, condition, consequence, description)
- Updated reality schema (id, title, description)
- Created 20+ banking rules covering accounts, transactions, lending, compliance
- Created 20+ banking evaluation questions
- Updated all prompts and samples to banking domain
- Archived old health insurance data and runs
- All tests passing

Implements ADR-001"
```

#### 8.2 Documentation Updates
- Update this ADR status from "Proposed" to "Accepted"
- Add completion date
- Document any deviations from plan
- Note any lessons learned

#### 8.3 Communication
- Notify team of completed migration
- Update any external documentation or wikis
- Share migration pattern for future reference

## Timeline Estimate

- **Phase 1**: 2-3 hours (schema code updates)
- **Phase 2**: 4-6 hours (constitution creation is creative work)
- **Phase 3**: 2-3 hours (prompts and terminology)
- **Phase 4**: 4-6 hours (evaluation dataset creation)
- **Phase 5**: 3-4 hours (test updates)
- **Phase 6**: 2-3 hours (samples and documentation)
- **Phase 7**: 1-2 hours (validation and cleanup)
- **Phase 8**: 1 hour (finalization and git)

**Total**: 19-28 hours of development work

## Supporting Documentation

This ADR is accompanied by detailed implementation guides:

1. **`MIGRATION_CHECKLIST.md`** - Complete step-by-step checklist with:
   - Checkbox tracking for all tasks
   - Detailed verification steps
   - Commands to run at each phase
   - Rollback procedures
   - Space for notes and learnings

2. **`BANKING_DOMAIN_EXAMPLES.md`** - Concrete examples including:
   - 20 sample banking constitution rules (ready to use)
   - 12 sample evaluation questions with reasoning
   - Additional rule ideas for expansion
   - Tips for creating quality questions
   - Validation checklist

3. **`README_MIGRATION.md`** - Overview document with:
   - Navigation guide for all migration documents
   - Quick reference for schema changes
   - Success criteria
   - Timeline summary

**Recommended workflow**: 
1. Read this ADR for strategic understanding
2. Review examples in `BANKING_DOMAIN_EXAMPLES.md`
3. Follow `MIGRATION_CHECKLIST.md` step-by-step during implementation
4. Use `README_MIGRATION.md` for quick reference

## Rollback Strategy

If issues arise:
1. Git revert to commit before migration
2. Old data files preserved in `data/archive/`
3. No database migrations needed (JSON-based)
4. Can maintain both schemas temporarily if needed

## Notes

- This ADR supersedes the domain-specific aspects of the original design
- The constitutional framework architecture remains unchanged
- Future domain changes will be easier with the simplified schema
- Consider creating a domain configuration system for easy domain switching in the
  future

## References

### Original Project Files
- Original project README: `../README.md`
- Current constitution schema: `data/constitution.json`
- Current evaluation dataset: `data/eval_dataset.json`
- Axiom store implementation: `src/core/axiom_store.py`
- Reality module: `src/core/reality.py`

### Supporting Migration Documents
- **Implementation Checklist**: `MIGRATION_CHECKLIST.md`
- **Sample Data and Examples**: `BANKING_DOMAIN_EXAMPLES.md`
- **Migration Overview**: `README_MIGRATION.md`

### Post-Migration Archives
- Archived constitution: `data/archive/constitution_health_insurance_YYYYMMDD.json`
- Archived eval dataset: `data/archive/eval_dataset_health_insurance_YYYYMMDD.json`
- Archived runs: `runs/archive/` (all health insurance domain runs)
