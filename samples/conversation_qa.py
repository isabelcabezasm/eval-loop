"""
Example demonstrating multi-turn conversations with the QA Engine.

This example shows how to:
1. Maintain conversation context across multiple questions
2. Use session IDs for conversation isolation
3. Reset a conversation thread
4. Show how the AI retains context from previous exchanges
"""

import asyncio
import uuid

from core.dependencies import qa_engine
from core.qa_engine import (
    AxiomCitationContent,
    RealityCitationContent,
    TextContent,
    UserSessionId,
)


async def stream_response(
    engine, question: str, session_id: UserSessionId
) -> None:
    """Stream and print a response for a given question."""
    print(f"\n\033[1mQ: {question}\033[0m\n")
    print("A: ", end="")

    stream = engine.invoke_streaming(question, session_id=session_id)
    async for chunk in stream:
        match chunk:
            case TextContent():
                print(chunk.content, end="", flush=True)
            case AxiomCitationContent():
                cyan = f"\033[1;36m[{chunk.item.id}]\033[0m"
                print(cyan, end="", flush=True)
            case RealityCitationContent():
                yellow = f"\033[1;33m[{chunk.item.id}]\033[0m"
                print(yellow, end="", flush=True)

    print("\n")


async def main():
    """Demonstrate multi-turn conversation with context retention."""
    # Initialize the QA engine
    engine = qa_engine()

    # Generate a unique session ID for this conversation
    # This session ID maintains conversation context across multiple questions
    session_id = UserSessionId(str(uuid.uuid4()))

    print("=" * 80)
    print("Multi-Turn Conversation Example")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print("-" * 80)

    # First question - establishes context
    await stream_response(
        engine,
        "What is Switzerland's current inflation rate and how does it compare "
        "to the central bank's typical target?",
        session_id,
    )

    # Follow-up question - references previous context
    # The AI should remember we were discussing Switzerland's inflation
    await stream_response(
        engine,
        "Given that, how might borrowing costs change in the near future?",
        session_id,
    )

    # Another follow-up - continues the conversation
    await stream_response(
        engine,
        "What would be the implications for mortgage holders?",
        session_id,
    )

    print("=" * 80)
    print("Demonstrating Session Isolation")
    print("=" * 80)

    # Create a NEW session to show isolation
    new_session_id = UserSessionId(str(uuid.uuid4()))
    print(f"New Session ID: {new_session_id}")
    print("-" * 80)

    # This question in a new session won't have context from previous session
    await stream_response(
        engine,
        "What did we discuss about inflation?",
        new_session_id,
    )

    print("=" * 80)
    print("Demonstrating Thread Reset")
    print("=" * 80)

    # Reset the original session thread
    await engine.reset_thread(session_id)
    print(f"Session {session_id} has been reset.")
    print("-" * 80)

    # After reset, the same session_id no longer has context
    await stream_response(
        engine,
        "What did we discuss about inflation?",
        session_id,
    )

    print("=" * 80)
    print("Conversation example complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
