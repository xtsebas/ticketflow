// Requerimientos 2 y 4: tablero del equipo de soporte para priorizar y atender la cola.
// Al hacer clic en una fila, el ticket se abre en un panel superpuesto a la derecha sin salir del tablero.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import { asignadoA, tomarTicket } from '../lib/asignacion'
import { ESTADOS, NIVELES, PRIORIDADES } from '../lib/constants'
import { estadoSla, fechaLocal, formatoFecha, haceCuanto, idCorto } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { useSesion } from '../lib/session'
import PanelTicket from '../components/PanelTicket'
import {
  Avatar,
  Cargando,
  ErrorBox,
  EstadoBadge,
  NivelBadge,
  PrioridadBadge,
  Sla,
  Tags,
  Vacio,
  useAviso,
} from '../components/ui'

const ACTIVOS = ['abierto', 'en_progreso']
const SIN_FILTROS = {
  buscar: '',
  estado: 'activos',
  prioridad: '',
  nivel: '',
  categoria_id: '',
  tag: '',
  responsable: '',
  desde: '',
  hasta: '',
}

export default function Tablero() {
  const sesion = useSesion()
  const avisar = useAviso()
  const ahora = useAhora()
  const [filtros, setFiltros] = useState(SIN_FILTROS)
  const [seleccionado, setSeleccionado] = useState(null)
  const [version, setVersion] = useState(0)
  const [minimizado, setMinimizado] = useState(false)
  const categorias = useCarga(() => api.categorias())
  const set = (k, v) => setFiltros((f) => ({ ...f, [k]: v }))
  const agente = sesion.nombreAgente.trim()

  // Estado, prioridad, nivel y categoría los filtra el backend; el resto se filtra aquí.
  // El listado no trae comentarios, así que el responsable sale del detalle de cada ticket.
  const estadoServidor = ESTADOS.some((e) => e.valor === filtros.estado) ? filtros.estado : undefined
  const tickets = useCarga(async () => {
    const lista = await api.listarTickets({
      estado: estadoServidor,
      prioridad: filtros.prioridad,
      nivel: filtros.nivel,
      categoria_id: filtros.categoria_id,
    })
    const detalles = await Promise.allSettled(lista.map((t) => api.obtenerTicket(t.id, 'agente')))
    return lista.map((t, i) => ({
      ...t,
      responsable: detalles[i].status === 'fulfilled' ? asignadoA(detalles[i].value.comentarios) : null,
    }))
  }, [estadoServidor, filtros.prioridad, filtros.nivel, filtros.categoria_id])

  const { recargar } = tickets
  const recargarSilencioso = useCallback(() => recargar({ silencioso: true }), [recargar])
  useEffect(() => {
    const t = setInterval(recargarSilencioso, 30000)
    return () => clearInterval(t)
  }, [recargarSilencioso])

  const cerrarPanel = useCallback(() => {
    setSeleccionado(null)
    setMinimizado(false)
  }, [])
  const abrir = (id) => {
    setSeleccionado(id)
    setMinimizado(false)
  }

  const q = filtros.buscar.trim().toLowerCase()
  const tag = filtros.tag.trim().toLowerCase()
  const visibles = (tickets.datos ?? []).filter((t) => {
    if (filtros.estado === 'activos' && !ACTIVOS.includes(t.estado)) return false
    if (q && ![t.titulo, t.solicitante, t.id, t.categoria_nombre].some((v) => v.toLowerCase().includes(q))) return false
    if (tag && !t.tags.some((x) => x.includes(tag))) return false
    if (filtros.responsable === 'mios' && t.responsable !== agente) return false
    if (filtros.responsable === 'sin' && t.responsable) return false
    const dia = fechaLocal(t.creado_en)
    if (filtros.desde && dia < filtros.desde) return false
    if (filtros.hasta && dia > filtros.hasta) return false
    return true
  })

  const enCurso = visibles.filter((t) => ACTIVOS.includes(t.estado))
  const metricas = {
    sinAsignar: enCurso.filter((t) => !t.responsable).length,
    vencidos: enCurso.filter((t) => estadoSla(t, ahora).vencido).length,
    p1: enCurso.filter((t) => t.prioridad === 'P1').length,
    mios: enCurso.filter((t) => agente && t.responsable === agente).length,
  }
  const hayFiltros = JSON.stringify(filtros) !== JSON.stringify(SIN_FILTROS)

  const tomar = async (t) => {
    if (!agente) {
      avisar('Escribe tu nombre de agente en la parte superior.', 'error')
      return
    }
    try {
      await tomarTicket(t, agente)
      avisar(`Tomaste «${t.titulo}»`)
      if (t.id === seleccionado) setVersion((v) => v + 1)
      recargarSilencioso()
    } catch (err) {
      avisar(err.message, 'error')
    }
  }

  return (
    <div className="pagina ancha">
      <header className="pagina-titulo con-acciones">
        <div>
          <h1>Tablero de soporte</h1>
          <p className="muted">Cola ordenada por prioridad y antigüedad. Haz clic en un ticket para atenderlo.</p>
        </div>
        <button className="btn" onClick={() => recargar()} disabled={tickets.cargando}>
          ↻ Actualizar
        </button>
      </header>

      <div className="metricas">
        <div className="metrica">
          <span>En curso</span>
          <strong>{enCurso.length}</strong>
          <small>abiertos y en progreso</small>
        </div>
        <div className={`metrica ${metricas.sinAsignar ? 'alerta' : ''}`}>
          <span>Sin asignar</span>
          <strong>{metricas.sinAsignar}</strong>
          <small>nadie los ha tomado</small>
        </div>
        <div className={`metrica ${metricas.vencidos ? 'peligro' : ''}`}>
          <span>SLA vencido</span>
          <strong>{metricas.vencidos}</strong>
          <small>fuera del plazo vigente</small>
        </div>
        <div className={`metrica ${metricas.p1 ? 'peligro' : ''}`}>
          <span>Críticos (P1)</span>
          <strong>{metricas.p1}</strong>
          <small>respuesta en 15 min</small>
        </div>
        <div className="metrica">
          <span>Asignados a mí</span>
          <strong>{metricas.mios}</strong>
          <small>{agente || 'sin nombre de agente'}</small>
        </div>
      </div>

      <div className="filtros">
        <input
          type="search"
          value={filtros.buscar}
          onChange={(e) => set('buscar', e.target.value)}
          placeholder="Buscar título, solicitante o #id"
          aria-label="Buscar"
        />
        <select value={filtros.estado} onChange={(e) => set('estado', e.target.value)} aria-label="Estado">
          <option value="activos">Activos (abierto y en progreso)</option>
          {ESTADOS.map((e) => (
            <option key={e.valor} value={e.valor}>
              {e.etiqueta}
            </option>
          ))}
          <option value="todos">Todos los estados</option>
        </select>
        <select value={filtros.prioridad} onChange={(e) => set('prioridad', e.target.value)} aria-label="Prioridad">
          <option value="">Toda prioridad</option>
          {PRIORIDADES.map((p) => (
            <option key={p.valor} value={p.valor}>
              {p.etiqueta}
            </option>
          ))}
        </select>
        <select value={filtros.nivel} onChange={(e) => set('nivel', e.target.value)} aria-label="Nivel">
          <option value="">Todo nivel</option>
          {NIVELES.map((n) => (
            <option key={n.valor} value={n.valor}>
              {n.valor}
            </option>
          ))}
        </select>
        <select value={filtros.categoria_id} onChange={(e) => set('categoria_id', e.target.value)} aria-label="Categoría">
          <option value="">Toda categoría</option>
          {(categorias.datos ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <select value={filtros.responsable} onChange={(e) => set('responsable', e.target.value)} aria-label="Responsable">
          <option value="">Cualquier responsable</option>
          <option value="mios">Asignados a mí</option>
          <option value="sin">Sin asignar</option>
        </select>
        <input
          className="filtro-tag"
          value={filtros.tag}
          onChange={(e) => set('tag', e.target.value)}
          placeholder="Tag"
          aria-label="Tag"
        />
        <label className="filtro-fecha">
          Desde
          <input type="date" value={filtros.desde} max={filtros.hasta || undefined} onChange={(e) => set('desde', e.target.value)} />
        </label>
        <label className="filtro-fecha">
          Hasta
          <input type="date" value={filtros.hasta} min={filtros.desde || undefined} onChange={(e) => set('hasta', e.target.value)} />
        </label>
        {hayFiltros && (
          <button className="btn btn-texto btn-sm" onClick={() => setFiltros(SIN_FILTROS)}>
            Limpiar filtros
          </button>
        )}
      </div>

      {seleccionado && (
        <PanelTicket
          id={seleccionado}
          version={version}
          minimizado={minimizado}
          onMinimizar={() => setMinimizado((m) => !m)}
          onCerrar={cerrarPanel}
          onCambio={recargarSilencioso}
        />
      )}

      <div className="tablero-lista">
        <ErrorBox error={tickets.error} alReintentar={recargar} />
        {tickets.cargando && !tickets.datos && <Cargando texto="Cargando la cola…" />}
        {tickets.datos && visibles.length === 0 && <Vacio>No hay tickets con estos filtros.</Vacio>}

        {visibles.length > 0 && (
          <div className="tablero-tabla">
            <table className="tabla-tickets">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Prioridad</th>
                  <th>Estado</th>
                  <th>Nivel</th>
                  <th>SLA</th>
                  <th>Responsable</th>
                  <th>Solicitante</th>
                  <th>Creado</th>
                </tr>
              </thead>
              <tbody>
                {visibles.map((t) => (
                  <tr
                    key={t.id}
                    className={t.id === seleccionado ? 'sel' : ''}
                    tabIndex={0}
                    onClick={() => abrir(t.id)}
                    onKeyDown={(e) => e.key === 'Enter' && abrir(t.id)}
                  >
                    <td className={`celda-prio prio-borde-${t.prioridad}`}>
                      <div className="celda-titulo">
                        <strong>{t.titulo}</strong>
                        <span className="muted pequeno">
                          <span className="mono">{idCorto(t.id)}</span> · {t.categoria_nombre}
                        </span>
                        <Tags tags={t.tags} />
                      </div>
                    </td>
                    <td>
                      <PrioridadBadge prioridad={t.prioridad} />
                    </td>
                    <td>
                      <EstadoBadge estado={t.estado} />
                    </td>
                    <td>
                      <span className="tt-fila">
                        <NivelBadge nivel={t.nivel} />
                        {t.escalamiento_jerarquico && <span className="badge escalado">Escalado</span>}
                      </span>
                    </td>
                    <td>
                      <Sla ticket={t} ahora={ahora} />
                    </td>
                    <td>
                      {t.responsable ? (
                        <span className="responsable-celda">
                          <Avatar nombre={t.responsable} rol="agente" />
                          {t.responsable}
                        </span>
                      ) : t.estado === 'cerrado' ? (
                        <span className="muted">—</span>
                      ) : (
                        <button
                          className="btn btn-sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            tomar(t)
                          }}
                        >
                          Tomar
                        </button>
                      )}
                    </td>
                    <td>{t.solicitante}</td>
                    <td className="nowrap" title={formatoFecha(t.creado_en)}>
                      {haceCuanto(t.creado_en, ahora)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {visibles.length > 0 && (
          <p className="muted pequeno">
            {visibles.length} ticket{visibles.length === 1 ? '' : 's'} · se actualiza cada 30 s
          </p>
        )}
      </div>
    </div>
  )
}
