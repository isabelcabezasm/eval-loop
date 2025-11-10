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


@pytest.fixture
def sample_entity_extraction():
    """Create a sample EntityExtraction object for testing."""
    return sample_entity_extraction_result


@pytest.fixture
def mock_engine(request: pytest.FixtureRequest) -> QAEvalEngine:
    """Create a mock QAEvalEngine with configurable expected result.

    Use with indirect parametrization to pass the expected_result.
    """
    expected_result: AccuracyEvaluationResults = request.param
    mock_agent = AsyncMock(spec=ChatAgent)
    mock_response = Mock(spec=AgentRunResponse)
    mock_response.value = expected_result
    mock_agent.run.return_value = mock_response
    engine: QAEvalEngine = QAEvalEngine(agent=mock_agent)
    # Store mock agent for test assertions
    engine._agent = mock_agent  # type: ignore[attr-defined]
    return engine
