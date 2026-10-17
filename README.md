# TicketFlow Service Desk

Service Desk de TicketFlow (plataforma de venta de entradas en línea) para el curso de Administración y Mantenimiento de Sistemas (ITIL v4). Los usuarios ingresan tickets y el equipo de soporte los atiende.

Monorepo:

- `backend/`: API en FastAPI con Supabase (Postgres). Tickets, comentarios, categorías y estadísticas implementados. Pendiente: el cálculo de prioridad y vencimientos SLA (`services/prioridad.py` y `services/sla.py`), por lo que los tickets nuevos nacen con prioridad y vencimientos en `null`.
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
cd backend
cp .env.example .env
```

| Variable | Descripción |
| --- | --- |
| `SUPABASE_URL` | URL de la API del proyecto, p. ej. `https://<ref>.supabase.co` (no la cadena `postgresql://`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (Project Settings → API). Solo backend, nunca en el frontend |
| `CORS_ORIGINS` | Orígenes permitidos separados por comas. Por defecto `http://localhost:5173,http://localhost:3000` |

El `.env` se lee desde el directorio donde se ejecuta el comando, así que usa siempre `backend/` como directorio de trabajo. La app arranca sin `.env`; en ese caso `/health` reporta `"supabase": false`.

## Base de datos

En el SQL editor de un proyecto Supabase vacío, ejecuta en este orden:

1. `backend/db/schema.sql`
2. `backend/db/seed.sql` (las 8 categorías)

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

No requieren Supabase ni `.env`: usan repositorios simulados.

## Datos de demostración

```
cd backend
python scripts/seed_demo.py           # inserta 25 tickets con comentarios
python scripts/seed_demo.py --reset   # borra los tickets demo_* y los vuelve a insertar
```

Requiere haber ejecutado `db/seed.sql` (categorías) y tener el `.env` configurado. Todos los tickets de demostración tienen un solicitante que empieza con `demo_`; `--reset` solo borra esos (sus comentarios se eliminan en cascada). Sin `--reset`, el script no inserta si ya existen tickets demo.

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/health` | Estado del servicio y si Supabase es alcanzable |
| GET | `/categorias` | Las 8 categorías, ordenadas por tipo y nombre |
| POST | `/tickets` | Crea un ticket (estado `abierto`, nivel `N1`) |
| GET | `/tickets` | Lista con filtros `estado`, `prioridad`, `nivel`, `categoria_id`, `tag` |
| GET | `/tickets/{ticket_id}` | Detalle con categoría y comentarios; `rol=solicitante` (por defecto) oculta los internos |
| PATCH | `/tickets/{ticket_id}` | Actualiza campos, valida transiciones de estado y registra escalamientos |
| POST | `/tickets/{ticket_id}/comentarios` | Agrega un comentario (los internos solo los crea un agente) |
| GET | `/estadisticas` | Conteos por categoría, tag, prioridad y estado |

Ejemplos (con el servidor en `localhost:8000`; reemplaza `$TICKET_ID` y `$CATEGORIA_ID` por UUID reales):

```
curl localhost:8000/health

curl localhost:8000/categorias

curl -X POST localhost:8000/tickets -H 'Content-Type: application/json' -d '{
  "titulo": "QR rechazado", "descripcion": "No me deja entrar",
  "categoria_id": "'$CATEGORIA_ID'", "tags": ["qr"],
  "impacto": "alto", "urgencia": "alta", "solicitante": "ana"}'

curl 'localhost:8000/tickets?estado=abierto&prioridad=P1&nivel=N1&tag=qr'

curl "localhost:8000/tickets/$TICKET_ID?rol=agente"

curl -X PATCH localhost:8000/tickets/$TICKET_ID -H 'Content-Type: application/json' \
  -d '{"nivel": "N3", "motivo": "Requiere ingeniería"}'

curl -X POST localhost:8000/tickets/$TICKET_ID/comentarios -H 'Content-Type: application/json' \
  -d '{"autor": "soporte_1", "autor_rol": "agente", "contenido": "Revisando", "interno": true}'

curl localhost:8000/estadisticas
```

### Errores

Todos los errores tienen el formato `{"detalle": ..., "codigo": ...}`:

| Estado | `codigo` | Cuándo |
| --- | --- | --- |
| 404 | `no_encontrado` | Ticket o categoría inexistente |
| 409 | `conflicto` | Transición de estado no permitida (abierto → en_progreso → resuelto → cerrado; resuelto → en_progreso reabre) |
| 422 | `validacion_error` | Valor fuera de catálogo, cuerpo inválido o comentario interno de un solicitante. `detalle` es una lista de `{campo, mensaje, tipo}` |

## Estructura

```
backend/
  app/
    main.py              aplicación FastAPI y CORS
    core/config.py       configuración con pydantic-settings
    core/errors.py       formato unificado de errores
    domain/enums.py      valores fijos del dominio
    db/client.py         cliente Supabase perezoso
    repositories/        único acceso a datos
    schemas/             modelos Pydantic
    services/            lógica de negocio (prioridad, sla, tickets)
    api/routers/         endpoints
  db/                    schema.sql y seed.sql
  scripts/seed_demo.py   datos de demostración
  tests/                 pruebas con repositorios simulados
frontend/README.md
```
