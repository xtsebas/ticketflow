// Requerimiento 5: visualización gráfica de los tickets ingresados, agrupados por categoría,
// junto con su distribución por tipo, estado, prioridad y tag.
import { api } from '../lib/api'
import { ESTADOS, PRIORIDADES, TIPOS, etiqueta } from '../lib/constants'
import { estadoSla, fechaLocal } from '../lib/format'
import { useAhora, useCarga } from '../lib/hooks'
import { BarrasHorizontales, BarrasVerticales, Dona } from '../components/Charts'
import { Cargando, ErrorBox, Vacio } from '../components/ui'

const COLOR_TIPO = { incidente: 'var(--incidente)', solicitud: 'var(--solicitud)' }
const COLOR_ESTADO = {
  abierto: 'var(--e-abierto)',
  en_progreso: 'var(--e-progreso)',
  resuelto: 'var(--e-resuelto)',
  cerrado: 'var(--e-cerrado)',
}
const COLOR_PRIORIDAD = { P1: 'var(--p1)', P2: 'var(--p2)', P3: 'var(--p3)', P4: 'var(--p4)', sin_prioridad: 'var(--gris)' }
const DIAS_TENDENCIA = 14
const MAX_TAGS = 10

export default function Estadisticas() {
  const ahora = useAhora(60000)
  // El endpoint da los conteos; el listado se usa para la tendencia por día y el SLA vencido.
  const datos = useCarga(async () => {
    const [est, categorias, tickets] = await Promise.all([api.estadisticas(), api.categorias(), api.listarTickets()])
    return { est, categorias, tickets }
  })

  if (datos.cargando && !datos.datos) {
    return (
      <div className="pagina">
        <Cargando texto="Calculando estadísticas…" />
      </div>
    )
  }
  if (datos.error && !datos.datos) {
    return (
      <div className="pagina">
        <ErrorBox error={datos.error} alReintentar={datos.recargar} />
      </div>
    )
  }

  const { est, categorias, tickets } = datos.datos
  const porSlug = Object.fromEntries(categorias.map((c) => [c.slug, c]))
  const conteo = (lista, clave) => lista.find((x) => x.clave === clave)?.total ?? 0

  const total = est.por_estado.reduce((s, x) => s + x.total, 0)
  const enCurso = conteo(est.por_estado, 'abierto') + conteo(est.por_estado, 'en_progreso')
  const atendidos = conteo(est.por_estado, 'resuelto') + conteo(est.por_estado, 'cerrado')
  const altaPrioridad = conteo(est.por_prioridad, 'P1') + conteo(est.por_prioridad, 'P2')
  const vencidos = tickets.filter((t) => estadoSla(t, ahora).vencido).length

  const categoriasItems = est.por_categoria.map((x) => ({
    clave: x.clave,
    etiqueta: porSlug[x.clave]?.nombre ?? x.clave,
    total: x.total,
    color: COLOR_TIPO[porSlug[x.clave]?.tipo],
  }))
  const tipoItems = TIPOS.map((t) => ({
    clave: t.valor,
    etiqueta: t.etiqueta,
    total: est.por_categoria.filter((x) => porSlug[x.clave]?.tipo === t.valor).reduce((s, x) => s + x.total, 0),
    color: COLOR_TIPO[t.valor],
  }))
  const estadoItems = est.por_estado.map((x) => ({
    clave: x.clave,
    etiqueta: etiqueta(ESTADOS, x.clave),
    total: x.total,
    color: COLOR_ESTADO[x.clave],
  }))
  const prioridadItems = est.por_prioridad.map((x) => ({
    clave: x.clave,
    etiqueta: x.clave === 'sin_prioridad' ? 'Sin prioridad' : etiqueta(PRIORIDADES, x.clave),
    total: x.total,
    color: COLOR_PRIORIDAD[x.clave],
  }))
  const tagItems = est.por_tag.slice(0, MAX_TAGS).map((x) => ({ clave: x.clave, etiqueta: x.clave, total: x.total }))

  // Tickets creados por día (hora de Guatemala) en las últimas dos semanas, incluido hoy.
  const porDia = {}
  tickets.forEach((t) => {
    const dia = fechaLocal(t.creado_en)
    porDia[dia] = (porDia[dia] ?? 0) + 1
  })
  const tendencia = Array.from({ length: DIAS_TENDENCIA }, (_, i) => {
    const dia = fechaLocal(new Date(ahora - (DIAS_TENDENCIA - 1 - i) * 86400000).toISOString())
    return { clave: dia, etiqueta: `${dia.slice(8)}/${dia.slice(5, 7)}`, total: porDia[dia] ?? 0 }
  })
  const enPeriodo = tendencia.reduce((s, x) => s + x.total, 0)

  return (
    <div className="pagina">
      <header className="pagina-titulo con-acciones">
        <div>
          <h1>Estadísticas</h1>
          <p className="muted">Tickets ingresados al Service Desk, agrupados por servicio del catálogo.</p>
        </div>
        <button className="btn" onClick={() => datos.recargar()} disabled={datos.cargando}>
          ↻ Actualizar
        </button>
      </header>

      <div className="metricas">
        <div className="metrica">
          <span>Total de tickets</span>
          <strong>{total}</strong>
          <small>desde el inicio</small>
        </div>
        <div className="metrica">
          <span>En curso</span>
          <strong>{enCurso}</strong>
          <small>abiertos y en progreso</small>
        </div>
        <div className="metrica">
          <span>Atendidos</span>
          <strong>{atendidos}</strong>
          <small>{total ? Math.round((atendidos / total) * 100) : 0} % resueltos o cerrados</small>
        </div>
        <div className={`metrica ${altaPrioridad ? 'alerta' : ''}`}>
          <span>Alta prioridad</span>
          <strong>{altaPrioridad}</strong>
          <small>P1 y P2</small>
        </div>
        <div className={`metrica ${vencidos ? 'peligro' : ''}`}>
          <span>SLA vencido</span>
          <strong>{vencidos}</strong>
          <small>en curso fuera de plazo</small>
        </div>
      </div>

      {total === 0 ? (
        <Vacio>Todavía no hay tickets. Las gráficas aparecen cuando se ingrese el primero.</Vacio>
      ) : (
        <div className="rejilla-graficas">
          <section className="tarjeta grafica ancho-2">
            <header>
              <h2>Tickets por categoría</h2>
              <div className="leyenda-inline">
                {TIPOS.map((t) => (
                  <span key={t.valor}>
                    <span className="punto" style={{ background: COLOR_TIPO[t.valor] }} />
                    {t.etiqueta}
                  </span>
                ))}
              </div>
            </header>
            <BarrasHorizontales items={categoriasItems} />
          </section>

          <section className="tarjeta grafica">
            <header>
              <h2>Por tipo</h2>
            </header>
            <Dona items={tipoItems} centro="tickets" />
          </section>

          <section className="tarjeta grafica">
            <header>
              <h2>Por estado</h2>
            </header>
            <Dona items={estadoItems} centro="tickets" />
          </section>

          <section className="tarjeta grafica">
            <header>
              <h2>Por prioridad</h2>
              <span className="muted pequeno">impacto × urgencia</span>
            </header>
            <BarrasVerticales items={prioridadItems} />
          </section>

          <section className="tarjeta grafica">
            <header>
              <h2>Por tag</h2>
              {est.por_tag.length > MAX_TAGS && <span className="muted pequeno">top {MAX_TAGS}</span>}
            </header>
            {tagItems.length ? (
              <BarrasHorizontales items={tagItems} />
            ) : (
              <p className="muted">Ningún ticket tiene tags.</p>
            )}
          </section>

          <section className="tarjeta grafica ancho-2">
            <header>
              <h2>Tickets creados por día</h2>
              <span className="muted pequeno">
                últimos {DIAS_TENDENCIA} días · {enPeriodo} ticket{enPeriodo === 1 ? '' : 's'}
              </span>
            </header>
            <BarrasVerticales items={tendencia} alto={140} />
          </section>
        </div>
      )}
    </div>
  )
}
