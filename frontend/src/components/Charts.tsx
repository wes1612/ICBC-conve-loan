import type { CashGapResult, DimensionScores } from '../types'

const dimensionLabels: Record<keyof DimensionScores, string> = {
  stability: '经营稳定性',
  growth: '成长性',
  authenticity: '经营真实性',
  capacity: '消费承接能力',
  online_reputation: '线上口碑',
  social_activity: '社媒活跃度',
  complaint_risk: '投诉风险控制',
  unstructured: '非结构化评价',
}

export function DimensionBars({ values }: { values: DimensionScores }) {
  return (
    <div className="dimension-list">
      {(Object.keys(dimensionLabels) as Array<keyof DimensionScores>).map((key) => {
        const value = values[key]
        return (
          <div className="dimension-row" key={key}>
            <div className="dimension-row__meta">
              <span>{dimensionLabels[key]}</span>
              <strong>{value.toFixed(1)}</strong>
            </div>
            <div className="dimension-track" aria-label={`${dimensionLabels[key]} ${value.toFixed(1)}分`}>
              <span
                className={value < 50 ? 'is-low' : value < 75 ? 'is-medium' : ''}
                style={{ width: `${Math.max(2, value)}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function currencyShort(value: number) {
  if (Math.abs(value) >= 10000) return `${(value / 10000).toFixed(1)}万`
  return `${Math.round(value)}`
}

export function CashGapChart({ data }: { data: CashGapResult }) {
  const width = 680
  const height = 250
  const padding = { x: 54, top: 28, bottom: 42 }
  const values = data.forecasts.flatMap((item) => [
    item.p50_ending_cash,
    item.p90_ending_cash,
    data.minimum_cash_balance,
  ])
  const max = Math.max(...values) * 1.12
  const min = Math.min(0, ...values) * 1.08
  const plotHeight = height - padding.top - padding.bottom
  const y = (value: number) => padding.top + ((max - value) / Math.max(1, max - min)) * plotHeight
  const x = (index: number) => padding.x + index * ((width - padding.x * 2) / Math.max(1, data.forecasts.length - 1))
  const p50 = data.forecasts.map((item, index) => `${x(index)},${y(item.p50_ending_cash)}`).join(' ')
  const p90 = data.forecasts.map((item, index) => `${x(index)},${y(item.p90_ending_cash)}`).join(' ')
  const minY = y(data.minimum_cash_balance)

  return (
    <div className="chart-wrap">
      <div className="chart-legend">
        <span><i className="legend-line legend-line--p50" />P50 期末现金</span>
        <span><i className="legend-line legend-line--p90" />P90 压力情景</span>
        <span><i className="legend-line legend-line--min" />最低安全现金</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="未来三个月现金余额情景图">
        {[0, 0.5, 1].map((ratio) => {
          const value = min + (max - min) * ratio
          const gridY = y(value)
          return (
            <g key={ratio}>
              <line x1={padding.x} y1={gridY} x2={width - padding.x} y2={gridY} className="chart-grid" />
              <text x={padding.x - 10} y={gridY + 4} textAnchor="end" className="chart-label">{currencyShort(value)}</text>
            </g>
          )
        })}
        <line x1={padding.x} y1={minY} x2={width - padding.x} y2={minY} className="chart-min" />
        <polyline points={p50} className="chart-line chart-line--p50" />
        <polyline points={p90} className="chart-line chart-line--p90" />
        {data.forecasts.map((item, index) => (
          <g key={item.forecast_month}>
            <circle cx={x(index)} cy={y(item.p50_ending_cash)} r="5" className="chart-dot chart-dot--p50" />
            <circle cx={x(index)} cy={y(item.p90_ending_cash)} r="5" className="chart-dot chart-dot--p90" />
            <text x={x(index)} y={height - 12} textAnchor="middle" className="chart-label">
              {new Intl.DateTimeFormat('zh-CN', { month: 'short' }).format(new Date(item.forecast_month))}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
