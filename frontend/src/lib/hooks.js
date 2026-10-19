import { useCallback, useEffect, useRef, useState } from 'react'

// Carga datos asíncronos con estado de carga y error. `recargar` repite la petición.
export function useCarga(fn, deps = []) {
  const [estado, setEstado] = useState({ datos: null, error: null, cargando: true })
  const vigente = useRef(0)

  const recargar = useCallback(
    async ({ silencioso = false } = {}) => {
      const id = ++vigente.current
      if (!silencioso) setEstado((e) => ({ ...e, cargando: true, error: null }))
      try {
        const datos = await fn()
        if (id === vigente.current) setEstado({ datos, error: null, cargando: false })
      } catch (error) {
        if (id === vigente.current) setEstado((e) => ({ ...e, error, cargando: false }))
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps,
  )

  useEffect(() => {
    recargar()
  }, [recargar])

  return { ...estado, recargar, setDatos: (datos) => setEstado((e) => ({ ...e, datos })) }
}

// Fuerza un re-render periódico para que los contadores de SLA se mantengan al día.
export function useAhora(intervalo = 30000) {
  const [ahora, setAhora] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), intervalo)
    return () => clearInterval(t)
  }, [intervalo])
  return ahora
}