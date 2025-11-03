"""
Tests for entity extraction functionality in QAEvalEngine and metrics.
"""

from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest
from agent_framework import AgentRunResponse, ChatAgent
from tests.eval.common import mock_chat_agent, sample_entity_extraction

from eval.llm_evaluator.qa_eval_engine import QAEvalEngine
from eval.metrics.extract_entities import get_entities
from eval.metrics.models import Entity, EntityExtraction


@pytest.fixture
def mock_azure_chat_client():
    """Create a mock Azure OpenAI chat client."""
    mock_client = Mock(spec=ChatAgent)
    return mock_client


@pytest.fixture
def sample_prompts():
    """Create sample prompt content for testing."""
    return {
        "system": "You are a senior actuary that analyze premium rates.",
        "entity_extraction": """Extract all entities from the following sentences.
        
User query: {user_query}
LLM answer: {llm_answer}
Expected answer: {expected_answer}
""",
    }


@pytest.mark.asyncio
async def test_qa_eval_engine_entity_extraction(
    mock_chat_agent, sample_entity_extraction, sample_prompts
):
    """Test entity_extraction method."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    # Mock the helper methods
    with patch.object(
        engine, "_get_prompt", return_value=sample_prompts["entity_extraction"]
    ) as mock_get_prompt:
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=sample_entity_extraction,
        ) as mock_invoke:
            result = await engine.entity_extraction(
                user_query="What are the health benefits of exercise?",
                llm_answer=(
                    "Exercise improves cardiovascular health and reduces mortality."
                ),
                expected_answer=(
                    "Regular physical activity enhances overall health and longevity."
                ),
            )

    assert result == sample_entity_extraction
    mock_get_prompt.assert_called_once_with("entity_extraction")
    mock_invoke.assert_called_once()

    # Check that the prompt was formatted correctly
    prompt = mock_invoke.call_args[0][0]
    assert "What are the health benefits of exercise?" in prompt
    assert "Exercise improves cardiovascular health and reduces mortality." in prompt
    assert "Regular physical activity enhances overall health and longevity." in prompt


@pytest.mark.asyncio
async def test_qa_eval_engine_entity_extraction_prompt_formatting(
    mock_chat_agent, sample_entity_extraction
):
    """Test that entity_extraction properly formats the prompt."""
    engine = QAEvalEngine(agent=mock_chat_agent)

    prompt_template = (
        "User: {user_query}\nLLM: {llm_answer}\nExpected: {expected_answer}"
    )

    with patch.object(engine, "_get_prompt", return_value=prompt_template):
        with patch.object(
            engine,
            "_perform_model_invocation",
            return_value=sample_entity_extraction,
        ) as mock_invoke:
            await engine.entity_extraction(
                user_query="test query",
                llm_answer="test llm answer",
                expected_answer="test expected answer",
            )

    # Verify the formatted prompt
    expected_prompt = (
        "User: test query\nLLM: test llm answer\nExpected: test expected answer"
    )
    mock_invoke.assert_called_once_with(expected_prompt, EntityExtraction)


@pytest.mark.asyncio
async def test_qa_eval_engine_entity_extraction_integration(
    sample_entity_extraction,  # pyright: ignore[reportRedefinedWhileInScope]
):
    """Test entity_extraction with realistic mock responses."""
    # Create more realistic mock
    mock_agent = AsyncMock(spec=ChatAgent)
    mock_response = Mock(spec=AgentRunResponse)
    mock_response.value = sample_entity_extraction
    mock_agent.run.return_value = mock_response

    engine = QAEvalEngine(agent=mock_agent)

    # Mock file reading for prompts
    with patch(
        "builtins.open",
        mock_open(
            read_data=(
                "mocked prompt content {user_query} {llm_answer} {expected_answer}"
            )
        ),
    ):
        with patch("eval.llm_evaluator.qa_eval_engine.Path"):
            result = await engine.entity_extraction(
                user_query="Does smoking affect health?",
                llm_answer="Smoking significantly increases health risks.",
                expected_answer="Tobacco use is linked to various health problems.",
            )

    assert result == sample_entity_extraction
    assert len(result.user_query_entities) == 2
    assert len(result.llm_answer_entities) == 2
    assert len(result.expected_answer_entities) == 2


@pytest.mark.asyncio
async def test_qa_eval_engine_entity_extraction_error_handling():
    """Test entity_extraction error handling."""
    mock_agent = AsyncMock(spec=ChatAgent)
    engine = QAEvalEngine(agent=mock_agent)

    # Mock an exception in _perform_model_invocation
    with patch.object(engine, "_get_prompt", return_value="prompt"):
        with patch.object(
            engine, "_perform_model_invocation", side_effect=Exception("API Error")
        ):
            with pytest.raises(Exception, match="API Error"):
                await engine.entity_extraction("query", "answer", "expected")


@pytest.mark.asyncio
@patch("eval.metrics.extract_entities.qa_eval_engine")
async def test_get_entities(mock_qa_eval_engine, sample_entity_extraction):
    """Test get_entities function."""
    # Setup mocks
    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.entity_extraction.return_value = sample_entity_extraction
    mock_qa_eval_engine.return_value = mock_engine

    result = await get_entities(
        user_prompt="What causes heart disease?",
        llm_answer="Poor diet and lack of exercise cause heart disease.",
        expected_answer="Cardiovascular disease is linked to lifestyle factors.",
    )

    assert result == sample_entity_extraction
    mock_qa_eval_engine.assert_called_once()
    mock_engine.entity_extraction.assert_called_once_with(
        "What causes heart disease?",
        "Poor diet and lack of exercise cause heart disease.",
        "Cardiovascular disease is linked to lifestyle factors.",
    )


@pytest.mark.asyncio
@patch("eval.metrics.extract_entities.qa_eval_engine")
async def test_get_entities_with_empty_strings(mock_qa_eval_engine):
    """Test get_entities function with empty string inputs."""
    # Setup mocks
    empty_extraction = EntityExtraction(
        user_query_entities=[], llm_answer_entities=[], expected_answer_entities=[]
    )

    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.entity_extraction.return_value = empty_extraction
    mock_qa_eval_engine.return_value = mock_engine

    result = await get_entities(user_prompt="", llm_answer="", expected_answer="")

    assert result == empty_extraction
    assert len(result.user_query_entities) == 0
    assert len(result.llm_answer_entities) == 0
    assert len(result.expected_answer_entities) == 0


@pytest.mark.asyncio
@patch("eval.metrics.extract_entities.qa_eval_engine")
async def test_get_entities_error_propagation(mock_qa_eval_engine):
    """Test that get_entities properly propagates errors from QAEvalEngine."""
    # Setup mocks
    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.entity_extraction.side_effect = Exception("Model API failed")
    mock_qa_eval_engine.return_value = mock_engine

    with pytest.raises(Exception, match="Model API failed"):
        await get_entities(
            user_prompt="test", llm_answer="test", expected_answer="test"
        )


@pytest.mark.asyncio
@patch("eval.metrics.extract_entities.qa_eval_engine")
async def test_get_entities_keyword_arguments(
    mock_qa_eval_engine, sample_entity_extraction
):
    """Test that get_entities uses keyword-only arguments correctly."""
    # Setup mocks
    mock_engine = AsyncMock(spec=QAEvalEngine)
    mock_engine.entity_extraction.return_value = sample_entity_extraction
    mock_qa_eval_engine.return_value = mock_engine

    # Test that keyword arguments are required
    result = await get_entities(
        user_prompt="test prompt",
        llm_answer="test answer",
        expected_answer="test expected",
    )

    assert result == sample_entity_extraction
    mock_engine.entity_extraction.assert_called_once_with(
        "test prompt", "test answer", "test expected"
    )


@pytest.mark.asyncio
async def test_full_entity_extraction_workflow(sample_entity_extraction):
    """Test the complete entity extraction workflow without external API calls."""
    # Mock all external dependencies
    with patch("eval.metrics.extract_entities.qa_eval_engine") as mock_qa_eval_engine:
        mock_engine = AsyncMock()
        mock_engine.entity_extraction.return_value = sample_entity_extraction
        mock_qa_eval_engine.return_value = mock_engine

        # Test the workflow
        result = await get_entities(
            user_prompt="How does age affect insurance premiums?",
            llm_answer=(
                "Older individuals typically pay higher premiums "
                "due to increased health risks."
            ),
            expected_answer=(
                "Age is a significant factor in premium calculation "
                "due to actuarial data."
            ),
        )

        # Verify the result
        assert isinstance(result, EntityExtraction)
        assert len(result.user_query_entities) == 2
        assert len(result.llm_answer_entities) == 2
        assert len(result.expected_answer_entities) == 2

        # Verify the workflow was called correctly
        mock_qa_eval_engine.assert_called_once()
        mock_engine.entity_extraction.assert_called_once()
