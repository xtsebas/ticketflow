import os
import sys
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ))

from app.core.config import get_settings

PREFIJO = "smoke_"
PLACEHOLDER_CLAVE = "your-service-role-key"


def credenciales_completas() -> bool:
    configuracion = get_settings()
    return (
        configuracion.supabase_url.startswith("https://")
        and bool(configuracion.supabase_service_role_key)
        and configuracion.supabase_service_role_key != PLACEHOLDER_CLAVE
    )


if not credenciales_completas():
    print("Faltan credenciales de Supabase en backend/.env (SUPABASE_URL https y SUPABASE_SERVICE_ROLE_KEY). No se ejecuto nada.")
    sys.exit(2)

from fastapi.testclient import TestClient

from app.db.client import get_client
from app.main import app
from app.repositories import tickets as repo_tickets
from app.services.prioridad import calcular_prioridad
from app.services.sla import calcular_vencimientos

cliente = TestClient(app)
corrida = uuid.uuid4().hex[:8]
etiqueta_corrida = f"smoke_{corrida}"
resultados: list[tuple[str, bool, str]] = []
creados: dict[str, dict] = {}

COMBINACIONES = [
    ("alto", "alta"),
    ("alto", "media"),
    ("medio", "alta"),
    ("medio", "media"),
    ("bajo", "alta"),
    ("medio", "baja"),
    ("bajo", "media"),
    ("alto", "baja"),
]
TAGS = ["login", "pagos", "qr", "correo", "panel", "login", "pagos", "qr"]


def verificar(nombre, funcion):
    try:
        funcion()
        resultados.append((nombre, True, ""))
        print(f"aprobado  {nombre}")
    except Exception as error:
        resultados.append((nombre, False, f"{type(error).__name__}: {error}"))
        print(f"fallido   {nombre}: {type(error).__name__}: {error}")


def fecha(valor: str) -> datetime:
    return datetime.fromisoformat(valor)


def detalle(ticket_id: str, rol: str = "solicitante") -> dict:
    respuesta = cliente.get(f"/tickets/{ticket_id}", params={"rol": rol})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def conteos(estadisticas: dict) -> dict:
    return {seccion: {c["clave"]: c["total"] for c in estadisticas[seccion]} for seccion in estadisticas}


