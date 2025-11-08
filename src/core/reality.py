import json
from dataclasses import dataclass
from typing import NewType

from pydantic import BaseModel, ConfigDict

RealityId = NewType("RealityId", str)


@dataclass(frozen=True)
class RealityStatement:
    id: RealityId
    description: str


def load_from_json(json_data: str, /) -> list[RealityStatement]:
    class RawRealityStatement(BaseModel):
        model_config = ConfigDict(extra="ignore")  # Ignore extra fields

        id: str
        description: str

    parsed_statements = [
        RawRealityStatement.model_validate(statement)
        for statement in json.loads(json_data)
    ]

    return [
        RealityStatement(
            id=RealityId(statement.id),
            description=statement.description,
        )
        for statement in parsed_statements
    ]
