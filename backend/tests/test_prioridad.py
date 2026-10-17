import pytest

from app.domain.enums import Impacto, Prioridad, Urgencia
from app.services.prioridad import calcular_prioridad

ESPERADAS = [
    ("alto", "alta", "P1"),
    ("alto", "media", "P2"),
    ("alto", "baja", "P3"),
    ("medio", "alta", "P2"),
    ("medio", "media", "P3"),
    ("medio", "baja", "P4"),
    ("bajo", "alta", "P3"),
    ("bajo", "media", "P4"),
    ("bajo", "baja", "P4"),
]


@pytest.mark.parametrize("impacto,urgencia,esperada", ESPERADAS)
def test_matriz_completa(impacto, urgencia, esperada):
    assert calcular_prioridad(Impacto(impacto), Urgencia(urgencia)) == Prioridad(esperada)


def test_acepta_cadenas():
    assert calcular_prioridad("alto", "alta") == Prioridad.P1


def test_la_matriz_cubre_las_nueve_combinaciones():
    assert len(ESPERADAS) == len(Impacto) * len(Urgencia)


@pytest.mark.parametrize("impacto,urgencia", [("critico", "alta"), ("alto", "urgente"), ("", ""), (None, "alta")])
def test_valor_fuera_de_catalogo(impacto, urgencia):
    with pytest.raises(ValueError):
        calcular_prioridad(impacto, urgencia)
