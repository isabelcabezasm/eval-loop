"""
Tests for accuracy metric functionality in QAEvalEngine and metrics.
"""

from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
from agent_framework import AgentRunResponse, ChatAgent
from tests.eval.common import mock_chat_agent

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.metrics.accuracy import get_accuracy
from eval.metrics.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
)


@pytest.fixture
def sample_entity_extraction():
    """Create a sample EntityExtraction object for testing."""
    return EntityExtraction(
        user_query_entities=[
            Entity(trigger_variable="exercise", consequence_variable="health"),
            Entity(trigger_variable="age", consequence_variable="mortality"),
        ],
        llm_answer_entities=[
            Entity(
                trigger_variable="physical_activity", consequence_variable="wellness"
            ),
            Entity(trigger_variable="smoking", consequence_variable="lung_disease"),
        ],
        expected_answer_entities=[
            Entity(trigger_variable="exercise", consequence_variable="health"),
            Entity(trigger_variable="smoking", consequence_variable="mortality"),
        ],
    )


@pytest.fixture
def sample_accuracy_results():
    """Create sample AccuracyEvaluationResults for testing."""
    return AccuracyEvaluationResults(
        entity_accuracies=[
            EntityAccuracy(
                entity="('exercise', 'health')",
                reason=(
                    "The entity exercise->health is accurately represented in "
                    "both answers with similar semantic meaning."
                ),
                score=1.0,
            ),
            EntityAccuracy(
                entity="('smoking', 'mortality')",
                reason=(
                    "The entity smoking->mortality is partially represented; "
                    "LLM mentions lung disease but not mortality specifically."
                ),
                score=0.7,
            ),
        ],
        accuracy_mean=0.85,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_extraction,prompt_template,expected_result_type,expected_mean,expected_count",
    [
        pytest.param(
            # fixtures cannot be used as value in the parameter.
            "_FIXTURE",  # Will be resolved from fixture
            "Entities: {entity_list}\nLLM: {llm_answer}\nExpected: {expected_answer}",
            "_FIXTURE",  # Will be resolved from fixture
            0.85,
            2,
            id="successful_evaluation",
        ),
        pytest.param(
            "_FIXTURE",  # Will be resolved from fixture
            "Entities: {entity_list}\nLLM: {llm_answer}\nExpected: {expected_answer}",
            "_FIXTURE",  # Will be resolved from fixture
            0.85,
            2,
            id="prompt_formatting_test",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            "Entities: {entity_list}\nLLM: {llm_answer}\nExpected: {expected_answer}",
            AccuracyEvaluationResults(entity_accuracies=[], accuracy_mean=0.0),
            0.0,
            0,
            id="empty_entity_list",
        ),
    ],
)
async def test_accuracy_evaluation_scenarios(
    mock_chat_agent,
    sample_entity_extraction,
    sample_accuracy_results,
    entity_extraction,
    prompt_template,
    expected_result_type,
    expected_mean,
    expected_count,
):
    """Test QAEvalEngine.accuracy_evaluation with different scenarios."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    # Resolve fixture references to actual objects
    if entity_extraction == "_FIXTURE":
        entity_extraction = sample_entity_extraction
    if expected_result_type == "_FIXTURE":
        expected_result_type = sample_accuracy_results

    with patch.object(
        engine, "_get_prompt", return_value=prompt_template
    ) as mock_get_prompt:
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=expected_result_type,
        ) as mock_invoke:
            llm_answer = "Exercise improves cardiovascular health significantly."
            expected_answer = (
                "Regular physical activity enhances overall health and "
                "reduces mortality risk."
            )
            result = await engine.accuracy_evaluation(
                entity_list=entity_extraction,
                llm_answer=llm_answer,
                expected_answer=expected_answer,
            )

    # Common assertions
    assert result == expected_result_type
    assert isinstance(result, AccuracyEvaluationResults)
    assert len(result.entity_accuracies) == expected_count
    assert result.accuracy_mean == expected_mean
    mock_get_prompt.assert_called_once_with("accuracy")

    formatted_prompt = mock_invoke.call_args[0][0]
    assert isinstance(formatted_prompt, str)
    mock_invoke.assert_called_once_with(formatted_prompt, AccuracyEvaluationResults)
    assert llm_answer in formatted_prompt
    assert expected_answer in formatted_prompt
    if expected_count > 0:
        assert "('exercise', 'health')" in formatted_prompt
        assert "('smoking', 'mortality')" in formatted_prompt


@pytest.mark.asyncio
async def test_accuracy_evaluation_integration(sample_entity_extraction):
    """Test accuracy_evaluation with realistic mock responses."""
    mock_agent = AsyncMock(spec=ChatAgent)

    sample_results = AccuracyEvaluationResults(
        entity_accuracies=[
            EntityAccuracy(
                entity="('exercise', 'health')",
                reason="Exercise strongly correlates with improved health outcomes.",
                score=0.95,
            ),
        ],
        accuracy_mean=0.95,
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
                "Evaluate entities: {entity_list} LLM: {llm_answer} Expected: {expected_answer}"
            )
        ),
    ):
        with patch("eval.llm_evaluator.qa_eval_engine.Path"):
            result = await engine.accuracy_evaluation(
                entity_list=sample_entity_extraction,
                llm_answer="Regular exercise significantly improves health.",
                expected_answer="Physical activity is beneficial for health.",
            )

    assert result == sample_results
    assert result.accuracy_mean == 0.95
    assert len(result.entity_accuracies) == 1


@pytest.mark.asyncio
async def test_accuracy_evaluation_error_handling(mock_chat_agent):
    """Test accuracy_evaluation error handling."""
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
                await engine.accuracy_evaluation(
                    entity_list=sample_extraction,
                    llm_answer="test answer",
                    expected_answer="test expected",
                )


@pytest.mark.asyncio
async def test_accuracy_evaluation_entity_list_formatting(
    mock_chat_agent, sample_accuracy_results
):
    """Test that entity list is properly formatted in the prompt."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    entity_extraction = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[],
        expected_answer_entities=[
            Entity(trigger_variable="exercise", consequence_variable="health"),
            Entity(trigger_variable="diet", consequence_variable="weight"),
            Entity(trigger_variable="sleep", consequence_variable="energy"),
        ],
    )

    with patch.object(engine, "_get_prompt", return_value="{entity_list}"):
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=sample_accuracy_results,
        ) as mock_invoke:
            await engine.accuracy_evaluation(
                entity_list=entity_extraction,
                llm_answer="test answer",
                expected_answer="test expected",
            )

    formatted_prompt = mock_invoke.call_args[0][0]
    # Check that all entities are properly formatted with quotes and commas
    assert "('exercise', 'health')" in formatted_prompt
    assert "('diet', 'weight')" in formatted_prompt
    assert "('sleep', 'energy')" in formatted_prompt
    # Check comma separation
    assert (
        "('exercise', 'health'), ('diet', 'weight'), ('sleep', 'energy')"
        in formatted_prompt
    )


