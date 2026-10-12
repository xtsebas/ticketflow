from uuid import UUID


def crear(ticket_id: UUID, datos: dict) -> dict:
    raise NotImplementedError


def listar_por_ticket(ticket_id: UUID) -> list[dict]:
    raise NotImplementedError
