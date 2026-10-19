// Gráficas simples en HTML/SVG, sin librerías.

// Barras horizontales. items: [{ clave, etiqueta, total, color? }]
export function BarrasHorizontales({ items }) {
  const max = Math.max(1, ...items.map((i) => i.total))
  return (
    <ul className="barras">
      {items.map((i) => (
        <li key={i.clave} className="barra-fila" title={`${i.etiqueta}: ${i.total}`}>
          <span className="barra-etiqueta">{i.etiqueta}</span>
          <span className="barra-pista">
            <span
              className="barra-relleno"
              style={{ width: `${(i.total / max) * 100}%`, background: i.color || 'var(--acento)' }}
            />
          </span>
          <span className="barra-valor">{i.total}</span>
        </li>
      ))}
    </ul>
  )
}

// Barras verticales. items: [{ clave, etiqueta, total, color? }]
export function BarrasVerticales({ items, alto = 180 }) {
  const max = Math.max(1, ...items.map((i) => i.total))
  return (
    <div className="columnas" style={{ height: alto + 40 }}>
      {items.map((i) => (
        <div key={i.clave} className="columna" title={`${i.etiqueta}: ${i.total}`}>
          <span className="columna-valor">{i.total}</span>
          <span
            className="columna-barra"
            style={{ height: Math.max(2, (i.total / max) * alto), background: i.color || 'var(--acento)' }}
          />
          <span className="columna-etiqueta">{i.etiqueta}</span>
        </div>
      ))}
    </div>
  )
}

// Dona. items: [{ clave, etiqueta, total, color }]
export function Dona({ items, centro }) {
  const total = items.reduce((s, i) => s + i.total, 0)
  const r = 60
  const c = 2 * Math.PI * r
  let acumulado = 0
  return (
    <div className="dona">
      <svg viewBox="0 0 160 160" role="img" aria-label={items.map((i) => `${i.etiqueta}: ${i.total}`).join(', ')}>
        <circle cx="80" cy="80" r={r} fill="none" stroke="var(--borde)" strokeWidth="22" />
        {total > 0 &&
          items.map((i) => {
            const largo = (i.total / total) * c
            const seg = (
              <circle
                key={i.clave}
                cx="80"
                cy="80"
                r={r}
                fill="none"
                stroke={i.color}
                strokeWidth="22"
                strokeDasharray={`${largo} ${c - largo}`}
                strokeDashoffset={-acumulado}
                transform="rotate(-90 80 80)"
              >
                <title>{`${i.etiqueta}: ${i.total}`}</title>
              </circle>
            )
            acumulado += largo
            return seg
          })}
        <text x="80" y="78" textAnchor="middle" className="dona-total">
          {total}
        </text>
        <text x="80" y="98" textAnchor="middle" className="dona-sub">
          {centro}
        </text>
      </svg>
      <ul className="leyenda">
        {items.map((i) => (
          <li key={i.clave}>
            <span className="punto" style={{ background: i.color }} />
            {i.etiqueta}
            <strong>{i.total}</strong>
            <small>{total ? Math.round((i.total / total) * 100) : 0}%</small>
          </li>
        ))}
      </ul>
    </div>
  )
}