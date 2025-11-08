import base64
import json
from collections.abc import Callable
from dataclasses import asdict
from typing import Final

import pytest
from fastapi.testclient import TestClient

from core.reality import RealityId, RealityStatement


def reality_as_base64():
    """
    Create realistic macro-economic reality statements for Switzerland.

    Encode them as base64.
    """
    reality: Final = [
        RealityStatement(
            id=RealityId("R-001"),
            description=(
                "Current inflation rate in Switzerland is 2.1% as of Q3 2024."
            ),
        ),
        RealityStatement(
            id=RealityId("R-002"),
            description=(
                "Swiss unemployment rate stands at 2.3%, among the "
                "lowest in Europe."
            ),
        ),
        RealityStatement(
            id=RealityId("R-003"),
            description=(
                "The Swiss National Bank (SNB) maintains a policy "
                "interest rate of 1.75%."
            ),
        ),
    ]
    reality_json = json.dumps([asdict(r) for r in reality])
    reality_base64 = base64.b64encode(reality_json.encode()).decode()
    return reality_base64


@pytest.mark.integration
@pytest.mark.parametrize(
    "reality",
    [
        pytest.param(lambda: None, id="No reality"),
        pytest.param(
            reality_as_base64,
            id="With reality",
        ),
    ],
)
def test_generate_endpoint(
    test_client: TestClient,
    reality: Callable[[], str | None],
):
    """
    Test the /api/generate endpoint with and without reality statements.

    This test validates:
    - The endpoint accepts questions and optional reality context
    - Response is streamed as newline-delimited JSON
    - Text responses have correct structure
    - Axiom citations (constitution references) are properly formatted
    - Reality citations (context references) are properly formatted
    """
    # arrange - realistic question about banking and economic factors
    request = {
        "question": (
            "How might interest rate changes affect "
            "borrowing costs given current economic conditions in Switzerland?"
        ),
        "reality": reality(),
    }

    # act
    response = test_client.post(
        "/api/generate", json=request
    ).raise_for_status()

    # assert
    lines = [line for line in response.text.splitlines() if line]

    assert len(lines) > 0, "Response should contain at least one line"

    # Track what we've seen to validate the response contains expected elements
    has_text = False
    text_chunks: list[str] = []

    for line in lines:
        obj = json.loads(line)

        # All responses must have a 'type' field
        assert "type" in obj, f"Response missing 'type' field: {obj}"

        if obj["type"] == "text":
            # Text response - validate structure
            assert "text" in obj, "Text response missing 'text' field"
            assert isinstance(obj["text"], str), "Text field must be a string"
            has_text = True
            text_chunks.append(obj["text"])

        elif obj["type"] == "axiom_citation":
            # Axiom citation (constitution reference) - validate structure
            assert "id" in obj, "Axiom citation missing 'id' field"
            assert "description" in obj, (
                "Axiom citation missing 'description' field"
            )

            # Validate id format
            assert obj["id"].startswith("A-"), (
                f"Axiom ID should start with 'A-': {obj['id']}"
            )

        elif obj["type"] == "reality_citation":
            # Reality citation (context reference) - validate structure
            assert "id" in obj, "Reality citation missing 'id' field"
            assert "description" in obj, (
                "Reality citation missing 'description' field"
            )

            # Validate id format
            assert obj["id"].startswith("R-"), (
                f"Reality ID should start with 'R-': {obj['id']}"
            )

        else:
            pytest.fail(f"Unexpected response type '{obj['type']}': {obj}")

    # Validate we got meaningful content
    assert has_text, "Response should contain text content"

    # Check that we got substantial text (not just citations)
    combined_text = "".join(text_chunks)
    assert len(combined_text) > 20, (
        "Response should contain substantial text content"
    )
