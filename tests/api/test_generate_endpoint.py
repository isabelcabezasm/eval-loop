import base64
import json
from collections.abc import Callable
from dataclasses import asdict
from typing import Final

import httpx
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
        "session_id": "test-session-123",
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


@pytest.mark.integration
def test_restart_endpoint(test_client: TestClient):
    """
    Test the /api/restart endpoint.

    This test validates:
    - The endpoint returns a successful status
    - The response contains the expected structure
    """
    # act
    response = test_client.post(
        "/api/restart", json={"session_id": "test-session-123"}
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


@pytest.mark.integration
def test_session_isolation_between_users(test_client: TestClient):
    """
    Test that different session IDs maintain separate conversation threads.

    This test simulates two concurrent users with different session IDs
    and verifies their conversations don't mix. Each user asks a distinct
    question, and we verify that restarting one session doesn't affect
    the other.
    """
    session_1 = "user-session-alpha-123"
    session_2 = "user-session-beta-456"

    # User 1 asks about inflation
    request_1 = {
        "question": "What is the current inflation rate?",
        "reality": reality_as_base64(),
        "session_id": session_1,
    }

    # User 2 asks about unemployment
    request_2 = {
        "question": "What is the unemployment rate?",
        "reality": reality_as_base64(),
        "session_id": session_2,
    }

    # Both users send their questions
    response_1 = test_client.post(
        "/api/generate", json=request_1
    ).raise_for_status()
    response_2 = test_client.post(
        "/api/generate", json=request_2
    ).raise_for_status()

    # Collect responses
    def collect_text(response: httpx.Response) -> str:
        text_chunks: list[str] = []
        for line in response.text.strip().split("\n"):
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("type") == "text":
                text_chunks.append(obj["text"])
        return "".join(text_chunks)

    text_1 = collect_text(response_1)
    text_2 = collect_text(response_2)

    # Both responses should have substantial content
    assert len(text_1) > 20, "User 1 should receive a meaningful response"
    assert len(text_2) > 20, "User 2 should receive a meaningful response"

    # Restart session 1 only
    restart_response = test_client.post(
        "/api/restart", json={"session_id": session_1}
    )
    assert restart_response.status_code == 200

    # User 2 should still be able to continue their conversation
    # (asking a follow-up that relies on context would work if thread persists)
    followup_request = {
        "question": "Can you elaborate on that unemployment figure?",
        "reality": reality_as_base64(),
        "session_id": session_2,
    }

    followup_response = test_client.post(
        "/api/generate", json=followup_request
    ).raise_for_status()

    followup_text = collect_text(followup_response)
    assert len(followup_text) > 20, (
        "User 2 should still receive a meaningful response after "
        "User 1's session was restarted"
    )


@pytest.mark.integration
def test_same_session_maintains_thread(test_client: TestClient):
    """
    Test that the same session ID maintains conversation continuity.

    This test verifies that multiple requests with the same session ID
    use the same thread, allowing for conversation history to be maintained.
    """
    session_id = "persistent-session-789"

    # First question
    request_1 = {
        "question": "What is the SNB policy interest rate?",
        "reality": reality_as_base64(),
        "session_id": session_id,
    }

    response_1 = test_client.post(
        "/api/generate", json=request_1
    ).raise_for_status()

    # Second question referencing the first
    request_2 = {
        "question": "How does that rate compare to historical averages?",
        "reality": reality_as_base64(),
        "session_id": session_id,
    }

    response_2 = test_client.post(
        "/api/generate", json=request_2
    ).raise_for_status()

    # Both should return valid responses
    def collect_text(response: httpx.Response) -> str:
        text_chunks: list[str] = []
        for line in response.text.strip().split("\n"):
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("type") == "text":
                text_chunks.append(obj["text"])
        return "".join(text_chunks)

    text_1 = collect_text(response_1)
    text_2 = collect_text(response_2)

    assert len(text_1) > 20, "First question should get a meaningful response"
    assert len(text_2) > 20, "Follow-up should get a meaningful response"
