from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.domain.enums import Prioridad
from app.services.sla import calcular_vencimientos, sumar_dias_habiles

GUATEMALA = ZoneInfo("America/Guatemala")
JUEVES = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "prioridad,respuesta,resolucion",
    [
        ("P1", timedelta(minutes=15), timedelta(hours=2)),
        ("P2", timedelta(minutes=30), timedelta(hours=4)),
        ("P3", timedelta(hours=1), timedelta(hours=8)),
    ],
)
def test_vencimientos_por_tiempo_transcurrido(prioridad, respuesta, resolucion):
    vence_respuesta, vence_resolucion = calcular_vencimientos(Prioridad(prioridad), JUEVES)
    assert vence_respuesta == JUEVES + respuesta
    assert vence_resolucion == JUEVES + resolucion


def test_p4_respuesta_en_cuatro_horas_y_resolucion_en_un_dia_habil():
    vence_respuesta, vence_resolucion = calcular_vencimientos(Prioridad.P4, JUEVES)
    assert vence_respuesta == JUEVES + timedelta(hours=4)
    assert vence_resolucion == JUEVES + timedelta(days=1)


@pytest.mark.parametrize("dia,nombre", [(2, "viernes"), (3, "sabado"), (4, "domingo")])
def test_p4_creado_en_viernes_sabado_o_domingo_termina_el_lunes(dia, nombre):
    creado = datetime(2026, 1, dia, 15, 30, tzinfo=GUATEMALA)
    assert creado.weekday() == {"viernes": 4, "sabado": 5, "domingo": 6}[nombre]
    _, vence_resolucion = calcular_vencimientos(Prioridad.P4, creado)
    esperado = datetime(2026, 1, 5, 15, 30, tzinfo=GUATEMALA)
    assert vence_resolucion == esperado
    assert vence_resolucion.astimezone(GUATEMALA).weekday() == 0


def test_dia_habil_usa_zona_guatemala_y_conserva_la_hora():
    creado_utc = datetime(2026, 1, 3, 3, 0, tzinfo=timezone.utc)
    assert creado_utc.astimezone(GUATEMALA).weekday() == 4
    resultado = sumar_dias_habiles(creado_utc, 1)
    assert resultado.astimezone(GUATEMALA) == datetime(2026, 1, 5, 21, 0, tzinfo=GUATEMALA)


def test_resultado_conserva_la_zona_del_origen():
    assert calcular_vencimientos(Prioridad.P4, JUEVES)[1].tzinfo == timezone.utc


def test_fecha_sin_zona_se_trata_como_utc():
    ingenua = datetime(2026, 1, 1, 10, 0)
    assert calcular_vencimientos(Prioridad.P1, ingenua)[0] == JUEVES + timedelta(minutes=15)


def test_prioridad_invalida():
    with pytest.raises(ValueError):
        calcular_vencimientos("P9", JUEVES)
