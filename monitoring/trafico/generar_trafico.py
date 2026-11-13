from __future__ import annotations

import argparse
import json
import math
import os
import random
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

CUENTAS = {
    "agente": ["soporte1", "soporte2", "soporte3", "soporte4"],
    "cliente": [
        "asa_promotions",
        "arceyut_producciones",
        "show_business_guatemala",
        "promotora_2_mundos",
        "epica_eventos",
    ],
}
VARIABLE_CONTRASENA = {"agente": "TRAFICO_CONTRASENA_SOPORTE", "cliente": "TRAFICO_CONTRASENA_CLIENTE"}
SERVICIOS_USUARIO = {"qr_rechazado_en_puerta", "reembolso_cancelacion_entrada", "reenvio_ticket_digital"}
SIGUIENTE_ESTADO = {"abierto": "en_progreso", "en_progreso": "resuelto", "resuelto": "cerrado"}
ETIQUETA = "trafico_auto"
PREFIJO_TITULO = "[trafico] "
RUTAS_INEXISTENTES = [
    "/admin",
    "/api/v1/tickets",
    "/tickets-v2",
    "/favicon.ico",
    "/login",
    "/wp-login.php",
    "/categorias/999",
    "/estadisticas/semanal",
]
TAGS_FILTRO = ["qr", "pago", "correo", "reembolso", ETIQUETA]


class Contexto:
    def __init__(self, args):
        self.url = args.url.rstrip("/")
        self.escritura = not args.solo_lectura
        self.max_creaciones = args.max_creaciones
        self.timeout = args.timeout
        self.cerrojo = threading.Lock()
        self.codigos = Counter()
        self.creaciones = 0
        self.categorias = []
        self.tokens = {}
        self.creados = []
        self.existentes = []
        self.contrasenas = {rol: os.environ.get(VARIABLE_CONTRASENA[rol], "") for rol in CUENTAS}

    def registrar(self, status):
        with self.cerrojo:
            self.codigos[status] += 1

    def puede_crear(self):
        with self.cerrojo:
            if not self.escritura or (self.max_creaciones and self.creaciones >= self.max_creaciones):
                return False
            self.creaciones += 1
            return True


def llamar(ctx, metodo, ruta, cuerpo=None, token=None):
    cabeceras = {"User-Agent": "generador-trafico/1.0", "Accept": "application/json", "X-Simular-Fallos": "1"}
    datos = None
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(ctx.url + ruta, data=datos, headers=cabeceras, method=metodo)
    try:
        with urllib.request.urlopen(peticion, timeout=ctx.timeout) as respuesta:
            status, crudo = respuesta.status, respuesta.read()
    except urllib.error.HTTPError as error:
        status, crudo = error.code, error.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        ctx.registrar(0)
        return 0, None
    ctx.registrar(status)
    try:
        return status, json.loads(crudo)
    except ValueError:
        return status, None


def token_de(ctx, rol):
    token = ctx.tokens.get(rol)
    if token:
        return token
    contrasena = ctx.contrasenas[rol]
    if not contrasena:
        return None
    status, datos = llamar(ctx, "POST", "/auth/login", {"usuario": random.choice(CUENTAS[rol]), "contrasena": contrasena})
    if status == 200 and datos and datos.get("rol") == rol:
        ctx.tokens[rol] = datos["token"]
        return datos["token"]
    return None


def con_sesion(ctx, rol, metodo, ruta, cuerpo=None):
    token = token_de(ctx, rol)
    if token is None:
        return None
    status, datos = llamar(ctx, metodo, ruta, cuerpo, token)
    if status == 401:
        ctx.tokens.pop(rol, None)
    return status, datos


def cargar_categorias(ctx):
    status, datos = llamar(ctx, "GET", "/categorias")
    if status == 200 and isinstance(datos, list) and datos:
        ctx.categorias = datos
    return status


def cuerpo_ticket(categoria, solicitante):
    return {
        "titulo": f"{PREFIJO_TITULO}{categoria['nombre']} caso {random.randint(1000, 9999)}",
        "descripcion": "Ticket generado automaticamente por el generador de trafico de monitoreo.",
        "categoria_id": categoria["id"],
        "tags": [ETIQUETA, categoria["slug"].split("_")[0]],
        "impacto": random.choice(["alto", "medio", "bajo"]),
        "urgencia": random.choice(["alta", "media", "baja"]),
        "solicitante": solicitante,
    }


