"""
Example demonstrating how to use the QA Engine non-streaming API.

This example shows how to:
1. Use the non-streaming API to get complete responses
2. Get the full response at once without streaming
"""

import asyncio

from core.dependencies import qa_engine


async def main():
    """Demonstrate non-streaming (complete) response."""
    # Initialize the QA engine
    engine = qa_engine()

    # Example question
    question = (
        "What would be the economic impact if Switzerland's inflation "
        "rate were to double from current levels?"
    )

    print("Non-Streaming Response Example")
    print("=" * 80)
    print(f"Question: {question}\n")
    print("Response:")
    print("-" * 80)

    # Get complete response
    response = await engine.invoke(question)
    print(response)
    print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
