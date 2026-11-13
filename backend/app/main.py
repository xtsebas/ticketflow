from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, categorias, comentarios, estadisticas, health, tickets
from app.core.access_log import AccessLogMiddleware, crear_logger_acceso
from app.core.config import get_settings
from app.core.errors import registrar_manejadores

settings = get_settings()

app = FastAPI(title="TicketFlow Service Desk")
registrar_manejadores(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.log_file:
    app.add_middleware(
        AccessLogMiddleware,
        logger=crear_logger_acceso(settings.log_file, settings.log_max_bytes, settings.log_backups),
        service_name=settings.service_name,
        fallos_porcentaje=settings.fallos_porcentaje,
    )

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(tickets.router)
app.include_router(comentarios.router)
app.include_router(estadisticas.router)
