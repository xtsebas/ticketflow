from pydantic import BaseModel


class ConteoOut(BaseModel):
    clave: str
    total: int


class EstadisticasOut(BaseModel):
    por_categoria: list[ConteoOut]
    por_tag: list[ConteoOut]
    por_prioridad: list[ConteoOut]
    por_estado: list[ConteoOut]