def recordar_creado(ctx, status, datos):
    if status == 201 and datos and "id" in datos:
        with ctx.cerrojo:
            ctx.creados.append({"id": datos["id"], "estado": datos.get("estado", "abierto")})
            if len(ctx.creados) > 200:
                ctx.creados.pop(0)


def elegir_creado(ctx, estados=None):
    with ctx.cerrojo:
        candidatos = [t for t in ctx.creados if estados is None or t["estado"] in estados]
        return random.choice(candidatos) if candidatos else None


def elegir_ticket(ctx):
    creado = elegir_creado(ctx)
    if creado and (not ctx.existentes or random.random() < 0.5):
        return creado["id"]
    if ctx.existentes:
        return random.choice(ctx.existentes)
    return None


def categorias_listar(ctx):
    cargar_categorias(ctx)
    return True


def health(ctx):
    llamar(ctx, "GET", "/health")
    return True


def tickets_listar(ctx):
    filtros = {}
    if random.random() < 0.6:
        filtros["estado"] = random.choice(["abierto", "en_progreso", "resuelto", "cerrado"])
    if random.random() < 0.4:
        filtros["prioridad"] = random.choice(["P1", "P2", "P3", "P4"])
    if random.random() < 0.3:
        filtros["nivel"] = random.choice(["N1", "N2", "N3"])
    if random.random() < 0.3:
        filtros["tag"] = random.choice(TAGS_FILTRO)
    consulta = "&".join(f"{k}={v}" for k, v in filtros.items())
    resultado = con_sesion(ctx, "agente", "GET", "/tickets" + (f"?{consulta}" if consulta else ""))
    if resultado is None:
        return False
    status, datos = resultado
    if status == 200 and isinstance(datos, list) and datos:
        with ctx.cerrojo:
            ctx.existentes = [t["id"] for t in datos[:50]]
    return True


def estadisticas(ctx):
    return con_sesion(ctx, "agente", "GET", "/estadisticas") is not None


def detalle_publico(ctx):
    ticket_id = elegir_ticket(ctx)
    if ticket_id is None:
        return False
    llamar(ctx, "GET", f"/tickets/{ticket_id}")
    return True


def detalle_agente(ctx):
    ticket_id = elegir_ticket(ctx)
    if ticket_id is None:
        return False
    return con_sesion(ctx, "agente", "GET", f"/tickets/{ticket_id}?rol=agente") is not None


def login_valido(ctx):
    rol = random.choice(list(CUENTAS))
    contrasena = ctx.contrasenas[rol]
    if not contrasena:
        return False
    llamar(ctx, "POST", "/auth/login", {"usuario": random.choice(CUENTAS[rol]), "contrasena": contrasena})
    return True


def crear_ticket_usuario(ctx):
    categorias = [c for c in ctx.categorias if c["slug"] in SERVICIOS_USUARIO]
    if not categorias or not ctx.puede_crear():
        return False
    cuerpo = cuerpo_ticket(random.choice(categorias), f"trafico_usuario_{random.randint(1, 40)}")
    recordar_creado(ctx, *llamar(ctx, "POST", "/tickets", cuerpo))
    return True


def crear_ticket_cliente(ctx):
    if not ctx.categorias or token_de(ctx, "cliente") is None or not ctx.puede_crear():
        return False
    cuerpo = cuerpo_ticket(random.choice(ctx.categorias), "trafico_cliente")
    resultado = con_sesion(ctx, "cliente", "POST", "/tickets", cuerpo)
    if resultado:
        recordar_creado(ctx, *resultado)
    return True


def avanzar_ticket(ctx):
    ticket = elegir_creado(ctx, set(SIGUIENTE_ESTADO))
    if ticket is None:
        return False
    if random.random() < 0.25:
        cuerpo = {"nivel": random.choice(["N2", "N3"]), "motivo": "Escalamiento generado por el trafico de monitoreo"}
    else:
        cuerpo = {"estado": SIGUIENTE_ESTADO[ticket["estado"]]}
    resultado = con_sesion(ctx, "agente", "PATCH", f"/tickets/{ticket['id']}", cuerpo)
    if resultado is None:
        return False
    status, datos = resultado
    if status == 200 and datos and "estado" in cuerpo:
        with ctx.cerrojo:
            ticket["estado"] = datos.get("estado", ticket["estado"])
    return True


