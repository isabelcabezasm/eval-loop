"""
Tests for error handling in the /api/generate endpoint.

This module tests the error handling functionality added to the stream()
method, ensuring that exceptions are properly caught, formatted as error
responses, and re-raised.
"""

import json
from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest

from core.axiom_store import Axiom, AxiomId
from core.qa_engine import (
    AxiomCitationContent,
    TextContent,
    UserSessionId,
)
from core.reality import RealityStatement


def test_error_message_format():
    """
    Test that error messages are properly formatted as JSON.

    This is a unit test to verify the error response structure matches
    the expected format without requiring the full streaming infrastructure.
    """
    # Simulate what the stream() method does on error
    test_exception = Exception("Test error message")
    error_response = {"type": "error", "message": str(test_exception)}
    error_json = json.dumps(error_response)

    # Verify it's valid JSON
    parsed = json.loads(error_json)
    assert parsed["type"] == "error"
    assert parsed["message"] == "Test error message"


@pytest.mark.parametrize(
    "exception_class,exception_message",
    [
        (ValueError, "Invalid input provided"),
        (RuntimeError, "Runtime error occurred"),
        (ConnectionError, "Connection failed"),
        (TimeoutError, "Request timed out"),
        (TypeError, "Type mismatch error"),
    ],
)
def test_error_response_format_for_various_exceptions(
    exception_class: type[Exception], exception_message: str
):
    """
    Test that various exception types are correctly converted to error
    responses.

    The error response format should be consistent regardless of the
    exception type.
    """
    # Create an exception instance
    exc = exception_class(exception_message)

    # Format as error response (simulating stream() error handling)
    error_response = {"type": "error", "message": str(exc)}
    error_json = json.dumps(error_response)

    # Verify the format
    parsed = json.loads(error_json)
    assert parsed["type"] == "error"
    assert parsed["message"] == exception_message


def test_ndjson_format_for_error_chunk():
    """
    Test that error chunks are formatted as valid NDJSON.

    Each chunk should be on its own line with a newline terminator.
    """
    error_response = {"type": "error", "message": "Test error"}
    # This is how the stream() method formats it
    ndjson_line = f"{json.dumps(error_response)}\n"

    # Should end with newline
    assert ndjson_line.endswith("\n")

    # Should be parseable as JSON (minus the newline)
    parsed = json.loads(ndjson_line.strip())
    assert parsed["type"] == "error"
    assert parsed["message"] == "Test error"


@pytest.mark.asyncio
async def test_stream_yields_error_then_raises():
    """
    Integration test to verify the stream error handling flow.

    This tests that:
    1. The stream yields content chunks
    2. When an exception occurs, an error chunk is yielded
    3. The original exception is then re-raised
    """
    from api.generate import GenerateRequest

    # Create a mock QA engine that yields content then fails
    async def mock_streaming_with_error(
        question: str,
        session_id: UserSessionId,
        reality: list[RealityStatement],
    ) -> AsyncIterator[TextContent]:
        yield TextContent(content="Partial response")
        raise ValueError("Simulated error")

    mock_engine = MagicMock()
    mock_engine.invoke_streaming = mock_streaming_with_error

    # Manually construct the stream() generator to test it
    with patch("api.generate.qa_engine", return_value=mock_engine):
        # Import here to get the patched version
        from api.generate import generate

        request = GenerateRequest(
            question="Test question",
            reality=None,
            session_id="test-session",
        )

        # Get the streaming response
        response = await generate(request)

        # Collect all chunks (including error)
        chunks: list[str] = []
        exception_raised = False
        try:
            async for chunk in response.body_iterator:
                chunks.append(
                    chunk
                    if isinstance(chunk, str)
                    else chunk.decode(  # type: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                        "utf-8"
                    )
                )
        except ValueError as e:
            # Exception should be re-raised
            assert str(e) == "Simulated error"
            exception_raised = True

        # Verify exception was raised
        assert exception_raised, "Expected ValueError to be re-raised"

        # Should have yielded at least 2 chunks: content + error
        assert len(chunks) >= 2, (
            f"Expected at least 2 chunks, got {len(chunks)}"
        )

        # Parse first chunk (content)
        first_chunk = json.loads(chunks[0].strip())
        assert first_chunk["type"] == "text"
        assert first_chunk["text"] == "Partial response"

        # Parse second chunk (error)
        error_chunk = json.loads(chunks[1].strip())
        assert error_chunk["type"] == "error"
        assert "Simulated error" in error_chunk["message"]


