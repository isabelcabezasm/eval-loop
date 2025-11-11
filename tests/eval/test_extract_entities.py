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
)

from eval.dependencies import qa_eval_engine
from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import Entity, EntityExtraction

# Minimum length for meaningful entity variables
# (at least 2 characters to avoid single letter placeholders)
MIN_ENTITY_VARIABLE_LENGTH = 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mock_engine,user_query,llm_answer,expected_answer,expected_result"),
    [
        pytest.param(
            # this is the parameter for mock_engine fixture
            sample_entity_extraction_result,
            "How does credit score affect loan approval?",
            (
                "A higher credit score increases loan approval chances "
                "and may result in lower interest rates."
            ),
            (
                "Credit scores directly influence lending decisions, "
                "with better scores leading to more favorable loan terms."
            ),
            sample_entity_extraction_result,
            id="basic_entity_extraction",
        ),
        pytest.param(
            # this is the parameter for mock_engine fixture
            sample_entity_extraction_with_overlap,
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
            sample_entity_extraction_with_overlap,
            id="entity_extraction_with_overlap",
        ),
    ],
    indirect=["mock_engine"],
)
async def test_qa_eval_engine_entity_extraction(
    mock_engine: QAEvalEngine,
    user_query: str,
    llm_answer: str,
    expected_answer: str,
    expected_result: EntityExtraction,
):
    """Test entity_extraction method with various scenarios.

    Validates:
    - Entities are correctly extracted from user query, LLM answer, and
      expected answer
    - Mock engine returns expected EntityExtraction result
    - Prompt is formatted correctly with all three inputs
    - Agent is called exactly once with proper response format
    - Optional: Validates realistic overlap patterns where user query and
      expected answer share core entities
    """

    result = await mock_engine.entity_extraction(
        user_query=user_query,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    # maybe this is a redundant check but let's keep it just in case
    # we change the implementation in the future
    assert result == expected_result

    # Verify the mock agent was called exactly once with:
    # - Correct response_format (EntityExtraction)
    # - All input texts (user_query, llm_answer, expected_answer) in the
    #   formatted prompt
    _ = assert_mock_agent_called_correctly(
        mock_engine,
        EntityExtraction,
        expected_content=[user_query, llm_answer, expected_answer],
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
    engine = qa_eval_engine()

    # act
    result = await engine.entity_extraction(
        user_query=user_query,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    # assert
    _ = EntityExtraction.model_validate(result)
    # Validate that each entity list has at least one item
    assert len(result.user_query_entities) >= 1, (
        "user_query_entities should contain at least one entity"
    )
    assert len(result.llm_answer_entities) >= 1, (
        "llm_answer_entities should contain at least one entity"
    )
    assert len(result.expected_answer_entities) >= 1, (
        "expected_answer_entities should contain at least one entity"
    )

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

    def _validate_entity_structure(
        entity: Entity, min_length: int = 2
    ) -> None:
        """Validate that an entity has proper structure and non-empty
        variables.

        Args:
            entity: The entity to validate.
            min_length: Minimum length for trigger and consequence variables.

        Raises:
            AssertionError: If entity structure is invalid or variables are too
                short.
        """
        _ = Entity.model_validate(entity)

        # Validate that variables are non-empty strings
        assert len(entity.trigger_variable) > 0, (
            "Trigger variable should not be empty"
        )
        assert len(entity.consequence_variable) > 0, (
            "Consequence variable should not be empty"
        )

        # Validate that variables are meaningful (meet minimum length)
        assert len(entity.trigger_variable) >= min_length, (
            f"Trigger variable '{entity.trigger_variable}' too short"
        )
        assert len(entity.consequence_variable) >= min_length, (
            f"Consequence variable '{entity.consequence_variable}' too short"
        )

    for entity in all_entities:
        _validate_entity_structure(
            entity, min_length=MIN_ENTITY_VARIABLE_LENGTH
        )
