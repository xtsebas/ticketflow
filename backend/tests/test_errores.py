import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import estadisticas as repo_estadisticas
from app.repositories import tickets as repo_tickets

client = TestClient(app)

CATEGORIA_ID = "00000000-0000-0000-0000-000000000001"
TICKET_ID = "00000000-0000-0000-0000-0000000000a1"
AHORA = "2026-01-01T10:00:00Z"

TICKET = {
    "id": TICKET_ID, "titulo": "QR rechazado", "descripcion": "No entra", "categoria_id": CATEGORIA_ID,
    "tags": ["qr"], "impacto": "alto", "urgencia": "alta", "prioridad": None, "estado": "abierto",
    "nivel": "N1", "escalamiento_jerarquico": None, "solicitante": "ana", "vence_respuesta_en": None,
    "vence_resolucion_en": None, "creado_en": AHORA, "actualizado_en": AHORA,
}
NUEVO = {
    "titulo": "QR rechazado", "descripcion": "No entra", "categoria_id": CATEGORIA_ID, "tags": ["qr"],
    "impacto": "alto", "urgencia": "alta", "solicitante": "ana",
}


@pytest.fixture
def repos(monkeypatch):
    estado = {"ticket": dict(TICKET), "comentarios": []}
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: {"id": CATEGORIA_ID})
    monkeypatch.setattr(repo_categorias, "listar", lambda: [])
    monkeypatch.setattr(repo_tickets, "crear", lambda datos: {**TICKET, **datos})
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: dict(estado["ticket"]) if estado["ticket"] else None)
    monkeypatch.setattr(repo_tickets, "actualizar", lambda _id, cambios: {**estado["ticket"], **cambios})
    monkeypatch.setattr(
        repo_comentarios, "crear", lambda _id, datos: estado["comentarios"].append(datos) or {**datos, "id": "x"}
    )
    monkeypatch.setattr(repo_estadisticas, "listar_campos_tickets", lambda: [])
    return estado


def verificar_error(respuesta, status, codigo):
    assert respuesta.status_code == status
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"detalle", "codigo"}
    assert cuerpo["codigo"] == codigo
    return cuerpo["detalle"]


def test_ticket_valido(repos):
    respuesta = client.post("/tickets", json=NUEVO)
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "abierto"


def test_categoria_invalida_404(repos, monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: None)
    detalle = verificar_error(client.post("/tickets", json=NUEVO), 404, "no_encontrado")
    assert "Categoria" in detalle


def test_ticket_inexistente_404(repos):
    repos["ticket"] = None
    verificar_error(client.get(f"/tickets/{TICKET_ID}"), 404, "no_encontrado")
    verificar_error(client.patch(f"/tickets/{TICKET_ID}", json={"prioridad": "P1"}), 404, "no_encontrado")
    comentario = {"autor": "a", "autor_rol": "agente", "contenido": "hola"}
    verificar_error(client.post(f"/tickets/{TICKET_ID}/comentarios", json=comentario), 404, "no_encontrado")


def test_valor_fuera_de_catalogo_422(repos):
    detalle = verificar_error(client.post("/tickets", json={**NUEVO, "impacto": "critico"}), 422, "validacion_error")
    assert detalle[0]["campo"] == "impacto"
    assert {"campo", "mensaje", "tipo"} == set(detalle[0])


def test_validacion_en_query_y_ruta_422(repos):
    verificar_error(client.get("/tickets", params={"estado": "nada"}), 422, "validacion_error")
    verificar_error(client.get("/tickets/no-es-uuid"), 422, "validacion_error")


def test_error_de_validador_de_modelo_es_json_serializable(repos):
    cuerpo = {"autor": "a", "autor_rol": "solicitante", "contenido": "x", "interno": True}
    detalle = verificar_error(client.post(f"/tickets/{TICKET_ID}/comentarios", json=cuerpo), 422, "validacion_error")
    assert "agentes" in detalle[0]["mensaje"]


def test_transicion_invalida_409(repos):
    detalle = verificar_error(client.patch(f"/tickets/{TICKET_ID}", json={"estado": "cerrado"}), 409, "conflicto")
    assert "abierto a cerrado" in detalle


def test_escalamiento_genera_comentario_interno(repos):
    respuesta = client.patch(f"/tickets/{TICKET_ID}", json={"nivel": "N3", "motivo": "complejo"})
    assert respuesta.status_code == 200
    assert repos["comentarios"] == [
        {"autor": "sistema", "autor_rol": "agente", "contenido": "Escalamiento: N1 a N3. Motivo: complejo", "interno": True}
    ]


def test_comentario_interno_de_solicitante_rechazado(repos):
    cuerpo = {"autor": "ana", "autor_rol": "solicitante", "contenido": "hola", "interno": True}
    verificar_error(client.post(f"/tickets/{TICKET_ID}/comentarios", json=cuerpo), 422, "validacion_error")
    assert repos["comentarios"] == []


def test_estadisticas_sin_datos(repos):
    respuesta = client.get("/estadisticas")
    assert respuesta.status_code == 200
    assert respuesta.json()["por_tag"] == []
    assert [e["total"] for e in respuesta.json()["por_estado"]] == [0, 0, 0, 0]


def test_estadisticas_con_datos(repos, monkeypatch):
    monkeypatch.setattr(repo_categorias, "listar", lambda: [{"id": CATEGORIA_ID, "slug": "qr"}])
    monkeypatch.setattr(
        repo_estadisticas,
        "listar_campos_tickets",
        lambda: [{"categoria_id": CATEGORIA_ID, "estado": "abierto", "prioridad": "P1", "tags": ["qr"]}],
    )
    cuerpo = client.get("/estadisticas").json()
    assert cuerpo["por_categoria"] == [{"clave": "qr", "total": 1}]
    assert cuerpo["por_tag"] == [{"clave": "qr", "total": 1}]


def test_ruta_inexistente_y_metodo_no_permitido():
    verificar_error(client.get("/no-existe"), 404, "no_encontrado")
    verificar_error(client.delete("/tickets"), 405, "metodo_no_permitido")


def test_error_inesperado_500(repos, monkeypatch):
    def falla(*_):
        raise ValueError("boom")

    monkeypatch.setattr(repo_tickets, "listar", falla)
    seguro = TestClient(app, raise_server_exceptions=False)
    detalle = verificar_error(seguro.get("/tickets"), 500, "error_interno")
    assert "boom" not in detalle


def test_cors_lee_cors_origins_del_entorno(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.ejemplo.com, http://localhost:4000")
    assert Settings(_env_file=None).cors_origins == ["https://app.ejemplo.com", "http://localhost:4000"]


def test_cors_aplica_origenes_configurados():
    from app.core.config import get_settings

    permitido = get_settings().cors_origins[0]
    preflight = {"Access-Control-Request-Method": "POST"}
    ok = client.options("/tickets", headers={"Origin": permitido, **preflight})
    assert ok.headers["access-control-allow-origin"] == permitido
    ajeno = client.options("/tickets", headers={"Origin": "https://malicioso.example", **preflight})
    assert "access-control-allow-origin" not in ajeno.headers
