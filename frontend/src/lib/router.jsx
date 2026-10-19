// Router mínimo basado en el hash (#/ruta). Evita configurar el servidor para rutas SPA.
import { useEffect, useState } from 'react'

function rutaActual() {
  const hash = window.location.hash.replace(/^#/, '') || '/'
  const [path, query = ''] = hash.split('?')
  return { path, query: new URLSearchParams(query) }
}

export function useRuta() {
  const [ruta, setRuta] = useState(rutaActual)
  useEffect(() => {
    const alCambiar = () => {
      setRuta(rutaActual())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])
  return ruta
}

export function navegar(path) {
  window.location.hash = path
}

// Compara "/tickets/:id" con "/tickets/abc" y devuelve { id: 'abc' } o null.
export function coincide(patron, path) {
  const a = patron.split('/').filter(Boolean)
  const b = path.split('/').filter(Boolean)
  if (a.length !== b.length) return null
  const params = {}
  for (let i = 0; i < a.length; i++) {
    if (a[i].startsWith(':')) params[a[i].slice(1)] = decodeURIComponent(b[i])
    else if (a[i] !== b[i]) return null
  }
  return params
}

export function Link({ to, children, ...props }) {
  return (
    <a href={'#' + to} {...props}>
      {children}
    </a>
  )
}