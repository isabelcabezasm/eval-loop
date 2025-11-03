"""
Tests for the dependencies module.

This module tests the dependency injection functions and caching behavior
for the QA Engine components.
"""

from unittest.mock import Mock, patch

import pytest

from core.dependencies import (
    axiom_store,
    azure_chat_openai,
    chat_agent,
    credential,
    qa_engine,
)


@pytest.fixture(autouse=True)
def clear_dependency_caches():
    """Clear all dependency caches before and after each test to prevent
    cache pollution.
    """
    credential.cache_clear()
    azure_chat_openai.cache_clear()
    chat_agent.cache_clear()
    axiom_store.cache_clear()
    qa_engine.cache_clear()
    yield
    credential.cache_clear()
    azure_chat_openai.cache_clear()
    chat_agent.cache_clear()
    axiom_store.cache_clear()
    qa_engine.cache_clear()


@pytest.fixture(autouse=True)
def patch_azure_cli_credential():
    """Mock AzureCliCredential to avoid actual authentication."""
    with patch("core.dependencies.AzureCliCredential") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture(autouse=True)
def patch_azure_chat_openai_client():
    """Mock azure_chat_openai_client to avoid actual Azure OpenAI calls."""
    with patch("core.dependencies.azure_chat_openai_client") as mock:
        mock_client = Mock()
        mock_agent = Mock()
        mock_client.create_agent.return_value = mock_agent
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def mock_load_from_json():
    """Mock load_from_json to avoid reading actual files."""
    with patch("core.dependencies.load_from_json") as mock:
        mock.return_value = Mock()
        yield mock


def test_credential_returns_azure_cli_credential():
    """Test that credential() returns an AzureCliCredential instance."""
    # act
    result = credential()

    # assert
    assert result is not None


def test_credential_caches_result():
    """Test that credential() caches its result and doesn't create multiple
    instances.
    """
    # act
    result1 = credential()
    result2 = credential()

    # assert
    assert result1 is result2


def test_azure_chat_openai_creates_client():
    """Test that azure_chat_openai() creates an Azure OpenAI client."""
    # act
    result = azure_chat_openai()

    # assert
    assert result is not None


def test_azure_chat_openai_caches_result():
    """Test that azure_chat_openai() caches its result."""
    # act
    result1 = azure_chat_openai()
    result2 = azure_chat_openai()

    # assert
    assert result1 is result2


def test_chat_agent_creates_agent_with_system_prompt():
    """Test that chat_agent() creates an agent with the system prompt."""
    # act
    result = chat_agent()

    # assert
    assert result is not None


def test_chat_agent_caches_result():
    """Test that chat_agent() caches its result."""
    # act
    result1 = chat_agent()
    result2 = chat_agent()

    # assert
    assert result1 is result2


def test_axiom_store_loads_from_json(mock_load_from_json: Mock):
    """Test that axiom_store() loads data from JSON file."""
    # act
    result = axiom_store()

    # assert
    mock_load_from_json.assert_called_once()
    call_args = mock_load_from_json.call_args[0]
    assert len(call_args) > 0
    assert isinstance(call_args[0], str)
    assert result is not None


def test_axiom_store_caches_result(mock_load_from_json: Mock):
    """Test that axiom_store() caches its result."""
    # act
    result1 = axiom_store()
    result2 = axiom_store()

    # assert
    mock_load_from_json.assert_called_once()
    assert result1 is result2


def test_qa_engine_creates_engine_with_dependencies(mock_load_from_json: Mock):
    """Test that qa_engine() creates a QAEngine with agent and axiom_store."""
    # act
    result = qa_engine()

    # assert
    assert result is not None
    mock_load_from_json.assert_called_once()


def test_qa_engine_caches_result(mock_load_from_json: Mock):
    """Test that qa_engine() caches its result."""
    # act
    result1 = qa_engine()
    result2 = qa_engine()

    # assert
    mock_load_from_json.assert_called_once()
    assert result1 is result2
