import base64
import hashlib
import hmac
import os
import time

from app.core.config import get_settings
from app.core.errors import NoAutenticado
from app.domain.enums import RolSesion
from app.repositories import usuarios as repo_usuarios

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 600_000
DURACION_TOKEN_SEGUNDOS = 8 * 3600
HASH_INEXISTENTE = "pbkdf2_sha256$600000$65d27165a9f8a2a7fa45a7dc93549628$251bbffd1f4cc5626d1fb97e493ab8f968e8fdb20bf484c9e685cbd5abd85ef5"


def _derivar(contrasena: str, sal: bytes, iteraciones: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", contrasena.encode(), sal, iteraciones)


def hashear_contrasena(contrasena: str) -> str:
    sal = os.urandom(16)
    return f"{ALGORITMO}${ITERACIONES}${sal.hex()}${_derivar(contrasena, sal, ITERACIONES).hex()}"


def verificar_contrasena(contrasena: str, almacenado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = almacenado.split("$")
        if algoritmo != ALGORITMO:
            return False
        calculado = _derivar(contrasena, bytes.fromhex(sal), int(iteraciones))
        return hmac.compare_digest(calculado, bytes.fromhex(esperado))
    except ValueError:
        return False


def _firmar(texto: str) -> str:
    return hmac.new(get_settings().auth_secret.encode(), texto.encode(), hashlib.sha256).hexdigest()


def crear_token(usuario: str, ahora: float | None = None) -> str:
    expira = int((time.time() if ahora is None else ahora) + DURACION_TOKEN_SEGUNDOS)
    carga = base64.urlsafe_b64encode(f"{usuario}:{expira}".encode()).decode()
    return f"{carga}.{_firmar(carga)}"


def validar_token(token: str, ahora: float | None = None) -> str | None:
    try:
        carga, firma = token.split(".")
        if not hmac.compare_digest(firma.encode(), _firmar(carga).encode()):
            return None
        usuario, expira = base64.urlsafe_b64decode(carga.encode()).decode().rsplit(":", 1)
        vigente = int(expira) >= (time.time() if ahora is None else ahora)
    except ValueError:
        return None
    if not vigente or repo_usuarios.obtener_hash_contrasena(usuario) is None:
        return None
    return usuario


def iniciar_sesion(usuario: str, contrasena: str) -> dict:
    almacenado = repo_usuarios.obtener_hash_contrasena(usuario)
    valida = verificar_contrasena(contrasena, almacenado or HASH_INEXISTENTE)
    if almacenado is None or not valida:
        raise NoAutenticado("Usuario o contrasena incorrectos")
    return {"token": crear_token(usuario), "usuario": usuario, "rol": repo_usuarios.obtener_rol(usuario)}


def rol_de(usuario: str | None) -> RolSesion | None:
    return None if usuario is None else repo_usuarios.obtener_rol(usuario)


def exigir_agente(usuario: str | None) -> str:
    if rol_de(usuario) != RolSesion.agente:
        raise NoAutenticado("Se requiere iniciar sesion como soporte")
    return usuario
