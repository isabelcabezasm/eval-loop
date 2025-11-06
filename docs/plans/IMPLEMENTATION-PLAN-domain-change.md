# Implementation Plan: Domain Change from Health Insurance to Banking

**Status**: Not Started  
**ADR Reference**: [ADR-001: Migration from Health Insurance to Banking Domain with
Schema Simplification](./ADR01-domain-change.md)  
**Created**: 2025-11-06  
**Target Branch**: `domain-change-to-banking-implementation-plan`

---

## Executive Summary

This plan outlines the steps to migrate the Constitutional Q&A Agent from the health
insurance domain to the banking domain while simultaneously simplifying the data schema.
The changes involve updating data models, templates, test data, documentation, and
creating comprehensive banking domain content.

**Total Estimated Effort**: 12-14 hours

---

## Phase 1: Data Model Updates (including tests) ⬜

**Goal**: Update core Python data models to use the simplified schema and their corresponding tests.

**Deliverable**: Pull request with updated data models and passing tests.

### Task 1.1: Update Axiom Schema ⬜

**Files**: `src/core/axiom_store.py`

**Changes Required**:

1. Update the `Axiom` dataclass:
   ```python
   # FROM (old schema):
   @dataclass(frozen=True)
   class Axiom:
       id: AxiomId
       subject: str
       entity: str
       trigger: str
       conditions: str
       description: str
       category: str
   
   # TO (new simplified schema):
   @dataclass(frozen=True)
   class Axiom:
       id: AxiomId
       description: str
   ```

2. Update `RawAxiom` Pydantic model in `load_from_json()`:
   ```python
   class RawAxiom(BaseModel):
       id: str
       description: str
       
       class Config:
           extra = "ignore"
   ```

3. Update the `AxiomStore` instantiation logic to use new field names.

**Estimated Time**: 30 minutes

---

### Task 1.2: Update Reality Schema ⬜

**Files**: `src/core/reality.py`

**Changes Required**:

1. Update the `RealityStatement` dataclass:
   ```python
   # FROM (old schema):
   @dataclass(frozen=True)
   class RealityStatement:
       id: RealityId
       entity: str
       attribute: str
       value: str
       number: str
       description: str
   
   # TO (new simplified schema):
   @dataclass(frozen=True)
   class RealityStatement:
       id: RealityId
       description: str
   ```

2. Update `RawRealityStatement` Pydantic model in `load_from_json()`:
   ```python
   class RawRealityStatement(BaseModel):
       id: str
       description: str
       
       class Config:
           extra = "ignore"
   ```

3. Update the list comprehension to use new field names.

**Estimated Time**: 20 minutes

---

### Task 1.3: Update Tests for Data Models ⬜

**Files**: 
- `tests/core/test_qa_engine.py`
- `tests/core/test_dependencies.py`

**Changes Required**:

1. Replace all test `Axiom` instances with new schema:
   ```python
   # OLD:
   Axiom(
       id=AxiomId("AXIOM-001"),
       subject="Physical Activity",
       entity="sport",
       trigger="Regular exercise habits detected",
       conditions="Activity meets or exceeds recommended guidelines",
       description="Higher physical activity reduces long-term health risk...",
       category="Preventive Health"
   )
   
   # NEW:
   Axiom(
       id=AxiomId("A001"),
       description="When central banks increase interest rates, borrowing costs rise for consumers and businesses, reducing spending and investment."
   )
   ```

2. Replace all test `RealityStatement` instances:
   ```python
   # OLD:
   RealityStatement(
       id=RealityId("REALITY-001"),
       entity="Test",
       attribute="Test Attr",
       value="Test Value",
       number="100",
       description="Test description"
   )
   
   # NEW:
   RealityStatement(
       id=RealityId("R001"),
       description="Current inflation in Switzerland is 7.5%."
   )
   ```

3. Update test assertions to check for new field names
4. Keep test content domain-neutral or use simple banking examples

