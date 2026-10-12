from datetime import datetime

from app.domain.enums import Prioridad


def calcular_vencimientos(prioridad: Prioridad, creado_en: datetime) -> tuple[datetime, datetime]:
    raise NotImplementedError
