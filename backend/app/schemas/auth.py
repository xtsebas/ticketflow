from pydantic import BaseModel

from app.domain.enums import RolSesion


class LoginIn(BaseModel):
    usuario: str
    contrasena: str


class LoginOut(BaseModel):
    token: str
    usuario: str
    rol: RolSesion
