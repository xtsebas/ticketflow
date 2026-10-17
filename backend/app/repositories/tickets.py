from uuid import UUID

from app.db.client import get_client


def crear(datos: dict) -> dict:
    respuesta = get_client().table("tickets").insert(datos).execute()
    return respuesta.data[0]


def listar(
    estado: str | None = None,
    prioridad: str | None = None,
    nivel: str | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
) -> list[dict]:
    consulta = get_client().table("tickets").select("*, categorias(nombre)")
    if estado:
        consulta = consulta.eq("estado", estado)
    if prioridad:
        consulta = consulta.eq("prioridad", prioridad)
    if nivel:
        consulta = consulta.eq("nivel", nivel)
    if categoria_id:
        consulta = consulta.eq("categoria_id", str(categoria_id))
    if tag:
        consulta = consulta.contains("tags", [tag])
    filas = consulta.order("prioridad", nullsfirst=False).order("creado_en").execute().data
    for fila in filas:
        fila["categoria_nombre"] = fila.pop("categorias")["nombre"]
    return filas


def obtener(ticket_id: UUID) -> dict | None:
    respuesta = get_client().table("tickets").select("*, categorias(*)").eq("id", str(ticket_id)).limit(1).execute()
    if not respuesta.data:
        return None
    fila = respuesta.data[0]
    fila["categoria"] = fila.pop("categorias")
    return fila


def actualizar(ticket_id: UUID, cambios: dict) -> dict | None:
    raise NotImplementedError
