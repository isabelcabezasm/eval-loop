"""
QA Engine for constitutional AI assistant.

This module provides the QAEngine class that handles question-answering
using Azure OpenAI with constitution-based prompting via the Microsoft Agent Framework.
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from agent_framework import ChatAgent
from pydantic import BaseModel, computed_field

from core.axiom_store import Axiom, AxiomId, AxiomStore
from core.prompt import build_user_prompt
from core.reality import RealityStatement


class Message(BaseModel):
    """Message in a conversation history."""

    role: Literal["user", "assistant"]
    content: str


class CitationContent(BaseModel):
    """Response containing the axiom cited in streaming chunk."""

    axiom: Axiom

    @computed_field
    @property
    def content(self) -> str:
        """Return formatted axiom ID."""
        return f"[{self.axiom.id}]"


class TextContent(BaseModel):
    """Response containing simple text content from a streaming chunk."""

    content: str


@dataclass(frozen=True)
class CitationCandidate:
    """Candidate citation found in streaming text."""

    id: AxiomId
    text: str


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

    async def _process_chunk(
        self,
        chunks: AsyncIterator[str],
    ) -> AsyncIterator[TextContent | CitationCandidate]:
        """
        Process a series of chunks and returns text or parsed references.

        Args:
            chunks: Text chunk content to process

        Returns:
            AsyncIterator of TextContent or CitationCandidate instances
        """
        buffer = ""

        async for chunk in chunks:
            buffer += chunk

            while match := re.search(r"\[(AXIOM-\d+)\]", buffer):
                # Yield text before the citation
                yield TextContent(content=buffer[: match.start()])
                # Yield the citation candidate
                yield CitationCandidate(id=AxiomId(match.group(1)), text=match.group(0))

                buffer = buffer[match.end() :]

            # Yield buffer if it doesn't contain an incomplete citation
            if buffer and (("[" not in buffer) or ("]" in buffer)):
                yield TextContent(content=buffer)
                buffer = ""

        # Yield remaining buffer
        if buffer:
            yield TextContent(content=buffer)

    async def invoke(
        self, question: str, reality: list[RealityStatement] | None = None
    ) -> str:
        """
        Process a user question and generate a response using Azure OpenAI.

        This method collects all chunks from the streaming response and returns
        the complete response as a single string.

        Args:
            question: The user's question.
            reality: Optional list of reality statements to include in the prompt.

        Returns:
            The complete AI-generated response based on the constitution and prompts.

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
        Process a user question and stream the response with citation detection.

        This method:
        1. Loads and formats the constitution with axiom data
        2. Prepares the system prompt (used as agent instructions)
        3. Formats the user prompt with the question, constitution, and reality
        4. Creates a ChatAgent with system instructions
        5. Streams the response from Azure OpenAI via the Agent Framework
        6. Parses citations in the format [AXIOM-XXX] and yields them as CitationContent
        7. Yields regular text as TextContent

        Args:
            question: The user's question.
            reality: Optional list of reality statements to include in the prompt.

        Yields:
            TextContent or CitationContent chunks as they are streamed and parsed.

        Note:
            TODO: Add support for conversation history with Message list.
        """
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
                case CitationCandidate() as candidate:
                    # Validate citation against axiom store
                    axiom_store = (
                        self.axiom_store
                        if isinstance(self.axiom_store, AxiomStore)
                        else None
                    )
                    if axiom_store and (axiom := axiom_store.get(id=candidate.id)):
                        yield CitationContent(axiom=axiom)
                    else:
                        # If axiom not found, yield as plain text
                        yield TextContent(content=candidate.text)
