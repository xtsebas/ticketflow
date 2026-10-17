import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import tickets as repo_tickets

client = TestClient(app)

CATEGORIA_ID = "00000000-0000-0000-0000-000000000001"
TICKET_ID = "00000000-0000-0000-0000-0000000000a1"
AHORA = "2026-01-01T10:00:00Z"

CATEGORIA = {
    "id": CATEGORIA_ID,
    "slug": "qr_rechazado_en_puerta",
    "nombre": "QR rechazado en puerta",
    "tipo": "incidente",
    "descripcion": "desc",
    "quien_reporta": "Usuario/asistente",
}

TICKET = {
    "id": TICKET_ID,
    "titulo": "QR rechazado",
    "descripcion": "No entra",
    "categoria_id": CATEGORIA_ID,
    "tags": ["qr"],
    "impacto": "alto",
    "urgencia": "alta",
    "prioridad": None,
    "estado": "abierto",
    "nivel": "N1",
    "escalamiento_jerarquico": None,
    "solicitante": "ana",
    "vence_respuesta_en": None,
    "vence_resolucion_en": None,
    "creado_en": AHORA,
    "actualizado_en": AHORA,
}

NUEVO = {
    "titulo": "QR rechazado",
    "descripcion": "No entra",
    "categoria_id": CATEGORIA_ID,
    "tags": ["qr"],
    "impacto": "alto",
    "urgencia": "alta",
    "solicitante": "ana",
}


def comentario(id_, interno):
    return {
        "id": f"00000000-0000-0000-0000-0000000000c{id_}",
        "ticket_id": TICKET_ID,
        "autor": "bea",
        "autor_rol": "agente",
        "contenido": f"comentario {id_}",
        "interno": interno,
        "creado_en": f"2026-01-01T10:0{id_}:00Z",
    }


def test_crear_ticket(monkeypatch):
    recibido = {}

    def crear(datos):
        recibido.update(datos)
        return {**TICKET, **datos, "id": TICKET_ID, "creado_en": AHORA, "actualizado_en": AHORA}

    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: CATEGORIA)
    monkeypatch.setattr(repo_tickets, "crear", crear)
    respuesta = client.post("/tickets", json=NUEVO)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "abierto"
    assert cuerpo["nivel"] == "N1"
    assert cuerpo["prioridad"] is None
    assert recibido["categoria_id"] == CATEGORIA_ID
    assert recibido["impacto"] == "alto"


def test_crear_ticket_categoria_inexistente(monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: None)
    monkeypatch.setattr(repo_tickets, "crear", lambda d: pytest.fail("no debe crear"))
    assert client.post("/tickets", json=NUEVO).status_code == 404


@pytest.mark.parametrize("campo,valor", [("impacto", "critico"), ("urgencia", "urgente")])
def test_crear_ticket_valor_invalido(campo, valor):
    assert client.post("/tickets", json={**NUEVO, campo: valor}).status_code == 422


def test_obtener_ticket_solicitante_omite_internos(monkeypatch):
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: {**TICKET, "categoria": CATEGORIA})
    monkeypatch.setattr(
        repo_comentarios, "listar_por_ticket", lambda _id: [comentario(1, False), comentario(2, True)]
    )
    cuerpo = client.get(f"/tickets/{TICKET_ID}").json()
    assert [c["interno"] for c in cuerpo["comentarios"]] == [False]
    assert cuerpo["categoria"]["nombre"] == "QR rechazado en puerta"
    assert cuerpo["categoria"]["tipo"] == "incidente"


def test_obtener_ticket_agente_ve_internos_en_orden(monkeypatch):
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: {**TICKET, "categoria": CATEGORIA})
    monkeypatch.setattr(
        repo_comentarios, "listar_por_ticket", lambda _id: [comentario(1, False), comentario(2, True)]
    )
    cuerpo = client.get(f"/tickets/{TICKET_ID}", params={"rol": "agente"}).json()
    assert [c["contenido"] for c in cuerpo["comentarios"]] == ["comentario 1", "comentario 2"]


def test_obtener_ticket_inexistente(monkeypatch):
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: None)
    assert client.get(f"/tickets/{TICKET_ID}").status_code == 404


def test_obtener_ticket_rol_invalido():
    assert client.get(f"/tickets/{TICKET_ID}", params={"rol": "admin"}).status_code == 422


def test_listar_tickets_pasa_filtros_e_incluye_categoria(monkeypatch):
    recibido = {}

    def listar(estado, prioridad, nivel, categoria_id, tag):
        recibido.update(estado=estado, prioridad=prioridad, nivel=nivel, categoria_id=categoria_id, tag=tag)
        return [{**TICKET, "categoria_nombre": "QR rechazado en puerta"}]

    monkeypatch.setattr(repo_tickets, "listar", listar)
    respuesta = client.get(
        "/tickets",
        params={"estado": "abierto", "prioridad": "P1", "nivel": "N1", "categoria_id": CATEGORIA_ID, "tag": "qr"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["categoria_nombre"] == "QR rechazado en puerta"
    assert recibido["estado"] == "abierto"
    assert recibido["prioridad"] == "P1"
    assert recibido["nivel"] == "N1"
    assert str(recibido["categoria_id"]) == CATEGORIA_ID
    assert recibido["tag"] == "qr"


def test_listar_tickets_sin_filtros(monkeypatch):
    monkeypatch.setattr(repo_tickets, "listar", lambda *a: [])
    assert client.get("/tickets").json() == []


def test_listar_tickets_filtro_invalido():
    assert client.get("/tickets", params={"estado": "nada"}).status_code == 422
