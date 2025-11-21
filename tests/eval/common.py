import os
import re
from unittest.mock import AsyncMock, Mock

import pytest
from agent_framework import AgentRunResponse, ChatAgent

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.models import (
    AccuracyEvaluationResults,
    Entity,
    EntityExtraction,
    TopicCoverageEvaluationResults,
)

# Environment variable names for Azure OpenAI integration tests
AZURE_ENDPOINT_VAR = "AZURE_OPENAI_ENDPOINT"
AZURE_DEPLOYMENT_VAR = "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"

# Minimum length for a meaningful reason explanation
# (a proper explanation should contain at least a short sentence)
MIN_MEANINGFUL_REASON_LENGTH = 10

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
    # Match parenthesized pair with matching quotes using backreferences.
    # Group 1: opening quote for trigger (single or double quote)
    # Group 2: trigger value (the string inside the quotes)
    # The backreference \1 ensures that the closing quote for the trigger
    # matches its opening quote (group 1).
    # Group 3: consequence value (the string inside the quotes)
    # The backreference \1 ensures all quotes are the same type.
    # Matches ("trigger", "consequence") or ('trigger', 'consequence').

    pattern = r"\(\s*(['\"])([^'\"]+)\1\s*,\s*\1([^'\"]+)\1\s*\)"

    match = re.match(pattern, entity_str)

    if not match:
        msg = (
            f"Expected entity format '(trigger, consequence)', "
            f"got: {entity_str}"
        )
        raise ValueError(msg)

    return match.group(2), match.group(3)


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
