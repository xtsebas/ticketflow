import Encabezado from './components/Encabezado'
import { ToastProvider, Vacio } from './components/ui'
import { coincide, Link, useRuta } from './lib/router'
import { SesionProvider } from './lib/session'
import MisTickets from './pages/MisTickets'
import NuevoTicket from './pages/NuevoTicket'
import TicketDetalle from './pages/TicketDetalle'

function Rutas({ path }) {
  if (path === '/') return <NuevoTicket />
  if (path === '/mis-tickets') return <MisTickets />
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