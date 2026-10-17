from fastapi.testclient import TestClient

from app.api.routers import health
from app.main import app

client = TestClient(app)


def test_health_responde_sin_supabase(monkeypatch):
    def sin_conexion():
        raise RuntimeError("sin supabase")

    monkeypatch.setattr(health, "get_client", sin_conexion)
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["supabase"] is False


def test_health_con_supabase_alcanzable(monkeypatch):
    class Cliente:
        def table(self, _):
            return self

        def __getattr__(self, _nombre):
            return lambda *a, **k: self

        def execute(self):
            return None

    monkeypatch.setattr(health, "get_client", lambda: Cliente())
    assert client.get("/health").json() == {"status": "ok", "supabase": True}


def test_openapi_lista_endpoints():
    rutas = client.get("/openapi.json").json()["paths"]
    assert "/health" in rutas
    assert "/categorias" in rutas
    assert set(rutas["/tickets"]) == {"get", "post"}
    assert set(rutas["/tickets/{ticket_id}"]) == {"get", "patch"}
    assert "post" in rutas["/tickets/{ticket_id}/comentarios"]
    assert "/estadisticas" in rutas