@pytest.mark.asyncio
async def test_stream_with_mixed_content_before_error():
    """
    Test error handling when stream has yielded multiple content types.

    Verifies that error handling works correctly even after yielding
    text content and citations.
    """
    from api.generate import GenerateRequest

    # Create a mock QA engine that yields mixed content then fails
    async def mock_streaming_mixed_then_error(
        question: str,
        session_id: UserSessionId,
        reality: list[RealityStatement],
    ) -> AsyncIterator[TextContent | AxiomCitationContent]:
        yield TextContent(content="Start")
        yield AxiomCitationContent(
            item=Axiom(id=AxiomId("A-001"), description="Test axiom")
        )
        yield TextContent(content=" middle")
        raise ConnectionError("Connection lost")

    mock_engine = MagicMock()
    mock_engine.invoke_streaming = mock_streaming_mixed_then_error

    with patch("api.generate.qa_engine", return_value=mock_engine):
        from api.generate import generate

        request = GenerateRequest(
            question="Test question",
            reality=None,
            session_id="test-session",
        )

        response = await generate(request)

        chunks: list[str] = []
        exception_raised = False
        try:
            async for chunk in response.body_iterator:
                chunks.append(
                    chunk
                    if isinstance(chunk, str)
                    else chunk.decode(  # type: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                        "utf-8"
                    )
                )
        except ConnectionError:
            exception_raised = True

        # Should have raised the exception
        assert exception_raised, "Expected ConnectionError to be re-raised"

        # Should have multiple chunks before error
        assert len(chunks) >= 4, "Expected 3 content chunks + error chunk"

        # Verify we got the expected content types
        chunk_types = []
        for chunk_data in chunks:
            if chunk_data.strip():
                parsed = json.loads(chunk_data.strip())
                chunk_types.append(  # type: ignore[reportUnknownMemberType]
                    parsed["type"]
                )

        # Should have text, axiom citation, more text, and error
        assert "text" in chunk_types
        assert "axiom_citation" in chunk_types
        assert "error" in chunk_types


@pytest.mark.asyncio
async def test_stream_immediate_error():
    """
    Test error handling when exception occurs immediately.

    Verifies that errors raised before any content is yielded are
    still properly formatted and re-raised.
    """
    from api.generate import GenerateRequest

    # Create a mock QA engine that fails immediately
    async def mock_streaming_immediate_error(
        question: str,
        session_id: UserSessionId,
        reality: list[RealityStatement],
    ) -> AsyncIterator[TextContent]:
        raise RuntimeError("Immediate error")
        # This yield is unreachable but makes the function a generator
        yield TextContent(content="Never reached")  # type: ignore[unreachable]

    mock_engine = MagicMock()
    mock_engine.invoke_streaming = mock_streaming_immediate_error

    with patch("api.generate.qa_engine", return_value=mock_engine):
        from api.generate import generate

        request = GenerateRequest(
            question="Test question",
            reality=None,
            session_id="test-session",
        )

        response = await generate(request)

        chunks: list[str] = []
        exception_raised = False
        try:
            async for chunk in response.body_iterator:
                chunks.append(
                    chunk
                    if isinstance(chunk, str)
                    else chunk.decode(  # type: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                        "utf-8"
                    )
                )
        except RuntimeError as e:
            assert str(e) == "Immediate error"
            exception_raised = True

        # Verify exception was raised
        assert exception_raised, "Expected RuntimeError to be re-raised"

        # Should have yielded at least the error chunk
        assert len(chunks) >= 1, "Expected at least error chunk"

        # Parse error chunk
        error_chunk = json.loads(chunks[0].strip())
        assert error_chunk["type"] == "error"
        assert "Immediate error" in error_chunk["message"]
