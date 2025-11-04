"""
Tests for the QA Engine module.

This module tests the QAEngine class and its interaction with the
Microsoft Agent Framework, including message streaming, citation handling,
and prompt formatting.
"""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from typing import TypeVar
from unittest.mock import MagicMock

import pytest
from agent_framework import ChatAgent

from core.axiom_store import Axiom, AxiomId, AxiomStore
from core.qa_engine import (
    CitationCandidate,
    CitationContent,
    Message,
    QAEngine,
    TextContent,
    process_chunk,
)

T = TypeVar("T")


async def async_iter(iterable: Iterable[T]) -> AsyncIterator[T]:
    """Convert an iterable to an async iterator for testing."""
    for element in iterable:
        yield element


class MockStreamChunk:
    """Mock class for agent stream chunks."""

    def __init__(self, text: str):
        self.text = text


@pytest.mark.asyncio
async def test_invoke_stream_calls_agent_correctly():
    """Test that invoke_streaming correctly calls the agent's run_stream method."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return chunks
    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Hello")
        yield MockStreamChunk(", ")
        yield MockStreamChunk("world")
        yield MockStreamChunk("!")

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("AXIOM-001"),
                subject="subject",
                entity="entity",
                trigger="trigger",
                conditions="conditions",
                description="description",
                category="category",
            )
        ]
    )

    subject = QAEngine(mock_agent, axiom_store)

    # Act
    result = []
    async for chunk in subject.invoke_streaming("Test question"):
        result.append(chunk)

    # Assert
    # Verify that we got the expected content
    # Note: Each chunk from the mock agent becomes a separate TextContent
    assert len(result) == 4
    assert all(isinstance(chunk, TextContent) for chunk in result)
    # Verify the concatenated content
    full_text = "".join(chunk.content for chunk in result)
    assert full_text == "Hello, world!"


async def act_invoke_stream(qa_engine: QAEngine) -> str:
    """Helper to collect all text from streaming invoke."""
    result = ""
    async for chunk in qa_engine.invoke_streaming(question="Test question"):
        if isinstance(chunk, TextContent):
            result += chunk.content
        elif isinstance(chunk, CitationContent):
            result += chunk.content
    return result


async def act_invoke(qa_engine: QAEngine) -> str:
    """Helper to test non-streaming invoke."""
    return await qa_engine.invoke(question="Test question")


@pytest.mark.parametrize(
    "act",
    [
        pytest.param(act_invoke_stream, id="invoke_stream"),
        pytest.param(act_invoke, id="invoke"),
    ],
)
@pytest.mark.asyncio
async def test_invoke_returns_correct_message(
    act: Callable[[QAEngine], Awaitable[str]],
):
    """Test that both streaming and non-streaming invoke return the correct message."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return chunks that form "Hello, world!"
    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        for content in ["Hello", ", ", "world", "!"]:
            yield MockStreamChunk(content)

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    result = await act(qa_engine)

    # Assert
    assert result == "Hello, world!"


