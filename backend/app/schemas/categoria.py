from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import Tipo


class CategoriaOut(BaseModel):
    id: UUID
    slug: str
    nombre: str
    tipo: Tipo
    descripcion: str
    quien_reporta: str
