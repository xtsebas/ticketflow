// Gestión de problemas (Fase 1, Flujo 3): mapa de los incidentes tipificados del catálogo con sus causas
// raíz probables y su solución temporal, y aviso cuando un incidente amerita abrir un registro de problema.
import { api } from '../lib/api'
import { PROBLEMAS_CONOCIDOS, UMBRAL_RECURRENCIA, VENTANA_PROBLEMAS_DIAS } from '../lib/constants'
import { haceCuanto, idCorto } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { Link } from '../lib/router'
import { Cargando, ErrorBox, EstadoBadge, NivelBadge, PrioridadBadge } from '../components/ui'

const DIA_MS = 24 * 3600 * 1000
const ACTIVOS = ['abierto', 'en_progreso']
const MAX_RECIENTES = 3

// Conexión Incidente → Problema de la Fase 1: incidente recurrente o de alto impacto.
function motivosProblema(recientes) {
  const motivos = []
  if (recientes.length >= UMBRAL_RECURRENCIA) {
    motivos.push(`Recurrente: ${recientes.length} incidentes en los últimos ${VENTANA_PROBLEMAS_DIAS} días`)
  }
  const p1 = recientes.filter((t) => t.prioridad === 'P1').length
  if (p1) motivos.push(`Alto impacto: ${p1} incidente${p1 === 1 ? '' : 's'} P1 en el periodo`)
  return motivos
}

export default function Problemas() {
  const ahora = useAhora(60000)
  const datos = useCarga(async () => {
    const [categorias, tickets] = await Promise.all([api.categorias(), api.listarTickets()])
    return { categorias, tickets }
  })

  if (datos.cargando && !datos.datos) {
    return (
      <div className="pagina">
        <Cargando texto="Cargando incidentes…" />
      </div>
    )
  }
  if (!datos.datos) {
    return (
      <div className="pagina">
        <ErrorBox error={datos.error} alReintentar={datos.recargar} />
      </div>
    )
  }

  const { categorias, tickets } = datos.datos
  const filas = categorias
    .filter((c) => c.tipo === 'incidente' && PROBLEMAS_CONOCIDOS[c.slug])
    .map((c) => {
      const delServicio = tickets
        .filter((t) => t.categoria_id === c.id)
        .sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en))
      const recientes = delServicio.filter((t) => ahora - new Date(t.creado_en).getTime() <= VENTANA_PROBLEMAS_DIAS * DIA_MS)
      return {
        categoria: c,
        info: PROBLEMAS_CONOCIDOS[c.slug],
        total: delServicio.length,
        enCurso: delServicio.filter((t) => ACTIVOS.includes(t.estado)).length,
        recientes,
        motivos: motivosProblema(recientes),
      }
    })
    .sort((a, b) => b.motivos.length - a.motivos.length || b.recientes.length - a.recientes.length)

  const candidatos = filas.filter((f) => f.motivos.length).length
  const enPeriodo = filas.reduce((s, f) => s + f.recientes.length, 0)

  return (
    <div className="pagina">
      <header className="pagina-titulo con-acciones">
        <div>
          <h1>Problemas</h1>
          <p className="muted">
            Causas raíz y soluciones temporales de los incidentes del catálogo. Un incidente recurrente o de alto
            impacto se lleva a gestión de problemas; si la solución definitiva modifica el servicio, pasa a gestión de
            cambios.
          </p>
        </div>
        <button className="btn" onClick={() => datos.recargar()} disabled={datos.cargando}>
          ↻ Actualizar
        </button>
      </header>
      <ErrorBox error={datos.error} alReintentar={datos.recargar} />

      <div className="metricas">
        <div className="metrica">
          <span>Incidentes tipificados</span>
          <strong>{filas.length}</strong>
          <small>servicios del catálogo</small>
        </div>
        <div className="metrica">
          <span>Incidentes recientes</span>
          <strong>{enPeriodo}</strong>
          <small>últimos {VENTANA_PROBLEMAS_DIAS} días</small>
        </div>
        <div className={`metrica ${candidatos ? 'peligro' : ''}`}>
          <span>Candidatos a problema</span>
          <strong>{candidatos}</strong>
          <small>
            {UMBRAL_RECURRENCIA} o más en {VENTANA_PROBLEMAS_DIAS} días, o algún P1
          </small>
        </div>
      </div>

      <div className="rejilla-problemas">
        {filas.map(({ categoria, info, total, enCurso, recientes, motivos }) => (
          <section key={categoria.id} className={`tarjeta problema ${motivos.length ? 'candidato' : ''}`}>
            <header>
              <div>
                <h2>{categoria.nombre}</h2>
                <p className="muted pequeno">
                  {recientes.length} en {VENTANA_PROBLEMAS_DIAS} días · {enCurso} en curso · {total} en total
                </p>
              </div>
              <NivelBadge nivel={info.nivel} completo />
            </header>

            {motivos.length > 0 && (
              <div className="aviso-problema">
                <strong>Abrir registro de problema</strong>
                <ul>
                  {motivos.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </div>
            )}

            <h3>Causas raíz probables</h3>
            <ul>
              {info.causas.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>

            <h3>Solución temporal (error conocido)</h3>
            <ul>
              {info.solucionTemporal.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>

            <h3>Incidentes recientes</h3>
            {recientes.length ? (
              <ul className="recientes-problema">
                {recientes.slice(0, MAX_RECIENTES).map((t) => (
                  <li key={t.id}>
                    <PrioridadBadge prioridad={t.prioridad} />
                    <Link to={`/tickets/${t.id}`}>{t.titulo}</Link>
                    <EstadoBadge estado={t.estado} />
                    <span className="muted pequeno">
                      <span className="mono">{idCorto(t.id)}</span> · {haceCuanto(t.creado_en, ahora)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted pequeno">Sin incidentes en los últimos {VENTANA_PROBLEMAS_DIAS} días.</p>
            )}
          </section>
        ))}
      </div>
    </div>
  )
}
