import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import tickets as repo_tickets

client = TestClient(app)

TICKET_ID = "00000000-0000-0000-0000-0000000000a1"
OTRA_CATEGORIA = "00000000-0000-0000-0000-000000000002"
URL = f"/tickets/{TICKET_ID}"
AHORA = "2026-01-01T10:00:00Z"


def ticket_base(**cambios):
    base = {
        "id": TICKET_ID,
        "titulo": "QR rechazado",
        "descripcion": "No entra",
        "categoria_id": "00000000-0000-0000-0000-000000000001",
        "tags": ["qr"],
        "impacto": "alto",
        "urgencia": "alta",
        "prioridad": None,
        "estado": "abierto",
        "nivel": "N1",
        "escalamiento_jerarquico": None,
        "solicitante": "ana",
        "vence_respuesta_en": None,
        "vence_resolucion_en": None,
        "creado_en": AHORA,
        "actualizado_en": AHORA,
    }
    return {**base, **cambios}


class Entorno:
    def __init__(self, monkeypatch, ticket):
        self.ticket = ticket
        self.actualizaciones = []
        self.comentarios = []
        monkeypatch.setattr(repo_tickets, "obtener", lambda _id: dict(self.ticket) if self.ticket else None)
        monkeypatch.setattr(repo_tickets, "actualizar", self.actualizar)
        monkeypatch.setattr(repo_comentarios, "crear", lambda _id, datos: self.comentarios.append(datos) or datos)
        monkeypatch.setattr(repo_categorias, "obtener", lambda _id: {"id": str(_id)} if str(_id) == OTRA_CATEGORIA else None)

    def actualizar(self, _id, cambios):
        self.actualizaciones.append(cambios)
        return {**self.ticket, **cambios}


def entorno(monkeypatch, **cambios):
    return Entorno(monkeypatch, ticket_base(**cambios))


def test_actualiza_solo_campos_enviados(monkeypatch):
    env = entorno(monkeypatch)
    respuesta = client.patch(URL, json={"prioridad": "P2", "tags": ["a", "b"]})
    assert respuesta.status_code == 200
    assert env.actualizaciones == [
        {
            "prioridad": "P2",
            "tags": ["a", "b"],
            "vence_respuesta_en": "2026-01-01T10:30:00+00:00",
            "vence_resolucion_en": "2026-01-01T14:00:00+00:00",
        }
    ]
    assert respuesta.json()["prioridad"] == "P2"
    assert env.comentarios == []


def test_motivo_no_se_guarda_en_ticket(monkeypatch):
    env = entorno(monkeypatch)
    client.patch(URL, json={"prioridad": "P3", "motivo": "porque si"})
    assert "motivo" not in env.actualizaciones[0]


def test_cambia_categoria_existente(monkeypatch):
    env = entorno(monkeypatch)
    assert client.patch(URL, json={"categoria_id": OTRA_CATEGORIA}).status_code == 200
    assert env.actualizaciones == [{"categoria_id": OTRA_CATEGORIA}]


def test_categoria_inexistente_404(monkeypatch):
    env = entorno(monkeypatch)
    respuesta = client.patch(URL, json={"categoria_id": "00000000-0000-0000-0000-000000000099"})
    assert respuesta.status_code == 404
    assert env.actualizaciones == []


def test_ticket_inexistente_404(monkeypatch):
    Entorno(monkeypatch, None)
    assert client.patch(URL, json={"prioridad": "P1"}).status_code == 404


@pytest.mark.parametrize("cuerpo", [{}, {"motivo": "solo motivo"}, {"estado": None}])
def test_sin_campos_actualizables_422(monkeypatch, cuerpo):
    env = entorno(monkeypatch)
    assert client.patch(URL, json=cuerpo).status_code == 422
    assert env.actualizaciones == []


@pytest.mark.parametrize(
    "cuerpo",
    [{"estado": "borrado"}, {"prioridad": "P9"}, {"nivel": "N4"}, {"escalamiento_jerarquico": "ceo"}, {"tags": "qr"}],
)
def test_valores_invalidos_422(monkeypatch, cuerpo):
    env = entorno(monkeypatch)
    assert client.patch(URL, json=cuerpo).status_code == 422
    assert env.actualizaciones == []


