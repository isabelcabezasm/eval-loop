"""
Tests for entity extraction functionality in QAEvalEngine and metrics.
"""

import os

import pytest
from tests.eval.common import (
    mock_engine,  # pyright: ignore[reportUnusedImport] it's a fixture
    sample_entity_extraction,  # pyright: ignore[reportUnusedImport] it's a fixture
    sample_entity_extraction_result,
)

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import Entity, EntityExtraction


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
    """Test entity_extraction method."""

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
    # Access the mock agent from the engine
    mock_agent = mock_engine._agent  # type: ignore[attr-defined]
    formatted_prompt: str = mock_agent.run.call_args[0][0]  # type: ignore[attr-defined]

    # Check that the prompt was formatted correctly
    assert "What are the health benefits of exercise?" in formatted_prompt
    assert (
        "Exercise improves cardiovascular health and reduces mortality."
        in formatted_prompt
    )
    assert (
        "Regular physical activity enhances overall health and longevity."
        in formatted_prompt
    )

    mock_agent.run.assert_called_once_with(  # type: ignore[attr-defined]
        formatted_prompt, response_format=EntityExtraction
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_ENDPOINT"),
    reason="Requires AZURE_OPENAI_ENDPOINT environment variable",
)
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    reason="Requires AZURE_OPENAI_CHAT_DEPLOYMENT_NAME environment variable",
)
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
    assert isinstance(result, EntityExtraction)

    # Validate structure
    assert hasattr(result, "user_query_entities")
    assert hasattr(result, "llm_answer_entities")
    assert hasattr(result, "expected_answer_entities")

    # Validate that entities were extracted
    assert isinstance(result.user_query_entities, list)
    assert isinstance(result.llm_answer_entities, list)
    assert isinstance(result.expected_answer_entities, list)

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

    # Validate entity structure for all extracted entities
    all_entities = (
        result.user_query_entities
        + result.llm_answer_entities
        + result.expected_answer_entities
    )

    for entity in all_entities:
        # Validate structure
        assert isinstance(entity, Entity)
        assert hasattr(entity, "trigger_variable")
        assert hasattr(entity, "consequence_variable")

        # Validate that variables are non-empty strings
        assert isinstance(entity.trigger_variable, str)
        assert isinstance(entity.consequence_variable, str)
        assert len(entity.trigger_variable) > 0, (
            "Trigger variable should not be empty"
        )
        assert len(entity.consequence_variable) > 0, (
            "Consequence variable should not be empty"
        )

        # Validate that variables are meaningful
        # (at least 2 characters to avoid single letter placeholders)
        assert len(entity.trigger_variable) >= 2, (
            f"Trigger variable '{entity.trigger_variable}' too short"
        )
        assert len(entity.consequence_variable) >= 2, (
            f"Consequence variable '{entity.consequence_variable}' too short"
        )
