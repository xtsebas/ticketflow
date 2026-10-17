from uuid import UUID

from fastapi import APIRouter

from app.schemas.comentario import ComentarioCreate, ComentarioOut
from app.services import tickets as servicio

router = APIRouter(prefix="/tickets/{ticket_id}/comentarios", tags=["comentarios"])


@router.post("", response_model=ComentarioOut, status_code=201)
def crear_comentario(ticket_id: UUID, datos: ComentarioCreate):
    return servicio.agregar_comentario(ticket_id, datos)
