"""
Tests for entity extraction functionality in QAEvalEngine and metrics.
"""

import pytest
from tests.eval.common import (
    assert_mock_agent_called_correctly,
    mock_engine,  # pyright: ignore[reportUnusedImport] it's a fixture
    requires_azure,
    sample_entity_extraction_result,
    sample_entity_extraction_with_overlap,
    validate_entity_extraction_structure,
    validate_entity_structure,
)

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import EntityExtraction

# Minimum length for meaningful entity variables
# (at least 2 characters to avoid single letter placeholders)
MIN_ENTITY_VARIABLE_LENGTH = 2


@pytest.fixture
def sample_entity_extraction():
    """Create a sample EntityExtraction object for testing."""
    return sample_entity_extraction_result


@pytest.fixture
def sample_entity_extraction_overlap():
    """Create a sample EntityExtraction with realistic overlap patterns.

    This fixture represents a more realistic scenario where:
    - User query contains the core entity being asked about
    - LLM answer includes semantically similar entities (e.g., loan_cost
      vs borrowing_cost)
    - Expected answer shares the exact entity from user query plus additional
      context
    """
    return sample_entity_extraction_with_overlap


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_engine",
    [
        pytest.param(
            sample_entity_extraction_result, id="entity_extraction_test"
        )
    ],
    indirect=["mock_engine"],
)
async def test_qa_eval_engine_entity_extraction(
    mock_engine: QAEvalEngine,
    sample_entity_extraction: EntityExtraction,
):
    """Test entity_extraction method with basic scenario.

    Validates:
    - Entities are correctly extracted from user query, LLM answer, and
      expected answer
    - Mock engine returns expected EntityExtraction result
    - Prompt is formatted correctly with all three inputs
    - Agent is called exactly once with proper response format
    """

    result = await mock_engine.entity_extraction(
        user_query="What are the health benefits of exercise?",
        llm_answer=(
            "Exercise improves cardiovascular health and reduces mortality."
        ),
        expected_answer=(
            "Regular physical activity enhances overall health and longevity."
        ),
    )

    assert result == sample_entity_extraction

    # Verify the agent's run method was called correctly
    _ = assert_mock_agent_called_correctly(
        mock_engine,
        EntityExtraction,
        expected_content=[
            "What are the health benefits of exercise?",
            "Exercise improves cardiovascular health and reduces mortality.",
            "Regular physical activity enhances overall health and longevity.",
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_engine",
    [
        pytest.param(
            sample_entity_extraction_with_overlap,
            id="entity_extraction_with_realistic_overlap",
        )
    ],
    indirect=["mock_engine"],
)
async def test_entity_extraction_with_overlap(
    mock_engine: QAEvalEngine,
    sample_entity_extraction_overlap: EntityExtraction,
):
    """Test entity_extraction with realistic overlap patterns.

    This test validates the extraction with a more realistic scenario where:
    - User query and expected answer share the same core entity
    - LLM answer contains semantically similar but not identical entities
    - Expected answer includes additional context beyond the user query
    """
    result = await mock_engine.entity_extraction(
        user_query="How do interest rates affect borrowing?",
        llm_answer=(
            "Interest rates directly impact loan costs and influence "
            "lending decisions by financial institutions."
        ),
        expected_answer=(
            "Changes in interest rates affect borrowing costs for consumers, "
            "while monetary policy influences overall credit availability."
        ),
    )

    assert result == sample_entity_extraction_overlap

    # Verify the core entity appears in both query and expected answer
    assert any(
        e.trigger_variable == "interest_rate"
        for e in result.user_query_entities
    )
    assert any(
        e.trigger_variable == "interest_rate"
        for e in result.expected_answer_entities
    )

    # Verify LLM answer has semantically related but different entities
    assert len(result.llm_answer_entities) > 0

    # Verify the agent was called correctly
    _ = assert_mock_agent_called_correctly(
        mock_engine,
        EntityExtraction,
        expected_content=[
            "How do interest rates affect borrowing?",
            (
                "Interest rates directly impact loan costs and influence "
                "lending decisions by financial institutions."
            ),
            (
                "Changes in interest rates affect borrowing costs for "
                "consumers, while monetary policy influences overall credit "
                "availability."
            ),
        ],
    )


@pytest.mark.integration
@pytest.mark.asyncio
@requires_azure
@pytest.mark.parametrize(
    "user_query,llm_answer,expected_answer,min_entity_count",
    [
        pytest.param(
            "How do interest rates affect borrowing costs?",
            (
                "Higher interest rates directly increase borrowing costs "
                "for consumers and businesses."
            ),
            (
                "When interest rates rise, the cost of borrowing money "
                "increases for both individuals and companies."
            ),
            1,
            id="single_causal_relationship",
        ),
        pytest.param(
            "What is the impact of inflation on the economy?",
            (
                "Rising inflation erodes purchasing power while high "
                "unemployment dampens economic activity."
            ),
            (
                "Inflation reduces purchasing power and unemployment "
                "decreases consumer spending levels."
            ),
            2,
            id="multiple_causal_relationships",
        ),
    ],
)
async def test_entity_extraction_integration(
    user_query: str,
    llm_answer: str,
    expected_answer: str,
    min_entity_count: int,
):
    """
    Integration test for entity_extraction with real LLM calls.

    This test validates:
    - The entity_extraction method works end-to-end with real API
    - Entities are extracted from user query, LLM answer, and expected answer
    - Each entity has valid trigger and consequence variables
    - Minimum expected entities are extracted
    """
    # arrange
    from eval.dependencies import qa_eval_engine

    engine = qa_eval_engine()

    # act
    result = await engine.entity_extraction(
        user_query=user_query,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    # assert
    # Validate structure using helper function
    validate_entity_extraction_structure(result)

    # Check minimum entity count across all categories
    total_entities = (
        len(result.user_query_entities)
        + len(result.llm_answer_entities)
        + len(result.expected_answer_entities)
    )
    assert total_entities >= min_entity_count, (
        f"Expected at least {min_entity_count} total entities, "
        f"got {total_entities}"
    )

    # Validate entity structure for all extracted entities using helper
    all_entities = (
        result.user_query_entities
        + result.llm_answer_entities
        + result.expected_answer_entities
    )

    for entity in all_entities:
        validate_entity_structure(
            entity, min_length=MIN_ENTITY_VARIABLE_LENGTH
        )
