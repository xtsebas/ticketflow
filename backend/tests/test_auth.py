import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import usuario_actual
from app.core.config import Settings
from app.main import app
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import estadisticas as repo_estadisticas
from app.repositories import tickets as repo_tickets
from app.repositories.usuarios import USUARIOS_CLIENTE, USUARIOS_SOPORTE
from app.services import auth as servicio

client = TestClient(app)

CONTRASENA = "soporte2026"
CONTRASENA_CLIENTE = "cliente2026"
CATEGORIA_ID = "00000000-0000-0000-0000-000000000001"
TICKET_ID = "00000000-0000-0000-0000-0000000000a1"
AHORA = "2026-01-01T10:00:00Z"

TICKET = {
    "id": TICKET_ID, "titulo": "QR rechazado", "descripcion": "No entra", "categoria_id": CATEGORIA_ID,
    "tags": ["qr"], "impacto": "alto", "urgencia": "alta", "prioridad": "P1", "estado": "abierto",
    "nivel": "N1", "escalamiento_jerarquico": None, "solicitante": "ana", "vence_respuesta_en": None,
    "vence_resolucion_en": None, "creado_en": AHORA, "actualizado_en": AHORA,
}
CATEGORIA = {
    "id": CATEGORIA_ID, "slug": "qr_rechazado_en_puerta", "nombre": "QR", "tipo": "incidente",
    "descripcion": "desc", "quien_reporta": "Usuario/asistente",
}
CATEGORIA_CLIENTE = {
    "id": CATEGORIA_ID, "slug": "pago_no_procesado_cobro_duplicado", "nombre": "Pago", "tipo": "incidente",
    "descripcion": "desc", "quien_reporta": "Cliente",
}
NUEVO = {
    "titulo": "QR rechazado", "descripcion": "No entra", "categoria_id": CATEGORIA_ID, "tags": ["qr"],
    "impacto": "alto", "urgencia": "alta", "solicitante": "ana",
}
COMENTARIO_AGENTE = {"autor": "soporte1", "autor_rol": "agente", "contenido": "revisando"}
COMENTARIO_SOLICITANTE = {"autor": "ana", "autor_rol": "solicitante", "contenido": "hola"}


@pytest.fixture(autouse=True)
def sin_sesion(sesion_agente):
    app.dependency_overrides.pop(usuario_actual, None)


@pytest.fixture(autouse=True)
def repos(monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: CATEGORIA)
    monkeypatch.setattr(repo_categorias, "listar", lambda: [CATEGORIA])
    monkeypatch.setattr(repo_tickets, "crear", lambda datos: {**TICKET, **datos})
    monkeypatch.setattr(repo_tickets, "listar", lambda *_: [{**TICKET, "categoria_nombre": "QR"}])
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: {**TICKET, "categoria": CATEGORIA})
    monkeypatch.setattr(repo_tickets, "actualizar", lambda _id, cambios: {**TICKET, **cambios})
    monkeypatch.setattr(repo_comentarios, "listar_por_ticket", lambda _id: [])
    monkeypatch.setattr(
        repo_comentarios,
        "crear",
        lambda _id, datos: {**datos, "id": "00000000-0000-0000-0000-0000000000c1", "ticket_id": TICKET_ID, "creado_en": AHORA},
    )
    monkeypatch.setattr(repo_estadisticas, "listar_campos_tickets", lambda: [])


def cabecera(usuario="soporte1"):
    return {"Authorization": f"Bearer {servicio.crear_token(usuario)}"}


def detalle_401(respuesta):
    assert respuesta.status_code == 401
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"detalle", "codigo"}
    assert cuerpo["codigo"] == "no_autenticado"


def test_hash_verifica_y_rechaza():
    almacenado = servicio.hashear_contrasena(CONTRASENA)
    assert servicio.verificar_contrasena(CONTRASENA, almacenado)
    assert not servicio.verificar_contrasena("otra", almacenado)
    assert CONTRASENA not in almacenado


def test_hash_usa_sal_distinta():
    assert servicio.hashear_contrasena(CONTRASENA) != servicio.hashear_contrasena(CONTRASENA)


@pytest.mark.parametrize("almacenado", ["", "texto", "a$b$c$d", "pbkdf2_sha256$x$00$00", "otro$1$00$00", "pbkdf2_sha256$1$zz$zz"])
def test_hash_malformado_no_valida(almacenado):
    assert not servicio.verificar_contrasena(CONTRASENA, almacenado)


def test_cuatro_usuarios_con_hash_y_sal_propia():
    assert list(USUARIOS_SOPORTE) == ["soporte1", "soporte2", "soporte3", "soporte4"]
    assert len(set(USUARIOS_SOPORTE.values())) == 4
    for almacenado in USUARIOS_SOPORTE.values():
        assert almacenado.startswith("pbkdf2_sha256$")
        assert CONTRASENA not in almacenado
        assert servicio.verificar_contrasena(CONTRASENA, almacenado)


