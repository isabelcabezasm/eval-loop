"""
Tests for topic coverage metric functionality in QAEvalEngine and metrics.
"""

from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
from agent_framework import AgentRunResponse, ChatAgent
from tests.eval.common import mock_chat_agent, sample_entity_extraction

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.metrics.models import (
    Entity,
    EntityExtraction,
    TopicCoverageEvaluationResults,
)
from eval.metrics.topic_coverage import get_topic_coverage


@pytest.fixture
def sample_topic_coverage_results():
    """Create sample TopicCoverageEvaluationResults for testing."""
    return TopicCoverageEvaluationResults(
        reason=(
            "The generated answer covers 1 out of 2 expected topics. "
            "The topic ('exercise', 'health') is well represented through "
            "('physical_activity', 'wellness') which are semantically equivalent. "
            "However, the topic ('smoking', 'mortality') is missing from the "
            "generated entities, though 'lung_disease' is mentioned instead of 'mortality'."
        ),
        coverage_score=0.5,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_extraction,prompt_template,expected_result_type,expected_score,expected_entities_count",
    [
        pytest.param(
            # fixtures cannot be used as value in the parameter.
            "_FIXTURE",  # Will be resolved from fixture
            "Expected: {expected_entities}\nGenerated: {generated_entities}",
            "_FIXTURE",  # Will be resolved from fixture
            0.5,
            2,
            id="successful_evaluation",
        ),
        pytest.param(
            "_FIXTURE",  # Will be resolved from fixture
            "Expected: {expected_entities}\nGenerated: {generated_entities}",
            "_FIXTURE",  # Will be resolved from fixture
            0.5,
            2,
            id="prompt_formatting_test",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            "Expected: {expected_entities}\nGenerated: {generated_entities}",
            TopicCoverageEvaluationResults(
                reason="No expected entities to evaluate coverage for.",
                coverage_score=1.0,
            ),
            1.0,
            0,
            id="empty_entity_list",
        ),
    ],
)
async def test_topic_coverage_evaluation_scenarios(
    mock_chat_agent,
    sample_entity_extraction,
    sample_topic_coverage_results,
    entity_extraction,
    prompt_template,
    expected_result_type,
    expected_score,
    expected_entities_count,
):
    """Test QAEvalEngine.topic_coverage_evaluation with different scenarios."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    # Resolve fixture references to actual objects
    if entity_extraction == "_FIXTURE":
        entity_extraction = sample_entity_extraction
    if expected_result_type == "_FIXTURE":
        expected_result_type = sample_topic_coverage_results

    with patch.object(
        engine, "_get_prompt", return_value=prompt_template
    ) as mock_get_prompt:
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=expected_result_type,
        ) as mock_invoke:
            result = await engine.topic_coverage_evaluation(
                entity_list=entity_extraction
            )

    # Common assertions
    assert result == expected_result_type
    assert isinstance(result, TopicCoverageEvaluationResults)
    assert result.coverage_score == expected_score
    mock_get_prompt.assert_called_once_with("topic_coverage")

    formatted_prompt = mock_invoke.call_args[0][0]
    assert isinstance(formatted_prompt, str)
    mock_invoke.assert_called_once_with(
        formatted_prompt, TopicCoverageEvaluationResults
    )

    if expected_entities_count > 0:
        assert "('exercise', 'health')" in formatted_prompt
        assert "('smoking', 'mortality')" in formatted_prompt
        assert "('physical_activity', 'wellness')" in formatted_prompt
        assert "('smoking', 'lung_disease')" in formatted_prompt


@pytest.mark.asyncio
# integration: no mocking _get_prompt and _perform_model_invocation
async def test_topic_coverage_evaluation_integration(sample_entity_extraction):
    """Test topic_coverage_evaluation with realistic mock responses."""
    mock_agent = AsyncMock(spec=ChatAgent)

    sample_results = TopicCoverageEvaluationResults(
        reason=(
            "The generated answer covers 2 out of 2 expected topics with high "
            "semantic similarity. Both exercise->health and smoking->mortality "
            "relationships are well represented."
        ),
        coverage_score=1.0,
    )

    mock_response = Mock(spec=AgentRunResponse)
    mock_response.value = sample_results
    mock_agent.run.return_value = mock_response

    engine = QAEvalEngine(agent=mock_agent)

    # Mock file reading for prompts
    with patch(
        "builtins.open",
        mock_open(
            read_data=(
                "Evaluate topic coverage: Expected: {expected_entities} Generated: {generated_entities}"
            )
        ),
    ):
        with patch("eval.llm_evaluator.qa_eval_engine.Path"):
            result = await engine.topic_coverage_evaluation(
                entity_list=sample_entity_extraction
            )

    assert result == sample_results
    assert result.coverage_score == 1.0
    assert "exercise->health" in result.reason
    assert "smoking->mortality" in result.reason


@pytest.mark.asyncio
async def test_topic_coverage_evaluation_error_handling(mock_chat_agent):
    """Test topic_coverage_evaluation error handling."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    sample_extraction = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[],
        expected_answer_entities=[
            Entity(trigger_variable="test", consequence_variable="test")
        ],
    )

    with patch.object(engine, "_get_prompt", return_value="test prompt"):
        with patch.object(
            engine, "_perform_model_invocation", side_effect=Exception("API Error")
        ):
            with pytest.raises(Exception, match="API Error"):
                await engine.topic_coverage_evaluation(entity_list=sample_extraction)


