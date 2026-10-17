import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import comentarios as repo_comentarios
from app.repositories import tickets as repo_tickets

client = TestClient(app)

TICKET_ID = "00000000-0000-0000-0000-0000000000a1"
URL = f"/tickets/{TICKET_ID}/comentarios"

NUEVO = {"autor": "bea", "autor_rol": "agente", "contenido": "revisando", "interno": False}


def simular_repos(monkeypatch, ticket_existe=True):
    creados = []

    def crear(ticket_id, datos):
        creados.append(datos)
        return {"id": "00000000-0000-0000-0000-0000000000c1", "ticket_id": str(ticket_id),
                "creado_en": "2026-01-01T10:00:00Z", **datos}

    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: {"id": TICKET_ID} if ticket_existe else None)
    monkeypatch.setattr(repo_comentarios, "crear", crear)
    return creados


def test_crear_comentario(monkeypatch):
    creados = simular_repos(monkeypatch)
    respuesta = client.post(URL, json=NUEVO)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["ticket_id"] == TICKET_ID
    assert cuerpo["contenido"] == "revisando"
    assert cuerpo["interno"] is False
    assert creados[0]["autor_rol"] == "agente"


def test_agente_crea_comentario_interno(monkeypatch):
    simular_repos(monkeypatch)
    respuesta = client.post(URL, json={**NUEVO, "interno": True})
    assert respuesta.status_code == 201
    assert respuesta.json()["interno"] is True


def test_solicitante_comentario_publico(monkeypatch):
    simular_repos(monkeypatch)
    respuesta = client.post(URL, json={**NUEVO, "autor_rol": "solicitante"})
    assert respuesta.status_code == 201


def test_ticket_inexistente(monkeypatch):
    creados = simular_repos(monkeypatch, ticket_existe=False)
    assert client.post(URL, json=NUEVO).status_code == 404
    assert creados == []


@pytest.mark.parametrize(
    "cambios",
    [
        {"autor_rol": "admin"},
        {"contenido": ""},
        {"contenido": "   "},
        {"autor_rol": "solicitante", "interno": True},
    ],
)
def test_validaciones_422(monkeypatch, cambios):
    creados = simular_repos(monkeypatch)
    assert client.post(URL, json={**NUEVO, **cambios}).status_code == 422
    assert creados == []
