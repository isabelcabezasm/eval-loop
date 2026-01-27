# Exposes the '/generate' endpoint

import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import (
    Base64Bytes,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    TypeAdapter,
)

from core.dependencies import qa_engine
from core.qa_engine import (
    AxiomCitationContent,
    RealityCitationContent,
    TextContent,
    UserSessionId,
)
from core.reality import RealityStatement, load_from_json


def _parse_reality(value: object) -> list[RealityStatement] | object:
    if not isinstance(value, bytes):
        # Not a blob, hence needs not be parsed
        return value

    return load_from_json(value.decode("utf-8"))


def _parse_base64(value: Any) -> bytes | object:
    if not isinstance(value, str):
        # Not a base64-string, hence needs not be parsed but can be passed
        # along the pipeline
        return value

    result = TypeAdapter(  # pyright: ignore [reportUnknownVariableType]
        Base64Bytes
    ).validate_python(value)
    return result  # pyright: ignore [reportUnknownVariableType]


# Note the following about the ordering of the validators:
# https://docs.pydantic.dev/latest/concepts/validators/#ordering-of-validators
Reality = Annotated[
    list[RealityStatement],
    BeforeValidator(_parse_reality),
    BeforeValidator(_parse_base64),
]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(..., min_length=1, description="Question to answer")
    reality: Reality | None = Field(description="Current reality (optional)")
    session_id: str = Field(..., min_length=1, description="User session ID")


class TextResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["text"] = Field(default="text")
    text: str


class AxiomCitationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["axiom_citation"] = Field(default="axiom_citation")
    id: str
    description: str


class RealityCitationResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["reality_citation"] = Field(default="reality_citation")
    id: str
    description: str


router = APIRouter()


@router.post("/generate")
async def generate(request: GenerateRequest):
    """
    Generate streaming responses for constitutional QA queries.

    Processes questions with constitutional axioms and reality context,
    streaming back text content and citations as newline-delimited JSON.

    Example Request:
        {
            "question": "How does inflation affect interest rates in
            Switzerland?",
            "reality": [
                {
                    "id": "R-001", "description": "Current inflation rate in
                    Switzerland is 2.1% as of Q3 2024."
                }
            ]
        }

    Example Response (streaming ndjson):
        {"type": "text", "text": "Based on economic principles..."}
        {"type": "axiom_citation",
        "id": "A-005",
        "description": "Interest rates..."}
        {"type": "reality_citation", "id": "R-001",
        "description": "Current inflation..."}
    """

    async def stream():
        """
        Generate streaming NDJSON response from QA engine chunks.

        Yields newline-delimited JSON chunks containing text content
        and citation responses.
        """
        try:
            async for chunk in qa_engine().invoke_streaming(
                question=request.question,
                session_id=UserSessionId(request.session_id),
                reality=request.reality or [],
            ):
                match chunk:
                    case TextContent():
                        response = TextResponse(text=chunk.content)
                    case AxiomCitationContent():
                        response = AxiomCitationResponse(
                            id=chunk.item.id,
                            description=chunk.item.description,
                        )
                    case RealityCitationContent():
                        response = RealityCitationResponse(
                            id=chunk.item.id,
                            description=chunk.item.description,
                        )

                yield f"{response.model_dump_json()}\n"
        except Exception as e:
            # Send error as final chunk
            error_response = {"type": "error", "message": str(e)}
            yield f"{json.dumps(error_response)}\n"
            raise

    return StreamingResponse(stream(), media_type="application/x-ndjson")


class RestartRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str = Field(..., min_length=1, description="User session ID")


@router.post("/restart")
async def restart(request: RestartRequest):
    """Reset the conversation thread for a specific session.

    Clears the conversation history by creating a new thread for the session.
    """
    await qa_engine().reset_thread(UserSessionId(request.session_id))
    return {"status": "ok"}
