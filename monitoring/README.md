# Fase 3 - Monitoreo con ELK

Monitoreo de la API de TicketFlow con Elasticsearch, Kibana, Filebeat y Heartbeat. Todo vive en esta carpeta y se levanta con su propio `docker-compose.yml`, separado del compose de la aplicación (`../docker-compose.yml`), para que `docker compose up` normal no arranque cuatro servicios de Elastic.

El informe técnico está en [`../docs/informe-fase3.md`](../docs/informe-fase3.md).

## Contenido

| Ruta | Qué es |
| --- | --- |
| `docker-compose.yml` | Elasticsearch, Kibana, Filebeat, Heartbeat (8.19.24 fijo), la API instrumentada y el generador de tráfico (perfil `trafico`) |
| `filebeat/filebeat.yml` | Input `filestream` con parser `ndjson` sobre el log de la API; salida al índice `ticketflow-api-AAAA.MM.dd` |
| `heartbeat/heartbeat.yml` | Tres monitores HTTP contra la API |
| `elasticsearch/ticketflow-api-template.json` | Index template explícito (mapeos de los 7 campos obligatorios) |
| `kibana/dashboard.ndjson` | Data views, visualizaciones Lens y dashboard "Monitoreo API - Fase 3" (saved objects) |
| `trafico/generar_trafico.py` | Generador de tráfico continuo (solo biblioteca estándar de Python) |
| `logs/muestra-api.log` | Muestra de registros reales generados por la API |
| `../scripts/importar-dashboard.sh` | Importa el dashboard por la API de Kibana |
| `../scripts/verify-fase3.sh` | Verificación automática de la fase |
| `../backend/app/core/access_log.py` | Middleware que escribe el log de la API |
| `../backend/scripts/limpiar_trafico.py` | Lista o borra los tickets que creó el generador |

## Requisitos

- Docker con Compose v2. Con la pila completa en marcha se midieron cerca de 1,5 GB de memoria en uso (Elasticsearch con 512 MB de heap), con 8 GB asignados a Docker. No se probó con menos; se recomienda no bajar de 4 GB.
- `backend/.env` con `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`. La API instrumentada es la misma de la Fase 2 y usa el Supabase real.
- `python3` y `curl` en el host, solo para el generador desde el host y para `verify-fase3.sh`.
- Puertos libres: 8000 (API), 9200 (Elasticsearch) y 5601 (Kibana). Si el compose de la aplicación está levantado, bájalo antes porque también usa el 8000.

## Configuración

```
cp .env.example .env
```

Edita `monitoring/.env`. El archivo está ignorado por git.

| Variable | Default | Uso |
| --- | --- | --- |
| `FALLOS_PORCENTAJE` | `8` | Porcentaje de peticiones del generador a las que la API responde 500 |
| `TRAFICO_RPS` | `3` | Peticiones por segundo promedio |
| `TRAFICO_DURACION` | `0` | Segundos de duración; `0` es infinito |
| `TRAFICO_PROPORCION_ERROR` | `0.2` | Fracción de peticiones pensadas para provocar 4xx |
| `TRAFICO_MAX_CREACIONES` | `300` | Tope de tickets que el generador crea por ejecución |
| `TRAFICO_SOLO_LECTURA` | vacío | Con `1` el generador no crea ni modifica tickets |
| `TRAFICO_CONTRASENA_SOPORTE` | vacío | Contraseña de las cuentas `soporte1` a `soporte4` |
| `TRAFICO_CONTRASENA_CLIENTE` | vacío | Contraseña de las cuentas de cliente |

Si las contraseñas están vacías, el generador omite los escenarios que requieren sesión y solo ejercita los endpoints públicos y los errores 401.

## Levantar

```
cd monitoring
docker compose up -d --build
```

Arrancan, en este orden: `elasticsearch`, `elasticsearch-setup` (carga el index template y termina), `kibana`, `kibana-setup` (importa el dashboard y termina), `api`, `filebeat` y `heartbeat`. No hay pasos manuales.

```
docker compose ps -a
```

`elasticsearch`, `kibana` y `api` deben figurar `healthy`; `filebeat` y `heartbeat` `running`; los dos `-setup` `Exited (0)`.

## URLs

| Servicio | URL |
| --- | --- |
| Dashboard | http://localhost:5601/app/dashboards#/view/dashboard-monitoreo-api-fase-3 |
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |
| API | http://localhost:8000 (`/health`, `/docs`) |

## Generar tráfico

Desde el compose, como servicio opcional:

```
docker compose --profile trafico up -d trafico
docker compose logs -f trafico
docker compose --profile trafico stop trafico
```

Desde el host:

```
set -a && . ./.env && set +a
python3 trafico/generar_trafico.py --url http://localhost:8000 --rps 3 --duracion 300
```

Parámetros: `--url`, `--rps`, `--duracion`, `--proporcion-error`, `--hilos`, `--max-creaciones`, `--timeout`, `--semilla` y `--solo-lectura`. Cada uno tiene su variable `TRAFICO_*`.

