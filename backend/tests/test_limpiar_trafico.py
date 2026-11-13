import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import limpiar_trafico


class Resultado:
    def __init__(self, data):
        self.data = data


class Consulta:
    def __init__(self, cliente):
        self.cliente = cliente
        self.rango = (0, 10**9)
        self.ids = []
        self.borrando = False

    def select(self, *_):
        return self

    def contains(self, *_):
        return self

    def order(self, *_):
        return self

    def range(self, inicio, fin):
        self.rango = (inicio, fin)
        return self

    def delete(self):
        self.borrando = True
        return self

    def in_(self, _campo, ids):
        self.ids = ids
        return self

    def execute(self):
        if self.borrando:
            self.cliente.lotes.append(list(self.ids))
            return Resultado([])
        inicio, fin = self.rango
        return Resultado(self.cliente.filas[inicio : fin + 1])


class ClienteFalso:
    def __init__(self, filas):
        self.filas = filas
        self.lotes = []

    def table(self, nombre):
        assert nombre == "tickets"
        return Consulta(self)


def fila(i, titulo=None):
    return {"id": f"id-{i}", "titulo": titulo or f"[trafico] caso {i}"}


def test_solo_se_seleccionan_los_titulos_con_el_prefijo():
    cliente = ClienteFalso([fila(1), fila(2, "Ticket real con la misma etiqueta"), fila(3)])
    assert [f["id"] for f in limpiar_trafico.tickets_trafico(cliente)] == ["id-1", "id-3"]


def test_pagina_hasta_agotar_los_resultados(monkeypatch):
    monkeypatch.setattr(limpiar_trafico, "PAGINA", 3)
    cliente = ClienteFalso([fila(i) for i in range(8)])
    assert len(limpiar_trafico.tickets_trafico(cliente)) == 8


def test_borrar_agrupa_en_lotes(monkeypatch):
    monkeypatch.setattr(limpiar_trafico, "LOTE", 2)
    cliente = ClienteFalso([])
    assert limpiar_trafico.borrar_tickets(cliente, ["a", "b", "c", "d", "e"]) == 5
    assert cliente.lotes == [["a", "b"], ["c", "d"], ["e"]]


def test_sin_borrar_solo_lista(monkeypatch, capsys):
    cliente = ClienteFalso([fila(1), fila(2)])
    monkeypatch.setattr(limpiar_trafico, "get_client", lambda: cliente)
    assert limpiar_trafico.main([]) == 0
    assert cliente.lotes == []
    assert "encontrados: 2" in capsys.readouterr().out


def test_con_borrar_elimina_solo_los_marcados(monkeypatch, capsys):
    cliente = ClienteFalso([fila(1), fila(2, "Ticket real"), fila(3)])
    monkeypatch.setattr(limpiar_trafico, "get_client", lambda: cliente)
    assert limpiar_trafico.main(["--borrar"]) == 0
    assert cliente.lotes == [["id-1", "id-3"]]
    assert "borrados: 2" in capsys.readouterr().out


def test_el_prefijo_y_la_etiqueta_coinciden_con_los_del_generador():
    generador = (Path(__file__).resolve().parents[2] / "monitoring" / "trafico" / "generar_trafico.py").read_text(encoding="utf-8")
    assert f'ETIQUETA = "{limpiar_trafico.ETIQUETA}"' in generador
    assert f'PREFIJO_TITULO = "{limpiar_trafico.PREFIJO_TITULO}"' in generador
