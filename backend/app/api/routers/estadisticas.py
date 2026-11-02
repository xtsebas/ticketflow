from fastapi import APIRouter, Depends

from app.api.dependencies import requiere_agente
from app.schemas.estadisticas import EstadisticasOut
from app.services import tickets as servicio

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("", response_model=EstadisticasOut, dependencies=[Depends(requiere_agente)])
def obtener_estadisticas():
    return servicio.obtener_estadisticas()
