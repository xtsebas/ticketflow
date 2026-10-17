from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.domain.enums import AutorRol


class ComentarioCreate(BaseModel):
    autor: str
    autor_rol: AutorRol
    contenido: str
    interno: bool = False

    @field_validator("contenido")
    @classmethod
    def contenido_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("contenido no puede estar vacio")
        return valor

    @model_validator(mode="after")
    def interno_solo_agentes(self):
        if self.interno and self.autor_rol == AutorRol.solicitante:
            raise ValueError("solo los agentes pueden crear comentarios internos")
        return self


class ComentarioOut(BaseModel):
    id: UUID
    ticket_id: UUID
    autor: str
    autor_rol: AutorRol
    contenido: str
    interno: bool
    creado_en: datetime
