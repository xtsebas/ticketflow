// Requerimientos 3 y 4: vista del ticket con sus comentarios de seguimiento,
// y edición/actualización por parte del equipo de soporte.
import { useState } from 'react'
import { api } from '../lib/api'
import { asignadoA, liberarTicket, tomarTicket } from '../lib/asignacion'
import {
  ACCION_TRANSICION,
  ESCALAMIENTOS,
  ESTADOS,
  IMPACTOS,
  NIVELES,
  PRIORIDADES,
  SUGERENCIA_POR_CATEGORIA,
  TRANSICIONES,
  URGENCIAS,
  etiqueta,
} from '../lib/constants'
import { formatoFecha, haceCuanto, idCorto } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { Link } from '../lib/router'
import { useSesion } from '../lib/session'
import {
  Avatar,
  Cargando,
  ErrorBox,
  EstadoBadge,
  NivelBadge,
  PrioridadBadge,
  Sla,
  TagInput,
  Tags,
  TipoBadge,
  useAviso,
} from '../components/ui'

const PASOS = ['abierto', 'en_progreso', 'resuelto', 'cerrado']

export default function TicketDetalle({ id }) {
  const sesion = useSesion()
  const ahora = useAhora()
  const rol = sesion.esAgente ? 'agente' : 'solicitante'
  const ticket = useCarga(() => api.obtenerTicket(id, rol), [id, rol])
  const volverA = sesion.esAgente ? '/soporte' : '/mis-tickets'

  if (ticket.cargando && !ticket.datos) {
    return (
      <div className="pagina">
        <Cargando />
      </div>
    )
  }
  if (ticket.error && !ticket.datos) {
    return (
      <div className="pagina estrecha">
        <ErrorBox error={ticket.error} alReintentar={ticket.recargar} />
        <Link to={volverA}>← Volver</Link>
      </div>
    )
  }

  const t = ticket.datos
  const recargar = () => ticket.recargar({ silencioso: true })

  return (
    <div className="pagina">
      <Link className="volver" to={volverA}>
        ← {sesion.esAgente ? 'Tablero' : 'Mis tickets'}
      </Link>

      <div className={sesion.esAgente ? 'detalle con-panel' : 'detalle'}>
        <div className="detalle-principal">
          <article className="tarjeta">
            <div className="tt-fila">
              <span className="mono muted">{idCorto(t.id)}</span>
              <TipoBadge tipo={t.categoria.tipo} />
              <EstadoBadge estado={t.estado} />
            </div>
            <h1 className="detalle-titulo">{t.titulo}</h1>
            <p className="detalle-desc">{t.descripcion}</p>

            <Progreso estado={t.estado} />

            <dl className="propiedades">
              <div>
                <dt>Categoría</dt>
                <dd>{t.categoria.nombre}</dd>
              </div>
              <div>
                <dt>Prioridad</dt>
                <dd>
                  <PrioridadBadge prioridad={t.prioridad} /> {etiqueta(PRIORIDADES, t.prioridad).split('· ')[1]}
                </dd>
              </div>
              <div>
                <dt>Impacto / urgencia</dt>
                <dd>
                  {etiqueta(IMPACTOS, t.impacto)} / {etiqueta(URGENCIAS, t.urgencia)}
                </dd>
              </div>
              <div>
                <dt>Nivel de atención</dt>
                <dd>
                  <NivelBadge nivel={t.nivel} completo />
                </dd>
              </div>
              {t.escalamiento_jerarquico && (
                <div>
                  <dt>Escalamiento jerárquico</dt>
                  <dd>{etiqueta(ESCALAMIENTOS, t.escalamiento_jerarquico)}</dd>
                </div>
              )}
              <div>
                <dt>Tags</dt>
                <dd>{t.tags.length ? <Tags tags={t.tags} /> : <span className="muted">—</span>}</dd>
              </div>
              <div>
                <dt>Solicitante</dt>
                <dd>{t.solicitante}</dd>
              </div>
              <div>
                <dt>Creado</dt>
                <dd>{formatoFecha(t.creado_en)}</dd>
              </div>
              <div>
                <dt>Responder antes de</dt>
                <dd>{formatoFecha(t.vence_respuesta_en)}</dd>
              </div>
              <div>
                <dt>Resolver antes de</dt>
                <dd>{formatoFecha(t.vence_resolucion_en)}</dd>
              </div>
              <div>
                <dt>SLA</dt>
                <dd>
                  <Sla ticket={t} ahora={ahora} />
                </dd>
              </div>
            </dl>
          </article>

          <Comentarios ticket={t} ahora={ahora} onNuevo={recargar} />
        </div>

        {sesion.esAgente && <PanelAgente key={t.actualizado_en} ticket={t} onCambio={recargar} />}
      </div>
    </div>
  )
}

