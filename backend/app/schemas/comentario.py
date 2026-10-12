from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import AutorRol


class ComentarioCreate(BaseModel):
    autor: str
    autor_rol: AutorRol
    contenido: str
    interno: bool = False


class ComentarioOut(BaseModel):
    id: UUID
    ticket_id: UUID
    autor: str
    autor_rol: AutorRol
    contenido: str
    interno: bool
    creado_en: datetime