El generador crea tickets reales en tu Supabase. Todos llevan la etiqueta `trafico_auto` y un título que empieza con `[trafico] `. Para verlos o borrarlos:

```
cd ../backend
python scripts/limpiar_trafico.py
python scripts/limpiar_trafico.py --borrar
```

Sin `--borrar` solo cuenta. Con `--borrar` elimina únicamente los tickets que tienen la etiqueta y el prefijo (sus comentarios se eliminan en cascada).

## Proporción de errores

El generador elige un grupo para cada petición: un 20 % (`TRAFICO_PROPORCION_ERROR`) va al grupo de errores del cliente y el resto al de peticiones válidas. Sobre eso, la API responde 500 al 8 % (`FALLOS_PORCENTAJE`) de las peticiones que llevan la cabecera `X-Simular-Fallos`, que solo envía el generador. Resultado esperado: alrededor de 72 % de 2xx, 20 % de 4xx y 8 % de 5xx. `/health` nunca recibe fallos inyectados, y Heartbeat tampoco, para que la disponibilidad refleje solo caídas reales.

## Importar el dashboard

Se importa solo al levantar. Para repetirlo a mano:

```
./scripts/importar-dashboard.sh
```

desde la raíz del repo. Equivale a:

```
curl -X POST 'http://localhost:5601/api/saved_objects/_import?overwrite=true' -H 'kbn-xsrf: true' --form file=@monitoring/kibana/dashboard.ndjson
```

Para exportar de nuevo después de editar en Kibana:

```
curl -X POST 'http://localhost:5601/api/saved_objects/_export' -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
  -d '{"objects":[{"type":"dashboard","id":"dashboard-monitoreo-api-fase-3"}],"includeReferencesDeep":true,"excludeExportDetails":true}' \
  > monitoring/kibana/dashboard.ndjson
```

## Prueba del caso DOWN

```
docker compose stop api
sleep 60
curl -s 'localhost:9200/heartbeat-*/_search?size=1&sort=@timestamp:desc&_source=monitor.id,monitor.status,error.message'
docker compose start api
```

Con la API detenida, el panel "System Status" pasa a DOWN en rojo en cuanto Heartbeat completa su siguiente chequeo (cada 10 a 15 segundos) y el historial muestra barras rojas. Al levantarla vuelve a UP en verde.

## Verificación

```
./scripts/verify-fase3.sh
```

Imprime PASS o FAIL por chequeo y sale con código distinto de cero si alguno falla. Necesita el stack levantado, tráfico en los últimos 15 minutos, la prueba DOWN ya hecha (si no, falla el chequeo de documentos `down`) y `monitoring/logs/muestra-api.log`.

## Estado para tomar la captura del dashboard

1. `docker compose ps -a` sin servicios caídos, y la API arriba.
2. Generador corriendo desde hace entre 6 y 10 minutos (para que haya varias barras por minuto).
3. Opcional pero recomendado: haber hecho la prueba DOWN entre 3 y 8 minutos antes de la captura, para que el historial muestre barras rojas y el estado actual vuelva a UP.
4. Abrir el dashboard. El rango (últimos 15 minutos) y el refresco de 5 segundos ya vienen guardados.
5. Cerrar cualquier aviso de Kibana y usar "Full screen". Con una ventana de 1920 x 1080 los cuatro renglones caben sin desplazarse.

## Bajar todo

```
docker compose --profile trafico down
```

Conserva los datos. Para empezar de cero, borrando índices, registro de Filebeat y dashboard:

```
docker compose --profile trafico down -v
rm -f logs/api.log*
```

## Variables de la API

El middleware solo se activa si `LOG_FILE` está definida; sin ella la API se comporta exactamente como en la Fase 2.

| Variable | Default | Uso |
| --- | --- | --- |
| `LOG_FILE` | vacío | Ruta del log NDJSON. En el compose: `/var/log/ticketflow/api.log` |
| `LOG_MAX_BYTES` | `5242880` | Tamaño máximo antes de rotar |
| `LOG_BACKUPS` | `3` | Archivos rotados que se conservan |
| `SERVICE_NAME` | `ticketflow-api` | Valor de `service.name` |
| `FALLOS_PORCENTAJE` | `0` | Fallos 500 inyectados (0 a 100), solo con la cabecera `X-Simular-Fallos` |

## Limitaciones

- La seguridad de Elasticsearch y Kibana está deshabilitada (`xpack.security.enabled=false`). Es solo para desarrollo local.
- Elasticsearch corre en un solo nodo, sin réplicas, y los índices no tienen política de retención.
- El cliente Supabase compartido usaba HTTP/2 y bajo carga sostenida producía 500 reales y peticiones colgadas; se corrigió forzando HTTP/1.1 en `backend/app/db/client.py`. Detalle y medición en el informe, sección 9, problema 8.
- La carpeta `logs/` se comparte por bind mount; en Linux el archivo lo crea `root` dentro del contenedor.
- Los avisos de Kibana sobre seguridad y telemetría están desactivados por configuración; el resto de la interfaz es la estándar.
