# TicketFlow Service Desk

Service Desk de TicketFlow (plataforma de venta de entradas en línea) para el curso de Administración y Mantenimiento de Sistemas (ITIL v4). Los usuarios ingresan tickets y el equipo de soporte los atiende.

Monorepo:

- `backend/`: API en FastAPI con Supabase (Postgres). Tickets, comentarios, categorías, estadísticas, cálculo de prioridad y vencimientos SLA.
- `frontend/`: SPA en React + Vite. Ingreso de tickets, tablero de soporte, detalle con comentarios y estadísticas.

Para levantar todo en local: configura la base de datos, arranca el servidor del backend y luego el frontend (secciones siguientes).

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
| `AUTH_SECRET` | Secreto con el que se firman los tokens de sesión de soporte. Si se deja vacío se genera uno aleatorio al arrancar y las sesiones se cierran cada vez que el servidor se reinicia. Defínelo para que persistan |

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

## Frontend

Requiere Node.js 20.19 o superior y el backend corriendo en `localhost:8000`.

```
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. Para apuntar a otro backend, crea `frontend/.env.local` con `VITE_API_URL=https://...` (el origen del frontend debe estar en `CORS_ORIGINS` del backend).

Build de producción: `npm run build` (genera `frontend/dist/`) y `npm run preview` para revisarlo.

### Vistas

El selector Usuario / Soporte del encabezado cambia de vista. El usuario del servicio no inicia sesión: escribe su nombre, que queda como solicitante y autor de sus comentarios. Las vistas de soporte piden iniciar sesión con un usuario de soporte (ver "Sesión de soporte"); el token se guarda en el navegador y "Salir" cierra la sesión.

| Ruta | Rol | Requerimiento | Descripción |
| --- | --- | --- | --- |
| `#/` | Ambos | 1 | Nuevo ticket: tipo, servicio del catálogo, impacto y urgencia sugeridos según la Fase 1, y prioridad y vencimientos SLA calculados |
| `#/mis-tickets` | Usuario | 3 | Tickets creados desde este navegador y búsqueda por número |
| `#/tickets/:id` | Ambos | 3 y 4 | Detalle con comentarios de seguimiento; con sesión de soporte además se ven las notas internas y se puede editar el ticket |
| `#/soporte` | Soporte (con sesión) | 2 y 4 | Tablero: cola ordenada por prioridad y antigüedad, filtros, métricas y panel lateral para atender sin salir del tablero |
| `#/estadisticas` | Soporte (con sesión) | 5 | Gráficas por categoría, tipo, estado, prioridad, tag y día |

Sin sesión, `#/soporte` y `#/estadisticas` muestran el formulario de inicio de sesión.

El router usa el hash (`#/ruta`), así que el build se puede servir como archivos estáticos sin configurar rutas en el servidor.

## Docker

Alternativa a levantar el backend y el frontend por separado. Requiere Docker con Compose y haber configurado la base de datos y `backend/.env` (secciones anteriores).

```
docker compose up --build
```

- Backend en http://localhost:8000: imagen de Python 3.12 con uvicorn; lee las variables de `backend/.env` (si no existe arranca igual, sin Supabase).
- Frontend en http://localhost:5173: build de Vite servido con nginx.

`VITE_API_URL` se fija al construir la imagen del frontend (por defecto `http://localhost:8000`). Para otro backend: `VITE_API_URL=https://... docker compose up --build`. Define `AUTH_SECRET` en `backend/.env` para que las sesiones de soporte sobrevivan a un reinicio del contenedor.

Los datos de demostración se cargan desde el contenedor del backend:

```
docker compose exec backend python scripts/seed_demo.py --reset
```

## Pruebas

```
cd backend
pytest
```

No requieren Supabase ni `.env`: usan repositorios simulados.

Prueba de humo contra el Supabase real (única excepción; requiere `.env` con credenciales):

```
cd backend
python scripts/smoke_real.py
```

Crea tickets con solicitante `smoke_*`, verifica los endpoints y los borra al final. Sale con código distinto de cero si alguna verificación falla.

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
| POST | `/auth/login` | Inicia sesión de soporte y devuelve un token |
| GET | `/categorias` | Las 8 categorías, ordenadas por tipo y nombre |
| POST | `/tickets` | Crea un ticket (estado `abierto`, nivel `N1`) |
| GET | `/tickets` | Lista con filtros `estado`, `prioridad`, `nivel`, `categoria_id`, `tag`. Requiere sesión de soporte |
| GET | `/tickets/{ticket_id}` | Detalle con categoría y comentarios; `rol=solicitante` (por defecto) oculta los internos. `rol=agente` requiere sesión de soporte |
| PATCH | `/tickets/{ticket_id}` | Actualiza campos, valida transiciones de estado y registra escalamientos. Requiere sesión de soporte |
| POST | `/tickets/{ticket_id}/comentarios` | Agrega un comentario (los internos solo los crea un agente). Con `autor_rol` `agente` requiere sesión de soporte |
| GET | `/estadisticas` | Conteos por categoría, tag, prioridad y estado. Requiere sesión de soporte |

