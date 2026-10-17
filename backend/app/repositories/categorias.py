from uuid import UUID

from app.db.client import get_client


def listar() -> list[dict]:
    respuesta = get_client().table("categorias").select("*").order("tipo").order("nombre").execute()
    return respuesta.data


def obtener(categoria_id: UUID) -> dict | None:
    raise NotImplementedError
