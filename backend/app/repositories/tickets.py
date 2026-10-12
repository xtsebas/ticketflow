from uuid import UUID


def crear(datos: dict) -> dict:
    raise NotImplementedError


def listar(
    estado: str | None = None,
    prioridad: str | None = None,
    nivel: str | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
) -> list[dict]:
    raise NotImplementedError


def obtener(ticket_id: UUID) -> dict | None:
    raise NotImplementedError


def actualizar(ticket_id: UUID, cambios: dict) -> dict | None:
    raise NotImplementedError
