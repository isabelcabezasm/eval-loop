from core.reality import RealityId, RealityStatement


def reality_statement(id: int = 1, /) -> RealityStatement:
    return RealityStatement(
        id=RealityId(f"R-{id}"),
        entity=f"Subject {id}",
        attribute=f"Attribute {id}",
        value=f"Value {id}",
        number=f"{id}",
        description=f"Description {id}",
    )
