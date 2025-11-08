from core.reality import RealityId, RealityStatement


def reality_statement(id: int = 1, /) -> RealityStatement:
    return RealityStatement(
        id=RealityId(f"R-{id}"),
        description=f"Description {id}",
    )
