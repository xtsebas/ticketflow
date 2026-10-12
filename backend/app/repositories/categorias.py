from uuid import UUID


def listar() -> list[dict]:
    raise NotImplementedError


def obtener(categoria_id: UUID) -> dict | None:
    raise NotImplementedError