def comentar(ctx):
    ticket = elegir_creado(ctx)
    if ticket is None:
        return False
    ruta = f"/tickets/{ticket['id']}/comentarios"
    if random.random() < 0.5:
        cuerpo = {
            "autor": random.choice(CUENTAS["agente"]),
            "autor_rol": "agente",
            "contenido": "Revisando el caso desde el trafico de monitoreo",
            "interno": random.random() < 0.3,
        }
        return con_sesion(ctx, "agente", "POST", ruta, cuerpo) is not None
    cuerpo = {"autor": f"trafico_usuario_{random.randint(1, 40)}", "autor_rol": "solicitante", "contenido": "Alguna novedad"}
    llamar(ctx, "POST", ruta, cuerpo)
    return True


def ruta_inexistente(ctx):
    llamar(ctx, "GET", random.choice(RUTAS_INEXISTENTES))
    return True


def tickets_sin_token(ctx):
    llamar(ctx, "GET", "/tickets")
    return True


def estadisticas_sin_token(ctx):
    llamar(ctx, "GET", "/estadisticas")
    return True


def login_invalido(ctx):
    llamar(ctx, "POST", "/auth/login", {"usuario": random.choice(CUENTAS["agente"]), "contrasena": "incorrecta"})
    return True


def ticket_invalido(ctx):
    cuerpo = random.choice(
        [
            {"titulo": "sin campos obligatorios"},
            {"titulo": "x", "descripcion": "y", "categoria_id": "no-es-uuid", "impacto": "alto", "urgencia": "alta", "solicitante": "a"},
            {"titulo": "x", "descripcion": "y", "categoria_id": str(uuid.uuid4()), "impacto": "enorme", "urgencia": "alta", "solicitante": "a"},
        ]
    )
    llamar(ctx, "POST", "/tickets", cuerpo)
    return True


def ticket_inexistente(ctx):
    llamar(ctx, "GET", f"/tickets/{uuid.uuid4()}")
    return True


def ticket_id_malformado(ctx):
    llamar(ctx, "GET", "/tickets/abc")
    return True


def transicion_invalida(ctx):
    ticket = elegir_creado(ctx, {"abierto"})
    if ticket is None:
        return False
    return con_sesion(ctx, "agente", "PATCH", f"/tickets/{ticket['id']}", {"estado": "cerrado"}) is not None


def metodo_no_permitido(ctx):
    llamar(ctx, "DELETE", "/categorias")
    return True


def patch_sin_token(ctx):
    ticket_id = elegir_ticket(ctx) or str(uuid.uuid4())
    llamar(ctx, "PATCH", f"/tickets/{ticket_id}", {"estado": "en_progreso"})
    return True


def servicio_sin_sesion(ctx):
    categorias = [c for c in ctx.categorias if c["slug"] not in SERVICIOS_USUARIO]
    if not categorias:
        return False
    llamar(ctx, "POST", "/tickets", cuerpo_ticket(random.choice(categorias), "trafico_usuario_1"))
    return True


ESCENARIOS_EXITO = [
    (16, categorias_listar),
    (6, health),
    (12, tickets_listar),
    (6, estadisticas),
    (8, detalle_publico),
    (7, detalle_agente),
    (4, login_valido),
    (4, crear_ticket_usuario),
    (4, crear_ticket_cliente),
    (6, avanzar_ticket),
    (6, comentar),
]
ESCENARIOS_ERROR = [
    (8, ruta_inexistente),
    (4, tickets_sin_token),
    (2, estadisticas_sin_token),
    (3, login_invalido),
    (4, ticket_invalido),
    (3, ticket_inexistente),
    (2, ticket_id_malformado),
    (3, transicion_invalida),
    (1, metodo_no_permitido),
    (2, patch_sin_token),
    (2, servicio_sin_sesion),
]


def elegir_escenario(escenarios):
    return random.choices([f for _, f in escenarios], weights=[p for p, _ in escenarios])[0]


def ejecutar(ctx, proporcion_error):
    grupo, respaldo = (ESCENARIOS_ERROR, ruta_inexistente) if random.random() < proporcion_error else (ESCENARIOS_EXITO, categorias_listar)
    try:
        if not elegir_escenario(grupo)(ctx):
            respaldo(ctx)
    except Exception as error:
        print(f"error inesperado en un escenario: {error!r}", file=sys.stderr)


