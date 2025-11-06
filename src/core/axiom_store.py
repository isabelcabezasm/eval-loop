import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import NewType

from pydantic import BaseModel

AxiomId = NewType("AxiomId", str)


@dataclass(frozen=True)
class Axiom:
    id: AxiomId
    subject: str
    entity: str
    trigger: str
    conditions: str
    description: str
    category: str


class AxiomStore:
    def __init__(self, axioms: Iterable[Axiom], /):
        super().__init__()
        self._axioms: dict[AxiomId, Axiom] = {axiom.id: axiom for axiom in axioms}

    def get(self, id: AxiomId) -> Axiom | None:
        return self._axioms.get(id)

    def list(self) -> list[Axiom]:
        return list(self._axioms.values())


def load_from_json(json_data: str) -> AxiomStore:
    class RawAxiom(BaseModel):
        id: str
        subject: str
        entity: str
        trigger: str
        conditions: str
        description: str
        category: str

        class Config:
            extra = "ignore"  # Ignore extra fields like 'object', 'link', 'amendments'

    parsed_axioms = {AxiomId(axiom["id"]): RawAxiom.model_validate(axiom) for axiom in json.loads(json_data)}

    return AxiomStore(
        Axiom(
            id=axiom_id,
            subject=parsed_axiom.subject,
            entity=parsed_axiom.entity,
            trigger=parsed_axiom.trigger,
            conditions=parsed_axiom.conditions,
            description=parsed_axiom.description,
            category=parsed_axiom.category,
        )
        for axiom_id, parsed_axiom in parsed_axioms.items()
    )