function Progreso({ estado }) {
  const actual = PASOS.indexOf(estado)
  return (
    <ol className="progreso" aria-label="Avance del ticket">
      {PASOS.map((p, i) => (
        <li key={p} className={i < actual ? 'hecho' : i === actual ? 'actual' : ''}>
          <span className="progreso-punto" />
          {etiqueta(ESTADOS, p)}
        </li>
      ))}
    </ol>
  )
}

export function Comentarios({ ticket, ahora, onNuevo }) {
  const sesion = useSesion()
  const avisar = useAviso()
  const [texto, setTexto] = useState('')
  const [interno, setInterno] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const cerrado = ticket.estado === 'cerrado'

  const enviar = async (e) => {
    e.preventDefault()
    if (!sesion.autor.trim()) {
      setError(new Error('Escribe tu nombre de usuario en la parte superior antes de comentar.'))
      return
    }
    setEnviando(true)
    setError(null)
    try {
      await api.comentar(ticket.id, {
        autor: sesion.autor.trim(),
        autor_rol: sesion.esAgente ? 'agente' : 'solicitante',
        contenido: texto.trim(),
        interno: sesion.esAgente && interno,
      })
      setTexto('')
      setInterno(false)
      avisar(interno ? 'Nota interna agregada' : 'Comentario agregado')
      onNuevo()
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="tarjeta">
      <h2 className="seccion-titulo">
        Seguimiento <span className="contador">{ticket.comentarios.length}</span>
      </h2>
      {ticket.comentarios.length === 0 && <p className="muted">Aún no hay comentarios.</p>}
      <ul className="hilo">
        {ticket.comentarios.map((c) => (
          <li
            key={c.id}
            className={`comentario ${c.interno ? 'interno' : ''} ${c.autor === 'sistema' ? 'sistema' : ''}`}
          >
            <Avatar nombre={c.autor} rol={c.autor_rol} />
            <div className="comentario-cuerpo">
              <div className="comentario-meta">
                <strong>{c.autor}</strong>
                <span className="muted">{c.autor_rol === 'agente' ? 'Soporte' : 'Usuario'}</span>
                {c.interno && <span className="badge interno-badge">Nota interna</span>}
                <span className="muted" title={formatoFecha(c.creado_en)}>
                  {haceCuanto(c.creado_en, ahora)}
                </span>
              </div>
              <p>{c.contenido}</p>
            </div>
          </li>
        ))}
      </ul>

      {cerrado ? (
        <p className="muted pequeno">Este ticket está cerrado. Si el problema persiste, crea un ticket nuevo.</p>
      ) : (
        <form className="nuevo-comentario" onSubmit={enviar}>
          <textarea
            rows={3}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder={
              sesion.esAgente
                ? 'Escribe una respuesta para el usuario o una nota interna…'
                : 'Agrega información o responde al equipo de soporte…'
            }
            required
          />
          <ErrorBox error={error} />
          <div className="acciones">
            {sesion.esAgente && (
              <label className="check">
                <input type="checkbox" checked={interno} onChange={(e) => setInterno(e.target.checked)} />
                Nota interna (no la ve el usuario)
              </label>
            )}
            <button className="btn btn-primario" disabled={enviando || !texto.trim()}>
              {enviando ? 'Enviando…' : interno ? 'Agregar nota' : 'Comentar'}
            </button>
          </div>
        </form>
      )}
    </section>
  )
}

export function PanelAgente({ ticket, onCambio }) {
  const avisar = useAviso()
  const categorias = useCarga(() => api.categorias())
  const inicial = {
    prioridad: ticket.prioridad ?? '',
    categoria_id: ticket.categoria_id,
    tags: ticket.tags,
    nivel: ticket.nivel,
    escalamiento_jerarquico: ticket.escalamiento_jerarquico ?? '',
    motivo: '',
  }
  const [form, setForm] = useState(inicial)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState(null)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  // Solo se envían los campos que cambiaron (el backend trata cada campo por separado).
  const cambios = {}
  if (form.prioridad && form.prioridad !== inicial.prioridad) cambios.prioridad = form.prioridad
  if (form.categoria_id !== inicial.categoria_id) cambios.categoria_id = form.categoria_id
  if (form.tags.join('|') !== inicial.tags.join('|')) cambios.tags = form.tags
  if (form.nivel !== inicial.nivel) cambios.nivel = form.nivel
  if (form.escalamiento_jerarquico && form.escalamiento_jerarquico !== inicial.escalamiento_jerarquico) {
    cambios.escalamiento_jerarquico = form.escalamiento_jerarquico
  }
  const hayCambios = Object.keys(cambios).length > 0
  const escala = 'nivel' in cambios || 'escalamiento_jerarquico' in cambios
  const cerrado = ticket.estado === 'cerrado'

  // Sugerencias de la Fase 1: nivel que corresponde a la categoría y ayuda de cada opción.
  const listaCategorias = categorias.datos ?? [ticket.categoria]
  const categoriaElegida = listaCategorias.find((c) => c.id === form.categoria_id)
  const nivelSugerido = SUGERENCIA_POR_CATEGORIA[categoriaElegida?.slug]?.nivel
  const ayudaNivel = NIVELES.find((n) => n.valor === form.nivel)?.ayuda
  const ayudaEscalamiento = ESCALAMIENTOS.find((x) => x.valor === form.escalamiento_jerarquico)?.ayuda

  const guardar = async (e) => {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      const motivo = form.motivo.trim()
      await api.actualizarTicket(ticket.id, { ...cambios, ...(motivo ? { motivo } : {}) })
      avisar('Ticket actualizado')
      onCambio()
    } catch (err) {
      setError(err)
      setGuardando(false)
    }
  }

  const transicion = async (destino) => {
    try {
      await api.actualizarTicket(ticket.id, { estado: destino })
      avisar(`Estado: ${etiqueta(ESTADOS, destino)}`)
      onCambio()
    } catch (err) {
      avisar(err.message, 'error')
    }
  }

  return (
    <aside className="panel-agente">
      <Asignacion ticket={ticket} onCambio={onCambio} />

      <section className="tarjeta">
        <h2 className="seccion-titulo">Estado</h2>
        <p className="pequeno muted">
          Actual: <EstadoBadge estado={ticket.estado} />
        </p>
        <div className="botones-estado">
          {TRANSICIONES[ticket.estado].map((d) => (
            <button
              key={d}
              className={`btn ${ticket.estado === 'resuelto' && d === 'en_progreso' ? '' : 'btn-primario'}`}
              onClick={() => transicion(d)}
            >
              {ACCION_TRANSICION[`${ticket.estado}>${d}`]}
            </button>
          ))}
          {cerrado && <p className="muted pequeno">El ticket está cerrado; ya no admite cambios.</p>}
        </div>
      </section>

      <form className="tarjeta formulario compacto" onSubmit={guardar}>
        <h2 className="seccion-titulo">Clasificación y escalamiento</h2>
        <fieldset disabled={cerrado}>
          <label className="campo">
            <span>Prioridad</span>
            <select value={form.prioridad} onChange={(e) => set('prioridad', e.target.value)}>
              {!inicial.prioridad && <option value="">Sin prioridad</option>}
              {PRIORIDADES.map((p) => (
                <option key={p.valor} value={p.valor}>
                  {p.etiqueta} — resp. {p.respuesta}, resol. {p.resolucion}
                </option>
              ))}
            </select>
            {'prioridad' in cambios && (
              <small className="nota">Los vencimientos SLA se recalculan desde la creación.</small>
            )}
          </label>

          <label className="campo">
            <span>Categoría</span>
            <select value={form.categoria_id} onChange={(e) => set('categoria_id', e.target.value)}>
              {['incidente', 'solicitud'].map((tipo) => (
                <optgroup key={tipo} label={tipo === 'incidente' ? 'Incidentes' : 'Solicitudes'}>
                  {listaCategorias
                    .filter((c) => c.tipo === tipo)
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>

          <label className="campo">
            <span>Tags</span>
            <TagInput valor={form.tags} onChange={(v) => set('tags', v)} />
          </label>

          <label className="campo">
            <span>Nivel de soporte</span>
            <select value={form.nivel} onChange={(e) => set('nivel', e.target.value)}>
              {NIVELES.map((n) => (
                <option key={n.valor} value={n.valor}>
                  {n.etiqueta}
                </option>
              ))}
            </select>
            {ayudaNivel && <small className="nota">{ayudaNivel}</small>}
            {nivelSugerido && nivelSugerido > form.nivel && (
              <small className="sugerencia">
                Según el catálogo, «{categoriaElegida.nombre}» corresponde a {etiqueta(NIVELES, nivelSugerido)}.{' '}
                <button type="button" className="enlace" onClick={() => set('nivel', nivelSugerido)}>
                  Escalar a {nivelSugerido}
                </button>
              </small>
            )}
          </label>

          <label className="campo">
            <span>Escalamiento jerárquico</span>
            <select
              value={form.escalamiento_jerarquico}
              onChange={(e) => set('escalamiento_jerarquico', e.target.value)}
            >
              {!inicial.escalamiento_jerarquico && <option value="">Ninguno</option>}
              {ESCALAMIENTOS.map((x) => (
                <option key={x.valor} value={x.valor}>
                  {x.etiqueta}
                </option>
              ))}
            </select>
            <small className="nota">
              {ayudaEscalamiento ??
                'Solo si hay riesgo de imagen, pérdida financiera o el organizador exige compensación.'}
            </small>
          </label>

          {escala && (
            <label className="campo">
              <span>Motivo del escalamiento</span>
              <textarea
                rows={2}
                value={form.motivo}
                onChange={(e) => set('motivo', e.target.value)}
                placeholder="p. ej. Falla del lector de QR, requiere soporte técnico"
                required
              />
              <small className="nota">Queda registrado como nota interna del sistema.</small>
            </label>
          )}

          <ErrorBox error={error} />
          <div className="acciones">
            {hayCambios && (
              <button type="button" className="btn btn-texto" onClick={() => setForm(inicial)}>
                Descartar
              </button>
            )}
            <button className="btn btn-primario" disabled={!hayCambios || guardando}>
              {guardando ? 'Guardando…' : 'Guardar cambios'}
            </button>
          </div>
        </fieldset>
      </form>
    </aside>
  )
}
function Asignacion({ ticket, onCambio }) {
  const sesion = useSesion()
  const avisar = useAviso()
  const [ocupado, setOcupado] = useState(false)
  const responsable = asignadoA(ticket.comentarios)
  const agente = sesion.nombreAgente.trim()
  const esMio = responsable && responsable === agente
  const cerrado = ticket.estado === 'cerrado'

  const ejecutar = async (accion, aviso) => {
    if (!agente) {
      avisar('Escribe tu nombre de agente en la parte superior.', 'error')
      return
    }
    setOcupado(true)
    try {
      await accion(ticket, agente)
      avisar(aviso)
      onCambio()
    } catch (err) {
      avisar(err.message, 'error')
    } finally {
      setOcupado(false)
    }
  }

  return (
    <section className="tarjeta">
      <h2 className="seccion-titulo">Responsable</h2>
      <div className="responsable">
        {responsable ? (
          <>
            <Avatar nombre={responsable} rol="agente" />
            <strong>{responsable}</strong>
            {esMio && <span className="muted pequeno">(tú)</span>}
          </>
        ) : (
          <span className="muted">Sin asignar</span>
        )}
      </div>
      {!cerrado && (
        <div className="botones-estado">
          {!esMio && (
            <button className="btn btn-primario" disabled={ocupado} onClick={() => ejecutar(tomarTicket, 'Ticket tomado')}>
              {responsable ? `Tomar (reasignar a ${agente || 'mí'})` : 'Tomar ticket'}
            </button>
          )}
          {esMio && (
            <button className="btn" disabled={ocupado} onClick={() => ejecutar(liberarTicket, 'Ticket liberado')}>
              Liberar ticket
            </button>
          )}
          {!responsable && ticket.estado === 'abierto' && (
            <small className="nota">Al tomarlo pasa a «En progreso».</small>
          )}
        </div>
      )}
    </section>
  )
}