**Estimated Time**: 1.5-2 hours

**Note**: All tests must pass before completing Phase 1.

---

### Task 6.2: Update Sample Scripts ⬜

**Files**:
- `samples/basic_qa.py`
- `samples/basic_qa_streaming.py`
- `samples/qa_with_reality.py`
- `samples/run_all_samples.py`

**Changes Required**:

1. **basic_qa.py**: Final polish with comprehensive banking question
   ```python
   question = (
       "What would happen to mortgage rates and the housing market if the "
       "central bank raises interest rates by 0.5% to combat inflation?"
   )
   ```

2. **basic_qa_streaming.py**: Update with streaming banking question
   ```python
   question = (
       "How does persistent high inflation affect savings, investments, "
       "and overall purchasing power in an economy?"
   )
   ```

3. **qa_with_reality.py**: Ensure reality data is fully integrated
   ```python
   # Already updated in Phase 4, verify it works well
   # Add more comprehensive example if needed
   question = (
       "Given the current inflation rate and SNB policy in Switzerland, "
       "what should I consider for my savings strategy?"
   )
   ```

4. **run_all_samples.py**: Update comments and ensure all samples work together

**Estimated Time**: 30 minutes

---

### Task 6.3: Update README with Banking Examples ⬜

**Files**: `README.md`

**Changes Required**:

1. Update project description:
   ```markdown
   # Constitutional Q&A Agent
   
   A Q&A agent for banking and finance queries, grounded on a constitutional framework...
   ```

2. Update Quick Start examples with banking questions
3. Update any references to "health insurance" → "banking"
4. Ensure schema examples reflect the simplified structure

**Estimated Time**: 30 minutes

---

### Task 6.4: Test All Sample Scripts ⬜

**Estimated Time**: 5 minutes

---

### Task 1.5: Validate Phase 1 ⬜

**Commands**:
```bash
uv run pytest tests/core/ -v
uv run ruff check src/core/axiom_store.py src/core/reality.py
uv run pyright src/core/axiom_store.py src/core/reality.py
uv run python samples/basic_qa.py
```

**Success Criteria**:
- ✅ All core tests pass
- ✅ No linting errors in modified files
- ✅ No type checking errors
- ✅ Sample script runs (even if answer not perfect yet)
- ✅ Code is ready for PR

**Estimated Time**: 15 minutes

---

## Phase 2: Template and Prompt Updates (including tests) ⬜

**Goal**: Update Jinja2 templates and system prompts to reflect the new schema and banking domain, and verify with tests.

**Deliverable**: Pull request with updated templates and passing tests.

### Task 2.1: Update Constitution Template ⬜

**Files**: `src/core/prompts/constitution.j2`

**Changes Required**:

Replace the current template with:
```jinja2
{%- for axiom in axioms -%}
## {{ axiom.id }}

{{ axiom.description }}

{% endfor %}
```

**Estimated Time**: 20 minutes

---

### Task 2.2: Update Reality Template ⬜

**Files**: `src/core/prompts/reality.j2`

**Changes Required**:

Replace the current template with:
```jinja2
{%- for statement in reality -%}
## {{ statement.id }}

{{ statement.description }}{% if not loop.last %}

{% endif %}
{%- endfor %}
```

**Estimated Time**: 15 minutes

---

### Task 2.3: Update System Prompt ⬜

**Files**: `src/core/prompts/system_prompt.md`

**Changes Required**:

1. Change domain from "Health Insurance" to "Banking and Finance"
2. Update scope limitations to cover banking topics:
   - Banking policies and regulations
   - Economic principles and market dynamics
   - Interest rates, inflation, and monetary policy
   - Investment and risk management
   - Credit and lending practices
   - Financial regulations and compliance

3. Update examples and terminology to reflect banking domain
4. Maintain the citation format `[AXIOM-XXX]` and `[REALITY-XXX]`

