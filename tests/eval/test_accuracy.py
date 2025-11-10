"""
Tests for accuracy metric functionality in QAEvalEngine and metrics.
"""

import math
import os

import pytest
from tests.eval.common import (
    mock_engine,  # pyright: ignore[reportUnusedImport] it's a fixture
    sample_accuracy_evaluation_results,
    sample_entity_extraction_result,
)

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_extraction,mock_engine,expected_mean,expected_count,check_entities",
    [
        pytest.param(
            sample_entity_extraction_result,
            sample_accuracy_evaluation_results,
            0.85,
            2,
            [
                "('interest_rate', 'borrowing_cost')",
                "('unemployment', 'purchasing_power')",
            ],
            id="successful_evaluation",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            AccuracyEvaluationResults(entity_accuracies=[], accuracy_mean=0.0),
            0.0,
            0,
            [],
            id="empty_entity_list",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[
                    Entity(
                        trigger_variable="gdp_growth",
                        consequence_variable="employment_rate",
                    ),
                ],
                llm_answer_entities=[
                    Entity(
                        trigger_variable="interest_rate",
                        consequence_variable="borrowing_cost",
                    ),
                    Entity(
                        trigger_variable="inflation",
                        consequence_variable="purchasing_power",
                    ),
                ],
                expected_answer_entities=[
                    Entity(
                        trigger_variable="interest_rate",
                        consequence_variable="borrowing_cost",
                    ),
                    Entity(
                        trigger_variable="inflation",
                        consequence_variable="purchasing_power",
                    ),
                    Entity(
                        trigger_variable="monetary_policy",
                        consequence_variable="investment_decisions",
                    ),
                ],
            ),
            AccuracyEvaluationResults(
                entity_accuracies=[
                    EntityAccuracy(
                        entity=Entity(
                            trigger_variable="interest_rate",
                            consequence_variable="borrowing_cost",
                        ),
                        reason="Test reason 1",
                        score=0.9,
                    ),
                    EntityAccuracy(
                        entity=Entity(
                            trigger_variable="inflation",
                            consequence_variable="purchasing_power",
                        ),
                        reason="Test reason 2",
                        score=0.85,
                    ),
                    EntityAccuracy(
                        entity=Entity(
                            trigger_variable="monetary_policy",
                            consequence_variable="investment_decisions",
                        ),
                        reason="Test reason 3",
                        score=0.75,
                    ),
                ],
                accuracy_mean=(0.9 + 0.85 + 0.75) / 3,
            ),
            (0.9 + 0.85 + 0.75) / 3,
            3,
            [
                "('interest_rate', 'borrowing_cost')",
                "('inflation', 'purchasing_power')",
                "('monetary_policy', 'investment_decisions')",
            ],
            id="multiple_expected_entities_formatting",
        ),
    ],
    indirect=["mock_engine"],
)
async def test_accuracy_evaluation_scenarios(
    entity_extraction: EntityExtraction,
    mock_engine: QAEvalEngine,
    expected_mean: float,
    expected_count: int,
    check_entities: list[str],
):
    """Test QAEvalEngine.accuracy_evaluation with different scenarios."""

    llm_answer = (
        "Higher interest rates increase borrowing costs for "
        "consumers and businesses."
    )
    expected_answer = (
        "Monetary policy changes affect lending rates and "
        "impact economic activity levels."
    )
    result = await mock_engine.accuracy_evaluation(
        entity_list=entity_extraction,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    # Common assertions
    assert isinstance(result, AccuracyEvaluationResults)
    assert len(result.entity_accuracies) == expected_count
    assert result.accuracy_mean == expected_mean

    # Verify the agent's run method was called correctly
    # Access the mock agent from the engine
    mock_agent = mock_engine._agent  # type: ignore[attr-defined]
    formatted_prompt: str = mock_agent.run.call_args[0][0]  # type: ignore[attr-defined]

    mock_agent.run.assert_called_once_with(  # type: ignore[attr-defined]
        formatted_prompt, response_format=AccuracyEvaluationResults
    )
    assert isinstance(formatted_prompt, str)
    assert llm_answer in formatted_prompt
    assert expected_answer in formatted_prompt

    # Check that all expected entities appear in the formatted prompt
    for entity_str in check_entities:
        assert entity_str in formatted_prompt

    # For multiple entity scenarios, verify comma-separated format
    if len(check_entities) > 1:
        # Verify entities are comma-space separated in the prompt
        formatted_entity_list = ", ".join(check_entities)
        assert formatted_entity_list in formatted_prompt, (
            f"Expected comma-separated entity list not found in prompt. "
            f"Looking for: {formatted_entity_list}"
        )


@pytest.mark.parametrize(
    "entity_accuracies,expected_mean",
    [
        pytest.param(
            [
                EntityAccuracy(
                    entity=Entity(
                        trigger_variable="trigger1",
                        consequence_variable="consequence1",
                    ),
                    reason="reason1",
                    score=0.8,
                ),
                EntityAccuracy(
                    entity=Entity(
                        trigger_variable="trigger2",
                        consequence_variable="consequence2",
                    ),
                    reason="reason2",
                    score=0.6,
                ),
                EntityAccuracy(
                    entity=Entity(
                        trigger_variable="trigger3",
                        consequence_variable="consequence3",
                    ),
                    reason="reason3",
                    score=1.0,
                ),
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
def test_calculate_accuracy_mean_scenarios(
    entity_accuracies: list[EntityAccuracy], expected_mean: float
):
    """
    Test the calculate_accuracy_mean method with different entity
    configurations.
    """
    results = AccuracyEvaluationResults(
        entity_accuracies=entity_accuracies,
        # accuracy_mean Will be recalculated with "calculate_accuracy_mean"
        accuracy_mean=0.0,
    )

    calculated_mean = results.calculate_accuracy_mean()

    # Use math.isclose for floating point comparison with proper type checking
    assert math.isclose(
        calculated_mean, expected_mean, rel_tol=1e-9, abs_tol=1e-9
    )


def test_entity_accuracy_validation():
    """Test EntityAccuracy validation with score bounds."""
    test_entity = Entity(
        trigger_variable="test_trigger",
        consequence_variable="test_consequence",
    )

    # Valid score
    entity_acc = EntityAccuracy(
        entity=test_entity,
        reason="Test reasoning",
        score=0.5,
    )
    assert entity_acc.score == 0.5

    # Test boundary values
    entity_acc_min = EntityAccuracy(
        entity=test_entity,
        reason="Test reasoning",
        score=0.0,
    )
    assert entity_acc_min.score == 0.0

    entity_acc_max = EntityAccuracy(
        entity=test_entity,
        reason="Test reasoning",
        score=1.0,
    )
    assert entity_acc_max.score == 1.0

    # Invalid scores should raise validation error
    with pytest.raises(ValueError):
        _ = EntityAccuracy(
            entity=test_entity,
            reason="Test reasoning",
            score=-0.1,
        )

    with pytest.raises(ValueError):
        _ = EntityAccuracy(
            entity=test_entity,
            reason="Test reasoning",
            score=1.1,
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
    "entity_extraction,llm_answer,expected_answer,expected_entity_count",
    [
        pytest.param(
            EntityExtraction(
                user_query_entities=[
                    Entity(
                        trigger_variable="interest_rate",
                        consequence_variable="borrowing_cost",
                    ),
                ],
                llm_answer_entities=[
                    Entity(
                        trigger_variable="interest_rate",
                        consequence_variable="borrowing_cost",
                    ),
                ],
                expected_answer_entities=[
                    Entity(
                        trigger_variable="interest_rate",
                        consequence_variable="borrowing_cost",
                    ),
                ],
            ),
            (
                "Higher interest rates directly increase borrowing costs "
                "for consumers and businesses."
            ),
            (
                "When interest rates rise, the cost of borrowing money "
                "increases for both individuals and companies."
            ),
            1,
            id="single_matching_entity",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[
                    Entity(
                        trigger_variable="inflation",
                        consequence_variable="purchasing_power",
                    ),
                    Entity(
                        trigger_variable="unemployment",
                        consequence_variable="consumer_spending",
                    ),
                ],
                llm_answer_entities=[
                    Entity(
                        trigger_variable="inflation",
                        consequence_variable="purchasing_power",
                    ),
                    Entity(
                        trigger_variable="unemployment",
                        consequence_variable="economic_activity",
                    ),
                ],
                expected_answer_entities=[
                    Entity(
                        trigger_variable="inflation",
                        consequence_variable="purchasing_power",
                    ),
                    Entity(
                        trigger_variable="unemployment",
                        consequence_variable="consumer_spending",
                    ),
                ],
            ),
            (
                "Rising inflation erodes purchasing power while high "
                "unemployment dampens economic activity."
            ),
            (
                "Inflation reduces purchasing power and unemployment "
                "decreases consumer spending levels."
            ),
            2,
            id="multiple_entities_partial_match",
        ),
    ],
)
async def test_accuracy_evaluation_integration(
    entity_extraction: EntityExtraction,
    llm_answer: str,
    expected_answer: str,
    expected_entity_count: int,
):
    """
    Integration test for accuracy_evaluation with real LLM calls.

    This test validates:
    - The accuracy_evaluation method works end-to-end with real API
    - Entity accuracy scores are calculated correctly
    - Score values are within valid bounds [0.0, 1.0]
    - Reasons are provided for each entity evaluation
    - Mean accuracy is calculated correctly
    """
    # arrange
    from eval.dependencies import qa_eval_engine

    engine = qa_eval_engine()

    # act
    result = await engine.accuracy_evaluation(
        entity_list=entity_extraction,
        llm_answer=llm_answer,
        expected_answer=expected_answer,
    )

    # assert
    assert isinstance(result, AccuracyEvaluationResults)

    # Validate structure
    assert hasattr(result, "entity_accuracies")
    assert hasattr(result, "accuracy_mean")

    # Validate entity accuracies count
    # Note: LLM may evaluate individual variables or entity pairs
    # So we check that we got at least the expected minimum evaluations
    assert len(result.entity_accuracies) == expected_entity_count, (
        f"Expected at least {expected_entity_count} entity evaluations, "
        f"got {len(result.entity_accuracies)}"
    )

    for entity_acc in result.entity_accuracies:
        # Validate structure
        assert isinstance(entity_acc, EntityAccuracy)
        assert isinstance(entity_acc.entity, Entity)
        assert isinstance(entity_acc.reason, str)
        assert isinstance(entity_acc.score, float)

        # Validate score bounds
        assert 0.0 <= entity_acc.score <= 1.0, (
            f"Score {entity_acc.score} out of valid range [0.0, 1.0]"
        )

        # Validate reason is meaningful (minimum 10 chars to ensure it's not
        # just a placeholder like "N/A" or "none" - a proper explanation
        # should contain at least a short sentence)
        assert len(entity_acc.reason) > 10, (
            "Reason should be a meaningful explanation"
        )

    # Validate mean accuracy
    assert isinstance(result.accuracy_mean, float)
    assert 0.0 <= result.accuracy_mean <= 1.0, (
        f"Mean accuracy {result.accuracy_mean} out of valid range"
    )

    # Verify mean is calculated correctly
    if result.entity_accuracies:
        calculated_mean = sum(
            ea.score for ea in result.entity_accuracies
        ) / len(result.entity_accuracies)
        assert math.isclose(
            result.accuracy_mean, calculated_mean, rel_tol=1e-9, abs_tol=1e-9
        ), (
            f"Mean accuracy {result.accuracy_mean} does not match "
            f"calculated mean {calculated_mean}"
        )