def crear_ticket(indice: int, categoria: dict) -> dict:
    impacto, urgencia = COMBINACIONES[indice]
    respuesta = cliente.post(
        "/tickets",
        json={
            "titulo": f"smoke {corrida} {indice}",
            "descripcion": "prueba real",
            "categoria_id": categoria["id"],
            "tags": [etiqueta_corrida, TAGS[indice]],
            "impacto": impacto,
            "urgencia": urgencia,
            "solicitante": f"{PREFIJO}{corrida}_{indice}",
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def verificar_ocho_categorias():
    categorias = cliente.get("/categorias").json()
    assert len(categorias) == 8, f"se esperaban 8 categorias y hay {len(categorias)}"
    for indice, categoria in enumerate(categorias):
        ticket = crear_ticket(indice, categoria)
        creados[f"t{indice}"] = ticket
        assert ticket["categoria_id"] == categoria["id"]
        assert ticket["estado"] == "abierto" and ticket["nivel"] == "N1"
        impacto, urgencia = COMBINACIONES[indice]
        prioridad = calcular_prioridad(impacto, urgencia)
        assert ticket["prioridad"] == prioridad.value, f"prioridad {ticket['prioridad']} != {prioridad.value}"
        respuesta, resolucion = calcular_vencimientos(prioridad, fecha(ticket["creado_en"]))
        assert fecha(ticket["vence_respuesta_en"]) == respuesta, "vence_respuesta_en no coincide"
        assert fecha(ticket["vence_resolucion_en"]) == resolucion, "vence_resolucion_en no coincide"
    assert {t["prioridad"] for t in creados.values()} == {"P1", "P2", "P3", "P4"}


def verificar_comentarios():
    ticket_id = creados["t3"]["id"]
    url = f"/tickets/{ticket_id}/comentarios"
    publico = cliente.post(url, json={"autor": "smoke_ana", "autor_rol": "solicitante", "contenido": "publico"})
    assert publico.status_code == 201 and publico.json()["interno"] is False, publico.text
    interno = cliente.post(url, json={"autor": "smoke_bea", "autor_rol": "agente", "contenido": "interno", "interno": True})
    assert interno.status_code == 201 and interno.json()["interno"] is True, interno.text
    rechazado = cliente.post(url, json={"autor": "smoke_ana", "autor_rol": "solicitante", "contenido": "x", "interno": True})
    assert rechazado.status_code == 422, rechazado.text
    assert rechazado.json()["codigo"] == "validacion_error"
    inexistente = cliente.post(
        "/tickets/00000000-0000-0000-0000-000000000000/comentarios",
        json={"autor": "smoke_ana", "autor_rol": "solicitante", "contenido": "x"},
    )
    assert inexistente.status_code == 404 and inexistente.json()["codigo"] == "no_encontrado"


def verificar_detalle_por_rol():
    ticket_id = creados["t3"]["id"]
    visibles = detalle(ticket_id, "solicitante")["comentarios"]
    assert [c["contenido"] for c in visibles] == ["publico"], visibles
    todos = detalle(ticket_id, "agente")["comentarios"]
    assert [c["contenido"] for c in todos] == ["publico", "interno"], todos
    fechas = [c["creado_en"] for c in todos]
    assert fechas == sorted(fechas), "comentarios fuera de orden"
    por_defecto = detalle(ticket_id)["comentarios"]
    assert all(not c["interno"] for c in por_defecto)
    ticket = detalle(ticket_id)
    assert ticket["categoria"]["nombre"] and ticket["categoria"]["tipo"] in ("solicitud", "incidente")


def verificar_patch_transiciones():
    ticket_id = creados["t0"]["id"]
    url = f"/tickets/{ticket_id}"
    valida = cliente.patch(url, json={"estado": "en_progreso"})
    assert valida.status_code == 200 and valida.json()["estado"] == "en_progreso", valida.text
    invalida = cliente.patch(url, json={"estado": "cerrado"})
    assert invalida.status_code == 409, invalida.text
    assert invalida.json()["codigo"] == "conflicto" and "en_progreso a cerrado" in invalida.json()["detalle"]
    assert detalle(ticket_id)["estado"] == "en_progreso"
    vacio = cliente.patch(url, json={"motivo": "solo motivo"})
    assert vacio.status_code == 422, vacio.text
    segunda = cliente.patch(url, json={"estado": "resuelto"})
    assert segunda.status_code == 200, segunda.text
    reapertura = cliente.patch(url, json={"estado": "en_progreso"})
    assert reapertura.status_code == 200, reapertura.text
    cliente.patch(f"/tickets/{creados['t1']['id']}", json={"estado": "en_progreso"})


def verificar_escalamiento():
    ticket_id = creados["t0"]["id"]
    respuesta = cliente.patch(f"/tickets/{ticket_id}", json={"nivel": "N3", "motivo": "requiere ingenieria"})
    assert respuesta.status_code == 200 and respuesta.json()["nivel"] == "N3", respuesta.text
    comentarios = detalle(ticket_id, "agente")["comentarios"]
    sistema = [c for c in comentarios if c["autor"] == "sistema"]
    assert len(sistema) == 1, comentarios
    assert sistema[0]["interno"] is True and sistema[0]["autor_rol"] == "agente"
    assert sistema[0]["contenido"] == "Escalamiento: N1 a N3. Motivo: requiere ingenieria", sistema[0]["contenido"]
    assert not [c for c in detalle(ticket_id, "solicitante")["comentarios"] if c["autor"] == "sistema"]
    segundo = creados["t2"]["id"]
    sin_motivo = cliente.patch(f"/tickets/{segundo}", json={"nivel": "N2"})
    assert sin_motivo.status_code == 200
    texto = [c for c in detalle(segundo, "agente")["comentarios"] if c["autor"] == "sistema"][0]["contenido"]
    assert texto == "Escalamiento: N1 a N2.", texto


def verificar_actualizado_en():
    ticket_id = creados["t4"]["id"]
    antes = detalle(ticket_id)["actualizado_en"]
    time.sleep(1.1)
    respuesta = cliente.patch(f"/tickets/{ticket_id}", json={"tags": [etiqueta_corrida, "qr", "extra"]})
    assert respuesta.status_code == 200, respuesta.text
    despues = respuesta.json()["actualizado_en"]
    assert fecha(despues) > fecha(antes), f"{antes} no cambio a {despues}"
    assert detalle(ticket_id)["tags"] == [etiqueta_corrida, "qr", "extra"]


def verificar_cambio_de_prioridad():
    ticket_id = creados["t1"]["id"]
    actual = detalle(ticket_id)
    respuesta = cliente.patch(f"/tickets/{ticket_id}", json={"prioridad": "P1"})
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["prioridad"] == "P1"
    esperado = calcular_vencimientos(calcular_prioridad("alto", "alta"), fecha(actual["creado_en"]))
    assert fecha(cuerpo["vence_respuesta_en"]) == esperado[0]
    assert fecha(cuerpo["vence_resolucion_en"]) == esperado[1]
    assert fecha(cuerpo["creado_en"]) == fecha(actual["creado_en"])


def verificar_ticket_inexistente_y_categoria_invalida():
    inexistente = "00000000-0000-0000-0000-000000000000"
    assert cliente.get(f"/tickets/{inexistente}").status_code == 404
    assert cliente.patch(f"/tickets/{inexistente}", json={"prioridad": "P1"}).status_code == 404
    categorias = cliente.get("/categorias").json()
    cuerpo = {
        "titulo": "smoke", "descripcion": "x", "categoria_id": inexistente, "tags": [],
        "impacto": "alto", "urgencia": "alta", "solicitante": f"{PREFIJO}{corrida}_invalido",
    }
    respuesta = cliente.post("/tickets", json=cuerpo)
    assert respuesta.status_code == 404 and respuesta.json()["codigo"] == "no_encontrado", respuesta.text
    fuera = cliente.post("/tickets", json={**cuerpo, "categoria_id": categorias[0]["id"], "impacto": "critico"})
    assert fuera.status_code == 422 and fuera.json()["codigo"] == "validacion_error", fuera.text


def estados_finales() -> dict[str, dict]:
    return {clave: detalle(ticket["id"]) for clave, ticket in creados.items()}


def verificar_filtros():
    finales = estados_finales()
    mios = {t["id"] for t in finales.values()}
    filtros = {
        "estado": ("estado", "en_progreso"),
        "prioridad": ("prioridad", "P1"),
        "nivel": ("nivel", "N3"),
        "categoria_id": ("categoria_id", finales["t5"]["categoria_id"]),
        "tag": ("tags", etiqueta_corrida),
    }
    for parametro, (campo, valor) in filtros.items():
        respuesta = cliente.get("/tickets", params={parametro: valor})
        assert respuesta.status_code == 200, respuesta.text
        filas = respuesta.json()
        for fila in filas:
            coincide = valor in fila[campo] if campo == "tags" else fila[campo] == valor
            assert coincide, f"filtro {parametro}: fila {fila['id']} no cumple"
            assert fila["categoria_nombre"], "falta categoria_nombre"
        devueltos = {f["id"] for f in filas}
        esperados = {
            t["id"] for t in finales.values() if (valor in t[campo] if campo == "tags" else t[campo] == valor)
        }
        assert esperados <= devueltos, f"filtro {parametro}: faltan {esperados - devueltos}"
    por_tag = cliente.get("/tickets", params={"tag": etiqueta_corrida}).json()
    assert {f["id"] for f in por_tag} == mios, "el filtro por tag debe devolver exactamente los tickets de esta corrida"
    combinado = cliente.get("/tickets", params={"tag": etiqueta_corrida, "estado": "en_progreso", "nivel": "N3"}).json()
    assert [f["id"] for f in combinado] == [finales["t0"]["id"]], combinado
    assert cliente.get("/tickets", params={"estado": "nada"}).status_code == 422


def verificar_orden():
    nulo = repo_tickets.crear(
        {
            "titulo": f"smoke {corrida} sin prioridad",
            "descripcion": "prueba real",
            "categoria_id": creados["t0"]["categoria_id"],
            "tags": [etiqueta_corrida],
            "impacto": "bajo",
            "urgencia": "baja",
            "prioridad": None,
            "estado": "abierto",
            "nivel": "N1",
            "solicitante": f"{PREFIJO}{corrida}_nulo",
        }
    )
    creados["nulo"] = nulo
    filas = cliente.get("/tickets").json()
    assert any(f["id"] == nulo["id"] for f in filas)
    claves = [(f["prioridad"] is None, f["prioridad"] or "", f["creado_en"]) for f in filas]
    for anterior, siguiente, fila in zip(claves, claves[1:], filas[1:]):
        assert (anterior[0], anterior[1]) <= (siguiente[0], siguiente[1]), f"prioridad desordenada en {fila['id']}"
        if anterior[:2] == siguiente[:2]:
            assert fecha(anterior[2]) <= fecha(siguiente[2]), f"creado_en desordenado en {fila['id']}"
    indices_nulos = [i for i, f in enumerate(filas) if f["prioridad"] is None]
    if indices_nulos:
        assert indices_nulos == list(range(len(filas) - len(indices_nulos), len(filas))), "los null deben ir al final"
    mias = [f for f in cliente.get("/tickets", params={"tag": etiqueta_corrida}).json()]
    assert mias[-1]["id"] == nulo["id"], "el ticket sin prioridad debe quedar al final"


def verificar_estadisticas(antes: dict):
    despues = conteos(cliente.get("/estadisticas").json())
    finales = list(estados_finales().values())
    esperado = {
        "por_categoria": Counter(),
        "por_tag": Counter(),
        "por_prioridad": Counter(),
        "por_estado": Counter(),
    }
    slug_por_id = {c["id"]: c["slug"] for c in cliente.get("/categorias").json()}
    for ticket in finales:
        esperado["por_categoria"][slug_por_id[ticket["categoria_id"]]] += 1
        esperado["por_estado"][ticket["estado"]] += 1
        esperado["por_prioridad"][ticket["prioridad"] or "sin_prioridad"] += 1
        esperado["por_tag"].update(ticket["tags"])
    for seccion, esperados in esperado.items():
        claves = set(antes[seccion]) | set(despues[seccion]) | set(esperados)
        for clave in claves:
            diferencia = despues[seccion].get(clave, 0) - antes[seccion].get(clave, 0)
            assert diferencia == esperados.get(clave, 0), (
                f"{seccion}[{clave}]: diferencia {diferencia} != esperado {esperados.get(clave, 0)}"
            )
    assert [c["clave"] for c in cliente.get("/estadisticas").json()["por_estado"]] == [
        "abierto", "en_progreso", "resuelto", "cerrado",
    ]


def limpiar() -> int:
    filas = get_client().table("tickets").select("id, solicitante").like("solicitante", "smoke*").execute().data
    ids = [f["id"] for f in filas if f["solicitante"].startswith(PREFIJO)]
    for inicio in range(0, len(ids), 100):
        get_client().table("tickets").delete().in_("id", ids[inicio : inicio + 100]).execute()
    return len(ids)


def main() -> int:
    antes = conteos(cliente.get("/estadisticas").json())
    try:
        verificar("un ticket por cada una de las 8 categorias con prioridad y vencimientos", verificar_ocho_categorias)
        verificar("comentario publico e interno y rechazo de interno de solicitante", verificar_comentarios)
        verificar("detalle con rol solicitante y agente", verificar_detalle_por_rol)
        verificar("PATCH con transicion valida e invalida (409)", verificar_patch_transiciones)
        verificar("escalamiento crea el comentario interno", verificar_escalamiento)
        verificar("actualizado_en cambia despues de un PATCH", verificar_actualizado_en)
        verificar("cambio de prioridad recalcula vencimientos", verificar_cambio_de_prioridad)
        verificar("404 y 422 en creacion y consulta", verificar_ticket_inexistente_y_categoria_invalida)
        verificar("listado con cada filtro", verificar_filtros)
        verificar("orden por prioridad, null al final y creado_en", verificar_orden)
        verificar("estadisticas coinciden con el conteo manual", lambda: verificar_estadisticas(antes))
    finally:
        borrados = limpiar()
        print(f"Tickets smoke borrados: {borrados}")
    fallidos = [r for r in resultados if not r[1]]
    print(f"{len(resultados) - len(fallidos)} aprobadas, {len(fallidos)} fallidas")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
