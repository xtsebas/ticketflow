from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import usuario_actual
from app.schemas.comentario import ComentarioCreate, ComentarioOut
from app.services import tickets as servicio

router = APIRouter(prefix="/tickets/{ticket_id}/comentarios", tags=["comentarios"])


@router.post("", response_model=ComentarioOut, status_code=201)
def crear_comentario(ticket_id: UUID, datos: ComentarioCreate, usuario: str | None = Depends(usuario_actual)):
    return servicio.agregar_comentario(ticket_id, datos, usuario)