@pytest.mark.parametrize("usuario", ["soporte1", "soporte2", "soporte3", "soporte4"])
def test_login_valido(usuario):
    respuesta = client.post("/auth/login", json={"usuario": usuario, "contrasena": CONTRASENA})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["usuario"] == usuario
    assert servicio.validar_token(cuerpo["token"]) == usuario


def test_login_contrasena_incorrecta_y_usuario_inexistente_responden_igual():
    mala = client.post("/auth/login", json={"usuario": "soporte1", "contrasena": "mala"})
    fantasma = client.post("/auth/login", json={"usuario": "soporte9", "contrasena": CONTRASENA})
    detalle_401(mala)
    detalle_401(fantasma)
    assert mala.json() == fantasma.json()


@pytest.mark.parametrize("cuerpo", [{}, {"usuario": "soporte1"}, {"contrasena": CONTRASENA}])
def test_login_sin_campos_422(cuerpo):
    assert client.post("/auth/login", json=cuerpo).status_code == 422


def test_token_alterado_o_basura_no_valida():
    token = servicio.crear_token("soporte1")
    carga, firma = token.split(".")
    assert servicio.validar_token(f"{carga}.{'0' * len(firma)}") is None
    assert servicio.validar_token(f"{carga}x.{firma}") is None
    assert servicio.validar_token(servicio.crear_token("soporte2").split(".")[0] + "." + firma) is None
    for basura in ["", "abc", "a.b.c", "....", "ñ.ñ"]:
        assert servicio.validar_token(basura) is None


def test_token_expira():
    token = servicio.crear_token("soporte1", ahora=1000)
    assert servicio.validar_token(token, ahora=1000 + servicio.DURACION_TOKEN_SEGUNDOS) == "soporte1"
    assert servicio.validar_token(token, ahora=1001 + servicio.DURACION_TOKEN_SEGUNDOS) is None


def test_token_de_usuario_que_ya_no_existe_no_valida():
    assert servicio.validar_token(servicio.crear_token("fantasma")) is None


def test_secreto_vacio_se_reemplaza_por_uno_aleatorio(monkeypatch):
    monkeypatch.delenv("AUTH_SECRET", raising=False)
    assert len(Settings(_env_file=None, auth_secret="").auth_secret) >= 32
    assert Settings(_env_file=None).auth_secret != Settings(_env_file=None).auth_secret


def test_secreto_se_lee_del_entorno(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "secreto-fijo")
    assert Settings(_env_file=None).auth_secret == "secreto-fijo"


PROTEGIDOS = [
    ("get", "/tickets", None),
    ("patch", f"/tickets/{TICKET_ID}", {"prioridad": "P2"}),
    ("get", "/estadisticas", None),
    ("get", f"/tickets/{TICKET_ID}?rol=agente", None),
    ("post", f"/tickets/{TICKET_ID}/comentarios", COMENTARIO_AGENTE),
]


@pytest.mark.parametrize("metodo,ruta,cuerpo", PROTEGIDOS)
def test_endpoints_de_soporte_exigen_sesion(metodo, ruta, cuerpo):
    detalle_401(client.request(metodo, ruta, json=cuerpo))


@pytest.mark.parametrize("metodo,ruta,cuerpo", PROTEGIDOS)
@pytest.mark.parametrize("autorizacion", ["Bearer basura", "Basic abc", "Bearer", servicio.crear_token("soporte1")])
def test_endpoints_de_soporte_rechazan_credenciales_invalidas(metodo, ruta, cuerpo, autorizacion):
    detalle_401(client.request(metodo, ruta, json=cuerpo, headers={"Authorization": autorizacion}))


@pytest.mark.parametrize("metodo,ruta,cuerpo", PROTEGIDOS)
def test_endpoints_de_soporte_con_sesion(metodo, ruta, cuerpo):
    respuesta = client.request(metodo, ruta, json=cuerpo, headers=cabecera())
    assert respuesta.status_code in (200, 201)


def test_esquema_bearer_no_distingue_mayusculas():
    token = servicio.crear_token("soporte3")
    assert client.get("/estadisticas", headers={"Authorization": f"bearer {token}"}).status_code == 200


def test_rutas_publicas_no_piden_sesion():
    assert client.get("/categorias").status_code == 200
    assert client.post("/tickets", json=NUEVO).status_code == 201
    assert client.get(f"/tickets/{TICKET_ID}").status_code == 200
    assert client.get(f"/tickets/{TICKET_ID}?rol=solicitante").status_code == 200
    assert client.post(f"/tickets/{TICKET_ID}/comentarios", json=COMENTARIO_SOLICITANTE).status_code == 201


def test_rutas_publicas_ignoran_un_token_invalido():
    invalido = {"Authorization": "Bearer basura"}
    assert client.get(f"/tickets/{TICKET_ID}", headers=invalido).status_code == 200
    assert client.post(f"/tickets/{TICKET_ID}/comentarios", json=COMENTARIO_SOLICITANTE, headers=invalido).status_code == 201


