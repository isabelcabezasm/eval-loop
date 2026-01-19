"""
Example demonstrating how to use the QA Engine non-streaming API.

This example shows how to:
1. Use the non-streaming API to get complete responses
2. Get the full response at once without streaming
3. Use session IDs for conversation isolation
"""

import asyncio
import uuid

from core.dependencies import qa_engine
from core.qa_engine import UserSessionId


async def main():
    """Demonstrate non-streaming (complete) response."""
    # Initialize the QA engine
    engine = qa_engine()

    # Generate a unique session ID for this conversation
    # Each session ID maintains its own conversation thread
    session_id = UserSessionId(str(uuid.uuid4()))

    # Example question
    question = (
        "What would be the economic impact if Switzerland's inflation "
        "rate were to double from current levels?"
    )

    print("Non-Streaming Response Example")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Question: {question}\n")
    print("Response:")
    print("-" * 80)

    # Get complete response with session_id for thread isolation
    response = await engine.invoke(question, session_id=session_id)
    print(response)
    print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
