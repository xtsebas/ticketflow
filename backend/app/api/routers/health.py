from fastapi import APIRouter

from app.db.client import get_client

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    try:
        get_client().table("categorias").select("id").limit(1).execute()
        supabase = True
    except Exception:
        supabase = False
    return {"status": "ok", "supabase": supabase}
