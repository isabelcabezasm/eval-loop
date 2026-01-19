"""
Tests for the QA Engine module.

This module tests the QAEngine class and its interaction with the
Microsoft Agent Framework, including message streaming, citation handling,
and prompt formatting.
"""

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from unittest.mock import MagicMock

import pytest
from agent_framework import ChatAgent

from core.axiom_store import Axiom, AxiomId, AxiomStore
from core.qa_engine import (
    AxiomCitationContent,
    CitationContent,
    InvokeStreamingResult,
    Message,
    QAEngine,
    RealityCitationContent,
    TextContent,
)
from core.reality import RealityId, RealityStatement


async def async_iter[T](iterable: Iterable[T]) -> AsyncIterator[T]:
    """Convert an iterable to an async iterator for testing."""
    for element in iterable:
        yield element


class MockStreamChunk:
    """Mock class for agent stream chunks."""

    def __init__(self, text: str):
        super().__init__()
        self.text = text


@pytest.mark.asyncio
async def test_invoke_stream_calls_agent_correctly():
    """Test that invoke_streaming correctly
    calls the agent's run_stream method."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return chunks
    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Hello")
        yield MockStreamChunk(", ")
        yield MockStreamChunk("world")
        yield MockStreamChunk("!")

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("A-001"),
                description="description",
            )
        ]
    )

    subject = QAEngine(mock_agent, axiom_store)

    # Act
    result: list[TextContent | CitationContent] = []
    streaming_result: InvokeStreamingResult = await subject.invoke_streaming(
        "Test question"
    )
    async for chunk in streaming_result.chunks:
        result.append(chunk)

    # Assert
    # Verify that we got the expected content
    # Note: Each chunk from the mock agent becomes a separate TextContent
    assert len(result) == 4
    assert streaming_result.thread_id  # Verify thread_id is returned
    assert all(isinstance(chunk, TextContent) for chunk in result)
    # Verify the concatenated content
    full_text = "".join(chunk.content for chunk in result)
    assert full_text == "Hello, world!"


async def act_invoke_stream(qa_engine: QAEngine) -> str:
    """Helper to collect all text from streaming invoke."""
    result = ""
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question"
    )
    async for chunk in streaming_result.chunks:
        if isinstance(chunk, TextContent):
            result += chunk.content
        else:
            # chunk is AxiomCitationContent or RealityCitationContent
            result += chunk.content
    return result


async def act_invoke(qa_engine: QAEngine) -> str:
    """Helper to test non-streaming invoke."""
    result, _thread_id = await qa_engine.invoke(question="Test question")
    return result


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
    """
    Test that both streaming and non-streaming invoke return the
    correct message.
    """
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return chunks that form "Hello, world!"
    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
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

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        nonlocal captured_prompt
        captured_prompt = _prompt
        yield MockStreamChunk("Test response")

    mock_agent.run_stream = mock_run_stream

    axioms = [
        Axiom(
            id=AxiomId("A-001"),
            description="Test Description",
        )
    ]

    axiom_store = AxiomStore(axioms)
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    streaming_result = await qa_engine.invoke_streaming("Test question?")
    async for _ in streaming_result.chunks:
        pass

    # Assert that the prompt includes constitution data
    assert captured_prompt is not None
    assert "A-001" in captured_prompt
    assert "Test Description" in captured_prompt
    assert "Test question?" in captured_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chunks_from_agent, expected_output",
    [
        pytest.param(
            ["Hello [A-001] world"],
            [
                TextContent(content="Hello "),
                AxiomCitationContent(
                    item=Axiom(
                        id=AxiomId("A-001"),
                        description="description",
                    )
                ),
                TextContent(content=" world"),
            ],
            id="valid axiom citation found in store",
        ),
        pytest.param(
            ["Hello [A-999] world"],
            [
                TextContent(content="Hello "),
                TextContent(content="[A-999]"),
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
            ["Multiple [A-001] citations [A-002] here"],
            [
                TextContent(content="Multiple "),
                AxiomCitationContent(
                    item=Axiom(
                        id=AxiomId("A-001"),
                        description="description",
                    )
                ),
                TextContent(content=" citations "),
                TextContent(content="[A-002]"),  # A-002 not in store
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
    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        for chunk_content in chunks_from_agent:
            yield MockStreamChunk(chunk_content)

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with one test axiom
    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("A-001"),
                description="description",
            )
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result: list[TextContent | CitationContent] = []
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question"
    )
    async for chunk in streaming_result.chunks:
        result.append(chunk)

    # Assert
    assert result == expected_output


def test_citation_content_property():
    """
    Test that AxiomCitationContent.content property returns formatted
    axiom ID.
    """
    # Arrange
    axiom = Axiom(
        id=AxiomId("A-001"),
        description="description",
    )

    # Act
    citation = AxiomCitationContent(item=axiom)

    # Assert
    assert citation.content == "[A-001]"
    assert isinstance(citation.content, str)


@pytest.mark.asyncio
async def test_invoke_streaming_empty_response():
    """Test that invoke_streaming handles empty responses gracefully."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return empty iterator
    mock_agent.run_stream = (
        lambda _prompt,  # pyright: ignore[reportUnknownLambdaType]
        **kwargs: async_iter([])  # pyright: ignore[reportUnknownLambdaType]
    )
    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    result: list[TextContent | CitationContent] = []
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question"
    )
    async for chunk in streaming_result.chunks:
        result.append(chunk)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_invoke_streaming_multiple_citations_in_sequence():
    """Test that invoke_streaming handles multiple citations in sequence."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("[A-001][A-002]")

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with two test axioms
    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("A-001"),
                description="description1",
            ),
            Axiom(
                id=AxiomId("A-002"),
                description="description2",
            ),
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result: list[TextContent | CitationContent] = []
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question"
    )
    async for chunk in streaming_result.chunks:
        result.append(chunk)

    # Assert
    # Should have: empty text, citation 1, empty text, citation 2
    # (Empty texts result from the regex processing)
    assert len(result) == 4
    citation_chunks = [
        c for c in result if isinstance(c, AxiomCitationContent)
    ]
    assert len(citation_chunks) == 2
    assert citation_chunks[0].item.id == AxiomId("A-001")
    assert citation_chunks[1].item.id == AxiomId("A-002")


@pytest.mark.asyncio
async def test_invoke_collects_all_streaming_chunks():
    """Test that invoke method correctly collects all streaming chunks."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        chunks = ["This ", "is ", "a ", "test ", "[A-001]"]
        for chunk in chunks:
            yield MockStreamChunk(chunk)

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("A-001"),
                description="description",
            )
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    result, thread_id = await qa_engine.invoke(question="Test question")

    # Assert
    assert result == "This is a test [A-001]"
    assert thread_id  # Verify thread_id is returned


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
            id=AxiomId("A-001"),
            description="description1",
        ),
        Axiom(
            id=AxiomId("A-002"),
            description="description2",
        ),
    ]

    axiom_store = AxiomStore(axioms)
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act
    assert qa_engine.axiom_store is not None
    retrieved_axiom = qa_engine.axiom_store.get(AxiomId("A-001"))

    # Assert
    assert retrieved_axiom is not None
    assert retrieved_axiom.id == AxiomId("A-001")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "agent_chunks",
        "expected_text",
        "num_axiom_citations",
        "num_reality_citations",
        "expected_axiom_ids",
        "expected_reality_ids",
    ),
    [
        pytest.param(
            ["foo"],
            "foo",
            0,
            0,
            [],
            [],
            id="default text case",
        ),
        pytest.param(
            ["foo]"],
            "foo]",
            0,
            0,
            [],
            [],
            id="closing bracket only with text",
        ),
        pytest.param(
            ["[foo]"],
            "[foo]",
            0,
            0,
            [],
            [],
            id="generic message in square brackets",
        ),
        pytest.param(
            ["[f", "oo]"],
            "[foo]",
            0,
            0,
            [],
            [],
            id="buffers unclosed open brackets",
        ),
        pytest.param(
            ["[", "]"],
            "[]",
            0,
            0,
            [],
            [],
            id="empty brackets",
        ),
        pytest.param(
            ["foo [A", "-001]"],
            "foo [A-001]",
            1,
            0,
            ["A-001"],
            [],
            id="parsed citation split across chunks",
        ),
        pytest.param(
            ["foo [A-12]", ""],
            "foo [A-12]",
            1,
            0,
            ["A-12"],
            [],
            id="parsed citation with two digits (single chunk)",
        ),
        pytest.param(
            ["foo", "[AX"],
            "foo[AX",
            0,
            0,
            [],
            [],
            id="unfinished axiom reference",
        ),
        pytest.param(
            ["", "\n", ""],
            "\n",
            0,
            0,
            [],
            [],
            id="omit empty chunks",
        ),
        pytest.param(
            ["Text before [A", "-", "001] text after"],
            "Text before [A-001] text after",
            1,
            0,
            ["A-001"],
            [],
            id="citation split across 3 chunks with surrounding text",
        ),
        pytest.param(
            ["Text with [random brackets] and [A-001]."],
            "Text with [random brackets] and [A-001].",
            1,
            0,
            ["A-001"],
            [],
            id="valid citation mixed with non-citation brackets",
        ),
        pytest.param(
            ["Valid [A-001] and incomplete [AX"],
            "Valid [A-001] and incomplete [AX",
            1,
            0,
            ["A-001"],
            [],
            id="valid citation with incomplete citation at end",
        ),
        pytest.param(
            ["", "Text ", "", "[A-001]", ""],
            "Text [A-001]",
            1,
            0,
            ["A-001"],
            [],
            id="empty chunks interspersed with content and citations",
        ),
        pytest.param(
            ["Based on [R-001]."],
            "Based on [R-001].",
            0,
            1,
            [],
            ["R-001"],
            id="single reality citation",
        ),
        pytest.param(
            ["Check [R-", "001] for details"],
            "Check [R-001] for details",
            0,
            1,
            [],
            ["R-001"],
            id="reality citation split across chunks",
        ),
        pytest.param(
            ["Mix [A-001] and [R-001]"],
            "Mix [A-001] and [R-001]",
            1,
            1,
            ["A-001"],
            ["R-001"],
            id="mixed axiom and reality citations",
        ),
        pytest.param(
            ["Considering [R-001] and [R-002]."],
            "Considering [R-001] and [R-002].",
            0,
            2,
            [],
            ["R-001", "R-002"],
            id="multiple reality citations in sequence",
        ),
    ],
)
async def test_invoke_streaming_handles_chunk_scenarios(
    agent_chunks: list[str],
    expected_text: str,
    num_axiom_citations: int,
    num_reality_citations: int,
    expected_axiom_ids: list[str],
    expected_reality_ids: list[str],
):
    """Test that streaming correctly handles various chunking scenarios."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        for chunk in agent_chunks:
            yield MockStreamChunk(chunk)

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with test axioms for citation tests
    axiom_store = AxiomStore(
        [
            Axiom(
                id=AxiomId("A-001"),
                description="description",
            ),
            Axiom(
                id=AxiomId("A-12"),
                description="description",
            ),
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Create reality statements for reality citation tests
    reality = [
        RealityStatement(
            id=RealityId("R-001"),
            description="Test description",
        ),
        RealityStatement(
            id=RealityId("R-002"),
            description="Interest rates are rising.",
        ),
    ]

    # Act
    result: list[TextContent | CitationContent] = []
    streaming_result = await qa_engine.invoke_streaming(
        question="Test", reality=reality
    )
    async for chunk in streaming_result.chunks:
        result.append(chunk)

    # Assert
    full_text = "".join(chunk.content for chunk in result)
    assert full_text == expected_text

    # Verify citation counts
    axiom_citations = [
        c for c in result if isinstance(c, AxiomCitationContent)
    ]
    reality_citations = [
        c for c in result if isinstance(c, RealityCitationContent)
    ]

    assert len(axiom_citations) == num_axiom_citations
    assert len(reality_citations) == num_reality_citations

    # Verify specific citation IDs
    actual_axiom_ids = [str(c.item.id) for c in axiom_citations]
    actual_reality_ids = [str(c.item.id) for c in reality_citations]

    assert actual_axiom_ids == expected_axiom_ids
    assert actual_reality_ids == expected_reality_ids


# =============================================================================
# Thread ID Tests (Task 3.1)
# =============================================================================


@pytest.mark.asyncio
async def test_invoke_streaming_without_thread_id_generates_new_thread():
    """Test that invoke_streaming generates a new thread_id when none."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Response")

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question"
    )
    async for _ in streaming_result.chunks:
        pass

    # Assert - thread_id should be generated (UUID format)
    assert streaming_result.thread_id is not None
    assert len(streaming_result.thread_id) == 36  # UUID format: 8-4-4-4-12


