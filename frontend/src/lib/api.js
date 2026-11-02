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

const CLAVE_TOKEN = 'tf.token'

function leerTokenGuardado() {
  try {
    return window.localStorage.getItem(CLAVE_TOKEN)
  } catch {
    return null
  }
}

let token = leerTokenGuardado()
let alExpirar = () => {}

export const obtenerToken = () => token

export function guardarToken(nuevo) {
  token = nuevo
  try {
    if (nuevo) window.localStorage.setItem(CLAVE_TOKEN, nuevo)
    else window.localStorage.removeItem(CLAVE_TOKEN)
  } catch {}
}

export function alExpirarSesion(funcion) {
  alExpirar = funcion
}

async function request(path, { method = 'GET', body, params, autenticado = true } = {}) {
  const url = new URL(API_URL + path)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const enviaToken = autenticado && Boolean(token)
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (enviaToken) headers.Authorization = `Bearer ${token}`
  let respuesta
  try {
    respuesta = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, null)
  }
  const texto = await respuesta.text()
  const datos = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) {
    if (respuesta.status === 401 && enviaToken) alExpirar()
    throw new ApiError(respuesta.status, datos)
  }
  return datos
}

export const api = {
  health: () => request('/health'),
  login: (usuario, contrasena) =>
    request('/auth/login', { method: 'POST', body: { usuario, contrasena }, autenticado: false }),
  categorias: () => request('/categorias'),
  listarTickets: (filtros = {}) => request('/tickets', { params: filtros }),
  obtenerTicket: (id, rol = 'solicitante') => request(`/tickets/${id}`, { params: { rol } }),
  crearTicket: (datos) => request('/tickets', { method: 'POST', body: datos }),
  actualizarTicket: (id, cambios) => request(`/tickets/${id}`, { method: 'PATCH', body: cambios }),
  comentar: (id, datos) => request(`/tickets/${id}/comentarios`, { method: 'POST', body: datos }),
  estadisticas: () => request('/estadisticas'),
}