**Example Opening**:
```markdown
# Banking and Finance AI Assistant System Prompt

You are a helpful AI assistant specialized in banking and finance matters. Your expertise covers banking policies, economic principles, monetary policy, investment strategies, and financial regulations.
```

**Estimated Time**: 30 minutes

---

### Task 2.4: Update Tests for Templates ⬜

**Files**: 
- `tests/core/test_qa_engine.py` (specifically prompt-related tests)

**Changes Required**:

1. Update any captured prompt assertions to reflect new template structure
2. Verify templates render correctly with new field names
3. Test that constitution and reality formatting matches expected output

**Example test update**:
```python
# Update assertions checking for old field names in prompts
assert "A001" in captured_prompt  # Instead of "AXIOM-001"
assert "description" in captured_prompt.lower()
# Remove checks for old fields like "subject", "entity", "trigger", "condition", "consequence", "title"
```

**Estimated Time**: 30 minutes

---

### Task 2.5: Update Samples for Manual Testing ⬜

**Files**: 
- `samples/basic_qa.py`
- `samples/basic_qa_streaming.py`

**Changes Required**:

Keep questions simple and domain-neutral since we don't have banking constitution yet:

```python
# basic_qa.py
question = "What happens when interest rates change?"

# basic_qa_streaming.py  
question = "What are the effects of inflation?"
```

**Estimated Time**: 5 minutes

---

### Task 2.6: Validate Phase 2 ⬜

**Commands**:
```bash
uv run pytest tests/core/test_qa_engine.py -v -k "prompt"
uv run ruff check src/core/prompts/
uv run python samples/basic_qa.py
uv run python samples/basic_qa_streaming.py
```

**Success Criteria**:
- ✅ All prompt-related tests pass
- ✅ Templates render correctly with new schema
- ✅ No linting errors
- ✅ Samples run successfully
- ✅ Code is ready for PR

**Estimated Time**: 15 minutes

---

## Phase 3: Banking Constitution Data (including tests) ⬜

**Goal**: Create comprehensive banking domain constitution data and update tests to use it.

**Deliverable**: Pull request with banking constitution data and passing tests.

### Task 3.1: Create Banking Constitution ⬜

**Files**: `data/constitution.json`

**Changes Required**:

Create ~10 banking axioms using the new simplified schema. 

Example of topics to cover:

- Interest rate effects
- Central bank operations
- Money supply impact
- Exchange rate dynamics
- Deposit insurance
- Reserve requirements
- Inflation and deflation
- Economic cycles
- GDP and growth indicators
- Unemployment effects
- Diversification principles
- Risk-return tradeoff
- Asset valuation
- Credit risk assessment

**Example Axioms**:
```json
[
  {
    "id": "A001",
    "description": "Political instability often disrupts markets and investor confidence, leading to economic downturns."
  },
  {
    "id": "A002",
    "description": "When central banks increase interest rates, borrowing costs rise for consumers and businesses, reducing spending and investment."
  },
  {
    "id": "A003",
    "description": "High inflation decreases the purchasing power of currency as prices rise and each unit of currency buys fewer goods and services."
  }
]
```

**Estimated Time**: 2-3 hours

---

### Task 3.2: Update Tests to Use Banking Constitution ⬜

**Files**: 
- `tests/core/test_qa_engine.py`
- `tests/core/test_dependencies.py`

**Changes Required**:

1. Update test data to reference actual banking axioms from constitution
2. Change test questions from health insurance to banking domain
3. Update assertions to expect banking-related responses

**Example updates**:
```python
# Update test questions
question = "What happens when interest rates increase?"

# Update expected content in responses
assert "borrowing" in response.lower() or "interest" in response.lower()
```

**Estimated Time**: 1 hour

---

### Task 3.3: Update Samples to Use Banking Constitution ⬜

**Files**: 
- `samples/basic_qa.py`
- `samples/basic_qa_streaming.py`

**Changes Required**:

Now that we have banking axioms, update samples with specific banking questions:

```python
# basic_qa.py
question = (
    "What would happen to borrowing costs if the central bank "
    "raises interest rates by 0.5%?"
)

# basic_qa_streaming.py
question = (
    "How does high inflation affect the purchasing power of savings?"
)
```

**Estimated Time**: 10 minutes

---

### Task 3.4: Validate Phase 3 ⬜

**Commands**:
```bash
uv run pytest tests/ -v
uv run python -c "import json; json.load(open('data/constitution.json'))"
uv run python samples/basic_qa.py
uv run python samples/basic_qa_streaming.py
```

**Success Criteria**:
- ✅ Constitution JSON is valid
- ✅ All tests pass with banking data
- ✅ At least 10 well-formed banking axioms
- ✅ Samples produce relevant banking responses
- ✅ Code is ready for PR

**Estimated Time**: 15 minutes

---

## Phase 4: Banking Reality Data (including tests) ⬜

**Goal**: Create banking reality data and update tests to use it.

**Deliverable**: Pull request with reality data and passing tests.

### Task 4.1: Create Banking Reality Data ⬜

**Files**: `data/reality.json` (new file)

**Changes Required**:

Create about 10 reality statements that describe the current state of banking and
economic conditions.

Reality statements provide specific, current facts that complement the constitution's
general principles. For example:
- If the constitution has an axiom about inflation effects, then a reality statement
  should give the actual inflation rate right now (e.g., "Current inflation in
  Switzerland is 7.5%")

**Example reality statements**:

```json
[
  {
    "id": "R001",
    "description": "Current inflation in Switzerland is elevated at 7.5%."
  },
  {
    "id": "R002",
    "description": "Unemployment rate in Switzerland is 5%."
  },
  {
    "id": "R003",
    "description": "The Swiss National Bank has set the policy rate at 1.75%."
  },
  {
    "id": "R004",
    "description": "Current EUR/CHF exchange rate is 0.95."
  },
  {
    "id": "R005",
    "description": "Switzerland's GDP grew by 2.1% in the last quarter."
  }
]
```

**Estimated Time**: 1 hour

---

### Task 4.2: Update Tests for Reality Data ⬜

**Files**: 
- `tests/core/test_qa_engine.py` (reality-related tests)

**Changes Required**:

1. Update tests that use reality statements
2. Verify reality citations work correctly with new format [R00X]
3. Test reality data loading and rendering

**Estimated Time**: 30 minutes

---

### Task 4.3: Update Sample to Use Reality Data ⬜

**Files**: `samples/qa_with_reality.py`

**Changes Required**:

Now that we have reality data, update this sample to demonstrate reality usage:

```python
# Update to load reality data and ask a question that uses it
from core.reality import load_from_json

# Load reality statements
with open("data/reality.json") as f:
    reality = load_from_json(f.read())

question = (
    "Given the current economic conditions in Switzerland, "
    "what impact would rising interest rates have?"
)
```

**Estimated Time**: 10 minutes

---

### Task 4.4: Validate Phase 4 ⬜

**Commands**:
```bash
uv run pytest tests/ -v -k "reality"
uv run python -c "import json; json.load(open('data/reality.json'))"
uv run python samples/qa_with_reality.py
```

**Success Criteria**:
- ✅ Reality JSON is valid
- ✅ All reality tests pass
- ✅ Reality citations work correctly
- ✅ Sample demonstrates reality usage
- ✅ Code is ready for PR

**Estimated Time**: 15 minutes

---

## Phase 5: Evaluation Dataset (including validation) ⬜

**Goal**: Create banking evaluation dataset with questions that test the axioms.

**Deliverable**: Pull request with evaluation dataset and validation.

### Task 5.1: Create Evaluation Dataset ⬜

**Files**: `data/eval_dataset.json`

**Changes Required**:

Replace existing health insurance questions with about 10 banking domain questions.

Each question should connect to at least one axiom from the constitution. When the LLM
has that axiom in its context, it should help answer the question correctly.

Make sure the expected answer and reasoning match what the axiom says.

**Example Questions**:
```json
[
  {
    "id": 1,
    "query": "What happens to borrowing costs when the central bank raises interest rates?",
    "context": "Central banks use interest rates as a primary monetary policy tool.",
    "expected_answer": "Borrowing costs increase for consumers and businesses, as higher interest rates make loans more expensive.",
    "reasoning": [
      "Central bank sets policy rates",
      "Higher rates increase cost of borrowing",
      "Reduces spending and investment"
    ],
    "axioms_used": ["A002"]
  },
  {
    "id": 2,
    "query": "How does political instability affect a country's economy?",
    "context": "Political events can have significant economic impacts.",
    "expected_answer": "Political instability often leads to economic recession as it disrupts markets and reduces investor confidence.",
    "reasoning": [
      "Instability creates uncertainty",
      "Investors become risk-averse",
      "Markets experience volatility and downturn"
    ],
    "axioms_used": ["A001"]
  },
  {
    "id": 3,
    "query": "Why does high inflation reduce purchasing power?",
    "context": "Inflation is a key economic indicator monitored by central banks.",
    "expected_answer": "High inflation decreases purchasing power because as prices rise, each unit of currency can buy fewer goods and services.",
    "reasoning": [
      "Inflation causes prices to increase",
      "Fixed currency amounts buy less",
      "Real value of money decreases"
    ],
    "axioms_used": ["A003"]
  }
]
```
**Estimated Time**: 2 hours

---

### Task 5.2: Test Evaluation Dataset ⬜

**Commands**:
```bash
uv run python -c "import json; data=json.load(open('data/eval_dataset.json')); print(f'Loaded {len(data)} questions')"
# Optionally run a single question to test
uv run python samples/basic_qa.py  # Using one of the eval questions
```

**Success Criteria**:
- ✅ Can manually test with eval questions
- ✅ Questions are well-formed and relevant

**Estimated Time**: 15 minutes

---

### Task 5.3: Validate Evaluation Dataset ⬜

**Commands**:
```bash
uv run python -c "import json; data=json.load(open('data/eval_dataset.json')); print(f'Loaded {len(data)} questions')"
uv run python -m eval.main --data_path data/eval_dataset.json
```

**Success Criteria**:
- ✅ Evaluation JSON is valid
- ✅ All questions reference valid axioms
- ✅ Evaluation runs without errors
- ✅ At least 10 banking questions
- ✅ Code is ready for PR

**Estimated Time**: 30 minutes

---

## Phase 6: Documentation Updates (including samples) ⬜

**Goal**: Update README and sample scripts to reflect banking domain.

**Deliverable**: Pull request with updated documentation and working sample scripts.

### Task 6.1: Update README ⬜

**Files**: `README.md`

**Changes Required**:

1. Update project description:
   ```markdown
   # Constitutional Q&A Agent
   
   A Q&A agent for banking and finance queries, grounded on a constitutional framework...
   ```

2. Update the three key elements description to use banking examples
3. Update Quick Start examples with banking questions
4. Update example queries throughout the document
5. Update any references to "health insurance" → "banking"
6. Ensure schema examples reflect the simplified structure

**Example Updates**:
- Change example questions to banking domain
- Update constitution/reality examples
- Modify "What you'll learn" sections if present

**Estimated Time**: 30 minutes

---

### Task 5.2: Update Sample Scripts ⬜

**Files**:
- `samples/basic_qa.py`
- `samples/basic_qa_streaming.py`
- `samples/qa_with_reality.py`
- `samples/run_all_samples.py`

**Changes Required**:

1. **basic_qa.py**: Replace health insurance question with banking question
   ```python
   # OLD:
   question = (
       "What if I quit smoking today - what would be the long-term "
       "impact on my health insurance costs and claim patterns?"
   )
   
   # NEW:
   question = (
       "What would happen to my mortgage rate if the central bank "
       "raises interest rates by 0.5%?"
   )
   ```

2. **basic_qa_streaming.py**: Update with streaming banking question
   ```python
   question = (
       "How does inflation affect my savings and investment strategy?"
   )
   ```

3. **qa_with_reality.py**: Add banking reality data and question
   ```python
   # Create reality data for Swiss banking scenario
   reality_data = [
       {
           "id": "R001",
           "description": "Swiss National Bank policy rate is at 1.75%."
       },
       {
           "id": "R002",
           "description": "Current inflation in Switzerland is 7.5%."
       }
   ]
   
   question = (
       "Given the current inflation rate in Switzerland, what impact "
       "would this have on my fixed-rate mortgage?"
   )
   ```

4. Update all comments and docstrings to reflect banking domain

**Estimated Time**: 45 minutes

---

### Task 6.3: Test Sample Scripts ⬜

**Commands**:
```bash
uv run python samples/basic_qa.py
uv run python samples/basic_qa_streaming.py
uv run python samples/qa_with_reality.py
uv run python samples/run_all_samples.py
```

**Success Criteria**:
- ✅ All sample scripts run without errors
- ✅ Responses are relevant to banking domain
- ✅ Citations appear correctly ([A00X] and [R00X])
- ✅ Sample scripts demonstrate the system properly
- ✅ README examples match working samples

**Estimated Time**: 20 minutes

---

### Task 6.5: Validate Phase 6 ⬜

**Commands**:
```bash
uv run ruff check samples/
uv run pyright samples/
uv run pytest tests/ -v
```

**Success Criteria**:
- ✅ README accurately describes banking domain
- ✅ All samples work correctly
- ✅ No linting or type errors
- ✅ All tests still pass
- ✅ Code is ready for PR

**Estimated Time**: 15 minutes

---

## Phase 7: Quality Assurance & Finalization ⬜

**Goal**: Final validation, cleanup, and project finalization.

**Deliverable**: Final pull request with all quality checks passed and ADR updated.

### Task 7.1: Run All Tests ⬜

**Commands**:
```bash
uv run pytest tests/ -v
```

**Success Criteria**:
- ✅ All unit tests pass
- ✅ No schema-related errors
- ✅ Citation parsing works correctly with new axiom IDs
- ✅ Reality and constitution loading works with new schemas

**Estimated Time**: 30 minutes (including fixes)

---

### Task 7.2: Run Linting and Type Checking ⬜

**Commands**:
```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pyright
```

**Success Criteria**:
- ✅ No linting errors
- ✅ Code is properly formatted
- ✅ No type checking errors
- ✅ All imports resolve correctly

**Estimated Time**: 20 minutes (including fixes)

---

### Task 7.3: Manual End-to-End Testing ⬜

**Test Scenarios**:

1. **Run basic_qa.py** (already tested in Phase 6)
2. **Run basic_qa_streaming.py** (already tested in Phase 6)
3. **Run qa_with_reality.py** (already tested in Phase 6)
4. **Test with various banking questions**:
   - Monetary policy question
   - Banking regulation question
   - Economic indicator question
   - Investment/risk question

**Success Criteria**:
- ✅ All sample scripts run without errors
- ✅ Responses are coherent and banking-relevant
- ✅ Citations appear correctly ([A00X] and [R00X] format)
- ✅ Reality data is properly incorporated when provided
- ✅ Streaming functionality works

**Estimated Time**: 30 minutes

---

### Task 7.4: Run Evaluation ⬜

**Commands**:
```bash
uv run python -m eval.main
```

**Success Criteria**:
- ✅ Evaluation runs without errors
- ✅ Results are saved to `runs/` directory
- ✅ Evaluation metrics are calculated
- ✅ Banking domain questions are processed correctly

**Estimated Time**: 30 minutes

---

### Task 7.5: Clean Up ⬜

**Actions**:
1. Review all files for any remaining health insurance references
2. Remove any commented-out old code
3. Ensure no debug prints or temporary code remains
4. Check that all file headers and docstrings are accurate

**Checklist**:
- [ ] No "health insurance" or "healthcare" references in active code
- [ ] No commented-out old schema code
- [ ] All docstrings are accurate
- [ ] No temporary debug code

**Estimated Time**: 15 minutes

---

### Task 7.6: Update ADR Status ⬜

**Files**: `docs/ADR01-domain-change.md`

**Changes**:
```markdown
## Status
Implemented

## Implementation Date
2025-11-06

## Implementation Notes
Successfully migrated from health insurance to banking domain with schema simplification.
- Simplified Axiom schema to: condition, consequence, description
- Simplified Reality schema to: title, description
- Created 25 banking axioms covering monetary policy, banking operations, economic principles, and regulations
- Updated all tests, templates, and documentation
- All quality checks passed
```

**Estimated Time**: 10 minutes

---

### Task 7.7: Create Implementation Notes ⬜

**Files**: `docs/notes/IMPLEMENTATION-PLAN-domain-change-notes.md`

**Content**: Summary of implementation including:
- Phases completed
- Any challenges encountered
- Deviations from plan (if any)
- Testing results
- Final validation outcomes

**Estimated Time**: 15 minutes

---

### Task 7.8: Final Commit ⬜

**Actions**:
1. Review all changes using `git status` and `git diff`
2. Stage all changes: `git add .`
3. Commit with descriptive message:
   ```bash
   git commit -m "feat: migrate from health insurance to banking domain (ADR-001)
   
   - Simplify Axiom schema to condition/consequence/description
   - Simplify Reality schema to title/description
   - Create 25 banking domain axioms
   - Update all templates for new schema
   - Replace all health insurance data with banking data
   - Update tests, samples, and documentation
   - All tests passing
   
   Implements ADR-001"
   ```
4. Push to branch: `git push origin domain-change-to-banking-implementation-plan`

**Estimated Time**: 10 minutes

---

## Summary

### Effort Breakdown
| Phase | Estimated Time | Deliverable |
|-------|---------------|-------------|
| Phase 1: Data Model Updates + Tests + Sample | 3 hours | PR with updated models, passing tests, testable sample |
| Phase 2: Template Updates + Tests + Samples | 2 hours | PR with updated templates, passing tests, testable samples |
| Phase 3: Banking Constitution + Tests + Samples | 4.5 hours | PR with constitution data, passing tests, testable samples |
| Phase 4: Banking Reality + Tests + Sample | 2.5 hours | PR with reality data, passing tests, testable sample |
| Phase 5: Evaluation Dataset + Validation + Testing | 2.5 hours | PR with eval dataset, validation, manual testing |
| Phase 6: Documentation + Samples (final polish) | 2.5 hours | PR with updated docs & polished working samples |
| Phase 7: QA & Finalization | 2.5 hours | Final PR with all quality checks |
| **Total** | **~19-20 hours** | **7 independent, testable PRs** |

### Phase Structure

Each phase is designed to be independently reviewable and mergeable:

1. **Phase 1**: Foundation - Update data models and their tests
2. **Phase 2**: Rendering - Update templates and verify with tests  
3. **Phase 3**: Content - Add banking constitution and update tests to use it
4. **Phase 4**: Context - Add banking reality data and test it
5. **Phase 5**: Evaluation - Add eval dataset and validate it works
6. **Phase 6**: User-Facing - Update docs and samples, test they work
7. **Phase 7**: Polish - Final QA, cleanup, and project finalization

### Critical Path
1. **Phase 1** must complete first (foundation for everything)
2. **Phase 2** depends on Phase 1 (templates need new schema)
3. **Phase 3-5** depend on Phases 1-2 (data needs models and templates)
4. **Phase 3-5** can potentially run in parallel after Phase 2
5. **Phase 6** depends on Phases 1-5 (docs need all content)
6. **Phase 7** depends on all previous phases (final validation)

### Dependencies

**Sequential Dependencies:**
- **Phase 2** requires **Phase 1** (templates use new schema)
- **Phase 3, 4, 5** require **Phases 1-2** (data needs models and templates)
- **Phase 6** requires **Phases 1-5** (docs need all content)
- **Phase 7** requires **Phases 1-6** (final validation needs everything)

**Parallel Opportunities:**
- **Phases 3, 4, 5** can potentially be done in parallel after Phase 2 completes
- Each can be its own PR without blocking the others

### Risk Mitigation

**Risk**: Breaking existing functionality during schema changes  
**Mitigation**: Each phase includes its own tests; tests must pass before PR

**Risk**: Insufficient coverage of banking principles  
**Mitigation**: Phase 3 focuses solely on creating quality axioms; can iterate

**Risk**: Poor quality banking axioms  
**Mitigation**: Separate phase allows focused review and iteration

**Risk**: Integration issues between phases  
**Mitigation**: Each phase validates independently; Phase 7 does full integration testing

**Risk**: Time overrun on specific phases  
**Mitigation**: Phases are independent; delays in one don't block others (after Phase 2)

### Success Criteria

#### Per-Phase Success Criteria

Each phase must meet these before creating its PR:
- ✅ All tests pass for that phase's changes
- ✅ No linting or type errors introduced
- ✅ Code is properly formatted
- ✅ Changes are focused and complete for that phase

#### Overall Project Success (Phase 7)

**Must Have (Blocking)**:
- [ ] All data models updated to new schema
- [ ] All templates updated and rendering correctly
- [ ] Constitution has minimum 10 banking axioms
- [ ] All unit tests passing
- [ ] No linting or type errors
- [ ] Sample scripts execute successfully
- [ ] No health insurance references in code

**Should Have (Important)**:
- [ ] Evaluation dataset with 10+ banking questions
- [ ] Reality data file with 10+ statements
- [ ] Manual testing completed successfully
- [ ] Documentation fully updated
- [ ] ADR marked as implemented

**Nice to Have (Optional)**:
- [ ] 20+ comprehensive banking axioms
- [ ] 15+ evaluation questions
- [ ] Advanced banking scenarios covered
- [ ] Performance benchmarks documented

---

## Notes

### Implementation Strategy

- Each phase produces an independent, reviewable pull request
- Tests are included in each phase to ensure quality at every step
- **Samples are progressively updated** to allow manual testing of each PR:
  - **Phase 1**: Update basic_qa.py with domain-neutral question
  - **Phase 2**: Update basic_qa.py and basic_qa_streaming.py with simple questions
  - **Phase 3**: Update both with specific banking questions using constitution
  - **Phase 4**: Update qa_with_reality.py to demonstrate reality usage
  - **Phase 6**: Final polish and complete README examples
- Phases 3-5 can potentially run in parallel after Phase 2 completes
- This approach allows for:
  - Incremental review and feedback
  - **Manual testing at each phase** with working samples
  - Early detection of issues
  - Ability to pause/resume work between phases
  - Multiple contributors working on different phases

### Technical Notes

- This plan assumes familiarity with Python 3.12, Pydantic, and Jinja2
- Banking domain expertise is helpful but not required; research is acceptable
- Focus on creating accurate, well-documented axioms over quantity
- The simplified schema significantly reduces complexity
- Constitution axioms should represent timeless banking/economic principles
- Reality statements should represent current, changeable data
- Use Switzerland as the primary geographic context for examples

### Pull Request Strategy

Each phase should have:
1. Clear PR title: `feat(phaseX): <description>`
2. Reference to this implementation plan
3. List of changes made
4. Confirmation that all tests pass
5. Screenshots/examples if relevant

---

**Plan Status**: Ready for Implementation  
**Next Step**: Begin Phase 1 - Data Model Updates (including tests)  
**Approach**: Implement phases sequentially, creating PRs as you complete each phase