def test_sesion_se_comprueba_antes_que_la_existencia_del_ticket(monkeypatch):
    monkeypatch.setattr(repo_tickets, "obtener", lambda _id: None)
    detalle_401(client.get(f"/tickets/{TICKET_ID}?rol=agente"))
    assert client.get(f"/tickets/{TICKET_ID}?rol=agente", headers=cabecera()).status_code == 404


def test_cinco_clientes_con_hash_y_sal_propia():
    assert list(USUARIOS_CLIENTE) == [
        "asa_promotions",
        "arceyut_producciones",
        "show_business_guatemala",
        "promotora_2_mundos",
        "epica_eventos",
    ]
    assert len(set(USUARIOS_CLIENTE.values())) == 5
    for almacenado in USUARIOS_CLIENTE.values():
        assert almacenado.startswith("pbkdf2_sha256$")
        assert CONTRASENA_CLIENTE not in almacenado
        assert servicio.verificar_contrasena(CONTRASENA_CLIENTE, almacenado)
        assert not servicio.verificar_contrasena(CONTRASENA, almacenado)


def test_usuarios_de_soporte_y_de_clientes_no_se_cruzan():
    assert not set(USUARIOS_SOPORTE) & set(USUARIOS_CLIENTE)


def test_rol_de_cada_cuenta():
    assert servicio.rol_de("soporte1") == "agente"
    assert servicio.rol_de("epica_eventos") == "cliente"
    assert servicio.rol_de("fantasma") is None
    assert servicio.rol_de(None) is None


@pytest.mark.parametrize("usuario", list(USUARIOS_CLIENTE))
def test_login_de_cliente(usuario):
    respuesta = client.post("/auth/login", json={"usuario": usuario, "contrasena": CONTRASENA_CLIENTE})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["usuario"] == usuario
    assert cuerpo["rol"] == "cliente"
    assert servicio.validar_token(cuerpo["token"]) == usuario


@pytest.mark.parametrize("usuario", list(USUARIOS_SOPORTE))
def test_login_de_soporte_indica_el_rol_agente(usuario):
    respuesta = client.post("/auth/login", json={"usuario": usuario, "contrasena": CONTRASENA})
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "agente"


def test_la_contrasena_de_un_grupo_no_sirve_en_el_otro():
    detalle_401(client.post("/auth/login", json={"usuario": "soporte1", "contrasena": CONTRASENA_CLIENTE}))
    detalle_401(client.post("/auth/login", json={"usuario": "epica_eventos", "contrasena": CONTRASENA}))


@pytest.mark.parametrize("metodo,ruta,cuerpo", PROTEGIDOS)
def test_endpoints_de_soporte_rechazan_a_un_cliente(metodo, ruta, cuerpo):
    detalle_401(client.request(metodo, ruta, json=cuerpo, headers=cabecera("asa_promotions")))


def test_sin_sesion_solo_se_crean_servicios_de_evento(monkeypatch):
    respuesta = client.post("/tickets", json=NUEVO)
    assert respuesta.status_code == 201
    assert respuesta.json()["solicitante"] == "ana"
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: CATEGORIA_CLIENTE)
    detalle_401(client.post("/tickets", json=NUEVO))


@pytest.mark.parametrize("slug", ["qr_rechazado_en_puerta", "reembolso_cancelacion_entrada", "reenvio_ticket_digital"])
def test_sin_sesion_se_crea_cada_servicio_de_usuario(monkeypatch, slug):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: {**CATEGORIA, "slug": slug})
    assert client.post("/tickets", json=NUEVO).status_code == 201


def test_token_invalido_se_trata_como_sin_sesion(monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: CATEGORIA_CLIENTE)
    detalle_401(client.post("/tickets", json=NUEVO, headers={"Authorization": "Bearer basura"}))


@pytest.mark.parametrize("categoria", [CATEGORIA, CATEGORIA_CLIENTE])
def test_cliente_crea_cualquier_servicio_y_queda_como_solicitante(monkeypatch, categoria):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: categoria)
    respuesta = client.post("/tickets", json={**NUEVO, "solicitante": "otra_persona"}, headers=cabecera("epica_eventos"))
    assert respuesta.status_code == 201
    assert respuesta.json()["solicitante"] == "epica_eventos"


def test_soporte_crea_cualquier_servicio_sin_cambiar_el_solicitante(monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: CATEGORIA_CLIENTE)
    respuesta = client.post("/tickets", json=NUEVO, headers=cabecera("soporte1"))
    assert respuesta.status_code == 201
    assert respuesta.json()["solicitante"] == "ana"


def test_servicio_inexistente_es_404_aunque_no_haya_sesion(monkeypatch):
    monkeypatch.setattr(repo_categorias, "obtener", lambda _id: None)
    assert client.post("/tickets", json=NUEVO).status_code == 404
