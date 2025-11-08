"""
Example demonstrating streaming QA with reality statements.

This example shows how to:
1. Define reality statements for macro-economic context
2. Use streaming API with reality statements
3. Handle text, axiom citations, and reality citations in real-time
"""

import asyncio

from core.dependencies import qa_engine
from core.qa_engine import (
    AxiomCitationContent,
    RealityCitationContent,
    TextContent,
)
from core.reality import RealityId, RealityStatement


async def main():
    """Demonstrate streaming QA with reality statements."""
    # Initialize the QA engine
    engine = qa_engine()

    # Define reality statements (macro-economic conditions for Switzerland)
    reality = [
        RealityStatement(
            id=RealityId("R-001"),
            description="Current inflation rate in Switzerland is 2.1% as of Q3 2024.",
        ),
        RealityStatement(
            id=RealityId("R-003"),
            description="The Swiss National Bank (SNB) maintains a policy interest rate of 1.75%.",
        ),
    ]

    question = (
        "How might borrowing costs be affected for someone seeking "
        "a mortgage in Switzerland?"
    )

    print("Streaming QA with Reality Example")
    print("=" * 80)
    print(f"Question: {question}\n")
    print("Reality Context:")
    for statement in reality:
        print(f"  [{statement.id}] {statement.description}")
    print("-" * 80)

    # Collect citations
    axiom_citations = []
    reality_citations = []

    # Stream the response
    async for chunk in engine.invoke_streaming(question, reality=reality):
        match chunk:
            case TextContent():
                print(chunk.content, end="", flush=True)
            case AxiomCitationContent():
                # Print axiom citation ID
                print(f"[{chunk.item.id}]", end="", flush=True)
                if chunk.item not in axiom_citations:
                    axiom_citations.append(chunk.item)
            case RealityCitationContent():
                # Print reality citation ID
                print(f"[{chunk.item.id}]", end="", flush=True)
                if chunk.item not in reality_citations:
                    reality_citations.append(chunk.item)

    print("\n" + "-" * 80)

    # Display references
    if axiom_citations:
        print("\nAxiom References:")
        for axiom in axiom_citations:
            print(f"  [{axiom.id}] {axiom.description}")

    if reality_citations:
        print("\nReality References:")
        for statement in reality_citations:
            print(f"  [{statement.id}] {statement.description}")

    if axiom_citations or reality_citations:
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
