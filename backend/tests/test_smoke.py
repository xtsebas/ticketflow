from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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

