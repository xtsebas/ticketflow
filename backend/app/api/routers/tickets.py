from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.domain.enums import Estado, Nivel, Prioridad
from app.schemas.ticket import TicketCreate, TicketDetalleOut, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=201)
def crear_ticket(datos: TicketCreate):
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("", response_model=list[TicketOut])
def listar_tickets(
    estado: Estado | None = None,
    prioridad: Prioridad | None = None,
    nivel: Nivel | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
):
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.get("/{ticket_id}", response_model=TicketDetalleOut)
def obtener_ticket(ticket_id: UUID):
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.patch("/{ticket_id}", response_model=TicketOut)
def actualizar_ticket(ticket_id: UUID, cambios: TicketUpdate):
    raise HTTPException(status_code=501, detail="Not Implemented")
