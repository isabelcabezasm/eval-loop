import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import NewType

from pydantic import BaseModel, ConfigDict

AxiomId = NewType("AxiomId", str)


@dataclass(frozen=True)
class Axiom:
    id: AxiomId
    description: str


class AxiomStore:
    def __init__(self, axioms: Iterable[Axiom], /):
        super().__init__()
        self._axioms: dict[AxiomId, Axiom] = {
            axiom.id: axiom for axiom in axioms
        }

    def get(self, id: AxiomId) -> Axiom | None:
        return self._axioms.get(id)

    def list(self) -> list[Axiom]:
        return list(self._axioms.values())


def load_from_json(json_data: str) -> AxiomStore:
    class RawAxiom(BaseModel):
        model_config = ConfigDict(extra="ignore")  # Ignore extra fields

        id: str
        description: str

    parsed_axioms = {
        AxiomId(axiom["id"]): RawAxiom.model_validate(axiom)
        for axiom in json.loads(json_data)
    }

    return AxiomStore(
        Axiom(
            id=axiom_id,
            description=parsed_axiom.description,
        )
        for axiom_id, parsed_axiom in parsed_axioms.items()
    )