@pytest.mark.asyncio
async def test_topic_coverage_evaluation_entity_formatting(
    mock_chat_agent, sample_topic_coverage_results
):
    """Test that entities are properly formatted in the prompt."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    entity_extraction = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[
            Entity(trigger_variable="diet", consequence_variable="weight"),
            Entity(trigger_variable="sleep", consequence_variable="energy"),
        ],
        expected_answer_entities=[
            Entity(trigger_variable="exercise", consequence_variable="health"),
            Entity(trigger_variable="nutrition", consequence_variable="wellness"),
            Entity(trigger_variable="rest", consequence_variable="recovery"),
        ],
    )

    with patch.object(
        engine,
        "_get_prompt",
        return_value="Expected: {expected_entities}\nGenerated: {generated_entities}",
    ):
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=sample_topic_coverage_results,
        ) as mock_invoke:
            await engine.topic_coverage_evaluation(entity_list=entity_extraction)

    formatted_prompt = mock_invoke.call_args[0][0]

    # Check that expected entities are properly formatted
    assert "('exercise', 'health')" in formatted_prompt
    assert "('nutrition', 'wellness')" in formatted_prompt
    assert "('rest', 'recovery')" in formatted_prompt

    # Check that generated entities are properly formatted
    assert "('diet', 'weight')" in formatted_prompt
    assert "('sleep', 'energy')" in formatted_prompt

    # Check comma separation for multiple entities
    assert (
        "('exercise', 'health'), ('nutrition', 'wellness'), ('rest', 'recovery')"
        in formatted_prompt
    )
    assert "('diet', 'weight'), ('sleep', 'energy')" in formatted_prompt


@pytest.mark.asyncio
@patch("eval.metrics.topic_coverage.qa_eval_engine")
async def test_get_topic_coverage_error(mock_qa_eval_engine):
    """Test that get_topic_coverage properly propagates errors from QAEvalEngine."""
    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.topic_coverage_evaluation.side_effect = Exception(
        "Model evaluation failed"
    )
    mock_qa_eval_engine.return_value = mock_engine

    entity_extraction = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[],
        expected_answer_entities=[],
    )

    with pytest.raises(Exception, match="Model evaluation failed"):
        await get_topic_coverage(entity_list=entity_extraction)


@pytest.mark.asyncio
@patch("eval.metrics.topic_coverage.qa_eval_engine")
@pytest.mark.parametrize(
    "entity_extraction,expected_score",
    [
        pytest.param(
            # Case 1: Entity extraction with partial coverage
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[
                    Entity(trigger_variable="exercise", consequence_variable="health")
                ],
                expected_answer_entities=[
                    Entity(trigger_variable="exercise", consequence_variable="health"),
                    Entity(trigger_variable="diet", consequence_variable="weight"),
                ],
            ),
            0.5,
            id="partial_coverage",
        ),
        pytest.param(
            # Case 2: Empty entity extraction (from empty entity list test)
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            1.0,
            id="empty_entity_list",
        ),
        pytest.param(
            # Case 3: Full entity extraction with complete coverage
            "_FIXTURE",  # Will be resolved to sample_entity_extraction
            0.8,
            id="complete_coverage",
        ),
    ],
)
async def test_get_topic_coverage_scenarios(
    mock_qa_eval_engine,
    entity_extraction,
    expected_score,
    sample_entity_extraction,
    sample_topic_coverage_results,
):
    """Test get_topic_coverage function with different entity extraction configurations."""
    mock_engine = AsyncMock(spec=QAEvalEngine)

    # Resolve fixture reference to actual object
    if entity_extraction == "_FIXTURE":
        entity_extraction = sample_entity_extraction

    if expected_score == 1.0 and len(entity_extraction.expected_answer_entities) == 0:
        # For empty entity list case
        empty_results = TopicCoverageEvaluationResults(
            reason="No expected entities to evaluate coverage for.",
            coverage_score=1.0,
        )
        mock_engine.topic_coverage_evaluation.return_value = empty_results
        expected_results = empty_results
    elif expected_score == 0.5:
        # For partial coverage case
        partial_results = TopicCoverageEvaluationResults(
            reason="The generated answer covers 1 out of 2 expected topics.",
            coverage_score=0.5,
        )
        mock_engine.topic_coverage_evaluation.return_value = partial_results
        expected_results = partial_results
    else:
        # For complete coverage case
        complete_results = TopicCoverageEvaluationResults(
            reason="The generated answer covers most expected topics.",
            coverage_score=0.8,
        )
        mock_engine.topic_coverage_evaluation.return_value = complete_results
        expected_results = complete_results

    mock_qa_eval_engine.return_value = mock_engine

    result = await get_topic_coverage(entity_list=entity_extraction)

    assert result == expected_results
    assert result.coverage_score == expected_score
    assert isinstance(result, TopicCoverageEvaluationResults)
    mock_qa_eval_engine.assert_called_once()
    mock_engine.topic_coverage_evaluation.assert_called_once_with(entity_extraction)


@pytest.mark.asyncio
async def test_full_topic_coverage_evaluation_workflow(sample_entity_extraction):
    """Test the complete topic coverage evaluation workflow without external API calls."""
    sample_results = TopicCoverageEvaluationResults(
        reason=(
            "The generated answer covers 1 out of 2 expected topics. "
            "The topic ('exercise', 'health') is well represented through "
            "('physical_activity', 'wellness') with high semantic similarity. "
            "However, the topic ('smoking', 'mortality') is only partially covered "
            "as the generated answer mentions 'lung_disease' but not 'mortality'."
        ),
        coverage_score=0.75,
    )

    with patch("eval.metrics.topic_coverage.qa_eval_engine") as mock_qa_eval_engine:
        mock_engine = AsyncMock()
        mock_engine.topic_coverage_evaluation.return_value = sample_results
        mock_qa_eval_engine.return_value = mock_engine

        result = await get_topic_coverage(entity_list=sample_entity_extraction)

        # Verify the result
        assert isinstance(result, TopicCoverageEvaluationResults)
        assert result.coverage_score == 0.75
        assert "exercise" in result.reason
        assert "smoking" in result.reason
        assert "semantic similarity" in result.reason

        # Verify the workflow was called correctly
        mock_qa_eval_engine.assert_called_once()
        mock_engine.topic_coverage_evaluation.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_query_entities,llm_answer_entities,expected_answer_entities,expected_score,expected_reason_contains,prompt_template,expected_prompt_contains",
    [
        pytest.param(
            # Case 1: No generated entities
            [Entity(trigger_variable="exercise", consequence_variable="health")],
            [],  # No generated entities
            [
                Entity(trigger_variable="exercise", consequence_variable="health"),
                Entity(trigger_variable="diet", consequence_variable="weight"),
            ],
            0.0,
            "No entities were generated",
            "{expected_entities} {generated_entities}",
            "('exercise', 'health'), ('diet', 'weight')",
            id="no_generated_entities",
        ),
        pytest.param(
            # Case 2: No expected entities
            [Entity(trigger_variable="exercise", consequence_variable="health")],
            [Entity(trigger_variable="diet", consequence_variable="weight")],
            [],  # No expected entities
            1.0,
            "No expected entities",
            "{expected_entities} {generated_entities}",
            "('diet', 'weight')",
            id="no_expected_entities",
        ),
        pytest.param(
            # Case 3: Normal case with specific prompt template
            [],
            [Entity(trigger_variable="nutrition", consequence_variable="health")],
            [Entity(trigger_variable="exercise", consequence_variable="fitness")],
            0.6,
            "Test evaluation",
            "Expected entities: {expected_entities}\nGenerated entities: {generated_entities}",
            "Expected entities: ('exercise', 'fitness')\nGenerated entities: ('nutrition', 'health')",
            id="normal_prompt_parameters",
        ),
    ],
)
async def test_topic_coverage_evaluation(
    mock_chat_agent,
    user_query_entities,
    llm_answer_entities,
    expected_answer_entities,
    expected_score,
    expected_reason_contains,
    prompt_template,
    expected_prompt_contains,
):
    """Test topic coverage evaluation edge cases and prompt parameter formatting."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    entity_extraction = EntityExtraction(
        user_query_entities=user_query_entities,
        llm_answer_entities=llm_answer_entities,
        expected_answer_entities=expected_answer_entities,
    )

    mock_results = TopicCoverageEvaluationResults(
        reason=expected_reason_contains,
        coverage_score=expected_score,
    )

    with patch.object(
        engine, "_get_prompt", return_value=prompt_template
    ) as mock_get_prompt:
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=mock_results,
        ) as mock_invoke:
            result = await engine.topic_coverage_evaluation(
                entity_list=entity_extraction
            )

    # Verify results
    assert result.coverage_score == expected_score
    assert expected_reason_contains in result.reason

    # Verify _get_prompt was called with correct parameter
    mock_get_prompt.assert_called_once_with("topic_coverage")

    # Verify the prompt was formatted correctly
    formatted_prompt = mock_invoke.call_args[0][0]
    assert expected_prompt_contains in formatted_prompt


@pytest.mark.parametrize(
    "coverage_score,expected_valid",
    [
        pytest.param(0.0, True, id="minimum_valid_score"),
        pytest.param(0.5, True, id="middle_valid_score"),
        pytest.param(1.0, True, id="maximum_valid_score"),
        pytest.param(-0.1, False, id="below_minimum_invalid"),
        pytest.param(1.1, False, id="above_maximum_invalid"),
    ],
)
def test_topic_coverage_results_validation(coverage_score, expected_valid):
    """Test TopicCoverageEvaluationResults validation with score bounds."""
    if expected_valid:
        # Valid score should not raise an exception
        result = TopicCoverageEvaluationResults(
            reason="Test reasoning",
            coverage_score=coverage_score,
        )
        assert result.coverage_score == coverage_score
    else:
        # Invalid scores should raise validation error
        with pytest.raises(ValueError):
            TopicCoverageEvaluationResults(
                reason="Test reasoning",
                coverage_score=coverage_score,
            )
