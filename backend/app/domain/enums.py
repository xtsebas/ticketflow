from enum import StrEnum


class Tipo(StrEnum):
    solicitud = "solicitud"
    incidente = "incidente"


class Impacto(StrEnum):
    alto = "alto"
    medio = "medio"
    bajo = "bajo"


class Urgencia(StrEnum):
    alta = "alta"
    media = "media"
    baja = "baja"


class Prioridad(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Estado(StrEnum):
    abierto = "abierto"
    en_progreso = "en_progreso"
    resuelto = "resuelto"
    cerrado = "cerrado"


class Nivel(StrEnum):
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"


class EscalamientoJerarquico(StrEnum):
    gerente_operaciones = "gerente_operaciones"
    direccion_comercial = "direccion_comercial"


class AutorRol(StrEnum):
    solicitante = "solicitante"
    agente = "agente"
