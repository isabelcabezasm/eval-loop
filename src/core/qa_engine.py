"""
QA Engine for constitutional AI assistant.

This module provides the QAEngine class that handles question-answering
using Azure OpenAI with constitution-based prompting via the Microsoft Agent Framework.
"""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from agent_framework import ChatAgent
from pydantic import BaseModel, computed_field

from core.axiom_store import Axiom, AxiomId, AxiomStore
from core.prompt import build_user_prompt
from core.reality import RealityId, RealityStatement


class Message(BaseModel):
    """Message in a conversation history."""

    role: Literal["user", "assistant"]
    content: str


class TextContent(BaseModel):
    """Response containing simple text content from a streaming chunk."""

    content: str


class AxiomCitationContent(BaseModel):
    """Response containing an axiom citation in streaming chunk."""

    item: Axiom

    @computed_field
    @property
    def content(self) -> str:
        """Return formatted citation ID."""
        return f"[{self.item.id}]"


class RealityCitationContent(BaseModel):
    """Response containing a reality citation in streaming chunk."""

    item: RealityStatement

    @computed_field
    @property
    def content(self) -> str:
        """Return formatted citation ID."""
        return f"[{self.item.id}]"


# Union type for citation content with discriminator
CitationContent = AxiomCitationContent | RealityCitationContent


@dataclass(frozen=True)
class AxiomCitationCandidate:
    """Candidate axiom citation found in streaming text."""

    id: AxiomId
    text: str


@dataclass(frozen=True)
class RealityCitationCandidate:
    """Candidate reality citation found in streaming text."""

    id: RealityId
    text: str


CitationCandidate = AxiomCitationCandidate | RealityCitationCandidate


class QAEngine:
    """
    Question-Answering engine for constitutional queries.

    This class handles the orchestration of prompts, constitution loading,
    and interaction with Azure OpenAI via the Microsoft Agent Framework to provide
    contextualized responses based on predefined axioms.

    Attributes:
        agent (ChatAgent): The chat agent for model inference.
        axiom_store (AxiomStore): Storage for axioms/constitution data.
    """

    def __init__(
        self,
        agent: ChatAgent,
        axiom_store: AxiomStore,
    ):
        """
        Initialize the QA Engine.

        Args:
            agent: ChatAgent instance for model inference.
            axiom_store: Storage for axioms/constitution data.
        """
        self.agent = agent
        self.axiom_store = axiom_store

    @staticmethod
    def _is_complete_or_no_citation(buffer: str) -> bool:
        """
        Check if buffer can be safely yielded without splitting incomplete citations.

        Returns True if:
        - Buffer contains no opening bracket (no potential citation), OR
        - Buffer contains a closing bracket (complete citation)

        Args:
            buffer: Text buffer to check

        Returns:
            True if buffer is safe to yield, False otherwise
        """
        return ("[" not in buffer) or ("]" in buffer)

    async def _process_chunk(
        self,
        chunks: AsyncIterator[str],
    ) -> AsyncIterator[TextContent | AxiomCitationCandidate | RealityCitationCandidate]:
        """
        Process a series of chunks and returns text or parsed references.

        Args:
            chunks: Text chunk content to process

        Returns:
            AsyncIterator of TextContent or citation candidate instances
        """
        buffer = ""

        async for chunk in chunks:
            buffer += chunk

            # Check for both AXIOM and REALITY citations
            while match := re.search(r"\[(AXIOM-\d+|REALITY-\d+)\]", buffer):
                # Yield text before the citation
                yield TextContent(content=buffer[: match.start()])

                # Determine citation type and create appropriate ID
                citation_id = match.group(1)
                if citation_id.startswith("AXIOM-"):
                    yield AxiomCitationCandidate(
                        id=AxiomId(citation_id),
                        text=match.group(0),
                    )
                else:  # REALITY-
                    yield RealityCitationCandidate(
                        id=RealityId(citation_id),
                        text=match.group(0),
                    )

                buffer = buffer[match.end() :]

            # Yield buffer if it doesn't contain an incomplete citation
            if buffer and self._is_complete_or_no_citation(buffer):
                yield TextContent(content=buffer)
                buffer = ""

        # Yield remaining buffer
        if buffer:
            yield TextContent(content=buffer)

    async def invoke(
        self, question: str, reality: list[RealityStatement] | None = None
    ) -> str:
        """
        Generate AI response by collecting all streaming chunks into a single string.

        Args:
            question: The user's question.
            reality: Optional reality statements for additional context.

        Returns:
            Complete AI response with citations formatted as text.

        Note:
            TODO: Add support for conversation history with Message list.
        """
        # Collect all chunks from the streaming response
        result = ""
        async for chunk in self.invoke_streaming(question, reality):
            result += chunk.content

        return result

    async def invoke_streaming(
        self,
        question: str,
        reality: list[RealityStatement] | None = None,
    ) -> AsyncIterator[TextContent | CitationContent]:
        """
        Stream AI response with real-time citation detection and validation.

        Parses [AXIOM-XXX] and [REALITY-XXX] citations from the streamed response,
        validates them, and yields either TextContent or CitationContent chunks.
        Thread-safe for concurrent requests with different reality statements.

        Args:
            question: The user's question.
            reality: Optional reality statements for additional context.

        Yields:
            TextContent, AxiomCitationContent, or RealityCitationContent chunks.

        Note:
            TODO: Add support for conversation history with Message list.
        """
        # Create local reality store for this request
        reality_store = {s.id: s for s in reality} if reality else {}

        # Load and format user prompt with constitution, reality, and question
        user_prompt = build_user_prompt(self.axiom_store, question, reality)

        # Create async generator for streaming chunks
        async def stream() -> AsyncIterator[str]:
            async for chunk in self.agent.run_stream(user_prompt):
                if chunk.text:
                    yield chunk.text

        # Process chunks for citations
        async for chunk in self._process_chunk(stream()):
            match chunk:
                case TextContent():
                    yield chunk
                case AxiomCitationCandidate() as candidate:
                    # Validate axiom citation against store
                    axiom = self.axiom_store.get(id=candidate.id)
                    if axiom:
                        yield AxiomCitationContent(item=axiom)
                    else:
                        # If axiom not found, yield as plain text
                        yield TextContent(content=candidate.text)
                case RealityCitationCandidate() as candidate:
                    # Validate reality citation against local store
                    reality_statement = reality_store.get(candidate.id)
                    if reality_statement:
                        yield RealityCitationContent(item=reality_statement)
                    else:
                        # If reality not found, yield as plain text
                        yield TextContent(content=candidate.text)
