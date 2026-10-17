from collections import Counter
from uuid import UUID

from app.core.errors import RecursoNoEncontrado, TransicionInvalida
from app.domain.enums import AutorRol, Estado, Nivel, Prioridad
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import estadisticas as repo_estadisticas
from app.repositories import tickets as repo_tickets
from app.schemas.comentario import ComentarioCreate
from app.schemas.ticket import TicketCreate, TicketUpdate


TRANSICIONES_ESTADO = {
    Estado.abierto: {Estado.en_progreso},
    Estado.en_progreso: {Estado.resuelto},
    Estado.resuelto: {Estado.cerrado, Estado.en_progreso},
    Estado.cerrado: set(),
}


def _texto_escalamiento(ticket: dict, cambios: dict, motivo: str | None) -> str | None:
    partes = []
    if "nivel" in cambios and cambios["nivel"] != ticket["nivel"]:
        partes.append(f"{ticket['nivel']} a {cambios['nivel']}")
    nuevo = cambios.get("escalamiento_jerarquico")
    if "escalamiento_jerarquico" in cambios and nuevo != ticket["escalamiento_jerarquico"]:
        partes.append(f"jerarquico {ticket['escalamiento_jerarquico'] or 'ninguno'} a {nuevo}")
    if not partes:
        return None
    texto = f"Escalamiento: {', '.join(partes)}."
    return f"{texto} Motivo: {motivo}" if motivo else texto


def crear_ticket(datos: TicketCreate) -> dict:
    if repo_categorias.obtener(datos.categoria_id) is None:
        raise RecursoNoEncontrado("Categoria no encontrada")
    nuevo = datos.model_dump(mode="json")
    nuevo["estado"] = Estado.abierto.value
    nuevo["nivel"] = Nivel.N1.value
    nuevo["prioridad"] = None
    return repo_tickets.crear(nuevo)


def listar_tickets(
    estado: str | None = None,
    prioridad: str | None = None,
    nivel: str | None = None,
    categoria_id: UUID | None = None,
    tag: str | None = None,
) -> list[dict]:
    return repo_tickets.listar(estado, prioridad, nivel, categoria_id, tag)


def obtener_ticket(ticket_id: UUID, rol: AutorRol = AutorRol.solicitante) -> dict:
    ticket = repo_tickets.obtener(ticket_id)
    if ticket is None:
        raise RecursoNoEncontrado("Ticket no encontrado")
    comentarios = repo_comentarios.listar_por_ticket(ticket_id)
    if rol == AutorRol.solicitante:
        comentarios = [c for c in comentarios if not c["interno"]]
    ticket["comentarios"] = comentarios
    return ticket


def actualizar_ticket(ticket_id: UUID, datos: TicketUpdate) -> dict:
    ticket = repo_tickets.obtener(ticket_id)
    if ticket is None:
        raise RecursoNoEncontrado("Ticket no encontrado")
    cambios = datos.campos_actualizables()
    if "estado" in cambios:
        actual, nuevo = Estado(ticket["estado"]), Estado(cambios["estado"])
        if nuevo not in TRANSICIONES_ESTADO[actual]:
            raise TransicionInvalida(f"Transicion de estado no permitida: {actual.value} a {nuevo.value}")
    if "categoria_id" in cambios and repo_categorias.obtener(cambios["categoria_id"]) is None:
        raise RecursoNoEncontrado("Categoria no encontrada")
    actualizado = repo_tickets.actualizar(ticket_id, cambios)
    texto = _texto_escalamiento(ticket, cambios, datos.motivo)
    if texto:
        repo_comentarios.crear(
            ticket_id,
            {"autor": "sistema", "autor_rol": AutorRol.agente.value, "contenido": texto, "interno": True},
        )
    return actualizado


def agregar_comentario(ticket_id: UUID, datos: ComentarioCreate) -> dict:
    if repo_tickets.obtener(ticket_id) is None:
        raise RecursoNoEncontrado("Ticket no encontrado")
    return repo_comentarios.crear(ticket_id, datos.model_dump(mode="json"))


def _conteos(claves: list[str], valores) -> list[dict]:
    conteo = Counter(valores)
    return [{"clave": clave, "total": conteo[clave]} for clave in claves]


def obtener_estadisticas() -> dict:
    tickets = repo_estadisticas.listar_campos_tickets()
    categorias = repo_categorias.listar()
    slug_por_id = {c["id"]: c["slug"] for c in categorias}

    por_prioridad = _conteos([p.value for p in Prioridad], (t["prioridad"] for t in tickets))
    sin_prioridad = sum(1 for t in tickets if t["prioridad"] is None)
    if sin_prioridad:
        por_prioridad.append({"clave": "sin_prioridad", "total": sin_prioridad})

    por_tag = Counter(tag for t in tickets for tag in t["tags"])
    return {
        "por_categoria": _conteos([c["slug"] for c in categorias], (slug_por_id.get(t["categoria_id"]) for t in tickets)),
        "por_tag": [{"clave": tag, "total": total} for tag, total in por_tag.most_common()],
        "por_prioridad": por_prioridad,
        "por_estado": _conteos([e.value for e in Estado], (t["estado"] for t in tickets)),
    }
