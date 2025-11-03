from unittest.mock import AsyncMock

import pytest
from agent_framework import ChatAgent


@pytest.fixture
def mock_chat_agent():
    """Create a mock chat agent."""
    mock_agent = AsyncMock(spec=ChatAgent)
    return mock_agent
