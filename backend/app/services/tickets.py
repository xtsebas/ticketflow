from uuid import UUID

from app.schemas.comentario import ComentarioCreate
from app.schemas.ticket import TicketCreate, TicketUpdate


def crear_ticket(datos: TicketCreate) -> dict:
    raise NotImplementedError


def listar_tickets(
    estado: str | None = None,
    prioridad: str | None = None,
    nivel: str | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
) -> list[dict]:
    raise NotImplementedError


def obtener_ticket(ticket_id: UUID) -> dict:
    raise NotImplementedError


def actualizar_ticket(ticket_id: UUID, cambios: TicketUpdate) -> dict:
    raise NotImplementedError


def agregar_comentario(ticket_id: UUID, datos: ComentarioCreate) -> dict:
    raise NotImplementedError


def obtener_estadisticas() -> dict:
    raise NotImplementedError
