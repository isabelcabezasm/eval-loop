import json
from dataclasses import dataclass
from typing import NewType

from pydantic import BaseModel

RealityId = NewType("RealityId", str)


@dataclass(frozen=True)
class RealityStatement:
    id: RealityId
    entity: str
    attribute: str
    value: str
    number: str
    description: str


def load_from_json(json_data: str, /) -> list[RealityStatement]:
    class RawRealityStatement(BaseModel):
        id: str
        entity: str
        attribute: str
        value: str
        number: str
        description: str

        class Config:
            extra = "ignore"  # Ignore extra fields if present

    parsed_statements = [RawRealityStatement.model_validate(statement) for statement in json.loads(json_data)]

    return [
        RealityStatement(
            id=RealityId(statement.id),
            entity=statement.entity,
            attribute=statement.attribute,
            value=statement.value,
            number=statement.number,
            description=statement.description,
        )
        for statement in parsed_statements
    ]
