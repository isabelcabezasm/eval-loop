"""
QA Engine for constitutional AI assistant.

This module provides the QAEngine class that handles question-answering
using Azure OpenAI with constitution-based prompting via the Microsoft Agent Framework.
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from functools import cache
from typing import Literal

from agent_framework import ChatAgent
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, computed_field

from core.axiom_store import Axiom, AxiomId, AxiomStore
from core.paths import root


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


async def process_chunk(
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


@cache
def load_template(file: str) -> Template:
    """Load a Jinja2 template from the prompts directory."""
    return Environment(
        loader=FileSystemLoader(root() / "src/core/prompts")
    ).get_template(file)


class QAEngine:
    """
    Question-Answering engine for constitutional queries.

    This class handles the orchestration of prompts, constitution loading,
    and interaction with Azure OpenAI via the Microsoft Agent Framework to provide
    contextualized responses based on predefined axioms.

    Attributes:
        agent (ChatAgent): The chat agent for model inference.
        axiom_store (AxiomStore | None): Storage for axioms/constitution data.
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
            axiom_store: Optional storage for axioms (defaults to loading from file).
        """
        self.agent = agent
        self.axiom_store = axiom_store

    def _load_constitution_data(self) -> list[Axiom]:
        """
        Load constitution data from JSON file.

        Returns:
            List of axioms from the constitution JSON file.
        """
        constitution_file = root() / "data/constitution.json"
        with open(constitution_file, encoding="utf-8") as f:
            return [Axiom(**item) for item in json.load(f)]

    def _load_and_format_constitution(self) -> str:
        """
        Load the constitution template and format it with axiom data.

        Returns:
            Formatted constitution text with axioms.
        """
        template = load_template("constitution.j2")
        axioms = self.axiom_store.list()
        return template.render(axioms=[asdict(axiom) for axiom in axioms])

    def _load_and_format_user_prompt(self, question: str) -> str:
        """
        Load and format the user prompt with constitution and question.

        Args:
            question: The user's question to be answered.

        Returns:
            Formatted user prompt with constitution and question.
        """
        template = load_template("user_prompt.j2")

        # Get formatted constitution
        constitution = self._load_and_format_constitution()

        # Render template with constitution and question
        return template.render(constitution=constitution, question=question)

    async def invoke(self, question: str) -> str:
        """
        Process a user question and generate a response using Azure OpenAI.

        This method collects all chunks from the streaming response and returns
        the complete response as a single string.

        Args:
            question: The user's question.

        Returns:
            The complete AI-generated response based on the constitution and prompts.

        Note:
            TODO: Add support for conversation history with Message list.
            TODO: Add support for reality
        """
        # Collect all chunks from the streaming response
        result = ""
        async for chunk in self.invoke_streaming(question):
            result += chunk.content

        return result

    async def invoke_streaming(
        self,
        question: str,
    ) -> AsyncIterator[TextContent | CitationContent]:
        """
        Process a user question and stream the response with citation detection.

        This method:
        1. Loads and formats the constitution with axiom data
        2. Prepares the system prompt (used as agent instructions)
        3. Formats the user prompt with the question and constitution
        4. Creates a ChatAgent with system instructions
        5. Streams the response from Azure OpenAI via the Agent Framework
        6. Parses citations in the format [AXIOM-XXX] and yields them as CitationContent
        7. Yields regular text as TextContent

        Args:
            question: The user's question.

        Yields:
            TextContent or CitationContent chunks as they are streamed and parsed.

        Note:
            TODO: Add support for conversation history with Message list.
            TODO: Add support for reality
        """
        # Load and format user prompt with constitution and question
        user_prompt = self._load_and_format_user_prompt(question)

        # Create async generator for streaming chunks
        async def stream() -> AsyncIterator[str]:
            async for chunk in self.agent.run_stream(user_prompt):
                if chunk.text:
                    yield chunk.text

        # Process chunks for citations
        async for chunk in process_chunk(stream()):
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
