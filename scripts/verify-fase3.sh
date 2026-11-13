#!/usr/bin/env bash
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 - "$RAIZ" <<'PYEOF'
import io
import json
import os
import re
import subprocess
import sys
import tokenize
import urllib.error
import urllib.request

RAIZ = sys.argv[1]
ES = os.environ.get("ES_URL", "http://localhost:9200")
KIBANA = os.environ.get("KIBANA_URL", "http://localhost:5601")
COMPOSE = os.path.join(RAIZ, "monitoring", "docker-compose.yml")
MUESTRA = os.path.join(RAIZ, "monitoring", "logs", "muestra-api.log")
API = "ticketflow-api-*"
HB = "heartbeat-*"
DASHBOARD = "dashboard-monitoreo-api-fase-3"
CAMPOS = ["@timestamp", "http.request.method", "http.response.status_code", "event.duration", "url.path", "service.name", "log.level"]
TIPOS = {
    "@timestamp": "date",
    "event.duration": "long",
    "http.request.method": "keyword",
    "http.response.status_code": "long",
    "log.level": "keyword",
    "service.name": "keyword",
    "url.path": "keyword",
}
RECIENTE = {"range": {"@timestamp": {"gte": "now-15m"}}}
resultados = []


def check(ok, texto):
    resultados.append(bool(ok))
    print(("PASS  " if ok else "FAIL  ") + texto)


def info(texto):
    print("INFO  " + texto)


def http(metodo, url, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, method=metodo, headers={"Content-Type": "application/json", "kbn-xsrf": "true"})
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            return json.loads(respuesta.read())
    except (urllib.error.URLError, OSError, ValueError):
        return None


def buscar(indice, cuerpo):
    return http("POST", f"{ES}/{indice}/_search", cuerpo) or {}


def contar(indice, consulta=None):
    respuesta = http("POST", f"{ES}/{indice}/_count", {"query": consulta or {"match_all": {}}})
    return respuesta["count"] if respuesta else 0


def agregar(indice, agregaciones, consulta=None):
    return buscar(indice, {"size": 0, "query": consulta or {"match_all": {}}, "aggs": agregaciones}).get("aggregations", {})


