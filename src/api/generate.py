# Exposes the '/generate' endpoint

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
)
from core.reality import RealityStatement, load_from_json


def _parse_reality(value: object) -> list[RealityStatement] | object:
    if not isinstance(value, bytes):
        # Not a blob, hence needs not be parsed
        return value

    return load_from_json(value.decode("utf-8"))


def _parse_base64(value: Any) -> bytes | object:
    if not isinstance(value, str):
        # Not a base64-string, hence needs not be parsed
        # but can be passed along the pipeline
        return value

    return TypeAdapter(Base64Bytes).validate_python(value)  # pyright: ignore [reportUnknownVariableType]


# Note the following about the ordering of the validators:
# https://docs.pydantic.dev/latest/concepts/validators/#ordering-of-validators
Reality = Annotated[
    list[RealityStatement],
    BeforeValidator(_parse_reality),
    BeforeValidator(_parse_base64),
]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(
        ..., min_length=1, description="Question must not be empty"
    )
    reality: Reality | None = Field(description="Current reality")


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
    entity: str
    attribute: str
    value: str
    number: str
    description: str


router = APIRouter()


@router.post("/generate")
async def generate(request: GenerateRequest):
    """
    Generate streaming responses for constitutional QA queries.

    Processes questions with context and streams back text content
    and citations as newline-delimited JSON.
    """

    async def stream():
        async for chunk in qa_engine().invoke_streaming(
            question=request.question, reality=request.reality or []
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
                        entity=chunk.item.entity,
                        attribute=chunk.item.attribute,
                        value=chunk.item.value,
                        number=chunk.item.number,
                        description=chunk.item.description,
                    )

            yield f"{response.model_dump_json()}\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")
