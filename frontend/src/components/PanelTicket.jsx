// Detalle del ticket en un panel superpuesto a la derecha del tablero (40 % del ancho).
// Se puede minimizar a una pestaña con flecha o expandir a toda la pantalla; el encabezado siempre queda visible.
import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import { formatoFecha, idCorto } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { Comentarios, PanelAgente } from '../pages/TicketDetalle'
import { Cargando, ErrorBox, EstadoBadge, NivelBadge, PrioridadBadge, Sla, Tags, TipoBadge } from './ui'

const DURACION_SALIDA = 280

export default function PanelTicket({ id, version, minimizado, onMinimizar, onCerrar, onCambio }) {
  const ahora = useAhora()
  const [expandido, setExpandido] = useState(false)
  const [saliendo, setSaliendo] = useState(false)
  const ticket = useCarga(() => api.obtenerTicket(id, 'agente'), [id, version])
  // Al cambiar de ticket se muestra la carga en lugar de los datos del anterior.
  const t = ticket.datos?.id === id ? ticket.datos : null

  const cerrar = () => {
    setSaliendo(true)
    setTimeout(onCerrar, DURACION_SALIDA)
  }

  // Escape cierra el panel, salvo mientras se escribe en un campo.
  useEffect(() => {
    const alPresionar = (e) => {
      if (e.key === 'Escape' && !minimizado && !['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) cerrar()
    }
    window.addEventListener('keydown', alPresionar)
    return () => window.removeEventListener('keydown', alPresionar)
  })

  const recargar = () => {
    ticket.recargar({ silencioso: true })
    onCambio()
  }

  const clases = ['panel-lateral', expandido && 'expandido', (minimizado || saliendo) && 'oculto']
  const resumen = t && <Resumen t={t} ahora={ahora} />
  const agente = t && <PanelAgente key={t.actualizado_en} ticket={t} onCambio={recargar} />
  const comentarios = t && <Comentarios key={t.id} ticket={t} ahora={ahora} onNuevo={recargar} />

  return (
    <>
      <aside className={clases.filter(Boolean).join(' ')} aria-label="Detalle del ticket" aria-hidden={minimizado}>
        <header className="panel-lateral-barra">
          <button className="btn btn-sm btn-icono" title="Minimizar" aria-label="Minimizar panel" onClick={onMinimizar}>
            ›
          </button>
          <span className="mono muted">{idCorto(id)}</span>
          <button className="btn btn-sm" onClick={() => setExpandido((x) => !x)}>
            {expandido ? '⤡ Reducir' : '⤢ Expandir'}
          </button>
          <button className="btn btn-sm btn-texto" aria-label="Cerrar detalle" onClick={cerrar}>
            ✕
          </button>
        </header>

        <div className="panel-lateral-cuerpo">
          {!t && ticket.cargando && <Cargando />}
          {!t && ticket.error && <ErrorBox error={ticket.error} alReintentar={ticket.recargar} />}
          {t &&
            (expandido ? (
              <div className="detalle con-panel">
                <div className="detalle-principal">
                  {resumen}
                  {comentarios}
                </div>
                {agente}
              </div>
            ) : (
              <>
                {resumen}
                {agente}
                {comentarios}
              </>
            ))}
        </div>
      </aside>

      {minimizado && !saliendo && (
        <button className="pestana-panel" title="Mostrar el ticket" aria-label="Mostrar panel del ticket" onClick={onMinimizar}>
          ‹
        </button>
      )}
    </>
  )
}

function Resumen({ t, ahora }) {
  return (
    <section className="tarjeta">
      <div className="tt-fila">
        <TipoBadge tipo={t.categoria.tipo} />
        <PrioridadBadge prioridad={t.prioridad} />
        <EstadoBadge estado={t.estado} />
        <NivelBadge nivel={t.nivel} />
      </div>
      <h2 className="panel-titulo">{t.titulo}</h2>
      <p className="detalle-desc">{t.descripcion}</p>
      <dl className="propiedades compactas">
        <div>
          <dt>Categoría</dt>
          <dd>{t.categoria.nombre}</dd>
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
          <dt>SLA</dt>
          <dd>
            <Sla ticket={t} ahora={ahora} />
          </dd>
        </div>
        {t.tags.length > 0 && (
          <div>
            <dt>Tags</dt>
            <dd>
              <Tags tags={t.tags} />
            </dd>
          </div>
        )}
      </dl>
    </section>
  )
}
