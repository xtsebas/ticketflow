from uuid import UUID

from app.domain.enums import AutorRol, Estado, Nivel
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import tickets as repo_tickets
from app.schemas.comentario import ComentarioCreate
from app.schemas.ticket import TicketCreate, TicketUpdate


class RecursoNoEncontrado(Exception):
    pass


def crear_ticket(datos: TicketCreate) -> dict:
    if repo_categorias.obtener(datos.categoria_id) is None:
        raise RecursoNoEncontrado("Categoria no encontrada")
    nuevo = datos.model_dump(mode="json")
    nuevo["estado"] = Estado.abierto.value
    nuevo["nivel"] = Nivel.N1.value
    nuevo["prioridad"] = None
    return repo_tickets.crear(nuevo)


def listar_tickets(
    estado: str | None = None,
    prioridad: str | None = None,
    nivel: str | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
) -> list[dict]:
    return repo_tickets.listar(estado, prioridad, nivel, categoria_id, tag)


def obtener_ticket(ticket_id: UUID, rol: AutorRol = AutorRol.solicitante) -> dict:
    ticket = repo_tickets.obtener(ticket_id)
    if ticket is None:
        raise RecursoNoEncontrado("Ticket no encontrado")
    comentarios = repo_comentarios.listar_por_ticket(ticket_id)
    if rol == AutorRol.solicitante:
        comentarios = [c for c in comentarios if not c["interno"]]
    ticket["comentarios"] = comentarios
    return ticket


def actualizar_ticket(ticket_id: UUID, cambios: TicketUpdate) -> dict:
    raise NotImplementedError


def agregar_comentario(ticket_id: UUID, datos: ComentarioCreate) -> dict:
    raise NotImplementedError


def obtener_estadisticas() -> dict:
    raise NotImplementedError
