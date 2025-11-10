import os
from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentRunResponse, ChatAgent

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
)

# Environment variable names for Azure OpenAI integration tests
AZURE_ENDPOINT_VAR = "AZURE_OPENAI_ENDPOINT"
AZURE_DEPLOYMENT_VAR = "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"

# Composite marker for Azure integration tests
requires_azure = pytest.mark.skipif(
    not (os.getenv(AZURE_ENDPOINT_VAR) and os.getenv(AZURE_DEPLOYMENT_VAR)),
    reason=(
        f"Requires {AZURE_ENDPOINT_VAR} and {AZURE_DEPLOYMENT_VAR} "
        "environment variables"
    ),
)

sample_entity_extraction_result = EntityExtraction(
    user_query_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
        Entity(
            trigger_variable="inflation",
            consequence_variable="purchasing_power",
        ),
    ],
    llm_answer_entities=[
        Entity(
            trigger_variable="monetary_policy",
            consequence_variable="investment_decisions",
        ),
        Entity(
            trigger_variable="unemployment",
            consequence_variable="consumer_spending",
        ),
    ],
    expected_answer_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
        Entity(
            trigger_variable="unemployment",
            consequence_variable="purchasing_power",
        ),
    ],
)

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

# More realistic sample with overlap between entities across different sources
# This simulates a real scenario where the user asks about interest rates,
# the LLM provides a related answer with some semantic overlap, and the
# expected answer shares core concepts
sample_entity_extraction_with_overlap = EntityExtraction(
    user_query_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
    ],
    llm_answer_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="loan_cost",
        ),
        Entity(
            trigger_variable="central_bank_policy",
            consequence_variable="lending_rates",
        ),
    ],
    expected_answer_entities=[
        Entity(
            trigger_variable="interest_rate",
            consequence_variable="borrowing_cost",
        ),
        Entity(
            trigger_variable="monetary_policy",
            consequence_variable="credit_availability",
        ),
    ],
)


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


@pytest.fixture
def mock_engine(request: pytest.FixtureRequest) -> QAEvalEngine:
    """Create a mock QAEvalEngine with configurable expected result.

    Use with indirect parametrization to pass the expected_result.
    Can accept AccuracyEvaluationResults or EntityExtraction.
    """
    expected_result: AccuracyEvaluationResults | EntityExtraction = (
        request.param
    )
    mock_agent = AsyncMock(spec=ChatAgent)
    mock_response = Mock(spec=AgentRunResponse)
    mock_response.value = expected_result
    mock_agent.run.return_value = mock_response
    engine: QAEvalEngine = QAEvalEngine(agent=mock_agent)
    return engine


# Helper functions for common validation patterns in integration tests


def validate_entity_structure(entity: Entity, min_length: int = 2) -> None:
    """Validate that an entity has proper structure and non-empty variables.

    Args:
        entity: The entity to validate.
        min_length: Minimum length for trigger and consequence variables.

    Raises:
        AssertionError: If entity structure is invalid or variables are too
            short.
    """
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

    # Validate that variables are meaningful (meet minimum length)
    assert len(entity.trigger_variable) >= min_length, (
        f"Trigger variable '{entity.trigger_variable}' too short"
    )
    assert len(entity.consequence_variable) >= min_length, (
        f"Consequence variable '{entity.consequence_variable}' too short"
    )


def validate_accuracy_results(
    result: AccuracyEvaluationResults, min_reason_length: int = 10
) -> None:
    """Validate AccuracyEvaluationResults structure and constraints.

    Args:
        result: The accuracy evaluation results to validate.
        min_reason_length: Minimum length for reason explanations.

    Raises:
        AssertionError: If results structure is invalid or values are out of
            bounds.
    """
    assert isinstance(result, AccuracyEvaluationResults)
    assert hasattr(result, "entity_accuracies")
    assert hasattr(result, "accuracy_mean")

    # Validate mean accuracy bounds
    assert isinstance(result.accuracy_mean, float)
    assert 0.0 <= result.accuracy_mean <= 1.0, (
        f"Mean accuracy {result.accuracy_mean} out of valid range [0.0, 1.0]"
    )

    # Validate each entity accuracy
    for entity_acc in result.entity_accuracies:
        assert isinstance(entity_acc, EntityAccuracy)
        assert isinstance(entity_acc.entity, Entity)
        assert isinstance(entity_acc.reason, str)
        assert isinstance(entity_acc.score, float)

        # Validate score bounds
        assert 0.0 <= entity_acc.score <= 1.0, (
            f"Score {entity_acc.score} out of valid range [0.0, 1.0]"
        )

        # Validate reason is meaningful
        assert len(entity_acc.reason) > min_reason_length, (
            "Reason should be a meaningful explanation"
        )


def validate_entity_extraction_structure(
    result: EntityExtraction,
) -> None:
    """Validate EntityExtraction structure.

    Args:
        result: The entity extraction results to validate.

    Raises:
        AssertionError: If structure is invalid.
    """
    assert isinstance(result, EntityExtraction)
    assert hasattr(result, "user_query_entities")
    assert hasattr(result, "llm_answer_entities")
    assert hasattr(result, "expected_answer_entities")

    # Validate that entities were extracted
    assert isinstance(result.user_query_entities, list)
    assert isinstance(result.llm_answer_entities, list)
    assert isinstance(result.expected_answer_entities, list)
