from app.db.client import get_client

TAMANO_PAGINA = 1000


def listar_campos_tickets() -> list[dict]:
    """Solo los campos usados en las estadisticas, paginando para no truncar en 1000 filas."""
    filas: list[dict] = []
    desde = 0
    while True:
        pagina = (
            get_client()
            .table("tickets")
            .select("categoria_id, estado, prioridad, tags")
            .order("creado_en")
            .order("id")
            .range(desde, desde + TAMANO_PAGINA - 1)
            .execute()
            .data
        )
        filas.extend(pagina)
        if len(pagina) < TAMANO_PAGINA:
            return filas
        desde += TAMANO_PAGINA
