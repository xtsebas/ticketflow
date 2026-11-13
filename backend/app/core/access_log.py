import json
import logging
import random
import re
import time
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import respuesta_error

RUTAS_SIN_FALLO = frozenset({"/health"})
CABECERA_FALLOS = b"x-simular-fallos"


def crear_logger_acceso(ruta: str, max_bytes: int, respaldos: int) -> logging.Logger:
    logger = logging.getLogger(f"acceso.{ruta}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(ruta, maxBytes=max_bytes, backupCount=respaldos, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def nivel_log(status: int) -> str:
    if status >= 500:
        return "error"
    if status >= 400:
        return "warn"
    return "info"


def plantillas_de_rutas(aplicacion) -> list[tuple[re.Pattern, str]]:
    esquema = aplicacion.openapi() if hasattr(aplicacion, "openapi") else {}
    plantillas = []
    for ruta in esquema.get("paths", {}):
        segmentos = ["[^/]+" if s.startswith("{") else re.escape(s) for s in ruta.split("/")]
        plantillas.append((ruta.count("{"), re.compile("^" + "/".join(segmentos) + "$"), ruta))
    return [(patron, ruta) for _, patron, ruta in sorted(plantillas, key=lambda t: t[0])]


def marca_de_tiempo() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class AccessLogMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        logger: logging.Logger,
        service_name: str,
        fallos_porcentaje: float = 0.0,
        azar: Callable[[], float] = random.random,
    ) -> None:
        self.app = app
        self.logger = logger
        self.service_name = service_name
        self.fallos_porcentaje = fallos_porcentaje
        self.azar = azar
        self.plantillas = None

    def _inyectar_fallo(self, scope: Scope) -> bool:
        if self.fallos_porcentaje <= 0 or scope["path"] in RUTAS_SIN_FALLO:
            return False
        if not any(nombre == CABECERA_FALLOS for nombre, _ in scope.get("headers", [])):
            return False
        return self.azar() * 100 < self.fallos_porcentaje

    def _plantilla(self, scope: Scope, path: str) -> str:
        if self.plantillas is None:
            self.plantillas = plantillas_de_rutas(scope.get("app"))
        return next((ruta for patron, ruta in self.plantillas if patron.match(path)), path)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inicio = time.perf_counter_ns()
        trace_id = uuid.uuid4().hex
        resultado: dict = {"status": 500, "error": None}

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                resultado["status"] = mensaje["status"]
                cabeceras = list(mensaje.get("headers", []))
                cabeceras.append((b"x-request-id", trace_id.encode()))
                mensaje = {**mensaje, "headers": cabeceras}
            await send(mensaje)

        try:
            if self._inyectar_fallo(scope):
                resultado["error"] = ("FalloInyectado", "Fallo inyectado por FALLOS_PORCENTAJE")
                respuesta = respuesta_error(500, "Error interno del servidor", "error_interno")
                await respuesta(scope, receive, enviar)
            else:
                await self.app(scope, receive, enviar)
        except Exception as error:
            resultado["error"] = (type(error).__name__, str(error))
            raise
        finally:
            self._registrar(scope, resultado, trace_id, time.perf_counter_ns() - inicio)

    def _registrar(self, scope: Scope, resultado: dict, trace_id: str, duracion_ns: int) -> None:
        status = resultado["status"]
        metodo = scope["method"]
        path = scope["path"]
        ruta = getattr(scope.get("route"), "path", None) or self._plantilla(scope, path)
        consulta = scope.get("query_string", b"").decode("latin-1")
        cliente = scope.get("client")
        agente = next(
            (v.decode("latin-1") for k, v in scope.get("headers", []) if k == b"user-agent"),
            None,
        )
        registro = {
            "@timestamp": marca_de_tiempo(),
            "log.level": nivel_log(status),
            "message": f"{metodo} {path} {status}",
            "http.request.method": metodo,
            "http.response.status_code": status,
            "event.duration": duracion_ns,
            "url.path": ruta,
            "url.original": f"{path}?{consulta}" if consulta else path,
            "service.name": self.service_name,
            "trace.id": trace_id,
        }
        if cliente:
            registro["client.ip"] = cliente[0]
        if agente:
            registro["user_agent.original"] = agente
        if resultado["error"]:
            registro["error.type"], registro["error.message"] = resultado["error"]
        self.logger.info(json.dumps(registro, ensure_ascii=False, separators=(",", ":")))
