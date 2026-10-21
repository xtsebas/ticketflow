// Responsable del ticket. El backend no tiene un campo de asignación: tomar o liberar un ticket
// deja una nota interna con un texto fijo, y el responsable actual es la última de esas notas.
import { api } from './api'

const TOMADO = 'Ticket tomado por '
const LIBERADO = 'Ticket liberado por '

function esNotaDeAsignacion(c) {
  return c.interno && c.autor_rol === 'agente' && (c.contenido.startsWith(TOMADO) || c.contenido.startsWith(LIBERADO))
}

// Los comentarios llegan ordenados por creado_en ascendente.
export function asignadoA(comentarios = []) {
  for (let i = comentarios.length - 1; i >= 0; i--) {
    const c = comentarios[i]
    if (!esNotaDeAsignacion(c)) continue
    return c.contenido.startsWith(TOMADO) ? c.contenido.slice(TOMADO.length).trim() : null
  }
  return null
}

// Tomar un ticket abierto también lo pasa a "en progreso".
export async function tomarTicket(ticket, agente) {
  await api.comentar(ticket.id, { autor: agente, autor_rol: 'agente', contenido: TOMADO + agente, interno: true })
  if (ticket.estado === 'abierto') await api.actualizarTicket(ticket.id, { estado: 'en_progreso' })
}

export async function liberarTicket(ticket, agente) {
  await api.comentar(ticket.id, { autor: agente, autor_rol: 'agente', contenido: LIBERADO + agente, interno: true })
}
