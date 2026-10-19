// Cliente del backend FastAPI. Ver "Contrato para el frontend" en el README raíz.

const env = (import.meta && import.meta.env) || {}
export const API_URL = (env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(status, cuerpo) {
    super(mensajeDeError(status, cuerpo))
    this.status = status
    this.codigo = cuerpo?.codigo
    this.detalle = cuerpo?.detalle
  }
}

function mensajeDeError(status, cuerpo) {
  const detalle = cuerpo?.detalle
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle.map((d) => (d.campo ? `${d.campo}: ${d.mensaje}` : d.mensaje)).join(' · ')
  }
  if (status === 0) return 'No se pudo conectar con el backend. ¿Está corriendo en ' + API_URL + '?'
  return `Error ${status}`
}

async function request(path, { method = 'GET', body, params } = {}) {
  const url = new URL(API_URL + path)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  let respuesta
  try {
    respuesta = await fetch(url, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, null)
  }
  const texto = await respuesta.text()
  const datos = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) throw new ApiError(respuesta.status, datos)
  return datos
}

export const api = {
  health: () => request('/health'),
  categorias: () => request('/categorias'),
  listarTickets: (filtros = {}) => request('/tickets', { params: filtros }),
  obtenerTicket: (id, rol = 'solicitante') => request(`/tickets/${id}`, { params: { rol } }),
  crearTicket: (datos) => request('/tickets', { method: 'POST', body: datos }),
  actualizarTicket: (id, cambios) => request(`/tickets/${id}`, { method: 'PATCH', body: cambios }),
  comentar: (id, datos) => request(`/tickets/${id}/comentarios`, { method: 'POST', body: datos }),
  estadisticas: () => request('/estadisticas'),
}