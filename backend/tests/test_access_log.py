import json
import logging
import re

import pytest
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.access_log import AccessLogMiddleware, crear_logger_acceso, nivel_log
from app.core.config import Settings
from app.core.errors import registrar_manejadores

CON_FALLOS = {"X-Simular-Fallos": "1"}
CAMPOS_OBLIGATORIOS = [
    "@timestamp",
    "http.request.method",
    "http.response.status_code",
    "event.duration",
    "url.path",
    "service.name",
    "log.level",
]


def crear_app(ruta_log, fallos_porcentaje=0.0, azar=None):
    app = FastAPI()
    registrar_manejadores(app)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/items/{item_id}")
    def item(item_id: int):
        if item_id == 404:
            raise HTTPException(status_code=404, detail="no existe")
        return {"id": item_id}

    @app.post("/items", status_code=201)
    def crear():
        return {"creado": True}

    @app.get("/boom")
    def boom():
        raise RuntimeError("fallo interno")

    logger = crear_logger_acceso(str(ruta_log), 1_000_000, 1)
    argumentos = {"logger": logger, "service_name": "servicio-prueba", "fallos_porcentaje": fallos_porcentaje}
    if azar is not None:
        argumentos["azar"] = azar
    app.add_middleware(AccessLogMiddleware, **argumentos)
    return app, logger


@pytest.fixture
def ruta_log(tmp_path):
    ruta = tmp_path / "api.log"
    yield ruta
    logger = logging.getLogger(f"acceso.{ruta}")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def leer(ruta_log):
    return [json.loads(linea) for linea in ruta_log.read_text(encoding="utf-8").splitlines()]


def test_cada_peticion_genera_una_linea_json_con_los_siete_campos(ruta_log):
    app, _ = crear_app(ruta_log)
    client = TestClient(app)
    client.get("/ok")
    client.post("/items")
    registros = leer(ruta_log)
    assert len(registros) == 2
    for registro in registros:
        for campo in CAMPOS_OBLIGATORIOS:
            assert campo in registro
        assert registro["service.name"] == "servicio-prueba"
    assert registros[0]["http.request.method"] == "GET"
    assert registros[1]["http.request.method"] == "POST"
    assert registros[1]["http.response.status_code"] == 201


def test_tipos_de_los_campos(ruta_log):
    app, _ = crear_app(ruta_log)
    TestClient(app).get("/ok")
    registro = leer(ruta_log)[0]
    assert isinstance(registro["event.duration"], int)
    assert registro["event.duration"] > 0
    assert isinstance(registro["http.response.status_code"], int)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", registro["@timestamp"])


def test_url_path_usa_la_plantilla_de_la_ruta(ruta_log):
    app, _ = crear_app(ruta_log)
    client = TestClient(app)
    client.get("/items/7?x=1")
    client.get("/items/8")
    registros = leer(ruta_log)
    assert [r["url.path"] for r in registros] == ["/items/{item_id}", "/items/{item_id}"]
    assert registros[0]["url.original"] == "/items/7?x=1"
    assert registros[1]["url.original"] == "/items/8"


def test_un_fallo_inyectado_tambien_registra_la_plantilla_de_la_ruta(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=100.0, azar=lambda: 0.0)
    TestClient(app).get("/items/7?x=1", headers=CON_FALLOS)
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 500
    assert registro["url.path"] == "/items/{item_id}"
    assert registro["url.original"] == "/items/7?x=1"


def test_un_fallo_inyectado_en_un_router_incluido_registra_la_plantilla(ruta_log):
    app = FastAPI()
    router = APIRouter(prefix="/tickets")

    @router.get("/{ticket_id}")
    def detalle(ticket_id: str):
        return {"id": ticket_id}

    @router.post("/{ticket_id}/comentarios")
    def comentar(ticket_id: str):
        return {"id": ticket_id}

    app.include_router(router)
    logger = crear_logger_acceso(str(ruta_log), 1_000_000, 1)
    app.add_middleware(AccessLogMiddleware, logger=logger, service_name="s", fallos_porcentaje=100.0, azar=lambda: 0.0)
    client = TestClient(app)
    client.get("/tickets/7a74f967-4b33-4258-b6aa-2967230e4e24", headers=CON_FALLOS)
    client.post("/tickets/7a74f967-4b33-4258-b6aa-2967230e4e24/comentarios", headers=CON_FALLOS)
    assert [r["url.path"] for r in leer(ruta_log)] == ["/tickets/{ticket_id}", "/tickets/{ticket_id}/comentarios"]


def test_un_fallo_inyectado_en_una_ruta_inexistente_registra_el_path_real(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=100.0, azar=lambda: 0.0)
    TestClient(app).get("/no-existe", headers=CON_FALLOS)
    assert leer(ruta_log)[0]["url.path"] == "/no-existe"


