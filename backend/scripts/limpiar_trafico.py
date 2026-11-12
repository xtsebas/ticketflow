import argparse
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
os.chdir(RAIZ)
sys.path.insert(0, str(RAIZ))

from app.db.client import get_client

ETIQUETA = "trafico_auto"
PREFIJO_TITULO = "[trafico] "
PAGINA = 500
LOTE = 100


def tickets_trafico(cliente) -> list[dict]:
    encontrados = []
    inicio = 0
    while True:
        filas = (
            cliente.table("tickets")
            .select("id, titulo")
            .contains("tags", [ETIQUETA])
            .order("id")
            .range(inicio, inicio + PAGINA - 1)
            .execute()
            .data
        )
        encontrados.extend(f for f in filas if f["titulo"].startswith(PREFIJO_TITULO))
        if len(filas) < PAGINA:
            return encontrados
        inicio += PAGINA


def borrar_tickets(cliente, ids: list[str]) -> int:
    for inicio in range(0, len(ids), LOTE):
        cliente.table("tickets").delete().in_("id", ids[inicio : inicio + LOTE]).execute()
    return len(ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lista o borra los tickets creados por el generador de trafico.")
    parser.add_argument(
        "--borrar",
        action="store_true",
        help=f"borra los tickets con la etiqueta '{ETIQUETA}' y titulo que empieza con '{PREFIJO_TITULO}' (sus comentarios se eliminan en cascada)",
    )
    args = parser.parse_args(argv)

    cliente = get_client()
    filas = tickets_trafico(cliente)
    print(f"Tickets del generador de trafico encontrados: {len(filas)}")
    if not args.borrar:
        print("No se borro nada. Usa --borrar para eliminarlos.")
        return 0
    print(f"Tickets borrados: {borrar_tickets(cliente, [f['id'] for f in filas])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
