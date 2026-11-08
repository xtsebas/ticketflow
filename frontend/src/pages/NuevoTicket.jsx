// Requerimiento 1: ingreso de un problema o solicitud por parte del usuario del servicio.
import { useState } from 'react'
import { api } from '../lib/api'
import {
  HORARIO,
  IMPACTOS,
  PERFILES,
  PRIORIDADES,
  SERVICIOS_USUARIO,
  SUGERENCIA_POR_CATEGORIA,
  TIPOS,
  URGENCIAS,
  calcularPrioridad,
  plazosSla,
} from '../lib/constants'
import { formatoFecha, idCorto } from '../lib/format'
import { useCarga } from '../lib/hooks'
import { Link } from '../lib/router'
import { useSesion } from '../lib/session'
import { Cargando, ErrorBox, PrioridadBadge, TagInput } from '../components/ui'
import { FormularioLogin } from './Login'

const VACIO = { tipo: '', categoria_id: '', titulo: '', descripcion: '', tags: [], impacto: '', urgencia: '' }

export default function NuevoTicket() {
  const sesion = useSesion()
  const categorias = useCarga(() => api.categorias())
  const [perfil, setPerfil] = useState('')
  const [form, setForm] = useState(VACIO)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)
  const [creado, setCreado] = useState(null)

  const set = (campo, valor) => setForm((f) => ({ ...f, [campo]: valor }))
  const lista = categorias.datos ?? []
  const esUsuario = perfil === 'usuario'
  const salto = esUsuario ? 1 : 0
  const clienteHabilitado = perfil === 'cliente' && (sesion.esCliente || sesion.sesionAgente)
  const necesitaLogin = perfil === 'cliente' && !clienteHabilitado
  const servicios = esUsuario
    ? lista.filter((c) => SERVICIOS_USUARIO.includes(c.slug))
    : lista.filter((c) => c.tipo === form.tipo)
  const mostrarServicios = esUsuario || (clienteHabilitado && form.tipo)
  const categoria = esUsuario || clienteHabilitado ? lista.find((c) => c.id === form.categoria_id) : undefined

  const elegirPerfil = (valor) => {
    setPerfil(valor)
    setForm(VACIO)
  }
  const prioridad = calcularPrioridad(form.impacto, form.urgencia)
  const infoPrioridad = PRIORIDADES.find((p) => p.valor === prioridad)
  const plazos = plazosSla(prioridad, form.impacto, form.urgencia)

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
            <legend>1. ¿Quién reporta?</legend>
            <div className="opciones-grandes">
              {PERFILES.map((p) => (
                <label key={p.valor} className={`opcion-grande ${perfil === p.valor ? 'sel' : ''}`}>
                  <input
                    type="radio"
                    name="perfil"
                    value={p.valor}
                    checked={perfil === p.valor}
                    onChange={() => elegirPerfil(p.valor)}
                    required
                  />
                  <strong>{p.etiqueta}</strong>
                  <span>{p.ayuda}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {clienteHabilitado && (
            <fieldset>
              <legend>2. Tipo de ticket</legend>
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
          )}

          {mostrarServicios && (
            <fieldset>
              <legend>{3 - salto}. Servicio afectado</legend>
              {esUsuario && (
                <p className="muted pequeno">
                  Como usuario puedes reportar aquí lo relacionado con tu entrada: QR rechazado en la puerta, reembolso o
                  reenvío de tu ticket.
                </p>
              )}
              <div className="lista-categorias">
                {servicios.map((c) => (
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
                <legend>{4 - salto}. Detalles</legend>
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
                  <span>{sesion.esCliente ? 'Cliente' : 'Tu usuario o correo'}</span>
                  <input
                    value={sesion.nombre}
                    onChange={(e) => sesion.setNombre(e.target.value)}
                    placeholder="p. ej. ana.lopez@correo.com"
                    readOnly={sesion.esCliente}
                    required
                  />
                </label>
              </fieldset>

              <fieldset>
                <legend>{5 - salto}. ¿Qué tan grave es?</legend>
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
                      {plazos.respuesta}, resolución objetivo en {plazos.resolucion}.
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

      {categorias.datos && necesitaLogin && (
        <div className="bloque-login">
          <p className="muted pequeno">Inicia sesión con la cuenta de tu empresa para reportar como cliente.</p>
          <FormularioLogin rolEsperado="cliente" />
        </div>
      )}
    </div>
  )
}