def estado_servicio(servicio):
    salida = subprocess.run(
        ["docker", "compose", "-f", COMPOSE, "ps", "-a", servicio, "--format", "{{.State}}|{{.Health}}|{{.ExitCode}}"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return salida


print("== Contenedores")
for servicio, esperado in [("elasticsearch", "running|healthy"), ("kibana", "running|healthy"), ("api", "running|healthy")]:
    estado = estado_servicio(servicio)
    check(estado.startswith(esperado), f"contenedor {servicio} ({estado})")
for servicio in ["filebeat", "heartbeat"]:
    estado = estado_servicio(servicio)
    check(estado.startswith("running"), f"contenedor {servicio} ({estado})")
for servicio in ["elasticsearch-setup", "kibana-setup"]:
    estado = estado_servicio(servicio)
    check(estado.startswith("exited") and estado.endswith("|0"), f"servicio de un solo uso {servicio} ({estado})")

print("== Elasticsearch y documentos")
salud = (http("GET", f"{ES}/_cluster/health") or {}).get("status")
check(salud in ("green", "yellow"), f"cluster Elasticsearch operativo (estado: {salud})")
total_api = contar(API)
check(total_api > 0, f"existen documentos en {API} ({total_api})")
total_hb = contar(HB)
check(total_hb > 0, f"existen documentos en {HB} ({total_hb})")

print("== Los 7 campos obligatorios")
for campo in CAMPOS:
    con_campo = contar(API, {"exists": {"field": campo}})
    check(total_api > 0 and con_campo == total_api, f"campo {campo} presente en {con_campo} de {total_api} documentos")
caps = (http("GET", f"{ES}/{API}/_field_caps?fields={','.join(CAMPOS)}") or {}).get("fields", {})
tipos = {campo: sorted(caps.get(campo, {}))[0] if caps.get(campo) else None for campo in CAMPOS}
check(tipos == TIPOS, "tipos de campo: " + " ".join(f"{k}={v}" for k, v in sorted(tipos.items())))

print("== Contenido de los logs")
agg = agregar(API, {"rutas": {"cardinality": {"field": "url.path"}}, "dur": {"cardinality": {"field": "event.duration"}}, "stats": {"extended_stats": {"field": "event.duration"}}})
rutas = int(agg.get("rutas", {}).get("value", 0))
check(5 <= rutas <= 25, f"entre 5 y 25 url.path distintos ({rutas})")
crudas = contar(API, {"regexp": {"url.path": ".*[0-9a-f]{8}-[0-9a-f]{4}-.*"}})
check(crudas == 0, f"url.path usa la plantilla de la ruta, sin identificadores crudos ({crudas} documentos con UUID)")
distintas = int(agg.get("dur", {}).get("value", 0))
desviacion = int(agg.get("stats", {}).get("std_deviation") or 0)
check(distintas > 20 and desviacion > 0, f"latencia variable: {distintas} valores distintos de event.duration, desviacion {desviacion} ns")

codigos = agregar(API, {"c": {"terms": {"field": "http.response.status_code", "size": 30}}})["c"]["buckets"] if total_api else []
info("distribucion de status codes: " + " ".join(f"{b['key']}:{b['doc_count']}" for b in codigos))
clases = {"2xx": 0, "4xx": 0, "5xx": 0}
for b in codigos:
    clase = f"{int(b['key']) // 100}xx"
    if clase in clases:
        clases[clase] += b["doc_count"]
porcentajes = {k: round(100 * v / total_api, 1) if total_api else 0 for k, v in clases.items()}
info("por clase: " + " ".join(f"{k}={v} ({porcentajes[k]}%)" for k, v in clases.items()))
check(all(v > 0 for v in clases.values()), "hay respuestas 2xx, 4xx y 5xx")

niveles = sorted(b["key"] for b in agregar(API, {"l": {"terms": {"field": "log.level"}}}).get("l", {}).get("buckets", []))
check(niveles == ["error", "info", "warn"], f"log.level con info, warn y error ({' '.join(niveles)})")
incoherentes = contar(
    API,
    {
        "bool": {
            "should": [
                {"bool": {"filter": [{"range": {"http.response.status_code": {"gte": 500}}}], "must_not": [{"term": {"log.level": "error"}}]}},
                {"bool": {"filter": [{"range": {"http.response.status_code": {"gte": 400, "lt": 500}}}], "must_not": [{"term": {"log.level": "warn"}}]}},
                {"bool": {"filter": [{"range": {"http.response.status_code": {"lt": 400}}}], "must_not": [{"term": {"log.level": "info"}}]}},
            ],
            "minimum_should_match": 1,
        }
    },
)
check(incoherentes == 0, f"log.level coincide con el status en todos los documentos ({incoherentes} incoherentes)")

print("== Heartbeat")
for estado in ["up", "down"]:
    n = contar(HB, {"term": {"monitor.status": estado}})
    check(n > 0, f"documentos de heartbeat con monitor.status={estado} ({n})")
monitores = sorted(b["key"] for b in agregar(HB, {"m": {"terms": {"field": "monitor.id"}}}).get("m", {}).get("buckets", []))
check(monitores == ["api-categorias", "api-health", "api-tickets-protegido"], f"monitores activos: {' '.join(monitores)}")

print("== Kibana")
lens = http("GET", f"{KIBANA}/api/saved_objects/_find?type=lens&per_page=100") or {}
titulos = {o["attributes"]["title"] for o in lens.get("saved_objects", [])}
for titulo in [
    "Traffic - Requests over time",
    "Top Endpoints",
    "HTTP Status Distribution",
    "Average Response Time (ms)",
    "System Status (UP / DOWN)",
    "Availability History (UP / DOWN)",
    "Error Rate (%)",
    "Error Rate over time (%)",
]:
    check(titulo in titulos, f"visualizacion Lens: {titulo}")
tablero = (http("GET", f"{KIBANA}/api/saved_objects/dashboard/{DASHBOARD}") or {}).get("attributes", {})
detalle = ""
if tablero:
    detalle = f"{tablero['title']} | {len(json.loads(tablero['panelsJSON']))} paneles | {tablero['timeFrom']} | refresh {tablero['refreshInterval']['value']} ms"
check(
    tablero.get("title") == "Monitoreo API - Fase 3"
    and len(json.loads(tablero.get("panelsJSON", "[]"))) == 9
    and tablero.get("timeFrom") == "now-15m"
    and tablero.get("refreshInterval", {}).get("value") == 5000
    and tablero.get("timeRestore") is True,
    f"dashboard guardado: {detalle}",
)
vistas = {v["title"] for v in (http("GET", f"{KIBANA}/api/data_views") or {}).get("data_view", [])}
for vista in [API, HB]:
    check(vista in vistas, f"data view {vista}")

print("== Datos para cada visualizacion (agregacion equivalente en Elasticsearch, ultimos 15 minutos)")
reciente_api = contar(API, RECIENTE)
check(reciente_api > 0, f"G1 trafico: {reciente_api} peticiones")
minutos = agregar(API, {"h": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1m"}}}, RECIENTE).get("h", {}).get("buckets", [])
check(len([b for b in minutos if b["doc_count"] > 0]) >= 2, f"G1 trafico: {len([b for b in minutos if b['doc_count'] > 0])} minutos con barras")
top = agregar(API, {"t": {"terms": {"field": "url.path", "size": 5}}}, RECIENTE).get("t", {})
check(len(top.get("buckets", [])) == 5 and top.get("sum_other_doc_count", 0) > 0, f"G2 top endpoints: {len(top.get('buckets', []))} rutas mas Other ({top.get('sum_other_doc_count', 0)} peticiones)")
estados = agregar(API, {"c": {"terms": {"field": "http.response.status_code", "size": 10}}}, RECIENTE).get("c", {}).get("buckets", [])
check(len(estados) >= 3, f"G3 distribucion HTTP: {len(estados)} codigos ({' '.join(str(b['key']) for b in estados)})")
prom = agregar(API, {"a": {"avg": {"field": "event.duration"}}}, RECIENTE).get("a", {}).get("value") or 0
por_minuto = agregar(API, {"h": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1m"}, "aggs": {"a": {"avg": {"field": "event.duration"}}}}}, RECIENTE).get("h", {}).get("buckets", [])
valores = [b["a"]["value"] for b in por_minuto if b["a"]["value"] is not None]
check(prom > 0 and len(set(round(v / 1e6, 2) for v in valores)) >= 2, f"G4 tiempo de respuesta promedio: {prom / 1e6:.2f} ms, {len(set(round(v / 1e6, 2) for v in valores))} valores distintos por minuto")
ultimo = buscar(HB, {"size": 1, "sort": [{"@timestamp": "desc"}], "query": {"term": {"monitor.id": "api-health"}}, "_source": ["monitor.status", "@timestamp"]}).get("hits", {}).get("hits", [])
estado_actual = ultimo[0]["_source"]["monitor"]["status"] if ultimo else None
check(estado_actual in ("up", "down"), f"G5 estado actual de api-health: {estado_actual}")
historial = agregar(HB, {"h": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1m"}, "aggs": {"s": {"terms": {"field": "monitor.status"}}}}}, RECIENTE).get("h", {}).get("buckets", [])
check(len([b for b in historial if b["doc_count"] > 0]) >= 2, f"G5 historial: {len([b for b in historial if b['doc_count'] > 0])} minutos con barras")
errores = contar(API, {"bool": {"filter": [RECIENTE, {"range": {"http.response.status_code": {"gte": 400}}}]}})
servidor = contar(API, {"bool": {"filter": [RECIENTE, {"range": {"http.response.status_code": {"gte": 500}}}]}})
if reciente_api:
    info(f"G6 error rate calculado a mano: {100 * errores / reciente_api:.2f}% ({errores}/{reciente_api}), solo 5xx: {100 * servidor / reciente_api:.2f}% ({servidor}/{reciente_api})")
check(errores > 0 and servidor > 0, "G6 error rate con datos en ambas series")

print("== Muestra de logs")
if os.path.isfile(MUESTRA):
    total = validas = 0
    for linea in open(MUESTRA, encoding="utf-8"):
        if not linea.strip():
            continue
        total += 1
        try:
            registro = json.loads(linea)
        except ValueError:
            continue
        if all(c in registro for c in CAMPOS):
            validas += 1
    check(total >= 50 and total == validas, f"muestra-api.log: {total} lineas, {validas} JSON validos con los 7 campos")
else:
    check(False, f"existe {MUESTRA}")

print("== Codigo y configuracion")
ARCHIVOS = [
    "monitoring/docker-compose.yml",
    "monitoring/filebeat/filebeat.yml",
    "monitoring/heartbeat/heartbeat.yml",
    "monitoring/trafico/generar_trafico.py",
    "monitoring/elasticsearch/ticketflow-api-template.json",
    "backend/app/core/access_log.py",
    "backend/scripts/limpiar_trafico.py",
    "backend/tests/test_access_log.py",
    "backend/tests/test_limpiar_trafico.py",
    "scripts/verify-fase3.sh",
    "scripts/importar-dashboard.sh",
]
DOCUMENTOS = ["docs/informe-fase3.md", "monitoring/README.md", "README.md"]
comentarios = []
for ruta in ARCHIVOS:
    contenido = open(os.path.join(RAIZ, ruta), encoding="utf-8").read()
    if ruta.endswith(".py"):
        for token in tokenize.generate_tokens(io.StringIO(contenido).readline):
            if token.type == tokenize.COMMENT:
                comentarios.append(f"{ruta}:{token.start[0]}")
    elif ruta.endswith((".yml", ".sh")):
        for numero, linea in enumerate(contenido.splitlines(), 1):
            if numero == 1 and linea.startswith("#!"):
                continue
            if re.match(r"\s*#", linea) or re.search(r"\s#\s", linea):
                comentarios.append(f"{ruta}:{numero}")
check(not comentarios, f"sin comentarios en codigo ni configuracion de la fase ({len(comentarios)} encontrados {comentarios[:3]})")
RANGOS_EMOJI = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF), (0xFE0F, 0xFE0F), (0x200D, 0x200D)]


def tiene_emoji(texto):
    return any(inicio <= ord(c) <= fin for c in texto for inicio, fin in RANGOS_EMOJI)


emojis = []
for ruta in ARCHIVOS + DOCUMENTOS:
    destino = os.path.join(RAIZ, ruta)
    if os.path.isfile(destino):
        for numero, linea in enumerate(open(destino, encoding="utf-8"), 1):
            if tiene_emoji(linea):
                emojis.append(f"{ruta}:{numero}")
check(not emojis, f"sin emojis en codigo, configuracion ni documentos ({len(emojis)} encontrados {emojis[:3]})")
main_py = open(os.path.join(RAIZ, "backend", "app", "main.py"), encoding="utf-8").read()
check("AccessLogMiddleware" in main_py, "los logs salen del codigo de la API: backend/app/main.py instala AccessLogMiddleware (backend/app/core/access_log.py, metodo _registrar)")

print()
fallidos = resultados.count(False)
if fallidos:
    print(f"RESULTADO: {fallidos} de {len(resultados)} chequeos fallaron")
    sys.exit(1)
print(f"RESULTADO: {len(resultados)} chequeos, todos PASS")
PYEOF
