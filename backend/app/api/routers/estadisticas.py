from fastapi import APIRouter, HTTPException

from app.schemas.estadisticas import EstadisticasOut

router = APIRouter(prefix="/estadisticas", tags=["estadisticas"])


@router.get("", response_model=EstadisticasOut)
def obtener_estadisticas():
    raise HTTPException(status_code=501, detail="Not Implemented")
