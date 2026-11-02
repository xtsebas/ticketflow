import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { alExpirarSesion, guardarToken, obtenerToken } from './api'

const SesionContext = createContext(null)

function leer(clave, porDefecto) {
  try {
    const v = window.localStorage.getItem(clave)
    return v === null ? porDefecto : JSON.parse(v)
  } catch {
    return porDefecto
  }
}

function guardar(clave, valor) {
  try {
    window.localStorage.setItem(clave, JSON.stringify(valor))
  } catch {
    /* almacenamiento no disponible */
  }
}

export function SesionProvider({ children }) {
  const [rol, setRol] = useState(() => leer('tf.rol', 'solicitante'))
  const [nombre, setNombre] = useState(() => leer('tf.nombre', ''))
  const [token, setToken] = useState(obtenerToken)
  const [nombreAgente, setNombreAgente] = useState(() => leer('tf.nombreAgente', ''))
  const [misTickets, setMisTickets] = useState(() => leer('tf.misTickets', []))

  useEffect(() => guardar('tf.rol', rol), [rol])
  useEffect(() => guardar('tf.nombre', nombre), [nombre])
  useEffect(() => guardar('tf.nombreAgente', nombreAgente), [nombreAgente])
  useEffect(() => guardar('tf.misTickets', misTickets), [misTickets])

  const cerrarSesion = useCallback(() => {
    guardarToken(null)
    setToken(null)
    setNombreAgente('')
    setRol('solicitante')
  }, [])

  useEffect(() => {
    alExpirarSesion(cerrarSesion)
  }, [cerrarSesion])

  const iniciarSesion = ({ token: nuevo, usuario }) => {
    guardarToken(nuevo)
    setToken(nuevo)
    setNombreAgente(usuario)
    setRol('agente')
  }

  const autenticado = Boolean(token && nombreAgente)
  const esAgente = autenticado && rol === 'agente'

  const valor = {
    rol,
    setRol,
    esAgente,
    autenticado,
    iniciarSesion,
    cerrarSesion,
    nombre,
    setNombre,
    nombreAgente,
    autor: esAgente ? nombreAgente : nombre,
    misTickets,
    recordarTicket: (id) => setMisTickets((lista) => [id, ...lista.filter((x) => x !== id)]),
    olvidarTicket: (id) => setMisTickets((lista) => lista.filter((x) => x !== id)),
  }
  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>
}

export function useSesion() {
  return useContext(SesionContext)
}
