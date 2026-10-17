from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.domain.enums import AutorRol, Estado, Nivel, Prioridad
from app.schemas.ticket import TicketCreate, TicketDetalleOut, TicketListadoOut, TicketOut, TicketUpdate
from app.services import tickets as servicio

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=201)
def crear_ticket(datos: TicketCreate):
    try:
        return servicio.crear_ticket(datos)
    except servicio.RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("", response_model=list[TicketListadoOut])
def listar_tickets(
    estado: Estado | None = None,
    prioridad: Prioridad | None = None,
    nivel: Nivel | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
):
    return servicio.listar_tickets(estado, prioridad, nivel, categoria_id, tag)


@router.get("/{ticket_id}", response_model=TicketDetalleOut)
def obtener_ticket(ticket_id: UUID, rol: AutorRol = AutorRol.solicitante):
    try:
        return servicio.obtener_ticket(ticket_id, rol)
    except servicio.RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.patch("/{ticket_id}", response_model=TicketOut)
def actualizar_ticket(ticket_id: UUID, cambios: TicketUpdate):
    try:
        return servicio.actualizar_ticket(ticket_id, cambios)
    except servicio.RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
    except servicio.TransicionInvalida as error:
        raise HTTPException(status_code=409, detail=str(error))
