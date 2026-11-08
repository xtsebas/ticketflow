import { useState } from 'react'
import { api } from '../lib/api'
import { useSesion } from '../lib/session'
import { ErrorBox } from '../components/ui'

const EJEMPLO = { agente: 'soporte1', cliente: 'asa_promotions' }
const CUENTA_INCORRECTA = {
  agente: 'Esta cuenta no es de soporte. Usa un usuario del equipo de soporte.',
  cliente: 'Esta cuenta no es de cliente. Usa la cuenta de tu empresa.',
}

export function FormularioLogin({ rolEsperado }) {
  const sesion = useSesion()
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState(null)

  const enviar = async (e) => {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      const nueva = await api.login(usuario.trim(), contrasena)
      if (nueva.rol !== rolEsperado) throw new Error(CUENTA_INCORRECTA[rolEsperado])
      sesion.iniciarSesion(nueva)
    } catch (err) {
      setError(err)
      setEnviando(false)
    }
  }

  return (
    <form className="tarjeta formulario" onSubmit={enviar}>
      <label className="campo">
        <span>Usuario</span>
        <input
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          placeholder={`p. ej. ${EJEMPLO[rolEsperado]}`}
          autoComplete="username"
          autoFocus
          required
        />
      </label>
      <label className="campo">
        <span>Contraseña</span>
        <input
          type="password"
          value={contrasena}
          onChange={(e) => setContrasena(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>
      <ErrorBox error={error} />
      <div className="acciones">
        <button className="btn btn-primario" disabled={enviando}>
          {enviando ? 'Ingresando…' : 'Ingresar'}
        </button>
      </div>
    </form>
  )
}

export default function Login() {
  return (
    <div className="pagina estrecha">
      <header className="pagina-titulo">
        <h1>Acceso de soporte</h1>
        <p className="muted">Inicia sesión para ver el tablero y las estadísticas del equipo de soporte.</p>
      </header>
      <FormularioLogin rolEsperado="agente" />
    </div>
  )
}
