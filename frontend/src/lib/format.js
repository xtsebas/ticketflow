const ZONA = 'America/Guatemala'

export function formatoFecha(iso) {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('es-GT', {
    timeZone: ZONA,
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function duracion(ms) {
  const min = Math.round(Math.abs(ms) / 60000)
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  if (h < 24) return min % 60 ? `${h} h ${min % 60} min` : `${h} h`
  const d = Math.floor(h / 24)
  return h % 24 ? `${d} d ${h % 24} h` : `${d} d`
}

export function haceCuanto(iso, ahora = Date.now()) {
  return 'hace ' + duracion(ahora - new Date(iso).getTime())
}

// Estado del SLA vigente del ticket según su estado:
// abierto → plazo de respuesta, en progreso → plazo de resolución, resuelto/cerrado → sin contador.
export function estadoSla(ticket, ahora = Date.now()) {
  if (!ticket.prioridad) return { clase: 'neutro', texto: 'Sin prioridad' }
  if (ticket.estado === 'resuelto' || ticket.estado === 'cerrado') {
    return { clase: 'neutro', texto: ticket.estado === 'cerrado' ? 'Cerrado' : 'Resuelto' }
  }
  const esRespuesta = ticket.estado === 'abierto'
  const vence = esRespuesta ? ticket.vence_respuesta_en : ticket.vence_resolucion_en
  if (!vence) return { clase: 'neutro', texto: 'Sin SLA' }
  const fin = new Date(vence).getTime()
  const inicio = new Date(ticket.creado_en).getTime()
  const restante = fin - ahora
  const tipo = esRespuesta ? 'Respuesta' : 'Resolución'
  if (restante <= 0) return { clase: 'vencido', texto: `${tipo} vencida hace ${duracion(restante)}`, vencido: true }
  const enRiesgo = restante < (fin - inicio) * 0.25
  return { clase: enRiesgo ? 'riesgo' : 'ok', texto: `${tipo} en ${duracion(restante)}` }
}

export function iniciales(nombre = '') {
  const limpio = nombre.replace(/^demo_/, '').replace(/[_\-.]+/g, ' ').trim()
  const partes = limpio.split(/\s+/).filter(Boolean)
  return ((partes[0]?.[0] ?? '?') + (partes[1]?.[0] ?? '')).toUpperCase()
}

export function idCorto(id) {
  return '#' + String(id).slice(0, 8)
}