Ejemplos (con el servidor en `localhost:8000`; reemplaza `$TICKET_ID` y `$CATEGORIA_ID` por UUID reales):

```
curl localhost:8000/health

curl localhost:8000/categorias

curl -X POST localhost:8000/tickets -H 'Content-Type: application/json' -d '{
  "titulo": "QR rechazado", "descripcion": "No me deja entrar",
  "categoria_id": "'$CATEGORIA_ID'", "tags": ["qr"],
  "impacto": "alto", "urgencia": "alta", "solicitante": "ana"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"usuario": "soporte1", "contrasena": "<contraseña>"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')

curl -H "Authorization: Bearer $TOKEN" 'localhost:8000/tickets?estado=abierto&prioridad=P1&nivel=N1&tag=qr'

curl -H "Authorization: Bearer $TOKEN" "localhost:8000/tickets/$TICKET_ID?rol=agente"

curl -X PATCH localhost:8000/tickets/$TICKET_ID -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nivel": "N3", "motivo": "Requiere ingeniería"}'

curl -X POST localhost:8000/tickets/$TICKET_ID/comentarios -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"autor": "soporte1", "autor_rol": "agente", "contenido": "Revisando", "interno": true}'

curl -H "Authorization: Bearer $TOKEN" localhost:8000/estadisticas
```

## Contrato para el frontend

Base: `http://localhost:8000`. Cuerpos y respuestas en JSON.

### Sesión de soporte

Hay cuatro usuarios de soporte: `soporte1`, `soporte2`, `soporte3` y `soporte4`. Sus contraseñas se guardan hasheadas (PBKDF2-SHA256 con sal propia) en `backend/app/repositories/usuarios.py`; no existe ninguna contraseña en texto plano en el repositorio. Para cambiar una:

```
cd backend
python -c "from app.services.auth import hashear_contrasena; print(hashear_contrasena('nueva_contrasena'))"
```

y pegar el resultado en `USUARIOS_SOPORTE`.

`POST /auth/login` recibe `{"usuario": "...", "contrasena": "..."}` y responde `{"token": "...", "usuario": "..."}`. El token dura 8 horas y se envía en el encabezado `Authorization: Bearer <token>`. Usuario o contraseña incorrectos responden 401 con el mismo mensaje en ambos casos.

Exigen sesión de soporte: `GET /tickets`, `PATCH /tickets/{id}`, `GET /estadisticas`, `GET /tickets/{id}?rol=agente` y `POST /tickets/{id}/comentarios` con `autor_rol` `agente`. Sin token válido responden 401 `no_autenticado`. Crear tickets, ver categorías, ver un ticket como solicitante y comentar como solicitante siguen sin autenticación.

### Detalle del ticket y parámetro `rol`

`GET /tickets/{ticket_id}?rol=solicitante|agente` (por defecto `solicitante`).

- `solicitante`: oculta los comentarios con `interno: true`.
- `agente`: devuelve todos los comentarios.
- Los comentarios vienen ordenados por `creado_en` ascendente y el ticket incluye `categoria` completa (`nombre` y `tipo`).
- Un valor de `rol` distinto responde 422.

### PATCH y campo `motivo`

`PATCH /tickets/{ticket_id}` acepta `estado`, `prioridad`, `categoria_id`, `tags`, `nivel`, `escalamiento_jerarquico` y `motivo`. Solo se actualizan los campos enviados; un campo en `null` se trata como no enviado.

- `motivo` es opcional y no se guarda en el ticket: solo acompaña el comentario automático.
- Si cambia `nivel` o `escalamiento_jerarquico`, el backend crea un comentario interno (autor `sistema`, `autor_rol` `agente`) con el texto `Escalamiento: N1 a N3. Motivo: ...` (sin la parte del motivo si no se envía).
- Si cambia `prioridad`, los vencimientos se recalculan a partir de `creado_en`.
- Un cuerpo sin ningún campo actualizable (por ejemplo solo `motivo`) responde 422.
- Transiciones de estado permitidas: `abierto` a `en_progreso`, `en_progreso` a `resuelto`, `resuelto` a `cerrado` y `resuelto` a `en_progreso` (reapertura). `cerrado` es final. Cualquier otra, incluida la repetición del mismo estado, responde 409.

### Formato de errores

Todos los errores tienen la forma `{"detalle": ..., "codigo": ...}`.

