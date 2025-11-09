"""
Example demonstrating how to use the QA Engine streaming API.

This example shows how to:
1. Use the streaming API to get real-time responses
2. Handle text content and axiom citations
3. Process citations to display axiom information
"""

import asyncio

from core.axiom_store import Axiom
from core.dependencies import qa_engine
from core.qa_engine import (
    AxiomCitationContent,
    RealityCitationContent,
    TextContent,
)


async def main():
    """Demonstrate streaming response with citation handling."""
    # Initialize the QA engine
    engine = qa_engine()

    # Example question
    question = (
        "How would a significant change in the Swiss National Bank's "
        "interest rate policy affect investment decisions?"
    )

    print("Streaming Response Example")
    print("=" * 80)
    print(f"Question: {question}\n")
    print("Response:")
    print("-" * 80)

    # Collect citations for reference section
    axiom_citations: list[Axiom] = []

    # Stream the response
    async for chunk in engine.invoke_streaming(question):
        match chunk:
            case TextContent():
                # Print text content as it arrives
                print(chunk.content, end="", flush=True)
            case AxiomCitationContent():
                # Print axiom citation with cyan color
                print(
                    f"\033[1;36m[{chunk.item.id}]\033[0m",
                    end="",
                    flush=True,
                )
                if chunk.item not in axiom_citations:
                    axiom_citations.append(chunk.item)
            case RealityCitationContent():
                # Skip reality citations in this basic example
                pass

    print("\n" + "-" * 80)

    # Display references section if there are axiom citations
    if axiom_citations:
        print("\n\033[1mAxiom References:\033[0m")
        print("=" * 80)
        for axiom in axiom_citations:
            print(f"\n\033[1;36m[{axiom.id}]\033[0m")
            print(f"  {axiom.description}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
