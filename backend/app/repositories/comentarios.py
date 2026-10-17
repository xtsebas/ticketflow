from uuid import UUID

from app.db.client import get_client


def crear(ticket_id: UUID, datos: dict) -> dict:
    raise NotImplementedError


def listar_por_ticket(ticket_id: UUID) -> list[dict]:
    respuesta = (
        get_client().table("comentarios").select("*").eq("ticket_id", str(ticket_id)).order("creado_en").execute()
    )
    return respuesta.data
