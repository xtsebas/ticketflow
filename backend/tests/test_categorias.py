from fastapi.testclient import TestClient

from app.main import app
from app.repositories import categorias as repo

client = TestClient(app)

CATEGORIAS = [
    {
        "id": "00000000-0000-0000-0000-00000000000%d" % i,
        "slug": f"cat_{i}",
        "nombre": f"Categoria {i}",
        "tipo": "incidente" if i < 4 else "solicitud",
        "descripcion": "desc",
        "quien_reporta": "Usuario/asistente",
    }
    for i in range(1, 9)
]


def test_listar_categorias_usa_repositorio(monkeypatch):
    monkeypatch.setattr(repo, "listar", lambda: CATEGORIAS)
    respuesta = client.get("/categorias")
    assert respuesta.status_code == 200
    assert respuesta.json() == CATEGORIAS


def test_listar_categorias_vacio(monkeypatch):
    monkeypatch.setattr(repo, "listar", lambda: [])
    respuesta = client.get("/categorias")
    assert respuesta.status_code == 200
    assert respuesta.json() == []
