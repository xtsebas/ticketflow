from app.domain.enums import Impacto, Prioridad, Urgencia

MATRIZ_PRIORIDAD = {
    (Impacto.alto, Urgencia.alta): Prioridad.P1,
    (Impacto.alto, Urgencia.media): Prioridad.P2,
    (Impacto.alto, Urgencia.baja): Prioridad.P3,
    (Impacto.medio, Urgencia.alta): Prioridad.P2,
    (Impacto.medio, Urgencia.media): Prioridad.P3,
    (Impacto.medio, Urgencia.baja): Prioridad.P4,
    (Impacto.bajo, Urgencia.alta): Prioridad.P3,
    (Impacto.bajo, Urgencia.media): Prioridad.P4,
    (Impacto.bajo, Urgencia.baja): Prioridad.P4,
}


def calcular_prioridad(impacto: Impacto, urgencia: Urgencia) -> Prioridad:
    return MATRIZ_PRIORIDAD[(Impacto(impacto), Urgencia(urgencia))]
