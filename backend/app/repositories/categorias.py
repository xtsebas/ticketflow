from uuid import UUID

from app.db.client import get_client


def listar() -> list[dict]:
    respuesta = get_client().table("categorias").select("*").order("tipo").order("nombre").execute()
    return respuesta.data


def obtener(categoria_id: UUID) -> dict | None:
    respuesta = get_client().table("categorias").select("*").eq("id", str(categoria_id)).limit(1).execute()
    return respuesta.data[0] if respuesta.data else None