@pytest.mark.asyncio
async def test_formatted_prompt_includes_constitution():
    """Test that the engine uses constitution data when processing queries."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Track the prompt that was passed to the agent
    captured_prompt = None

    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        nonlocal captured_prompt
        captured_prompt = _prompt
        yield MockStreamChunk("Test response")

    mock_agent.run_stream = mock_run_stream

    axioms = [
        Axiom(
            id=AxiomId("AXIOM-001"),
            subject="Test Subject",
            entity="Test Entity",
            trigger="Test Trigger",
            conditions="Test Conditions",
            description="Test Description",
            category="Test Category",
        )
    ]

    axiom_store = AxiomStore(axioms)
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    async for _ in qa_engine.invoke_streaming("Test question?"):
        pass

    # Assert that the prompt includes constitution data
    assert captured_prompt is not None
    assert "AXIOM-001" in captured_prompt
    assert "Test Subject" in captured_prompt
    assert "Test Entity" in captured_prompt
    assert "Test Trigger" in captured_prompt
    assert "Test Conditions" in captured_prompt
    assert "Test Description" in captured_prompt
    assert "Test question?" in captured_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            ["foo"],
            [TextContent(content="foo")],
            id="default text case",
        ),
        pytest.param(
            ["foo]"],
            [TextContent(content="foo]")],
            id="closing bracket only with text",
        ),
        pytest.param(
            ["[foo]"],
            [TextContent(content="[foo]")],
            id="generic message in square brackets",
        ),
        pytest.param(
            ["[f", "oo]"],
            [TextContent(content="[foo]")],
            id="buffers unclosed open brackets",
        ),
        pytest.param(
            ["[", "]"],
            [TextContent(content="[]")],
            id="empty brackets",
        ),
        pytest.param(
            ["foo [AXIOM", "-001]"],
            [
                TextContent(content="foo "),
                CitationCandidate(id=AxiomId("AXIOM-001"), text="[AXIOM-001]"),
            ],
            id="parsed citation",
        ),
        pytest.param(
            ["foo [AXIOM-12]", ""],
            [
                TextContent(content="foo "),
                CitationCandidate(id=AxiomId("AXIOM-12"), text="[AXIOM-12]"),
            ],
            id="parsed citation with two digits (single chunk)",
        ),
        pytest.param(
            ["foo", "[AX"],
            [
                TextContent(content="foo"),
                TextContent(content="[AX"),
            ],
            id="unfinished axiom reference",
        ),
        pytest.param(
            ["", "\n", ""],
            [
                TextContent(content="\n"),
            ],
            id="omit empty chunks",
        ),
    ],
)
async def test_process_chunk(
    test_input: Iterable[str],
    expected: Iterable[TextContent | CitationCandidate],
):
    """Test that process_chunk correctly parses text and citations."""
    result = [chunk async for chunk in process_chunk(async_iter(test_input))]
    expected_list = list(expected)

    assert result == expected_list


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunks_from_agent, expected_output",
    [
        pytest.param(
            ["Hello [AXIOM-001] world"],
            [
                TextContent(content="Hello "),
                CitationContent(
                    axiom=Axiom(
                        id=AxiomId("AXIOM-001"),
                        subject="subject",
                        entity="entity",
                        trigger="trigger",
                        conditions="conditions",
                        description="description",
                        category="category",
                    )
                ),
                TextContent(content=" world"),
            ],
            id="valid axiom citation found in store",
        ),
        pytest.param(
            ["Hello [AXIOM-999] world"],
            [
                TextContent(content="Hello "),
                TextContent(content="[AXIOM-999]"),
                TextContent(content=" world"),
            ],
            id="axiom citation not found in store - returns original text",
        ),
        pytest.param(
            ["Plain text without citations"],
            [
                TextContent(content="Plain text without citations"),
            ],
            id="no citations - passthrough chunk content",
        ),
        pytest.param(
            ["Multiple [AXIOM-001] citations [AXIOM-002] here"],
            [
                TextContent(content="Multiple "),
                CitationContent(
                    axiom=Axiom(
                        id=AxiomId("AXIOM-001"),
                        subject="subject",
                        entity="entity",
                        trigger="trigger",
                        conditions="conditions",
                        description="description",
                        category="category",
                    )
                ),
                TextContent(content=" citations "),
                TextContent(content="[AXIOM-002]"),  # AXIOM-002 not in store
                TextContent(content=" here"),
            ],
            id="mix of valid and invalid axiom citations",
        ),
    ],
)
async def test_invoke_streaming_citation_handling(
    chunks_from_agent: list[str],
    expected_output: list[TextContent | CitationContent],
):
    """Test that invoke_streaming correctly handles citations."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock the run_stream method to return MockStreamChunk objects
    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        for chunk_content in chunks_from_agent:
            yield MockStreamChunk(chunk_content)

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with one test axiom
    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("AXIOM-001"),
                subject="subject",
                entity="entity",
                trigger="trigger",
                conditions="conditions",
                description="description",
                category="category",
            )
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result: list[TextContent | CitationContent] = []
    async for chunk in qa_engine.invoke_streaming(question="Test question"):
        result.append(chunk)

    # Assert
    assert result == expected_output


def test_citation_content_property():
    """Test that CitationContent.content property returns formatted axiom ID."""
    # Arrange
    axiom = Axiom(
        id=AxiomId("AXIOM-001"),
        subject="subject",
        entity="entity",
        trigger="trigger",
        conditions="conditions",
        description="description",
        category="category",
    )

    # Act
    citation = CitationContent(axiom=axiom)

    # Assert
    assert citation.content == "[AXIOM-001]"
    assert isinstance(citation.content, str)


