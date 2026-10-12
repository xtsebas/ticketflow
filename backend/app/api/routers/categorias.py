from fastapi import APIRouter, HTTPException

from app.schemas.categoria import CategoriaOut

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
def listar_categorias():
    raise HTTPException(status_code=501, detail="Not Implemented")
