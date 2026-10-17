from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import categorias, comentarios, estadisticas, health, tickets
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

app.include_router(health.router)
app.include_router(categorias.router)
app.include_router(tickets.router)
app.include_router(comentarios.router)
app.include_router(estadisticas.router)
