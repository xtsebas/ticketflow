from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.domain.enums import Prioridad

ZONA_HORARIA = ZoneInfo("America/Guatemala")
DIAS_HABILES = range(5)


def sumar_dias_habiles(inicio: datetime, dias: int) -> datetime:
    local = inicio.astimezone(ZONA_HORARIA)
    pendientes = dias
    while pendientes > 0:
        local += timedelta(days=1)
        if local.weekday() in DIAS_HABILES:
            pendientes -= 1
    return local.astimezone(inicio.tzinfo)


TIEMPOS_RESPUESTA = {
    Prioridad.P1: timedelta(minutes=15),
    Prioridad.P2: timedelta(minutes=30),
    Prioridad.P3: timedelta(hours=1),
    Prioridad.P4: timedelta(hours=4),
}

PLAZOS_RESOLUCION = {
    Prioridad.P1: lambda creado_en: creado_en + timedelta(hours=2),
    Prioridad.P2: lambda creado_en: creado_en + timedelta(hours=4),
    Prioridad.P3: lambda creado_en: creado_en + timedelta(hours=8),
    Prioridad.P4: lambda creado_en: sumar_dias_habiles(creado_en, 1),
}


def calcular_vencimientos(prioridad: Prioridad, creado_en: datetime) -> tuple[datetime, datetime]:
    prioridad = Prioridad(prioridad)
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)
    return creado_en + TIEMPOS_RESPUESTA[prioridad], PLAZOS_RESOLUCION[prioridad](creado_en)
