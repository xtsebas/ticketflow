from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.comentario import ComentarioCreate, ComentarioOut

router = APIRouter(prefix="/tickets/{ticket_id}/comentarios", tags=["comentarios"])


@router.post("", response_model=ComentarioOut, status_code=201)
def crear_comentario(ticket_id: UUID, datos: ComentarioCreate):
    raise HTTPException(status_code=501, detail="Not Implemented")
