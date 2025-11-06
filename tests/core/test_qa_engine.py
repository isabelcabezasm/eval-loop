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
    result: list[TextContent | CitationContent] = []
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
        else:  # the chunk only can be AxiomCitationContent or RealityCitationContent
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
    "chunks_from_agent, expected_output",
    [
        pytest.param(
            ["Hello [AXIOM-001] world"],
            [
                TextContent(content="Hello "),
                AxiomCitationContent(
                    item=Axiom(
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
                AxiomCitationContent(
                    item=Axiom(
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
    """Test that AxiomCitationContent.content property returns formatted axiom ID."""
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
    citation = AxiomCitationContent(item=axiom)

    # Assert
    assert citation.content == "[AXIOM-001]"
    assert isinstance(citation.content, str)


@pytest.mark.asyncio
async def test_invoke_streaming_empty_response():
    """Test that invoke_streaming handles empty responses gracefully."""
    # Arrange
    mock_agent = MagicMock(spec=ChatAgent)

    # Mock run_stream to return empty iterator
    mock_agent.run_stream = lambda _prompt: async_iter([])  # pyright: ignore[reportUnknownLambdaType]
    qa_engine = QAEngine(mock_agent, MagicMock(spec=AxiomStore))

    # Act
    result: list[TextContent | CitationContent] = []
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
    result: list[TextContent | CitationContent] = []
    async for chunk in qa_engine.invoke_streaming(question="Test question"):
        result.append(chunk)

    # Assert
    # Should have: empty text, citation 1, empty text, citation 2
    # (Empty texts result from the regex processing)
    assert len(result) == 4
    citation_chunks = [c for c in result if isinstance(c, AxiomCitationContent)]
    assert len(citation_chunks) == 2
    assert citation_chunks[0].item.id == AxiomId("AXIOM-001")
    assert citation_chunks[1].item.id == AxiomId("AXIOM-002")


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
            ["foo [AXIOM", "-001]"],
            "foo [AXIOM-001]",
            1,
            0,
            ["AXIOM-001"],
            [],
            id="parsed citation split across chunks",
        ),
        pytest.param(
            ["foo [AXIOM-12]", ""],
            "foo [AXIOM-12]",
            1,
            0,
            ["AXIOM-12"],
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
            ["Text before [AX", "IOM-", "001] text after"],
            "Text before [AXIOM-001] text after",
            1,
            0,
            ["AXIOM-001"],
            [],
            id="citation split across 3 chunks with surrounding text",
        ),
        pytest.param(
            ["Text with [random brackets] and [AXIOM-001]."],
            "Text with [random brackets] and [AXIOM-001].",
            1,
            0,
            ["AXIOM-001"],
            [],
            id="valid citation mixed with non-citation brackets",
        ),
        pytest.param(
            ["Valid [AXIOM-001] and incomplete [AX"],
            "Valid [AXIOM-001] and incomplete [AX",
            1,
            0,
            ["AXIOM-001"],
            [],
            id="valid citation with incomplete citation at end",
        ),
        pytest.param(
            ["", "Text ", "", "[AXIOM-001]", ""],
            "Text [AXIOM-001]",
            1,
            0,
            ["AXIOM-001"],
            [],
            id="empty chunks interspersed with content and citations",
        ),
        pytest.param(
            ["Based on [REALITY-001]."],
            "Based on [REALITY-001].",
            0,
            1,
            [],
            ["REALITY-001"],
            id="single reality citation",
        ),
        pytest.param(
            ["Check [REALITY-", "001] for details"],
            "Check [REALITY-001] for details",
            0,
            1,
            [],
            ["REALITY-001"],
            id="reality citation split across chunks",
        ),
        pytest.param(
            ["Mix [AXIOM-001] and [REALITY-001]"],
            "Mix [AXIOM-001] and [REALITY-001]",
            1,
            1,
            ["AXIOM-001"],
            ["REALITY-001"],
            id="mixed axiom and reality citations",
        ),
        pytest.param(
            ["Considering [REALITY-001] and [REALITY-002]."],
            "Considering [REALITY-001] and [REALITY-002].",
            0,
            2,
            [],
            ["REALITY-001", "REALITY-002"],
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

    async def mock_run_stream(_prompt: str) -> AsyncIterator[MockStreamChunk]:
        for chunk in agent_chunks:
            yield MockStreamChunk(chunk)

    mock_agent.run_stream = mock_run_stream

    # Create axiom store with test axioms for citation tests
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
            ),
            Axiom(
                id=AxiomId("AXIOM-12"),
                subject="subject",
                entity="entity",
                trigger="trigger",
                conditions="conditions",
                description="description",
                category="category",
            ),
        ]
    )

    qa_engine = QAEngine(mock_agent, axiom_store)

    # Create reality statements for reality citation tests
    reality = [
        RealityStatement(
            id=RealityId("REALITY-001"),
            entity="Test",
            attribute="Test Attr",
            value="Test Value",
            number="100",
            description="Test description",
        ),
        RealityStatement(
            id=RealityId("REALITY-002"),
            entity="Healthcare",
            attribute="Medical Costs",
            value="Rising",
            number="12%",
            description="Medical costs are rising.",
        ),
    ]

    # Act
    result: list[TextContent | CitationContent] = []
    async for chunk in qa_engine.invoke_streaming(question="Test", reality=reality):
        result.append(chunk)

    # Assert
    full_text = "".join(chunk.content for chunk in result)
    assert full_text == expected_text

    # Verify citation counts
    axiom_citations = [c for c in result if isinstance(c, AxiomCitationContent)]
    reality_citations = [c for c in result if isinstance(c, RealityCitationContent)]

    assert len(axiom_citations) == num_axiom_citations
    assert len(reality_citations) == num_reality_citations

    # Verify specific citation IDs
    actual_axiom_ids = [str(c.item.id) for c in axiom_citations]
    actual_reality_ids = [str(c.item.id) for c in reality_citations]

    assert actual_axiom_ids == expected_axiom_ids
    assert actual_reality_ids == expected_reality_ids
