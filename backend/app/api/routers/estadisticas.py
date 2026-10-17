from fastapi import APIRouter

from app.schemas.estadisticas import EstadisticasOut
from app.services import tickets as servicio

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("", response_model=EstadisticasOut)
def obtener_estadisticas():
    return servicio.obtener_estadisticas()
