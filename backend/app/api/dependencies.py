from fastapi import Depends, Header

from app.services import auth as servicio


def usuario_actual(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    esquema, _, token = authorization.partition(" ")
    if esquema.lower() != "bearer":
        return None
    return servicio.validar_token(token.strip())


def requiere_agente(usuario: str | None = Depends(usuario_actual)) -> str:
    return servicio.exigir_agente(usuario)
