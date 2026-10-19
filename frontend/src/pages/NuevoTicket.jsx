// Requerimiento 1: ingreso de un problema o solicitud por parte del usuario del servicio.
import { useState } from 'react'
import { api } from '../lib/api'
import {
  HORARIO,
  IMPACTOS,
  PRIORIDADES,
  SUGERENCIA_POR_CATEGORIA,
  TIPOS,
  URGENCIAS,
  calcularPrioridad,
} from '../lib/constants'
import { formatoFecha, idCorto } from '../lib/format'
import { useCarga } from '../lib/hooks'
import { Link } from '../lib/router'
import { useSesion } from '../lib/session'
import { Cargando, ErrorBox, PrioridadBadge, TagInput } from '../components/ui'

const VACIO = { tipo: '', categoria_id: '', titulo: '', descripcion: '', tags: [], impacto: '', urgencia: '' }

export default function NuevoTicket() {
  const sesion = useSesion()
  const categorias = useCarga(() => api.categorias())
  const [form, setForm] = useState(VACIO)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const [creado, setCreado] = useState(null)

  const set = (campo, valor) => setForm((f) => ({ ...f, [campo]: valor }))
  const lista = categorias.datos ?? []
  const delTipo = lista.filter((c) => c.tipo === form.tipo)
  const categoria = lista.find((c) => c.id === form.categoria_id)
  const prioridad = calcularPrioridad(form.impacto, form.urgencia)
  const infoPrioridad = PRIORIDADES.find((p) => p.valor === prioridad)

  // Al elegir un servicio se preseleccionan impacto y urgencia según su criticidad (Fase 1).
  const elegirCategoria = (id) => {
    const c = lista.find((x) => x.id === id)
    const sug = c ? SUGERENCIA_POR_CATEGORIA[c.slug] : null
    setForm((f) => ({
      ...f,
      categoria_id: id,
      ...(sug ? { impacto: sug.impacto, urgencia: sug.urgencia } : {}),
    }))
  }

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const ticket = await api.crearTicket({
        titulo: form.titulo.trim(),
        descripcion: form.descripcion.trim(),
        categoria_id: form.categoria_id,
        tags: form.tags,
        impacto: form.impacto,
        urgencia: form.urgencia,
        solicitante: (sesion.nombre || '').trim(),
      })
      sesion.recordarTicket(ticket.id)
      setCreado(ticket)
      setForm(VACIO)
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }

  if (creado) {
    const p = PRIORIDADES.find((x) => x.valor === creado.prioridad)
    return (
      <div className="pagina estrecha">
        <div className="tarjeta exito">
          <div className="exito-icono" aria-hidden="true">
            ✓
          </div>
          <h1>Ticket registrado</h1>
          <p className="muted">
            Tu número de seguimiento es <strong className="mono">{idCorto(creado.id)}</strong>. El equipo de soporte ya
            lo tiene en cola.
          </p>
          <dl className="resumen-sla">
            <div>
              <dt>Prioridad asignada</dt>
              <dd>
                <PrioridadBadge prioridad={creado.prioridad} /> {p?.etiqueta.split('· ')[1]}
              </dd>
            </div>
            <div>
              <dt>Primera respuesta antes de</dt>
              <dd>{formatoFecha(creado.vence_respuesta_en)}</dd>
            </div>
            <div>
              <dt>Resolución objetivo</dt>
              <dd>{formatoFecha(creado.vence_resolucion_en)}</dd>
            </div>
          </dl>
          <p className="muted pequeno">Horario de atención: {HORARIO}</p>
          <div className="acciones">
            <Link className="btn btn-primario" to={`/tickets/${creado.id}`}>
              Ver mi ticket
            </Link>
            <button className="btn" onClick={() => setCreado(null)}>
              Crear otro
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="pagina estrecha">
      <header className="pagina-titulo">
        <h1>¿En qué te podemos ayudar?</h1>
        <p className="muted">Reporta un problema con la plataforma o solicita un servicio de TicketFlow.</p>
      </header>

      {categorias.cargando && <Cargando texto="Cargando catálogo de servicios…" />}
      <ErrorBox error={categorias.error} alReintentar={categorias.recargar} />

      {categorias.datos && (
        <form className="tarjeta formulario" onSubmit={enviar}>
          <fieldset>
            <legend>1. Tipo de ticket</legend>
            <div className="opciones-grandes">
              {TIPOS.map((t) => (
                <label key={t.valor} className={`opcion-grande ${form.tipo === t.valor ? 'sel' : ''}`}>
                  <input
                    type="radio"
                    name="tipo"
                    value={t.valor}
                    checked={form.tipo === t.valor}
                    onChange={() => setForm((f) => ({ ...f, tipo: t.valor, categoria_id: '' }))}
                    required
                  />
                  <strong>{t.etiqueta}</strong>
                  <span>{t.ayuda}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {form.tipo && (
            <fieldset>
              <legend>2. Servicio afectado</legend>
              <div className="lista-categorias">
                {delTipo.map((c) => (
                  <label key={c.id} className={`opcion-cat ${form.categoria_id === c.id ? 'sel' : ''}`}>
                    <input
                      type="radio"
                      name="categoria"
                      value={c.id}
                      checked={form.categoria_id === c.id}
                      onChange={() => elegirCategoria(c.id)}
                      required
                    />
                    <span>
                      <strong>{c.nombre}</strong>
                      <small>{c.descripcion}</small>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {categoria && (
            <>
              <fieldset>
                <legend>3. Detalles</legend>
                <label className="campo">
                  <span>Título</span>
                  <input
                    value={form.titulo}
                    onChange={(e) => set('titulo', e.target.value)}
                    placeholder="Resumen corto, p. ej. «Mi QR no pasa en la puerta 3»"
                    maxLength={120}
                    required
                  />
                </label>
                <label className="campo">
                  <span>Descripción</span>
                  <textarea
                    rows={4}
                    value={form.descripcion}
                    onChange={(e) => set('descripcion', e.target.value)}
                    placeholder="¿Qué pasó? Incluye evento, número de orden, fecha y lo que ya intentaste."
                    required
                  />
                </label>
                <label className="campo">
                  <span>
                    Tags <small className="muted">(opcional)</small>
                  </span>
                  <TagInput id="tags" valor={form.tags} onChange={(v) => set('tags', v)} />
                </label>
                <label className="campo">
                  <span>Tu usuario o correo</span>
                  <input
                    value={sesion.nombre}
                    onChange={(e) => sesion.setNombre(e.target.value)}
                    placeholder="p. ej. ana.lopez@correo.com"
                    required
                  />
                </label>
              </fieldset>

              <fieldset>
                <legend>4. ¿Qué tan grave es?</legend>
                <p className="muted pequeno">
                  Sugerimos valores según el servicio elegido; ajústalos si tu caso es distinto.
                </p>
                <div className="dos-columnas">
                  <div>
                    <span className="sub-legend">Impacto</span>
                    {IMPACTOS.map((i) => (
                      <label key={i.valor} className={`opcion-fila ${form.impacto === i.valor ? 'sel' : ''}`}>
                        <input
                          type="radio"
                          name="impacto"
                          checked={form.impacto === i.valor}
                          onChange={() => set('impacto', i.valor)}
                          required
                        />
                        <span>
                          <strong>{i.etiqueta}</strong>
                          <small>{i.ayuda}</small>
                        </span>
                      </label>
                    ))}
                  </div>
                  <div>
                    <span className="sub-legend">Urgencia</span>
                    {URGENCIAS.map((u) => (
                      <label key={u.valor} className={`opcion-fila ${form.urgencia === u.valor ? 'sel' : ''}`}>
                        <input
                          type="radio"
                          name="urgencia"
                          checked={form.urgencia === u.valor}
                          onChange={() => set('urgencia', u.valor)}
                          required
                        />
                        <span>
                          <strong>{u.etiqueta}</strong>
                          <small>{u.ayuda}</small>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
                {infoPrioridad && (
                  <div className={`vista-prioridad prio-borde-${prioridad}`}>
                    <PrioridadBadge prioridad={prioridad} />
                    <span>
                      Prioridad <strong>{infoPrioridad.etiqueta.split('· ')[1]}</strong>: primera respuesta en{' '}
                      {infoPrioridad.respuesta}, resolución objetivo en {infoPrioridad.resolucion}.
                    </span>
                  </div>
                )}
              </fieldset>

              <ErrorBox error={error} />
              <div className="acciones">
                <button className="btn btn-primario" disabled={enviando}>
                  {enviando ? 'Enviando…' : 'Enviar ticket'}
                </button>
              </div>
            </>
          )}
        </form>
      )}
    </div>
  )
}