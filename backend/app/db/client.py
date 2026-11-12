from functools import lru_cache

import httpx
from supabase import Client, create_client
from supabase.lib.client_options import SyncClientOptions

from app.core.config import get_settings

TIMEOUT_SEGUNDOS = 30


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY no estan configuradas")
    opciones = SyncClientOptions(httpx_client=httpx.Client(http2=False, timeout=TIMEOUT_SEGUNDOS))
    return create_client(settings.supabase_url, settings.supabase_service_role_key, opciones)