@pytest.mark.asyncio
async def test_invoke_streaming_with_thread_id_uses_provided_thread():
    """Test that invoke_streaming uses the provided thread_id."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)
    provided_thread_id = "existing-thread-123"
    captured_thread_id = None

    async def mock_run_stream(
        _prompt: str, **kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        nonlocal captured_thread_id
        captured_thread_id = kwargs.get("thread_id")
        yield MockStreamChunk("Response")

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    streaming_result = await qa_engine.invoke_streaming(
        question="Test question", thread_id=provided_thread_id
    )
    async for _ in streaming_result.chunks:
        pass

    # Assert
    assert captured_thread_id == provided_thread_id
    assert streaming_result.thread_id == provided_thread_id


@pytest.mark.asyncio
async def test_invoke_without_thread_id_generates_new_thread():
    """Test that invoke generates a new thread_id when none provided."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Response")

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    _response, thread_id = await qa_engine.invoke(question="Test question")

    # Assert - thread_id should be generated (UUID format)
    assert thread_id is not None
    assert len(thread_id) == 36  # UUID format: 8-4-4-4-12


@pytest.mark.asyncio
async def test_invoke_with_thread_id_uses_provided_thread():
    """Test that invoke uses the provided thread_id."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)
    provided_thread_id = "existing-thread-456"
    captured_thread_id = None

    async def mock_run_stream(
        _prompt: str, **kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        nonlocal captured_thread_id
        captured_thread_id = kwargs.get("thread_id")
        yield MockStreamChunk("Response")

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    _response, thread_id = await qa_engine.invoke(
        question="Test question", thread_id=provided_thread_id
    )

    # Assert
    assert captured_thread_id == provided_thread_id
    assert thread_id == provided_thread_id


@pytest.mark.asyncio
async def test_invoke_streaming_backward_compatible_without_thread_id():
    """Test invoke_streaming backward compatibility without thread_id."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Hello")
        yield MockStreamChunk(" World")

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [Axiom(id=AxiomId("A-001"), description="description")]
    )
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act - call without thread_id (old usage pattern)
    streaming_result = await qa_engine.invoke_streaming(question="Test?")
    chunks: list[TextContent | CitationContent] = []
    async for chunk in streaming_result.chunks:
        chunks.append(chunk)

    # Assert - should work and return thread_id
    full_text = "".join(c.content for c in chunks)
    assert full_text == "Hello World"
    assert streaming_result.thread_id is not None


