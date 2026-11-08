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
  const [usuarioSesion, setUsuarioSesion] = useState(() => leer('tf.usuarioSesion', ''))
  const [rolSesion, setRolSesion] = useState(() => leer('tf.rolSesion', ''))
  const [misTickets, setMisTickets] = useState(() => leer('tf.misTickets', []))

  useEffect(() => guardar('tf.rol', rol), [rol])
  useEffect(() => guardar('tf.nombre', nombre), [nombre])
  useEffect(() => guardar('tf.usuarioSesion', usuarioSesion), [usuarioSesion])
  useEffect(() => guardar('tf.rolSesion', rolSesion), [rolSesion])
  useEffect(() => guardar('tf.misTickets', misTickets), [misTickets])

  const cerrarSesion = useCallback(() => {
    guardarToken(null)
    setToken(null)
    setUsuarioSesion('')
    setRolSesion('')
    setRol('solicitante')
  }, [])

  useEffect(() => {
    alExpirarSesion(cerrarSesion)
  }, [cerrarSesion])

  const iniciarSesion = ({ token: nuevo, usuario, rol: rolCuenta }) => {
    guardarToken(nuevo)
    setToken(nuevo)
    setUsuarioSesion(usuario)
    setRolSesion(rolCuenta)
    setRol(rolCuenta === 'agente' ? 'agente' : 'solicitante')
  }

  const autenticado = Boolean(token && usuarioSesion && rolSesion)
  const sesionAgente = autenticado && rolSesion === 'agente'
  const esCliente = autenticado && rolSesion === 'cliente'
  const esAgente = sesionAgente && rol === 'agente'
  const nombreAgente = sesionAgente ? usuarioSesion : ''
  const nombreVisible = esCliente ? usuarioSesion : nombre

  const valor = {
    rol,
    setRol,
    esAgente,
    esCliente,
    sesionAgente,
    autenticado,
    iniciarSesion,
    cerrarSesion,
    nombre: nombreVisible,
    setNombre,
    nombreAgente,
    autor: esAgente ? nombreAgente : nombreVisible,
    misTickets,
    recordarTicket: (id) => setMisTickets((lista) => [id, ...lista.filter((x) => x !== id)]),
    olvidarTicket: (id) => setMisTickets((lista) => lista.filter((x) => x !== id)),
  }
  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>
}

export function useSesion() {
  return useContext(SesionContext)
}
