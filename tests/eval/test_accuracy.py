"""
Tests for accuracy metric functionality in QAEvalEngine and metrics.
"""

import math

import pytest
from tests.eval.common import (
    assert_mock_agent_called_correctly,
    mock_engine,  # pyright: ignore[reportUnusedImport] it's a fixture
    parse_entity_string,
    requires_azure,
    sample_entity_extraction_result,
    sample_entity_extraction_with_overlap,
)

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
)

# Minimum length for a meaningful reason explanation
# (a proper explanation should contain at least a short sentence)
MIN_MEANINGFUL_REASON_LENGTH = 10


sample_accuracy_evaluation_results = AccuracyEvaluationResults(
    entity_accuracies=[
        EntityAccuracy(
            entity=Entity(
                trigger_variable="interest_rate",
                consequence_variable="borrowing_cost",
            ),
            reason=(
                "The entity interest_rate->borrowing_cost is accurately "
                "represented in both answers with similar semantic meaning."
            ),
            score=1.0,
        ),
        EntityAccuracy(
            entity=Entity(
                trigger_variable="unemployment",
                consequence_variable="purchasing_power",
            ),
            reason=(
                "The entity unemployment->purchasing_power is partially "
                "represented; LLM mentions economic impact but not "
                "purchasing power specifically."
            ),
            score=0.7,
        ),
    ],
    accuracy_mean=0.85,
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
        pytest.param(
            sample_entity_extraction_with_overlap,
            AccuracyEvaluationResults(
                entity_accuracies=[
                    EntityAccuracy(
                        entity=Entity(
                            trigger_variable="interest_rate",
                            consequence_variable="borrowing_cost",
                        ),
                        reason=(
                            "Exact match between expected and query entities"
                        ),
                        score=1.0,
                    ),
                    EntityAccuracy(
                        entity=Entity(
                            trigger_variable="monetary_policy",
                            consequence_variable="credit_availability",
                        ),
                        reason=(
                            "Related concept with partial semantic overlap"
                        ),
                        score=0.6,
                    ),
                ],
                accuracy_mean=0.8,
            ),
            0.8,
            2,
            [
                "('interest_rate', 'borrowing_cost')",
                "('monetary_policy', 'credit_availability')",
            ],
            id="realistic_overlap_scenario",
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
    """Test QAEvalEngine.accuracy_evaluation with different scenarios.

    Validates:
    - Successful evaluation with multiple entities (successful_evaluation)
    - Empty entity list handling returns zero mean (empty_entity_list)
    - Multiple expected entities with proper comma-separated formatting
      (multiple_expected_entities_formatting)
    - Realistic overlap scenario with semantic similarity
      (realistic_overlap_scenario)
    - Proper prompt formatting with entity lists
    - Mock agent called exactly once with correct parameters
    """

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

    assert isinstance(result, AccuracyEvaluationResults)
    assert len(result.entity_accuracies) == expected_count
    assert result.accuracy_mean == expected_mean

    # Verify the mock agent was called exactly once with:
    # - Correct response_format (AccuracyEvaluationResults)
    # - All input texts (user_query, llm_answer, expected_answer) in the
    #   formatted prompt
    formatted_prompt = assert_mock_agent_called_correctly(
        mock_engine,
        AccuracyEvaluationResults,
        expected_content=[llm_answer, expected_answer],
    )

    # Check that all expected entities appear in the formatted prompt
    # by verifying both trigger and consequence variables are present
    for entity_str in check_entities:
        # Extract trigger and consequence from entity_str format
        # "('{trigger}', '{consequence}')" or '("{trigger}", "{consequence}")'
        if entity_str:
            # Parse the entity string to extract variables
            trigger, consequence = parse_entity_string(entity_str)
            # Verify both components appear in prompt
            # (allows for format variations)
            assert (
                trigger in formatted_prompt and consequence in formatted_prompt
            ), (
                f"Entity components '{trigger}' and "
                f"'{consequence}' not found in prompt"
            )

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
    """Test the calculate_accuracy_mean method with different configurations.

    Validates:
    - Correct mean calculation with multiple entities (with_entities)
    - Empty entity list returns 0.0 mean (empty_list)
    - Floating-point precision in calculations using math.isclose
    - Mean is sum of scores divided by count
    """
    results = AccuracyEvaluationResults(
        entity_accuracies=entity_accuracies,
        # accuracy_mean will be recalculated with "calculate_accuracy_mean"
        accuracy_mean=0.0,
    )

    calculated_mean = results.calculate_accuracy_mean()

    # Use math.isclose for floating point comparison with proper type checking
    assert math.isclose(
        calculated_mean, expected_mean, rel_tol=1e-9, abs_tol=1e-9
    )


@pytest.mark.integration
@pytest.mark.asyncio
@requires_azure
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

    def _validate_accuracy_results(
        result: AccuracyEvaluationResults, min_length: int = 10
    ) -> None:
        """Validate AccuracyEvaluationResults structure and constraints.

        Args:
            result: The accuracy evaluation results to validate.
            min_length: Minimum length for reason explanations.

        Raises:
            AssertionError: If results structure is invalid or values are out
            of bounds.
        """

        _ = AccuracyEvaluationResults.model_validate(result)

        # Validate mean accuracy bounds
        assert 0.0 <= result.accuracy_mean <= 1.0, (
            f"Mean accuracy {result.accuracy_mean} "
            f"out of valid range [0.0, 1.0]"
        )

        # Validate each entity accuracy
        for entity_acc in result.entity_accuracies:
            # Validate score bounds
            assert 0.0 <= entity_acc.score <= 1.0, (
                f"Score {entity_acc.score} out of valid range [0.0, 1.0]"
            )

            # Validate reason is meaningful
            assert len(entity_acc.reason) > min_length, (
                "Reason should be a meaningful explanation"
            )

    # assert
    # Validate structure and constraints using helper function
    _validate_accuracy_results(result, min_length=MIN_MEANINGFUL_REASON_LENGTH)

    # Validate entity accuracies count
    # We expect exactly the expected number of entity evaluations
    assert len(result.entity_accuracies) == expected_entity_count, (
        f"Expected exactly {expected_entity_count} entity evaluations, "
        f"got {len(result.entity_accuracies)}"
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
