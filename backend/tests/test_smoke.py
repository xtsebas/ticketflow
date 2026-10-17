import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

UUID_EJEMPLO = "00000000-0000-0000-0000-000000000001"

TICKET_NUEVO = {
    "titulo": "QR rechazado",
    "descripcion": "No entra",
    "categoria_id": UUID_EJEMPLO,
    "tags": ["qr"],
    "impacto": "alto",
    "urgencia": "alta",
    "solicitante": "ana",
}

COMENTARIO_NUEVO = {
    "autor": "ana",
    "autor_rol": "solicitante",
    "contenido": "hola",
    "interno": False,
}


def test_health_responde_sin_supabase():
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["supabase"] is False


def test_openapi_lista_endpoints():
    rutas = client.get("/openapi.json").json()["paths"]
    assert "/health" in rutas
    assert "/categorias" in rutas
    assert set(rutas["/tickets"]) == {"get", "post"}
    assert set(rutas["/tickets/{ticket_id}"]) == {"get", "patch"}
    assert "post" in rutas["/tickets/{ticket_id}/comentarios"]
    assert "/estadisticas" in rutas


@pytest.mark.parametrize(
    "metodo,ruta,cuerpo",
    [
        ("patch", f"/tickets/{UUID_EJEMPLO}", {"estado": "cerrado"}),
        ("post", f"/tickets/{UUID_EJEMPLO}/comentarios", COMENTARIO_NUEVO),
        ("get", "/estadisticas", None),
    ],
)
def test_endpoints_devuelven_501(metodo, ruta, cuerpo):
    respuesta = getattr(client, metodo)(ruta, json=cuerpo) if cuerpo else getattr(client, metodo)(ruta)
    assert respuesta.status_code == 501
