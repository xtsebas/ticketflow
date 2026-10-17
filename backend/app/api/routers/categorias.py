from fastapi import APIRouter

from app.repositories import categorias as repo
from app.schemas.categoria import CategoriaOut

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
def listar_categorias():
    return repo.listar()
