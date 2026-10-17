import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.client import get_client
from app.repositories import categorias as repo_categorias
from app.repositories import comentarios as repo_comentarios
from app.repositories import tickets as repo_tickets
from app.services.prioridad import calcular_prioridad
from app.services.sla import calcular_vencimientos

PREFIJO = "demo_"

TICKETS = [
    ("reenvio_ticket_digital", "No encuentro el correo con mi QR", ["correo", "qr"], "bajo", "media", "abierto", "N1", None, "demo_ana",
     [("demo_ana", "solicitante", False, "Lo borre por error, me lo pueden reenviar?")]),
    ("reenvio_ticket_digital", "Reenvio de entradas de grupo", ["correo"], "medio", "baja", "cerrado", "N1", None, "demo_luis",
     [("soporte_1", "agente", False, "Reenviadas las 4 entradas al correo registrado."),
      ("demo_luis", "solicitante", False, "Recibidas, gracias.")]),
    ("reenvio_ticket_digital", "Ticket digital llega con otro nombre", ["correo", "login"], "bajo", "baja", "abierto", "N1", None, "demo_marta", []),
    ("reembolso_cancelacion_entrada", "Reembolso por evento cancelado", ["pagos"], "medio", "media", "en_progreso", "N1", None, "demo_carlos",
     [("soporte_2", "agente", False, "Estamos validando la politica de reembolso."),
      ("soporte_2", "agente", True, "Evento cancelado por el organizador, aplica reembolso total.")]),
    ("reembolso_cancelacion_entrada", "Cancelar compra dentro de la ventana", ["pagos"], "bajo", "media", "resuelto", "N1", None, "demo_sofia",
     [("soporte_1", "agente", False, "Cancelacion procesada, el reembolso llega en 5 dias habiles.")]),
    ("reembolso_cancelacion_entrada", "Reembolso solicitado fuera de plazo", ["pagos"], "bajo", "baja", "cerrado", "N1", None, "demo_pedro", []),
    ("creacion_publicacion_evento", "Alta de concierto con aforo de 5000", ["panel"], "alto", "media", "en_progreso", "N2", None, "demo_org_rock",
     [("soporte_3", "agente", False, "Recibimos el formulario, revisamos fechas y precios."),
      ("soporte_3", "agente", True, "Falta confirmar el aforo con el recinto.")]),
    ("creacion_publicacion_evento", "Publicar evento de teatro", ["panel"], "medio", "baja", "abierto", "N1", None, "demo_org_teatro", []),
    ("creacion_publicacion_evento", "Evento no aparece tras publicarlo", ["panel", "login"], "alto", "alta", "resuelto", "N2", None, "demo_org_feria",
     [("soporte_3", "agente", False, "Corregimos la visibilidad del evento."),
      ("demo_org_feria", "solicitante", False, "Ya lo veo publicado, gracias.")]),
    ("cambio_asiento_categoria_entrada", "Cambiar a asiento VIP", ["qr"], "bajo", "alta", "abierto", "N1", None, "demo_diana", []),
    ("cambio_asiento_categoria_entrada", "Asiento duplicado asignado", ["qr"], "medio", "alta", "en_progreso", "N2", None, "demo_jorge",
     [("soporte_2", "agente", False, "Reasignamos tu asiento, revisa tu correo."),
      ("soporte_2", "agente", True, "Bug de inventario: dos ventas sobre el mismo asiento.")]),
    ("cambio_asiento_categoria_entrada", "Upgrade de general a platea", ["pagos"], "bajo", "baja", "cerrado", "N1", None, "demo_valeria", []),
    ("pago_no_procesado_cobro_duplicado", "Cobro doble en tarjeta", ["pagos"], "alto", "alta", "en_progreso", "N3", "gerente_operaciones", "demo_roberto",
     [("soporte_1", "agente", False, "Detectamos el cobro duplicado, iniciamos la reversion."),
      ("sistema", "agente", True, "Escalamiento: N1 a N3. Motivo: cobro duplicado con la pasarela."),
      ("demo_roberto", "solicitante", False, "Sigo viendo los dos cargos.")]),
    ("pago_no_procesado_cobro_duplicado", "Pago rechazado pero con cargo", ["pagos"], "alto", "alta", "abierto", "N2", None, "demo_elena",
     [("soporte_2", "agente", True, "Revisar logs de la pasarela para esta transaccion.")]),
    ("pago_no_procesado_cobro_duplicado", "Error al pagar con tarjeta", ["pagos", "login"], "medio", "media", "resuelto", "N1", None, "demo_felipe",
     [("soporte_1", "agente", False, "Era un limite de la tarjeta, ya pago correctamente.")]),
    ("qr_rechazado_en_puerta", "QR rechazado en acceso principal", ["qr"], "alto", "alta", "en_progreso", "N3", "direccion_comercial", "demo_gabriela",
     [("soporte_3", "agente", False, "Habilitamos el ingreso manual mientras corregimos."),
      ("sistema", "agente", True, "Escalamiento: N2 a N3. Motivo: falla masiva del validador."),
      ("soporte_3", "agente", True, "Afecta a todo el evento, notificar a direccion comercial.")]),
    ("qr_rechazado_en_puerta", "QR ya utilizado segun el lector", ["qr"], "medio", "alta", "resuelto", "N2", None, "demo_hugo",
     [("soporte_2", "agente", False, "Reseteamos el estado del QR.")]),
    ("qr_rechazado_en_puerta", "Lector no reconoce QR en pantalla", ["qr"], "bajo", "media", "abierto", "N1", None, "demo_irene", []),
    ("correo_confirmacion_no_entregado", "Pague y no llego el correo", ["correo", "pagos"], "medio", "alta", "abierto", "N1", None, "demo_juan",
     [("demo_juan", "solicitante", False, "Ya revise spam y no esta.")]),
    ("correo_confirmacion_no_entregado", "Confirmacion llega con retraso de horas", ["correo"], "bajo", "media", "resuelto", "N2", None, "demo_karen",
     [("soporte_2", "agente", True, "Cola de correo saturada, ya se normalizo.")]),
    ("correo_confirmacion_no_entregado", "Correo rebotado por dominio", ["correo"], "medio", "media", "en_progreso", "N2", None, "demo_leo", []),
    ("panel_ventas_desincronizado", "Ventas del panel no cuadran", ["panel"], "alto", "media", "en_progreso", "N2", None, "demo_org_rock",
     [("soporte_3", "agente", True, "La replica del reporte esta atrasada 2 horas.")]),
    ("panel_ventas_desincronizado", "Disponibilidad incorrecta en panel", ["panel"], "medio", "baja", "cerrado", "N2", None, "demo_org_teatro", []),
    ("panel_ventas_desincronizado", "No puedo iniciar sesion en el panel", ["panel", "login"], "medio", "alta", "abierto", "N1", None, "demo_org_feria",
     [("soporte_1", "agente", False, "Prueba restablecer tu contrasena desde el enlace de acceso.")]),
    ("panel_ventas_desincronizado", "Exportacion de ventas incompleta", ["panel"], "alto", "baja", "abierto", "N1", None, "demo_mauricio", []),
]


