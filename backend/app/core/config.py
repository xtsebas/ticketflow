import secrets
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    auth_secret: str = Field(default="", validate_default=True)
    log_file: str = ""
    log_max_bytes: int = Field(default=5_242_880, gt=0)
    log_backups: int = Field(default=3, ge=0)
    service_name: str = "ticketflow-api"
    fallos_porcentaje: float = Field(default=0.0, ge=0, le=100)

    @field_validator("auth_secret")
    @classmethod
    def generar_secreto(cls, valor: str) -> str:
        return valor or secrets.token_urlsafe(32)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def separar_origenes(cls, valor):
        if isinstance(valor, str):
            return [o.strip() for o in valor.split(",") if o.strip()]
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()
