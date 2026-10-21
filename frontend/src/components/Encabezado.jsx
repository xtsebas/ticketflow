import { useEffect, useRef } from 'react'
import { Link } from '../lib/router'
import { useSesion } from '../lib/session'

const NAV_USUARIO = [
  { to: '/', texto: 'Nuevo ticket' },
  { to: '/mis-tickets', texto: 'Mis tickets' },
]

const NAV_SOPORTE = [
  { to: '/soporte', texto: 'Tablero' },
  { to: '/estadisticas', texto: 'Estadísticas' },
  { to: '/', texto: 'Nuevo ticket' },
]

export default function Encabezado({ path }) {
  const s = useSesion()
  const nav = s.esAgente ? NAV_SOPORTE : NAV_USUARIO
  const activo = (to) => (to === '/' ? path === '/' : path.startsWith(to))
  const ref = useRef(null)

  // Publica la altura del encabezado para que los paneles superpuestos empiecen debajo de él.
  useEffect(() => {
    const raiz = document.documentElement
    const medir = () => raiz.style.setProperty('--alto-encabezado', `${ref.current.offsetHeight}px`)
    const observador = new ResizeObserver(medir)
    observador.observe(ref.current)
    return () => observador.disconnect()
  }, [])

  return (
    <header className="encabezado" ref={ref}>
      <div className="encabezado-in">
        <Link to={s.esAgente ? '/soporte' : '/'} className="marca">
          <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="var(--acento)" />
            <path d="M8 11h16v3a2 2 0 0 0 0 4v3H8v-3a2 2 0 0 0 0-4z" fill="#fff" />
          </svg>
          <span>
            TicketFlow <small>Service Desk</small>
          </span>
        </Link>

        <nav className="nav">
          {nav.map((n) => (
            <Link key={n.to} to={n.to} className={activo(n.to) ? 'activo' : ''}>
              {n.texto}
            </Link>
          ))}
        </nav>

        <div className="sesion">
          <div className="segmentado" role="group" aria-label="Vista">
            <button
              className={!s.esAgente ? 'activo' : ''}
              onClick={() => {
                s.setRol('solicitante')
                window.location.hash = '/'
              }}
            >
              Usuario
            </button>
            <button
              className={s.esAgente ? 'activo' : ''}
              onClick={() => {
                s.setRol('agente')
                window.location.hash = '/soporte'
              }}
            >
              Soporte
            </button>
          </div>
          <label className="nombre-sesion" title={s.esAgente ? 'Nombre del agente' : 'Tu nombre o usuario'}>
            <span className="visually-hidden">{s.esAgente ? 'Agente' : 'Usuario'}</span>
            <input
              value={s.esAgente ? s.nombreAgente : s.nombre}
              placeholder={s.esAgente ? 'agente' : 'tu usuario'}
              onChange={(e) => (s.esAgente ? s.setNombreAgente(e.target.value) : s.setNombre(e.target.value))}
            />
          </label>
        </div>
      </div>
    </header>
  )
}