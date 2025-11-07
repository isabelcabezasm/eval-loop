import base64
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from typing import Final

import pytest
from pydantic import ValidationError
from tests.core.reality_test_data import reality_statement

from api.generate import GenerateRequest
from core.reality import RealityStatement

REALITY: Final = [reality_statement(1), reality_statement(2)]


def reality_base64_json(reality: list[RealityStatement]) -> str:
    reality_dicts = [asdict(statement) for statement in reality]
    reality_json = json.dumps(reality_dicts)
    reality_base64 = base64.b64encode(reality_json.encode()).decode()
    return reality_base64


@dataclass(frozen=True)
class RequestFixture:
    question: str
    reality: str


DEFAULT_REQUEST: Final = RequestFixture(
    question="What is the capital of France?",
    reality=reality_base64_json(REALITY),
)


def predicate(predicate: Callable[[GenerateRequest], bool]):
    """Ensures that the type hints are picked up for the assert functions."""

    return predicate


DESERIALIZATION_SUCCESS_TEST_DATA: Final = [
    pytest.param(
        DEFAULT_REQUEST,
        predicate(
            lambda actual: actual
            == GenerateRequest(
                question="What is the capital of France?",
                reality=REALITY,
            )
        ),
        id="Full request payload reality",
    ),
    pytest.param(
        replace(DEFAULT_REQUEST, reality=
                [asdict(statement) for statement in REALITY]),
        predicate(
            lambda actual: actual
            == GenerateRequest(
                question="What is the capital of France?",
                reality=REALITY,
            )
        ),
        id="Full request payload reality as python object",
    ),
    pytest.param(
        replace(DEFAULT_REQUEST, reality=[]),
        predicate(lambda actual: actual.reality == []),
        id="Empty reality",
    ),
]


@pytest.mark.parametrize("input, predicate", DESERIALIZATION_SUCCESS_TEST_DATA)
def test_deserializes_payload_from_json(
    input: RequestFixture, predicate: Callable[[GenerateRequest], bool]
):
    assert predicate(
        GenerateRequest.model_validate_json(json.dumps(asdict(input)))
    )


@pytest.mark.parametrize("input, predicate", DESERIALIZATION_SUCCESS_TEST_DATA)
def test_deserializes_payload_from_python(
    input: RequestFixture, predicate: Callable[[GenerateRequest], bool]
):
    assert predicate(GenerateRequest.model_validate(asdict(input)))


@pytest.mark.parametrize(
    "input, error",
    [
        pytest.param(
            replace(DEFAULT_REQUEST, question=""),
            "String should have at least 1 character",
            id="Empty question",
        ),
    ],
)
def test_deserialization_failures_on_bad_request(
    input: RequestFixture, error: str
):
    with pytest.raises(ValidationError, match=error):
        _ = GenerateRequest.model_validate_json(json.dumps(asdict(input)))
