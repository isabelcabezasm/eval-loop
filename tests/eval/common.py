from unittest.mock import AsyncMock

import pytest
from agent_framework import ChatAgent

from eval.metrics.models import Entity, EntityExtraction


@pytest.fixture
def mock_chat_agent():
    """Create a mock chat agent."""
    mock_agent = AsyncMock(spec=ChatAgent)
    return mock_agent


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