def tasa_actual(rps, transcurrido, rafaga_hasta):
    tasa = rps * (1 + 0.4 * math.sin(2 * math.pi * transcurrido / 90))
    if transcurrido < rafaga_hasta:
        tasa *= 2
    return max(tasa, 0.1)


def resumen(ctx, transcurrido):
    with ctx.cerrojo:
        codigos = dict(ctx.codigos)
        creaciones = ctx.creaciones
    total = sum(codigos.values())
    por_clase = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "sin_respuesta": 0}
    for status, cantidad in codigos.items():
        if status == 0:
            por_clase["sin_respuesta"] += cantidad
        else:
            por_clase[f"{status // 100}xx"] += cantidad
    partes = " ".join(f"{k}={v}" for k, v in por_clase.items() if v)
    return f"t={int(transcurrido)}s total={total} {partes} creaciones={creaciones}"


def esperar_api(ctx, detener, limite=90):
    inicio = time.monotonic()
    while not detener.is_set() and time.monotonic() - inicio < limite:
        status, _ = llamar(ctx, "GET", "/health")
        if status == 200:
            return True
        detener.wait(2)
    return False


def leer_argumentos():
    entorno = os.environ.get
    parser = argparse.ArgumentParser(description="Genera trafico continuo contra la API de TicketFlow.")
    parser.add_argument("--url", default=entorno("TRAFICO_URL", "http://localhost:8000"))
    parser.add_argument("--rps", type=float, default=float(entorno("TRAFICO_RPS", "3")))
    parser.add_argument("--duracion", type=float, default=float(entorno("TRAFICO_DURACION", "0")))
    parser.add_argument("--proporcion-error", type=float, default=float(entorno("TRAFICO_PROPORCION_ERROR", "0.2")))
    parser.add_argument("--hilos", type=int, default=int(entorno("TRAFICO_HILOS", "8")))
    parser.add_argument("--max-creaciones", type=int, default=int(entorno("TRAFICO_MAX_CREACIONES", "300")))
    parser.add_argument("--timeout", type=float, default=float(entorno("TRAFICO_TIMEOUT", "20")))
    parser.add_argument("--semilla", type=int, default=None)
    parser.add_argument("--solo-lectura", action="store_true", default=entorno("TRAFICO_SOLO_LECTURA", "") == "1")
    return parser.parse_args()


def main():
    args = leer_argumentos()
    if args.semilla is not None:
        random.seed(args.semilla)
    ctx = Contexto(args)
    detener = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: detener.set())
    signal.signal(signal.SIGTERM, lambda *_: detener.set())

    print(
        f"objetivo={ctx.url} rps={args.rps} duracion={'infinita' if not args.duracion else args.duracion} "
        f"proporcion_error={args.proporcion_error} escritura={'si' if ctx.escritura else 'no'} "
        f"max_creaciones={args.max_creaciones}",
        flush=True,
    )
    for rol, variable in VARIABLE_CONTRASENA.items():
        if not ctx.contrasenas[rol]:
            print(f"aviso: {variable} no esta definida; se omiten los escenarios de {rol}", file=sys.stderr, flush=True)
    if not esperar_api(ctx, detener):
        print("la API no respondio en /health", file=sys.stderr)
        return 1
    cargar_categorias(ctx)
    token_de(ctx, "agente")
    tickets_listar(ctx)

    ejecutor = ThreadPoolExecutor(max_workers=args.hilos)
    cupos = threading.Semaphore(args.hilos * 4)
    inicio = time.monotonic()
    ultimo_resumen = inicio
    rafaga_hasta = 0.0

    def tarea():
        try:
            ejecutar(ctx, args.proporcion_error)
        finally:
            cupos.release()

    while not detener.is_set():
        ahora = time.monotonic()
        transcurrido = ahora - inicio
        if args.duracion and transcurrido >= args.duracion:
            break
        if transcurrido >= rafaga_hasta and random.random() < 0.004:
            rafaga_hasta = transcurrido + random.uniform(3, 6)
        detener.wait(random.expovariate(tasa_actual(args.rps, transcurrido, rafaga_hasta)))
        if cupos.acquire(blocking=False):
            ejecutor.submit(tarea)
        if ahora - ultimo_resumen >= 10:
            print(resumen(ctx, transcurrido), flush=True)
            ultimo_resumen = ahora

    ejecutor.shutdown(wait=True)
    print("final " + resumen(ctx, time.monotonic() - inicio), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
