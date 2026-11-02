import { useEffect } from 'react'
import Encabezado from './components/Encabezado'
import { ToastProvider, Vacio } from './components/ui'
import { coincide, Link, useRuta } from './lib/router'
import { SesionProvider, useSesion } from './lib/session'
import Estadisticas from './pages/Estadisticas'
import Login from './pages/Login'
import MisTickets from './pages/MisTickets'
import NuevoTicket from './pages/NuevoTicket'
import Problemas from './pages/Problemas'
import Tablero from './pages/Tablero'
import TicketDetalle from './pages/TicketDetalle'

function RutaSoporte({ children }) {
  const { autenticado, esAgente, setRol } = useSesion()
  useEffect(() => {
    if (autenticado && !esAgente) setRol('agente')
  }, [autenticado, esAgente, setRol])
  return autenticado ? children : <Login />
}

function Rutas({ path }) {
  if (path === '/') return <NuevoTicket />
  if (path === '/mis-tickets') return <MisTickets />
  if (path === '/soporte') {
    return (
      <RutaSoporte>
        <Tablero />
      </RutaSoporte>
    )
  }
  if (path === '/estadisticas') {
    return (
      <RutaSoporte>
        <Estadisticas />
      </RutaSoporte>
    )
  }
  if (path === '/problemas') {
    return (
      <RutaSoporte>
        <Problemas />
      </RutaSoporte>
    )
  }
  const detalle = coincide('/tickets/:id', path)
  if (detalle) return <TicketDetalle key={detalle.id} id={detalle.id} />
  return (
    <div className="pagina estrecha">
      <Vacio>
        Esta vista todavía no está lista. <Link to="/">Ir al inicio</Link>
      </Vacio>
    </div>
  )
}

export default function App() {
  const { path } = useRuta()
  return (
    <SesionProvider>
      <ToastProvider>
        <Encabezado path={path} />
        <main>
          <Rutas path={path} />
        </main>
      </ToastProvider>
    </SesionProvider>
  )
}