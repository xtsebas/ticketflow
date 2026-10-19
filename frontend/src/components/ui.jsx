import { createContext, useCallback, useContext, useState } from 'react'
import { ESTADOS, NIVELES, etiqueta } from '../lib/constants'
import { estadoSla, iniciales } from '../lib/format'

export function PrioridadBadge({ prioridad }) {
  return <span className={`badge prio prio-${prioridad ?? 'none'}`}>{prioridad ?? 'Sin prioridad'}</span>
}

export function EstadoBadge({ estado }) {
  return <span className={`badge estado estado-${estado}`}>{etiqueta(ESTADOS, estado)}</span>
}

export function NivelBadge({ nivel, completo = false }) {
  return (
    <span className={`badge nivel nivel-${nivel}`} title={etiqueta(NIVELES, nivel)}>
      {completo ? etiqueta(NIVELES, nivel) : nivel}
    </span>
  )
}

export function TipoBadge({ tipo }) {
  return <span className={`badge tipo tipo-${tipo}`}>{tipo === 'incidente' ? 'Incidente' : 'Solicitud'}</span>
}

export function Tags({ tags }) {
  if (!tags?.length) return null
  return (
    <span className="tags">
      {tags.map((t) => (
        <span key={t} className="tag">
          {t}
        </span>
      ))}
    </span>
  )
}

export function Sla({ ticket, ahora }) {
  const s = estadoSla(ticket, ahora)
  return <span className={`sla sla-${s.clase}`}>{s.texto}</span>
}

export function Avatar({ nombre, rol }) {
  return (
    <span className={`avatar avatar-${rol}`} aria-hidden="true">
      {nombre === 'sistema' ? '⚙' : iniciales(nombre)}
    </span>
  )
}

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <div className="cargando" role="status">
      <span className="spinner" /> {texto}
    </div>
  )
}

export function ErrorBox({ error, alReintentar }) {
  if (!error) return null
  return (
    <div className="error-box" role="alert">
      <strong>No se pudo completar la acción.</strong> {error.message}
      {alReintentar && (
        <button className="btn btn-sm" onClick={() => alReintentar()}>
          Reintentar
        </button>
      )}
    </div>
  )
}

export function Vacio({ children }) {
  return <div className="vacio">{children}</div>
}

// Campo de tags: Enter o coma agrega, Backspace en vacío quita el último.
export function TagInput({ valor, onChange, id }) {
  const [texto, setTexto] = useState('')
  const agregar = () => {
    const t = texto.trim().toLowerCase().replace(/\s+/g, '-')
    if (t && !valor.includes(t)) onChange([...valor, t])
    setTexto('')
  }
  return (
    <div className="tag-input">
      {valor.map((t) => (
        <span key={t} className="tag">
          {t}
          <button type="button" aria-label={`Quitar ${t}`} onClick={() => onChange(valor.filter((x) => x !== t))}>
            ×
          </button>
        </span>
      ))}
      <input
        id={id}
        value={texto}
        placeholder={valor.length ? '' : 'Escribe y presiona Enter (p. ej. qr, pagos)'}
        onChange={(e) => setTexto(e.target.value)}
        onBlur={agregar}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault()
            agregar()
          } else if (e.key === 'Backspace' && !texto && valor.length) {
            onChange(valor.slice(0, -1))
          }
        }}
      />
    </div>
  )
}

const ToastContext = createContext(() => {})

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const avisar = useCallback((texto, tipo = 'ok') => {
    const id = Math.random()
    setToasts((t) => [...t, { id, texto, tipo }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500)
  }, [])
  return (
    <ToastContext.Provider value={avisar}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.tipo}`}>
            {t.texto}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useAviso() {
  return useContext(ToastContext)
}