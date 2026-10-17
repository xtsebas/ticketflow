import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import seed_demo

from app.domain.enums import Estado, Impacto, Nivel, Prioridad, Urgencia
from app.services.prioridad import calcular_prioridad
from app.services.sla import calcular_vencimientos

CATEGORIAS = [{"id": f"id-{slug}", "slug": slug} for slug in dict.fromkeys(t[0] for t in seed_demo.TICKETS)]


def datos():
    return seed_demo.construir(CATEGORIAS)


def test_25_tickets_con_prefijo_demo():
    tickets = [t for t, _ in datos()]
    assert len(tickets) == 25
    assert all(t["solicitante"].startswith("demo_") for t in tickets)


def test_cubre_catalogos():
    tickets = [t for t, _ in datos()]
    assert len({t["categoria_id"] for t in tickets}) == 8
    assert {t["estado"] for t in tickets} == {e.value for e in Estado}
    assert {t["nivel"] for t in tickets} == {n.value for n in Nivel}
    assert {t["prioridad"] for t in tickets} == {p.value for p in Prioridad}
    assert {"login", "pagos", "qr", "correo", "panel"} <= {tag for t in tickets for tag in t["tags"]}


def test_valores_validos():
    for ticket, _ in datos():
        Impacto(ticket["impacto"])
        Urgencia(ticket["urgencia"])


def test_cubre_las_nueve_combinaciones_de_impacto_y_urgencia():
    combinaciones = {(t["impacto"], t["urgencia"]) for t, _ in datos()}
    assert len(combinaciones) == len(Impacto) * len(Urgencia)


def test_prioridad_y_vencimientos_vienen_de_los_servicios():
    for ticket, _ in datos():
        esperada = calcular_prioridad(ticket["impacto"], ticket["urgencia"])
        assert ticket["prioridad"] == esperada.value
        creado = datetime.fromisoformat(ticket["creado_en"])
        respuesta, resolucion = calcular_vencimientos(esperada, creado)
        assert ticket["vence_respuesta_en"] == respuesta.isoformat()
        assert ticket["vence_resolucion_en"] == resolucion.isoformat()


def test_aparecen_las_cuatro_prioridades():
    assert {t["prioridad"] for t, _ in datos()} == {p.value for p in Prioridad}


def test_comentarios_en_al_menos_10_tickets_publicos_e_internos():
    con_comentarios = [c for _, c in datos() if c]
    assert len(con_comentarios) >= 10
    todos = [c for coms in con_comentarios for c in coms]
    assert any(c["interno"] for c in todos) and any(not c["interno"] for c in todos)
    assert all(c["autor_rol"] == "agente" for c in todos if c["interno"])


def test_reset_solo_borra_prefijo_exacto(monkeypatch):
    filas = [
        {"id": "1", "solicitante": "demo_ana"},
        {"id": "2", "solicitante": "demoX_otro"},
        {"id": "3", "solicitante": "demonio"},
    ]

    class Consulta:
        def __init__(self):
            self.borrados = []

        def table(self, _):
            return self

        def select(self, *_):
            return self

        def like(self, *_):
            return self

        def execute(self):
            class R:
                data = filas

            return R

        def delete(self):
            return self

        def in_(self, _campo, ids):
            self.borrados.extend(ids)
            return self

    cliente = Consulta()
    monkeypatch.setattr(seed_demo, "get_client", lambda: cliente)
    assert seed_demo.borrar_demo() == 1
    assert cliente.borrados == ["1"]
