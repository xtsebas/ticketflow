from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.comentario import ComentarioCreate, ComentarioOut
from app.services import tickets as servicio

router = APIRouter(prefix="/tickets/{ticket_id}/comentarios", tags=["comentarios"])


@router.post("", response_model=ComentarioOut, status_code=201)
def crear_comentario(ticket_id: UUID, datos: ComentarioCreate):
    try:
        return servicio.agregar_comentario(ticket_id, datos)
    except servicio.RecursoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