| Estado | `codigo` | Cuándo ocurre |
| --- | --- | --- |
| 201 | (sin error) | `POST /tickets` y `POST /tickets/{id}/comentarios` crean el recurso y lo devuelven |
| 401 | `no_autenticado` | Falta el token, es inválido o expiró, o las credenciales de `/auth/login` son incorrectas. `detalle` es un texto |
| 404 | `no_encontrado` | El ticket o la categoría no existen, o la ruta no existe. `detalle` es un texto |
| 409 | `conflicto` | Transición de estado no permitida. `detalle` es un texto, p. ej. `Transicion de estado no permitida: abierto a cerrado` |
| 422 | `validacion_error` | Valor fuera de catálogo, UUID mal formado, cuerpo vacío en PATCH, contenido vacío o comentario interno de un solicitante. `detalle` es una lista de `{campo, mensaje, tipo}` |

También usan este formato el 405 (`metodo_no_permitido`) y el 500 (`error_interno`).

### Filtros de `GET /tickets`

Todos opcionales y combinables (se aplican con AND):

| Parámetro | Valores |
| --- | --- |
| `estado` | `abierto`, `en_progreso`, `resuelto`, `cerrado` |
| `prioridad` | `P1`, `P2`, `P3`, `P4` |
| `nivel` | `N1`, `N2`, `N3` |
| `categoria_id` | UUID de una categoría |
| `tag` | Un tag; coincide si está dentro del arreglo `tags` |

Orden: prioridad ascendente con los tickets sin prioridad al final, y luego `creado_en` ascendente. Cada elemento incluye `categoria_nombre`.

### Respuesta de `/estadisticas`

```
{
  "por_categoria": [{"clave": "correo_confirmacion_no_entregado", "total": 0}, ...],
  "por_tag": [{"clave": "qr", "total": 4}, ...],
  "por_prioridad": [{"clave": "P1", "total": 2}, ..., {"clave": "sin_prioridad", "total": 1}],
  "por_estado": [{"clave": "abierto", "total": 5}, {"clave": "en_progreso", "total": 0}, ...]
}
```

- `por_categoria`: las 8 categorías (clave = `slug`), aunque tengan 0, ordenadas por tipo y nombre como `/categorias`.
- `por_estado`: los 4 estados con 0, en el orden del flujo.
- `por_prioridad`: P1 a P4 con 0; `sin_prioridad` aparece solo si hay tickets sin prioridad.
- `por_tag`: solo tags existentes, de mayor a menor total.

### Reglas de SLA

La prioridad se calcula al crear el ticket a partir de `impacto` y `urgencia`:

| Impacto \ Urgencia | alta | media | baja |
| --- | --- | --- | --- |
| alto | P1 | P2 | P3 |
| medio | P2 | P3 | P4 |
| bajo | P3 | P4 | P4 |

| Prioridad | Vence respuesta | Vence resolución |
| --- | --- | --- |
| P1 | 15 minutos | 2 horas |
| P2 | 30 minutos | 4 horas |
| P3 | 1 hora | 8 horas |
| P4 | 4 horas | 1 día hábil |

- Los minutos y las horas son tiempo transcurrido desde `creado_en`.
- Un día hábil se calcula en la zona `America/Guatemala`: se avanza día por día contando solo de lunes a viernes, conservando la hora y sin feriados. Un P4 creado en viernes, sábado o domingo vence el lunes a la misma hora.
- Provisional: el plazo de resolución de P4 (1 día hábil) es una decisión provisional.
- Pendiente: en la matriz de la Fase 1 (sección 6), la celda bajo × baja tiene respuesta en 8 horas y resolución en 2 días hábiles. Hoy el backend le aplica los tiempos generales de P4.
- `vence_respuesta_en` y `vence_resolucion_en` se guardan al crear y se recalculan si cambia la prioridad.

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
    services/            lógica de negocio (prioridad, sla, tickets, auth)
    api/routers/         endpoints
  db/                    schema.sql y seed.sql
  scripts/seed_demo.py   datos de demostración
  scripts/smoke_real.py  prueba de humo contra Supabase real
  tests/                 pruebas con repositorios simulados
  Dockerfile             imagen del backend
frontend/
  src/
    main.jsx             punto de entrada
    App.jsx              rutas
    pages/               una vista por ruta
    components/          encabezado, panel de ticket, gráficas y componentes compartidos
    lib/api.js           cliente del backend
    lib/constants.js     valores del dominio y criterios de la Fase 1
    lib/router.jsx       router por hash
    lib/session.jsx      rol, nombre y sesión de soporte
    styles.css           estilos
docker/                  Dockerfile del frontend
docker-compose.yml       backend y frontend con Docker
```
