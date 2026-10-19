// Tickets que el usuario creó desde este navegador, más búsqueda por número de ticket.
import { useState } from 'react'
import { api } from '../lib/api'
import { haceCuanto, idCorto } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { Link, navegar } from '../lib/router'
import { useSesion } from '../lib/session'
import { Cargando, EstadoBadge, PrioridadBadge, Vacio } from '../components/ui'

export default function MisTickets() {
  const sesion = useSesion()
  const ahora = useAhora()
  const [buscar, setBuscar] = useState('')
  const ids = sesion.misTickets

  const tickets = useCarga(async () => {
    const resultados = await Promise.allSettled(ids.map((id) => api.obtenerTicket(id)))
    resultados.forEach((r, i) => {
      if (r.status === 'rejected' && r.reason?.status === 404) sesion.olvidarTicket(ids[i])
    })
    return resultados.filter((r) => r.status === 'fulfilled').map((r) => r.value)
  }, [ids.join(',')])

  return (
    <div className="pagina estrecha">
      <header className="pagina-titulo con-acciones">
        <div>
          <h1>Mis tickets</h1>
          <p className="muted">Los tickets que creaste desde este navegador.</p>
        </div>
        <Link className="btn btn-primario" to="/">
          + Nuevo ticket
        </Link>
      </header>

      <form
        className="buscar-id"
        onSubmit={(e) => {
          e.preventDefault()
          const id = buscar.trim().replace(/^#/, '')
          if (id) navegar(`/tickets/${id}`)
        }}
      >
        <input
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
          placeholder="¿Tienes el número completo de un ticket? Pégalo aquí"
          aria-label="Número de ticket"
        />
        <button className="btn">Buscar</button>
      </form>

      {tickets.cargando && ids.length > 0 && <Cargando />}
      {!tickets.cargando && (tickets.datos ?? []).length === 0 && (
        <Vacio>
          Aún no has creado tickets. <Link to="/">Crea el primero</Link>.
        </Vacio>
      )}

      <ul className="lista-tickets">
        {(tickets.datos ?? []).map((t) => (
          <li key={t.id}>
            <Link to={`/tickets/${t.id}`} className="fila-ticket">
              <div>
                <strong>{t.titulo}</strong>
                <span className="muted pequeno">
                  {idCorto(t.id)} · {t.categoria.nombre} · {haceCuanto(t.creado_en, ahora)} ·{' '}
                  {t.comentarios.length} comentario{t.comentarios.length === 1 ? '' : 's'}
                </span>
              </div>
              <div className="fila-badges">
                <PrioridadBadge prioridad={t.prioridad} />
                <EstadoBadge estado={t.estado} />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}