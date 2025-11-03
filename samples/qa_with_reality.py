"""
Example demonstrating streaming QA with reality statements.

This example shows how to:
1. Define reality statements for macro-economic context
2. Use streaming API with reality statements
3. Handle text and citation content in real-time
"""

import asyncio

from core.dependencies import qa_engine
from core.qa_engine import CitationContent, TextContent
from core.reality import RealityId, RealityStatement


async def main():
    """Demonstrate streaming QA with reality statements."""
    # Initialize the QA engine
    engine = qa_engine()

    # Define reality statements (macro-economic conditions)
    reality = [
        RealityStatement(
            id=RealityId("REALITY-001"),
            entity="Economy",
            attribute="Inflation Rate",
            value="High",
            number="7.5%",
            description="Current inflation is elevated at 7.5%.",
        ),
        RealityStatement(
            id=RealityId("REALITY-002"),
            entity="Healthcare",
            attribute="Medical Cost Trend",
            value="Increasing",
            number="12% YoY",
            description="Medical costs rising at 12% year-over-year.",
        ),
    ]

    question = (
        "How might premium rates be affected for someone with a chronic condition?"
    )

    print("Streaming QA with Reality Example")
    print("=" * 80)
    print(f"Question: {question}\n")
    print("Reality Context:")
    for statement in reality:
        print(f"  [{statement.id}] {statement.attribute}: {statement.number}")
    print("-" * 80)

    # Collect citations
    citations = []

    # Stream the response
    async for chunk in engine.invoke_streaming(question, reality=reality):
        match chunk:
            case TextContent():
                print(chunk.content, end="", flush=True)
            case CitationContent():
                print(f"[{chunk.axiom.id}]", end="", flush=True)
                if chunk.axiom not in citations:
                    citations.append(chunk.axiom)

    print("\n" + "-" * 80)

    # Display references
    if citations:
        print("\nReferences:")
        for axiom in citations:
            print(f"  [{axiom.id}] {axiom.subject}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