def construir(categorias: list[dict]) -> list[tuple[dict, list[dict]]]:
    id_por_slug = {c["slug"]: c["id"] for c in categorias}
    base = datetime.now(timezone.utc) - timedelta(days=len(TICKETS))
    resultado = []
    for i, (slug, titulo, tags, impacto, urgencia, estado, nivel, escal, solicitante, coms) in enumerate(TICKETS):
        creado = base + timedelta(days=i, minutes=i * 7)
        prioridad = calcular_prioridad(impacto, urgencia)
        vence_respuesta, vence_resolucion = calcular_vencimientos(prioridad, creado)
        ticket = {
            "titulo": titulo,
            "descripcion": f"{titulo}. Ticket de demostracion.",
            "categoria_id": id_por_slug[slug],
            "tags": tags,
            "impacto": impacto,
            "urgencia": urgencia,
            "prioridad": prioridad.value,
            "vence_respuesta_en": vence_respuesta.isoformat(),
            "vence_resolucion_en": vence_resolucion.isoformat(),
            "estado": estado,
            "nivel": nivel,
            "escalamiento_jerarquico": escal,
            "solicitante": solicitante,
            "creado_en": creado.isoformat(),
        }
        comentarios = [
            {
                "autor": autor,
                "autor_rol": rol,
                "interno": interno,
                "contenido": contenido,
                "creado_en": (creado + timedelta(hours=j + 1)).isoformat(),
            }
            for j, (autor, rol, interno, contenido) in enumerate(coms)
        ]
        resultado.append((ticket, comentarios))
    return resultado


def ids_demo() -> list[str]:
    filas = get_client().table("tickets").select("id, solicitante").like("solicitante", "demo*").execute().data
    return [f["id"] for f in filas if f["solicitante"].startswith(PREFIJO)]


def borrar_demo() -> int:
    ids = ids_demo()
    for inicio in range(0, len(ids), 100):
        get_client().table("tickets").delete().in_("id", ids[inicio : inicio + 100]).execute()
    return len(ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inserta tickets de demostracion.")
    parser.add_argument("--reset", action="store_true", help=f"borra antes los tickets cuyo solicitante empieza con '{PREFIJO}'")
    args = parser.parse_args()

    if args.reset:
        print(f"Tickets demo borrados: {borrar_demo()}")
    elif existentes := len(ids_demo()):
        print(f"Ya existen {existentes} tickets demo. Usa --reset para reemplazarlos.")
        return 1

    categorias = repo_categorias.listar()
    faltantes = {t[0] for t in TICKETS} - {c["slug"] for c in categorias}
    if faltantes:
        print(f"Faltan categorias en la base (ejecuta db/seed.sql): {sorted(faltantes)}")
        return 1

    total_comentarios = 0
    for ticket, comentarios in construir(categorias):
        creado = repo_tickets.crear(ticket)
        for comentario in comentarios:
            repo_comentarios.crear(creado["id"], comentario)
            total_comentarios += 1
    print(f"Insertados {len(TICKETS)} tickets y {total_comentarios} comentarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