def test_ruta_inexistente_registra_el_path_real(ruta_log):
    app, _ = crear_app(ruta_log)
    TestClient(app).get("/no-existe")
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 404
    assert registro["url.path"] == "/no-existe"
    assert registro["log.level"] == "warn"


@pytest.mark.parametrize(
    "status,nivel",
    [(200, "info"), (201, "info"), (301, "info"), (400, "warn"), (404, "warn"), (499, "warn"), (500, "error"), (503, "error")],
)
def test_nivel_segun_el_status(status, nivel):
    assert nivel_log(status) == nivel


def test_un_4xx_de_la_aplicacion_se_registra_como_warn(ruta_log):
    app, _ = crear_app(ruta_log)
    TestClient(app).get("/items/404")
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 404
    assert registro["log.level"] == "warn"


def test_validacion_422_se_registra_como_warn(ruta_log):
    app, _ = crear_app(ruta_log)
    TestClient(app).get("/items/abc")
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 422
    assert registro["log.level"] == "warn"


def test_excepcion_no_controlada_se_registra_como_500_con_error(ruta_log):
    app, _ = crear_app(ruta_log)
    respuesta = TestClient(app, raise_server_exceptions=False).get("/boom")
    assert respuesta.status_code == 500
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 500
    assert registro["log.level"] == "error"
    assert registro["error.type"] == "RuntimeError"
    assert registro["error.message"] == "fallo interno"


def test_la_respuesta_lleva_el_mismo_trace_id_que_el_log(ruta_log):
    app, _ = crear_app(ruta_log)
    respuesta = TestClient(app).get("/ok")
    assert leer(ruta_log)[0]["trace.id"] == respuesta.headers["x-request-id"]


def test_sin_fallos_configurados_nunca_se_inyecta_un_500(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=0.0, azar=lambda: 0.0)
    client = TestClient(app)
    assert all(client.get("/ok", headers=CON_FALLOS).status_code == 200 for _ in range(20))


def test_sin_la_cabecera_nunca_se_inyecta_un_500(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=100.0, azar=lambda: 0.0)
    client = TestClient(app)
    assert all(client.get("/ok").status_code == 200 for _ in range(20))


def test_fallo_inyectado_responde_500_y_lo_registra(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=100.0, azar=lambda: 0.5)
    respuesta = TestClient(app).get("/ok", headers=CON_FALLOS)
    assert respuesta.status_code == 500
    assert respuesta.json() == {"detalle": "Error interno del servidor", "codigo": "error_interno"}
    registro = leer(ruta_log)[0]
    assert registro["http.response.status_code"] == 500
    assert registro["log.level"] == "error"
    assert registro["error.type"] == "FalloInyectado"


def test_el_porcentaje_de_fallos_se_respeta(ruta_log):
    valores = iter([0.04, 0.10, 0.049, 0.5])
    app, _ = crear_app(ruta_log, fallos_porcentaje=5.0, azar=lambda: next(valores))
    client = TestClient(app)
    estados = [client.get("/ok", headers=CON_FALLOS).status_code for _ in range(4)]
    assert estados == [500, 200, 500, 200]


def test_health_nunca_recibe_fallos_inyectados(ruta_log):
    app, _ = crear_app(ruta_log, fallos_porcentaje=100.0, azar=lambda: 0.0)
    client = TestClient(app)
    assert all(client.get("/health", headers=CON_FALLOS).status_code == 200 for _ in range(10))


def test_el_archivo_rota_al_superar_el_tamano(tmp_path):
    ruta = tmp_path / "rota.log"
    logger = crear_logger_acceso(str(ruta), 300, 2)
    try:
        for i in range(30):
            logger.info(json.dumps({"n": i, "relleno": "x" * 50}))
        archivos = sorted(p.name for p in tmp_path.iterdir())
        assert archivos == ["rota.log", "rota.log.1", "rota.log.2"]
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def test_crear_logger_acceso_crea_el_directorio(tmp_path):
    ruta = tmp_path / "nuevo" / "sub" / "api.log"
    logger = crear_logger_acceso(str(ruta), 1000, 1)
    try:
        logger.info("{}")
        assert ruta.exists()
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def test_por_defecto_el_logging_de_acceso_esta_apagado():
    ajustes = Settings(_env_file=None)
    assert ajustes.log_file == ""
    assert ajustes.fallos_porcentaje == 0.0
    assert ajustes.service_name == "ticketflow-api"


def test_fallos_porcentaje_fuera_de_rango_se_rechaza():
    with pytest.raises(ValueError):
        Settings(_env_file=None, fallos_porcentaje=101)
    with pytest.raises(ValueError):
        Settings(_env_file=None, fallos_porcentaje=-1)


def test_la_aplicacion_real_no_instala_el_middleware_sin_log_file():
    from app.main import app

    assert all(m.cls is not AccessLogMiddleware for m in app.user_middleware)
