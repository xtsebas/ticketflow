from fastapi.testclient import TestClient

from app.main import app
from app.repositories import categorias as repo_categorias
from app.repositories import estadisticas as repo_estadisticas

client = TestClient(app)

SLUGS = [f"cat_{i}" for i in range(1, 9)]
CATEGORIAS = [{"id": f"id-{i}", "slug": slug} for i, slug in enumerate(SLUGS, start=1)]


def ticket(categoria, estado="abierto", prioridad=None, tags=()):
    return {"categoria_id": f"id-{categoria}", "estado": estado, "prioridad": prioridad, "tags": list(tags)}


def pedir(monkeypatch, tickets):
    monkeypatch.setattr(repo_categorias, "listar", lambda: CATEGORIAS)
    monkeypatch.setattr(repo_estadisticas, "listar_campos_tickets", lambda: tickets)
    respuesta = client.get("/estadisticas")
    assert respuesta.status_code == 200
    return respuesta.json()


def test_sin_datos(monkeypatch):
    cuerpo = pedir(monkeypatch, [])
    assert cuerpo["por_categoria"] == [{"clave": slug, "total": 0} for slug in SLUGS]
    assert cuerpo["por_estado"] == [
        {"clave": e, "total": 0} for e in ["abierto", "en_progreso", "resuelto", "cerrado"]
    ]
    assert cuerpo["por_prioridad"] == [{"clave": p, "total": 0} for p in ["P1", "P2", "P3", "P4"]]
    assert cuerpo["por_tag"] == []


def test_con_datos(monkeypatch):
    cuerpo = pedir(
        monkeypatch,
        [
            ticket(3, "abierto", "P1", ["qr", "pago"]),
            ticket(3, "resuelto", "P1", ["qr"]),
            ticket(1, "cerrado", "P3", ["qr", "correo"]),
            ticket(8, "abierto", None, []),
        ],
    )
    categorias = {c["clave"]: c["total"] for c in cuerpo["por_categoria"]}
    assert categorias["cat_3"] == 2 and categorias["cat_1"] == 1 and categorias["cat_8"] == 1
    assert categorias["cat_2"] == 0
    assert [c["clave"] for c in cuerpo["por_categoria"]] == SLUGS
    assert cuerpo["por_estado"] == [
        {"clave": "abierto", "total": 2},
        {"clave": "en_progreso", "total": 0},
        {"clave": "resuelto", "total": 1},
        {"clave": "cerrado", "total": 1},
    ]
    assert cuerpo["por_prioridad"] == [
        {"clave": "P1", "total": 2},
        {"clave": "P2", "total": 0},
        {"clave": "P3", "total": 1},
        {"clave": "P4", "total": 0},
        {"clave": "sin_prioridad", "total": 1},
    ]
    assert cuerpo["por_tag"][0] == {"clave": "qr", "total": 3}
    assert {t["clave"]: t["total"] for t in cuerpo["por_tag"]} == {"qr": 3, "pago": 1, "correo": 1}


def test_sin_prioridad_ausente_si_todos_tienen(monkeypatch):
    cuerpo = pedir(monkeypatch, [ticket(1, prioridad="P2")])
    assert "sin_prioridad" not in [p["clave"] for p in cuerpo["por_prioridad"]]


def test_tags_ordenados_descendente(monkeypatch):
    cuerpo = pedir(monkeypatch, [ticket(1, tags=["a"]), ticket(1, tags=["b", "c"]), ticket(1, tags=["c"])])
    totales = [t["total"] for t in cuerpo["por_tag"]]
    assert totales == sorted(totales, reverse=True)
    assert cuerpo["por_tag"][0] == {"clave": "c", "total": 2}


def test_paginacion_del_repositorio(monkeypatch):
    paginas = [[{"x": i} for i in range(1000)], [{"x": 1}]]
    rangos = []

    class Consulta:
        def __getattr__(self, _nombre):
            return lambda *a, **k: self

        def range(self, desde, hasta):
            rangos.append((desde, hasta))
            self.pagina = paginas[len(rangos) - 1]
            return self

        def execute(self):
            class R:
                data = self.pagina

            return R

    class Cliente:
        def table(self, _):
            return Consulta()

    monkeypatch.setattr(repo_estadisticas, "get_client", lambda: Cliente())
    assert len(repo_estadisticas.listar_campos_tickets()) == 1001
    assert rangos == [(0, 999), (1000, 1999)]
