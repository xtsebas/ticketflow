# TicketFlow Service Desk

Service Desk de TicketFlow (plataforma de venta de entradas en línea) para el curso de Administración y Mantenimiento de Sistemas (ITIL v4). Los usuarios ingresan tickets y el equipo de soporte los atiende.

Monorepo:

- `backend/`: API en FastAPI con Supabase (Postgres). Solo estructura; los endpoints devuelven 501 salvo `/health`.
- `frontend/`: pendiente.

## Entorno virtual

Requiere Python 3.11 o superior.

```
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

```
cp .env.example .env
```

| Variable | Descripción |
| --- | --- |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (solo backend, nunca en el frontend) |
| `CORS_ORIGINS` | Orígenes permitidos separados por comas. Por defecto `http://localhost:5173,http://localhost:3000` |

La app arranca sin `.env`; en ese caso `/health` reporta `"supabase": false`.

## Base de datos

En el SQL editor de un proyecto Supabase vacío, ejecuta en este orden:

1. `backend/db/schema.sql`
2. `backend/db/seed.sql`

Las tres tablas tienen RLS habilitado sin políticas: el backend usa la service role key, que ignora RLS.

## Servidor

```
cd backend
uvicorn app.main:app --reload
```

Documentación interactiva en http://localhost:8000/docs.

## Pruebas

```
cd backend
pytest
```

No requieren Supabase.

## Estructura

```
backend/
  app/
    main.py              aplicación FastAPI y CORS
    core/config.py       configuración con pydantic-settings
    domain/enums.py      valores fijos del dominio
    db/client.py         cliente Supabase perezoso
    repositories/        único acceso a datos
    schemas/             modelos Pydantic
    services/            lógica de negocio (prioridad, sla, tickets)
    api/routers/         endpoints
  db/                    schema.sql y seed.sql
  tests/                 test_smoke.py
frontend/README.md
```