@pytest.mark.asyncio
async def test_invoke_streaming_empty_response():
    """Test that invoke_streaming handles empty responses gracefully."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return empty iterator
    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        # Return an empty async iterator
        return
        yield  # noqa: unreachable - needed for type checker

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    result = []
    async for chunk in qa_engine.invoke_streaming(question="Test question"):
        result.append(chunk)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_invoke_streaming_multiple_citations_in_sequence():
    """Test that invoke_streaming handles multiple citations in sequence."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("[AXIOM-001][AXIOM-002]")

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with two test axioms
    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("AXIOM-001"),
                subject="subject1",
                entity="entity1",
                trigger="trigger1",
                conditions="conditions1",
                description="description1",
                category="category1",
            ),
            Axiom(
                id=AxiomId("AXIOM-002"),
                subject="subject2",
                entity="entity2",
                trigger="trigger2",
                conditions="conditions2",
                description="description2",
                category="category2",
            ),
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result = []
    async for chunk in qa_engine.invoke_streaming(question="Test question"):
        result.append(chunk)

    # Assert
    # Should have: empty text, citation 1, empty text, citation 2
    # (Empty texts result from the regex processing)
    assert len(result) == 4
    citation_chunks = [c for c in result if isinstance(c, CitationContent)]
    assert len(citation_chunks) == 2
    assert citation_chunks[0].axiom.id == AxiomId("AXIOM-001")
    assert citation_chunks[1].axiom.id == AxiomId("AXIOM-002")


@pytest.mark.asyncio
async def test_invoke_collects_all_streaming_chunks():
    """Test that invoke method correctly collects all streaming chunks."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        chunks = ["This ", "is ", "a ", "test ", "[AXIOM-001]"]
        for chunk in chunks:
            yield MockStreamChunk(chunk)

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("AXIOM-001"),
                subject="subject",
                entity="entity",
                trigger="trigger",
                conditions="conditions",
                description="description",
                category="category",
            )
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result = await qa_engine.invoke(question="Test question")

    # Assert
    assert result == "This is a test [AXIOM-001]"


def test_message_model():
    """Test the Message model for conversation history."""
    # Arrange & Act
    user_message = Message(role="user", content="Hello")
    assistant_message = Message(role="assistant", content="Hi there")

    # Assert
    assert user_message.role == "user"
    assert user_message.content == "Hello"
    assert assistant_message.role == "assistant"
    assert assistant_message.content == "Hi there"


def test_text_content_model():
    """Test the TextContent model."""
    # Arrange & Act
    text_content = TextContent(content="Some text")

    # Assert
    assert text_content.content == "Some text"
    assert isinstance(text_content.content, str)


def test_axiom_store_integration():
    """Test that QAEngine integrates correctly with AxiomStore."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    axioms = [
        Axiom(
            id=AxiomId("AXIOM-001"),
            subject="subject1",
            entity="entity1",
            trigger="trigger1",
            conditions="conditions1",
            description="description1",
            category="category1",
        ),
        Axiom(
            id=AxiomId("AXIOM-002"),
            subject="subject2",
            entity="entity2",
            trigger="trigger2",
            conditions="conditions2",
            description="description2",
            category="category2",
        ),
    ]

    axiom_store = AxiomStore(axioms)
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    assert qa_engine.axiom_store is not None
    retrieved_axiom = qa_engine.axiom_store.get(AxiomId("AXIOM-001"))

    # Assert
    assert retrieved_axiom is not None
    assert retrieved_axiom.id == AxiomId("AXIOM-001")
    assert retrieved_axiom.subject == "subject1"


@pytest.mark.asyncio
async def test_process_chunk_with_split_citation():
    """Test that process_chunk correctly handles citations split across chunks."""
    # Arrange
    chunks = ["Text before ", "[AX", "IOM-", "001", "] text after"]

    # Act
    result = [chunk async for chunk in process_chunk(async_iter(chunks))]

    # Assert
    # Should have: text before, empty text, citation candidate, text after
    # (The empty text results from regex processing)
    assert len(result) >= 3
    # Filter out empty text chunks for easier assertion
    non_empty_result = [
        chunk
        for chunk in result
        if not (isinstance(chunk, TextContent) and chunk.content == "")
    ]
    assert len(non_empty_result) == 3
    assert isinstance(non_empty_result[0], TextContent)
    assert non_empty_result[0].content == "Text before "
    assert isinstance(non_empty_result[1], CitationCandidate)
    assert non_empty_result[1].id == AxiomId("AXIOM-001")
    assert isinstance(non_empty_result[2], TextContent)
    assert non_empty_result[2].content == " text after"
