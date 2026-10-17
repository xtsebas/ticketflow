from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class RecursoNoEncontrado(Exception):
    pass


class TransicionInvalida(Exception):
    pass


CODIGOS_HTTP = {
    400: "solicitud_invalida",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    409: "conflicto",
    422: "validacion_error",
}


def respuesta_error(status: int, detalle, codigo: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detalle": detalle, "codigo": codigo})


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(RecursoNoEncontrado)
    async def no_encontrado(_: Request, error: RecursoNoEncontrado):
        return respuesta_error(404, str(error), "no_encontrado")

    @app.exception_handler(TransicionInvalida)
    async def conflicto(_: Request, error: TransicionInvalida):
        return respuesta_error(409, str(error), "conflicto")

    @app.exception_handler(RequestValidationError)
    async def validacion(_: Request, error: RequestValidationError):
        detalle = [
            {
                "campo": ".".join(str(parte) for parte in e["loc"][1:]) or str(e["loc"][0]),
                "mensaje": e["msg"],
                "tipo": e["type"],
            }
            for e in error.errors()
        ]
        return respuesta_error(422, detalle, "validacion_error")

    @app.exception_handler(StarletteHTTPException)
    async def http(_: Request, error: StarletteHTTPException):
        codigo = CODIGOS_HTTP.get(error.status_code, "error_http")
        return respuesta_error(error.status_code, error.detail, codigo)

    @app.exception_handler(Exception)
    async def inesperado(_: Request, error: Exception):
        return respuesta_error(500, "Error interno del servidor", "error_interno")
