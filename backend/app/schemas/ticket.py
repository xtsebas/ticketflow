from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import (
    EscalamientoJerarquico,
    Estado,
    Impacto,
    Nivel,
    Prioridad,
    Urgencia,
)
from app.schemas.categoria import CategoriaOut
from app.schemas.comentario import ComentarioOut


class TicketCreate(BaseModel):
    titulo: str
    descripcion: str
    categoria_id: UUID
    tags: list[str] = Field(default_factory=list)
    impacto: Impacto
    urgencia: Urgencia
    solicitante: str


class TicketUpdate(BaseModel):
    estado: Estado | None = None
    prioridad: Prioridad | None = None
    categoria_id: UUID | None = None
    tags: list[str] | None = None
    nivel: Nivel | None = None
    escalamiento_jerarquico: EscalamientoJerarquico | None = None


class TicketOut(BaseModel):
    id: UUID
    titulo: str
    descripcion: str
    categoria_id: UUID
    tags: list[str]
    impacto: Impacto
    urgencia: Urgencia
    prioridad: Prioridad | None
    estado: Estado
    nivel: Nivel
    escalamiento_jerarquico: EscalamientoJerarquico | None
    solicitante: str
    vence_respuesta_en: datetime | None
    vence_resolucion_en: datetime | None
    creado_en: datetime
    actualizado_en: datetime


class TicketDetalleOut(TicketOut):
    categoria: CategoriaOut
    comentarios: list[ComentarioOut]