@pytest.mark.asyncio
async def test_invoke_backward_compatible_without_thread_id():
    """Test that invoke works correctly without thread_id (backward compat)."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    async def mock_run_stream(
        _prompt: str, **_kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        yield MockStreamChunk("Hello World")

    mock_agent.run_stream = mock_run_stream

    axiom_store = AxiomStore(
        [Axiom(id=AxiomId("A-001"), description="description")]
    )
    qa_engine = QAEngine(mock_agent, axiom_store)

    # Act - call without thread_id (old usage pattern)
    response, thread_id = await qa_engine.invoke(question="Test?")

    # Assert - should work and return both response and thread_id
    assert response == "Hello World"
    assert thread_id is not None


@pytest.mark.asyncio
async def test_multiple_calls_with_same_thread_id():
    """Test that multiple calls with the same thread_id use that thread."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)
    shared_thread_id = "shared-conversation-thread"
    captured_thread_ids: list[str | None] = []

    async def mock_run_stream(
        _prompt: str, **kwargs: object
    ) -> AsyncIterator[MockStreamChunk]:
        captured_thread_ids.append(kwargs.get(
            "thread_id"))  # type: ignore[arg-type]
        yield MockStreamChunk("Response")

    mock_agent.run_stream = mock_run_stream

    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act - make multiple calls with the same thread_id
    for _ in range(3):
        streaming_result = await qa_engine.invoke_streaming(
            question="Question", thread_id=shared_thread_id
        )
        async for _ in streaming_result.chunks:
            pass

    # Assert - all calls should use the same thread_id
    assert len(captured_thread_ids) == 3
    assert all(tid == shared_thread_id for tid in captured_thread_ids)