@pytest.mark.parametrize(
    "actual,nuevo",
    [
        ("abierto", "en_progreso"),
        ("en_progreso", "resuelto"),
        ("resuelto", "cerrado"),
        ("resuelto", "en_progreso"),
    ],
)
def test_transiciones_validas(monkeypatch, actual, nuevo):
    env = entorno(monkeypatch, estado=actual)
    respuesta = client.patch(URL, json={"estado": nuevo})
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == nuevo
    assert env.actualizaciones == [{"estado": nuevo}]


@pytest.mark.parametrize(
    "actual,nuevo",
    [
        ("abierto", "resuelto"),
        ("abierto", "cerrado"),
        ("abierto", "abierto"),
        ("en_progreso", "abierto"),
        ("en_progreso", "cerrado"),
        ("resuelto", "abierto"),
        ("cerrado", "abierto"),
        ("cerrado", "en_progreso"),
        ("cerrado", "resuelto"),
    ],
)
def test_transiciones_invalidas_409(monkeypatch, actual, nuevo):
    env = entorno(monkeypatch, estado=actual)
    respuesta = client.patch(URL, json={"estado": nuevo})
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "conflicto"
    assert actual in respuesta.json()["detalle"] and nuevo in respuesta.json()["detalle"]
    assert env.actualizaciones == []
    assert env.comentarios == []


def test_cambio_de_nivel_crea_comentario_interno_con_motivo(monkeypatch):
    env = entorno(monkeypatch)
    respuesta = client.patch(URL, json={"nivel": "N3", "motivo": "requiere ingenieria"})
    assert respuesta.status_code == 200
    assert env.comentarios == [
        {
            "autor": "sistema",
            "autor_rol": "agente",
            "contenido": "Escalamiento: N1 a N3. Motivo: requiere ingenieria",
            "interno": True,
        }
    ]


def test_cambio_de_nivel_sin_motivo_omite_motivo(monkeypatch):
    env = entorno(monkeypatch)
    client.patch(URL, json={"nivel": "N3"})
    assert env.comentarios[0]["contenido"] == "Escalamiento: N1 a N3."


def test_cambio_de_escalamiento_jerarquico_crea_comentario(monkeypatch):
    env = entorno(monkeypatch)
    client.patch(URL, json={"escalamiento_jerarquico": "gerente_operaciones", "motivo": "caida masiva"})
    assert len(env.comentarios) == 1
    assert env.comentarios[0]["interno"] is True
    assert "gerente_operaciones" in env.comentarios[0]["contenido"]
    assert env.comentarios[0]["contenido"].endswith("Motivo: caida masiva")


def test_nivel_sin_cambio_real_no_crea_comentario(monkeypatch):
    env = entorno(monkeypatch)
    assert client.patch(URL, json={"nivel": "N1"}).status_code == 200
    assert env.comentarios == []


def test_cambio_de_prioridad_recalcula_vencimientos_desde_creado_en(monkeypatch):
    env = entorno(monkeypatch, prioridad="P4")
    respuesta = client.patch(URL, json={"prioridad": "P1"})
    assert respuesta.status_code == 200
    assert env.actualizaciones[0]["vence_respuesta_en"] == "2026-01-01T10:15:00+00:00"
    assert env.actualizaciones[0]["vence_resolucion_en"] == "2026-01-01T12:00:00+00:00"


def test_prioridad_sin_cambio_no_recalcula_vencimientos(monkeypatch):
    env = entorno(monkeypatch, prioridad="P2")
    client.patch(URL, json={"prioridad": "P2", "tags": ["x"]})
    assert "vence_respuesta_en" not in env.actualizaciones[0]
    assert "vence_resolucion_en" not in env.actualizaciones[0]


def test_patch_sin_prioridad_no_toca_vencimientos(monkeypatch):
    env = entorno(monkeypatch)
    client.patch(URL, json={"nivel": "N2"})
    assert env.actualizaciones == [{"nivel": "N2"}]


def test_prioridad_desde_null_calcula_vencimientos(monkeypatch):
    env = entorno(monkeypatch, prioridad=None)
    client.patch(URL, json={"prioridad": "P3"})
    assert env.actualizaciones[0]["vence_resolucion_en"] == "2026-01-01T18:00:00+00:00"
