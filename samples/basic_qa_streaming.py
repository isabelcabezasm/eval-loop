"""
Example demonstrating how to use the QA Engine streaming API.

This example shows how to:
1. Use the streaming API to get real-time responses
2. Handle text content, axiom citations, and reality citations
3. Process citations to display axiom information
"""

import asyncio

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
        "What if I start exercising regularly and lose 20 pounds - "
        "how would that affect my future premium and coverage?"
    )

    print("Streaming Response Example")
    print("=" * 80)
    print(f"Question: {question}\n")
    print("Response:")
    print("-" * 80)

    # Collect citations for reference section
    axiom_citations = []
    reality_citations = []

    # Stream the response
    async for chunk in engine.invoke_streaming(question):
        match chunk:
            case TextContent():
                # Print text content as it arrives
                print(chunk.content, end="", flush=True)
            case AxiomCitationContent():
                # Print axiom citation with cyan color
                print(f"\033[1;36m[{chunk.item.id}]\033[0m", end="", flush=True)
                if chunk.axiom not in axiom_citations:
                    axiom_citations.append(chunk.axiom)
            case RealityCitationContent():
                # Print reality citation with magenta color
                print(f"\033[1;35m[{chunk.item.id}]\033[0m", end="", flush=True)
                if chunk.reality not in reality_citations:
                    reality_citations.append(chunk.reality)

    print("\n" + "-" * 80)

    # Display references section if there are axiom citations
    if axiom_citations:
        print("\n\033[1mAxiom References:\033[0m")
        print("=" * 80)
        for axiom in axiom_citations:
            print(f"\n\033[1;36m[{axiom.id}]\033[0m \033[1m{axiom.subject}\033[0m")
            print(f"  Entity: {axiom.entity}")
            print(f"  Trigger: {axiom.trigger}")
            print(f"  Conditions: {axiom.conditions}")
            print(f"  Description: {axiom.description}")
            print(f"  \033[2mCategory: {axiom.category}\033[0m")
        print("=" * 80)

    # Display references section if there are reality citations
    if reality_citations:
        print("\n\033[1mReality References:\033[0m")
        print("=" * 80)
        for reality in reality_citations:
            print(
                f"\n\033[1;35m[{reality.id}]\033[0m \033[1m{reality.attribute}\033[0m"
            )
            print(f"  Entity: {reality.entity}")
            print(f"  Value: {reality.value}")
            print(f"  Number: {reality.number}")
            print(f"  Description: {reality.description}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
