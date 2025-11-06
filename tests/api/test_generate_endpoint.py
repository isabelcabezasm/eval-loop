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
    Create realistic macro-economic reality statements.

    Encode them as base64.
    """
    reality: Final = [
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
        RealityStatement(
            id=RealityId("REALITY-003"),
            entity="Currency",
            attribute="US Dollar Index",
            value="Strong",
            number="105.2",
            description="US Dollar showing strength amid global uncertainty.",
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
    # arrange - realistic question about insurance and economic factors
    request = {
        "question": (
            "How might premium rates be affected for someone with "
            "a chronic condition given current economic trends?"
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
    has_axiom_citation = False
    has_reality_citation = False
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
            assert "subject" in obj, "Axiom citation missing 'subject' field"
            assert "entity" in obj, "Axiom citation missing 'entity' field"
            assert "trigger" in obj, "Axiom citation missing 'trigger' field"
            assert "conditions" in obj, (
                "Axiom citation missing 'conditions' field"
            )
            assert "description" in obj, (
                "Axiom citation missing 'description' field"
            )
            assert "category" in obj, "Axiom citation missing 'category' field"

            # Validate id format
            assert obj["id"].startswith("AXIOM-"), (
                f"Axiom ID should start with 'AXIOM-': {obj['id']}"
            )
            has_axiom_citation = True

        elif obj["type"] == "reality_citation":
            # Reality citation (context reference) - validate structure
            assert "id" in obj, "Reality citation missing 'id' field"
            assert "entity" in obj, "Reality citation missing 'entity' field"
            assert "attribute" in obj, (
                "Reality citation missing 'attribute' field"
            )
            assert "value" in obj, "Reality citation missing 'value' field"
            assert "number" in obj, "Reality citation missing 'number' field"
            assert "description" in obj, (
                "Reality citation missing 'description' field"
            )

            # Validate id format
            assert obj["id"].startswith("REALITY-"), (
                f"Reality ID should start with 'REALITY-': {obj['id']}"
            )
            has_reality_citation = True

        else:
            pytest.fail(f"Unexpected response type '{obj['type']}': {obj}")

    # Validate we got meaningful content
    assert has_text, "Response should contain text content"

    # Check that we got substantial text (not just citations)
    combined_text = "".join(text_chunks)
    assert len(combined_text) > 20, (
        "Response should contain substantial text content"
    )

    # Constitution citations should always appear since we're asking
    # about health-related topics
    assert has_axiom_citation, (
        "Response should reference constitution axioms "
        "for this health/insurance question"
    )

    # Reality citations should only appear when reality context
    # is provided
    if reality():
        assert has_reality_citation, (
            "Response should reference reality statements "
            "when context is provided"
        )
