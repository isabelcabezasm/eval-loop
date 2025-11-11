"""
Tests for topic coverage metric functionality in QAEvalEngine and metrics.
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
    Entity,
    EntityExtraction,
    TopicCoverageEvaluationResults,
)

# Minimum length for a meaningful reason explanation
MIN_MEANINGFUL_REASON_LENGTH = 10

sample_topic_coverage_results = TopicCoverageEvaluationResults(
    reason=(
        "The generated answer covers 1 out of 2 expected topics. "
        "The topic ('exercise', 'health') is well represented through "
        "('physical_activity', 'wellness') which are semantically equivalent. "
        "However, the topic ('smoking', 'mortality') is missing from the "
        "generated entities, though 'lung_disease' is mentioned instead of "
        "'mortality'."
    ),
    coverage_score=0.5,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entity_extraction,mock_engine,expected_score,expected_entity_count,check_entities",
    [
        pytest.param(
            sample_entity_extraction_result,
            sample_topic_coverage_results,
            0.5,
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
            TopicCoverageEvaluationResults(
                reason="No expected entities to evaluate coverage for.",
                coverage_score=1.0,
            ),
            1.0,
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
            TopicCoverageEvaluationResults(
                reason=(
                    "Generated answer covers 2 out of 3 expected topics. "
                    "Strong overlap with interest rates and inflation, "
                    "but missing monetary policy discussion."
                ),
                coverage_score=0.67,
            ),
            0.67,
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
            TopicCoverageEvaluationResults(
                reason=(
                    "Expected entities partially covered in generated "
                    "answer. The interest_rate->borrowing_cost relationship "
                    "is present with semantic similarity (loan_cost vs "
                    "borrowing_cost)."
                ),
                coverage_score=0.5,
            ),
            0.5,
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
async def test_topic_coverage_evaluation_scenarios(
    entity_extraction: EntityExtraction,
    mock_engine: QAEvalEngine,
    expected_score: float,
    expected_entity_count: int,
    check_entities: list[str],
):
    """Test QAEvalEngine.topic_coverage_evaluation with different scenarios.

    Validates:
    - Successful evaluation with multiple entities (successful_evaluation)
    - Empty entity list handling returns score of 1.0 (empty_entity_list)
    - Multiple expected entities with proper comma-separated formatting
      (multiple_expected_entities_formatting)
    - Realistic overlap scenario with semantic similarity
      (realistic_overlap_scenario)
    - Proper prompt formatting with entity lists
    - Mock agent called exactly once with correct parameters
    """

    result = await mock_engine.topic_coverage_evaluation(
        entity_list=entity_extraction
    )

    assert isinstance(result, TopicCoverageEvaluationResults)
    assert math.isclose(
        result.coverage_score, expected_score, rel_tol=1e-2, abs_tol=1e-2
    )

    # Verify the mock agent was called exactly once with:
    # - Correct response_format (EntityExtraction)
    # - All input texts (user_query, llm_answer, expected_answer) in the
    #   formatted prompt
    formatted_prompt = assert_mock_agent_called_correctly(
        mock_engine,
        TopicCoverageEvaluationResults,
    )

    # Check that all expected entities appear in the formatted prompt
    for entity_str in check_entities:
        if entity_str:
            # Parse the entity string to extract variables
            trigger, consequence = parse_entity_string(entity_str)
            # Verify both components appear in prompt
            assert (
                trigger in formatted_prompt and consequence in formatted_prompt
            ), (
                f"Entity components '{trigger}' and "
                f"'{consequence}' not found in prompt"
            )

    # For multiple entity scenarios, verify all entities are present
    if len(check_entities) > 1:
        # Verify all entities are properly formatted in the prompt
        for entity_str in check_entities:
            assert entity_str in formatted_prompt, (
                f"Entity {entity_str} not found in formatted prompt. "
                f"All entities should be present for evaluation."
            )


@pytest.mark.integration
@pytest.mark.asyncio
@requires_azure
@pytest.mark.parametrize(
    "entity_extraction,expected_entity_count",
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
            2,
            id="multiple_entities_partial_match",
        ),
        pytest.param(
            EntityExtraction(
                user_query_entities=[],
                llm_answer_entities=[],
                expected_answer_entities=[],
            ),
            0,
            id="empty_entity_lists",
        ),
    ],
)
async def test_topic_coverage_evaluation_integration(
    entity_extraction: EntityExtraction,
    expected_entity_count: int,
):
    """
    Integration test for topic_coverage_evaluation with real LLM calls.

    This test validates:
    - The topic_coverage_evaluation method works end-to-end with real API
    - Coverage scores are calculated correctly
    - Score values are within valid bounds [0.0, 1.0]
    - Reasons are provided for coverage evaluation
    - Structure matches expected TopicCoverageEvaluationResults
    - Empty entity lists are handled gracefully (returns score 1.0)
    """
    # arrange
    from eval.dependencies import qa_eval_engine

    engine = qa_eval_engine()

    # act
    result = await engine.topic_coverage_evaluation(
        entity_list=entity_extraction
    )

    # assert

    # result: The topic coverage evaluation results to validate.
    _ = TopicCoverageEvaluationResults.model_validate(result)

    # Validate reason is meaningful
    assert isinstance(result.reason, str)
    # assume meaningful if longer than x characters
    assert len(result.reason) > MIN_MEANINGFUL_REASON_LENGTH, (
        "Reason should be a meaningful explanation"
    )

    # Verify coverage score is calculated correctly
    # (within valid bounds and is a reasonable value)
    assert 0.0 <= result.coverage_score <= 1.0, (
        f"Coverage score {result.coverage_score} out of valid range [0.0, 1.0]"
    )

    # For empty entity lists, expect perfect coverage (1.0)
    if expected_entity_count == 0:
        if result.coverage_score != 1.0:
            # if it's going to fail, get the reason for debugging
            print(result.reason)
        assert result.coverage_score == 1.0, (
            "Empty expected entities should return perfect coverage (1.0)"
        )
