from fastapi import APIRouter

from app.schemas.auth import LoginIn, LoginOut
from app.services import auth as servicio

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
def login(datos: LoginIn):
    return servicio.iniciar_sesion(datos.usuario, datos.contrasena)