@pytest.mark.asyncio
@patch("eval.metrics.accuracy.qa_eval_engine")
async def test_get_accuracy_error(mock_qa_eval_engine):
    """Test that get_accuracy properly propagates errors from QAEvalEngine."""
    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.accuracy_evaluation.side_effect = Exception("Model evaluation failed")
    mock_qa_eval_engine.return_value = mock_engine

    entity_extraction = EntityExtraction(
        user_query_entities=[],
        llm_answer_entities=[],
        expected_answer_entities=[],
    )

    with pytest.raises(Exception, match="Model evaluation failed"):
        await get_accuracy(
            entity_list=entity_extraction,
            llm_answer="test answer",
            expected_answer="test expected",
        )


@pytest.mark.asyncio
@patch("eval.metrics.accuracy.qa_eval_engine")
@pytest.mark.parametrize(
    "entity_extraction,expected_mean,llm_answer,expected_answer",
    [
        pytest.param(
            # Case 1: Entity extraction with one entity (from keyword arguments test)
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[
                    Entity(trigger_variable="exercise", consequence_variable="health")
                ],
            ),
            0.85,
            "test llm answer",
            "test expected answer",
            id="single_entity",
        ),
        pytest.param(
            # Case 2: Empty entity extraction (from empty entity list test)
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            0.0,
            "test llm answer",
            "test expected answer",
            id="empty_entity_list",
        ),
        pytest.param(
            # Case 3: Full entity extraction with realistic data (from success test)
            "_FIXTURE",  # Will be resolved to sample_entity_extraction
            0.85,
            "Exercise improves health significantly.",
            "Physical activity enhances wellness and reduces disease risk.",
            id="realistic_data_success",
        ),
    ],
)
async def test_accuracy_evaluation_entity_list(
    mock_qa_eval_engine,
    entity_extraction,
    expected_mean,
    llm_answer,
    expected_answer,
    sample_entity_extraction,
    sample_accuracy_results,
):
    """Test get_accuracy function with different entity extraction configurations."""
    mock_engine = AsyncMock(spec=QAEvalEngine)

    # Resolve fixture reference to actual object
    if entity_extraction == "_FIXTURE":
        entity_extraction = sample_entity_extraction

    if expected_mean == 0.0:
        # For empty entity list case
        empty_results = AccuracyEvaluationResults(
            entity_accuracies=[], accuracy_mean=0.0
        )
        mock_engine.accuracy_evaluation.return_value = empty_results
        expected_results = empty_results
    else:
        # For non-empty entity list case
        mock_engine.accuracy_evaluation.return_value = sample_accuracy_results
        expected_results = sample_accuracy_results

    mock_qa_eval_engine.return_value = mock_engine

    result = await get_accuracy(
        entity_list=entity_extraction,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    assert result == expected_results
    assert result.accuracy_mean == expected_mean
    assert isinstance(result, AccuracyEvaluationResults)
    mock_qa_eval_engine.assert_called_once()
    mock_engine.accuracy_evaluation.assert_called_once_with(
        entity_extraction, llm_answer, expected_answer
    )


@pytest.mark.asyncio
async def test_full_accuracy_evaluation_workflow(sample_entity_extraction):
    """Test the complete accuracy evaluation workflow without external API calls."""
    sample_results = AccuracyEvaluationResults(
        entity_accuracies=[
            EntityAccuracy(
                entity="('exercise', 'health')",
                reason="Both answers correctly indicate that exercise improves health outcomes.",
                score=0.9,
            ),
            EntityAccuracy(
                entity="('smoking', 'mortality')",
                reason="LLM answer mentions health risks but not mortality specifically.",
                score=0.6,
            ),
        ],
        accuracy_mean=0.75,
    )

    with patch("eval.metrics.accuracy.qa_eval_engine") as mock_qa_eval_engine:
        mock_engine = AsyncMock()
        mock_engine.accuracy_evaluation.return_value = sample_results
        mock_qa_eval_engine.return_value = mock_engine

        result = await get_accuracy(
            entity_list=sample_entity_extraction,
            llm_answer=(
                "Regular exercise significantly improves cardiovascular health "
                "and reduces the risk of chronic diseases. Smoking cessation "
                "also greatly benefits overall health."
            ),
            expected_answer=(
                "Physical activity enhances health outcomes and longevity. "
                "Avoiding tobacco use reduces mortality risk substantially."
            ),
        )

        # Verify the result
        assert isinstance(result, AccuracyEvaluationResults)
        assert result.accuracy_mean == 0.75
        assert len(result.entity_accuracies) == 2

        # Verify individual entity accuracies
        entity_scores = {ea.entity: ea.score for ea in result.entity_accuracies}
        assert entity_scores["('exercise', 'health')"] == 0.9
        assert entity_scores["('smoking', 'mortality')"] == 0.6

        # Verify the workflow was called correctly
        mock_qa_eval_engine.assert_called_once()
        mock_engine.accuracy_evaluation.assert_called_once()


@pytest.mark.parametrize(
    "entity_accuracies,expected_mean",
    [
        pytest.param(
            [
                EntityAccuracy(entity="entity1", reason="reason1", score=0.8),
                EntityAccuracy(entity="entity2", reason="reason2", score=0.6),
                EntityAccuracy(entity="entity3", reason="reason3", score=1.0),
            ],
            (0.8 + 0.6 + 1.0) / 3,
            id="with_entities",
        ),
        pytest.param(
            [],
            0.0,
            id="empty_list",
        ),
    ],
)
def test_calculate_accuracy_mean_scenarios(entity_accuracies, expected_mean):
    """Test the calculate_accuracy_mean method with different entity configurations."""
    results = AccuracyEvaluationResults(
        entity_accuracies=entity_accuracies,
        accuracy_mean=0.0,  # Will be recalculated
    )

    calculated_mean = results.calculate_accuracy_mean()

    if entity_accuracies:
        # For non-empty lists, use approximate comparison due to floating point
        assert abs(calculated_mean - expected_mean) < 1e-6
    else:
        # For empty list, exact comparison is fine
        assert calculated_mean == expected_mean


def test_entity_accuracy_validation():
    """Test EntityAccuracy validation with score bounds."""
    # Valid score
    entity_acc = EntityAccuracy(
        entity="test_entity",
        reason="Test reasoning",
        score=0.5,
    )
    assert entity_acc.score == 0.5

    # Test boundary values
    entity_acc_min = EntityAccuracy(
        entity="test_entity",
        reason="Test reasoning",
        score=0.0,
    )
    assert entity_acc_min.score == 0.0

    entity_acc_max = EntityAccuracy(
        entity="test_entity",
        reason="Test reasoning",
        score=1.0,
    )
    assert entity_acc_max.score == 1.0

    # Invalid scores should raise validation error
    with pytest.raises(ValueError):
        EntityAccuracy(
            entity="test_entity",
            reason="Test reasoning",
            score=-0.1,
        )

    with pytest.raises(ValueError):
        EntityAccuracy(
            entity="test_entity",
            reason="Test reasoning",
            score=1.1,
        )
