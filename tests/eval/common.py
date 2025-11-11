import os
import re
from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentRunResponse, ChatAgent

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityAccuracy,
    EntityExtraction,
    TopicCoverageEvaluationResults,
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
def mock_engine(request: pytest.FixtureRequest) -> QAEvalEngine:
    """Create a mock QAEvalEngine with configurable expected result.

    Use with indirect parametrization to pass the expected_result.
    Can accept AccuracyEvaluationResults, EntityExtraction, or
    TopicCoverageEvaluationResults.

    Raises:
        TypeError: If expected_result is not one of the supported types.
    """
    expected_result = request.param

    # Runtime type validation
    valid_types = (
        AccuracyEvaluationResults,
        EntityExtraction,
        TopicCoverageEvaluationResults,
    )
    if not isinstance(expected_result, valid_types):
        msg = (
            f"mock_engine fixture requires one of {valid_types}, "
            f"got {type(expected_result)}"
        )
        raise TypeError(msg)

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


@pytest.fixture
def sample_topic_coverage():
    """Create a sample TopicCoverageEvaluationResults for testing."""
    return sample_topic_coverage_results


def validate_topic_coverage_results(
    result: TopicCoverageEvaluationResults, min_length: int = 10
) -> None:
    """Validate TopicCoverageEvaluationResults structure and constraints.

    Args:
        result: The topic coverage evaluation results to validate.
        min_length: Minimum length for reason explanations.

    Raises:
        AssertionError: If results structure is invalid or values are out of
            bounds.
    """
    assert isinstance(result, TopicCoverageEvaluationResults)
    assert hasattr(result, "reason")
    assert hasattr(result, "coverage_score")

    # Validate coverage score bounds
    assert isinstance(result.coverage_score, float)
    assert 0.0 <= result.coverage_score <= 1.0, (
        f"Coverage score {result.coverage_score} out of valid range [0.0, 1.0]"
    )

    # Validate reason is meaningful
    assert isinstance(result.reason, str)
    assert len(result.reason) > min_length, (
        "Reason should be a meaningful explanation"
    )


def validate_accuracy_results(
    result: AccuracyEvaluationResults, min_length: int = 10
) -> None:
    """Validate AccuracyEvaluationResults structure and constraints.

    Args:
        result: The accuracy evaluation results to validate.
        min_length: Minimum length for reason explanations.

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
        assert len(entity_acc.reason) > min_length, (
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


def parse_entity_string(entity_str: str) -> tuple[str, str]:
    """Parse entity string into trigger and consequence components.

    Parses entity strings in format "('trigger', 'consequence')" or
    '("trigger", "consequence")' into their component parts using regex.

    Args:
        entity_str: Entity string in format "('trigger', 'consequence')".

    Returns:
        Tuple of (trigger_variable, consequence_variable).

    Raises:
        ValueError: If entity string format is invalid.

    Example:
        >>> trigger, consequence = parse_entity_string(
        ...     "('interest_rate', 'borrowing_cost')"
        ... )
        >>> assert trigger == "interest_rate"
        >>> assert consequence == "borrowing_cost"
    """
    # Match parenthesized pair with matching quotes using backreferences
    # Group 1: opening quote for trigger, Group 2: trigger value
    # Group 3: opening quote for consequence, Group 4: consequence value
    pattern = r"\(\s*(['\"])([^'\"]+)\1\s*,\s*(['\"])([^'\"]+)\3\s*\)"
    match = re.match(pattern, entity_str)

    if not match:
        msg = (
            f"Expected entity format '(trigger, consequence)', "
            f"got: {entity_str}"
        )
        raise ValueError(msg)

    return match.group(2), match.group(4)


def assert_mock_agent_called_correctly(
    engine: QAEvalEngine,
    expected_response_type: type,
    expected_content: list[str] | None = None,
) -> str:
    """Verify mock agent was called correctly and return formatted prompt.

    This helper reduces duplication in tests that verify mock agent calls.
    It checks that the agent's run method was called exactly once with the
    correct response format and optionally verifies expected content in the
    prompt.

    Args:
        engine: The mock QAEvalEngine to verify.
        expected_response_type: Expected response format type (e.g.,
            AccuracyEvaluationResults, EntityExtraction).
        expected_content: Optional list of strings that should appear in the
            formatted prompt.

    Returns:
        The formatted prompt string that was passed to the agent.

    Raises:
        AssertionError: If agent wasn't called correctly or expected content
            is missing from the prompt.

    Example:
        >>> prompt = assert_mock_agent_called_correctly(
        ...     mock_engine,
        ...     AccuracyEvaluationResults,
        ...     expected_content=[llm_answer, expected_answer]
        ... )
        >>> # Now use prompt for additional assertions if needed
    """
    mock_agent = engine.agent
    mock_agent.run.assert_called_once()  # type: ignore[attr-defined]

    call_args = mock_agent.run.call_args  # type: ignore[attr-defined]
    formatted_prompt: str = call_args[0][0]  # type: ignore[index, assignment]

    # Ensure we have a string (should always be true for our usage)
    assert isinstance(formatted_prompt, str), "Expected prompt to be string"

    # Verify response format
    actual_response_format = call_args[1].get("response_format")  # type: ignore[index, call-arg]
    assert actual_response_format == expected_response_type, (
        f"Expected response_format={expected_response_type.__name__}, "
        f"got {actual_response_format}"
    )

    # Verify expected content appears in prompt
    if expected_content:
        for content in expected_content:
            # Truncate long content for better error messages
            content_preview = (
                content[:50] + "..." if len(content) > 50 else content
            )
            assert content in formatted_prompt, (
                f"Expected content '{content_preview}' not found in prompt"
            )

    return formatted_prompt
