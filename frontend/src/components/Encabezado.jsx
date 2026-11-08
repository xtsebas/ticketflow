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
  { to: '/problemas', texto: 'Problemas' },
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
                window.location.hash = '/soporte'
              }}
            >
              Soporte
            </button>
          </div>
          {s.esAgente && <strong title="Sesión de soporte">{s.nombreAgente}</strong>}
          {s.esCliente && <strong title="Sesión de cliente">{s.nombre}</strong>}
          {!s.esAgente && !s.esCliente && (
            <label className="nombre-sesion" title="Tu nombre o usuario">
              <span className="visually-hidden">Usuario</span>
              <input value={s.nombre} placeholder="tu usuario" onChange={(e) => s.setNombre(e.target.value)} />
            </label>
          )}
          {s.autenticado && (
            <button
              className="btn btn-sm btn-texto"
              onClick={() => {
                s.cerrarSesion()
                window.location.hash = '/'
              }}
            >
              Salir
            </button>
          )}
        </div>
      </div>
    </header>
  )
}