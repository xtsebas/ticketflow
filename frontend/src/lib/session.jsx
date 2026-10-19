// Rol y nombre de quien usa la app. No hay autenticación en el backend: el rol solo
// cambia la vista (usuario del servicio o equipo de soporte) y el autor de los comentarios.
import { createContext, useContext, useEffect, useState } from 'react'

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
  const [nombreAgente, setNombreAgente] = useState(() => leer('tf.nombreAgente', 'soporte_1'))
  const [misTickets, setMisTickets] = useState(() => leer('tf.misTickets', []))

  useEffect(() => guardar('tf.rol', rol), [rol])
  useEffect(() => guardar('tf.nombre', nombre), [nombre])
  useEffect(() => guardar('tf.nombreAgente', nombreAgente), [nombreAgente])
  useEffect(() => guardar('tf.misTickets', misTickets), [misTickets])

  const valor = {
    rol,
    setRol,
    esAgente: rol === 'agente',
    nombre,
    setNombre,
    nombreAgente,
    setNombreAgente,
    autor: rol === 'agente' ? nombreAgente : nombre,
    misTickets,
    recordarTicket: (id) => setMisTickets((lista) => [id, ...lista.filter((x) => x !== id)]),
    olvidarTicket: (id) => setMisTickets((lista) => lista.filter((x) => x !== id)),
  }
  return <SesionContext.Provider value={valor}>{children}</SesionContext.Provider>
}

export function useSesion() {
  return useContext(SesionContext)
}