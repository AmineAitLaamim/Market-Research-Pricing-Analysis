import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import { TrendingUp } from 'lucide-react'

function CustomDot(props) {
  const { cx, cy, payload } = props
  if (cx == null || cy == null) return null
  const color = payload.is_lowest ? '#3B6D11' : payload.is_highest ? '#A32D2D' : '#C1502E'
  const r = (payload.is_lowest || payload.is_highest) ? 5 : 3
  return <circle cx={cx} cy={cy} r={r} fill={color} stroke="#fff" strokeWidth={1.5} />
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null
  const d = payload[0].payload
  return (
    <div style={{ background: '#fff', border: '0.5px solid var(--border)', borderRadius: '8px', padding: '10px 12px', fontSize: '13px' }}>
      <div style={{ fontWeight: 500, marginBottom: '4px' }}>{d.dateLabel}</div>
      <div style={{ color: '#C1502E', fontWeight: 500 }}>{d.price_mad.toFixed(2)} MAD</div>
      {d.is_lowest && <span style={{ fontSize: '11px', background: '#e8f5e9', color: '#2e7d32', padding: '1px 6px', borderRadius: '4px', marginTop: '4px', display: 'inline-block' }}>All-time low</span>}
      {d.is_highest && <span style={{ fontSize: '11px', background: '#ffebee', color: '#c62828', padding: '1px 6px', borderRadius: '4px', marginTop: '4px', display: 'inline-block' }}>All-time high</span>}
    </div>
  )
}

export default function PriceChart({ priceHistory, calendarData, avgPrice, threshold }) {
  if (!priceHistory || priceHistory.length === 0) return null

  if (priceHistory.length === 1) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '200px', border: '0.5px solid var(--border)', borderRadius: '12px', gap: '10px', color: 'var(--text-muted)' }}>
        <TrendingUp size={24} />
        <span style={{ fontSize: '13px', textAlign: 'center' }}>Only one scrape recorded. Scrape again to see price evolution.</span>
      </div>
    )
  }

  // Build calendar flag lookup by date string
  const calMap = {}
  if (calendarData) calendarData.forEach(c => { calMap[c.date] = c })

  // Build chart data sorted chronologically (oldest → newest = left → right)
  const chartData = priceHistory
    .map(p => {
      const dt = new Date(p.date)
      const cal = calMap[p.date]
      return {
        ...p,
        _ts: dt.getTime(),
        dateLabel: dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        is_lowest: cal?.is_lowest || false,
        is_highest: cal?.is_highest || false,
      }
    })
    .sort((a, b) => a._ts - b._ts)

  const prices = chartData.map(d => d.price_mad)
  const minP = Math.min(...prices)
  const maxP = Math.max(...prices)
  const padding = (maxP - minP) * 0.1 || 10

  return (
    <div style={{ borderRadius: '12px', border: '0.5px solid var(--border)', padding: '16px' }}>
      <h3 style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 16px' }}>Price history</h3>
      <div style={{ height: '280px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
            <XAxis
              dataKey="dateLabel" tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
              tickLine={false} axisLine={false} dy={8}
              interval={chartData.length <= 12 ? 0 : 'preserveStartEnd'}
            />
            <YAxis
              domain={[minP - padding, maxP + padding]}
              tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
              tickLine={false} axisLine={false} width={55}
              tickFormatter={v => `${Math.round(v)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={avgPrice} strokeDasharray="5 5" stroke="var(--text-muted)" label={{ value: 'avg', position: 'right', fill: 'var(--text-muted)', fontSize: 11 }} />
            {threshold && (
              <ReferenceLine y={threshold.threshold_mad} strokeDasharray="5 5" stroke="#C1502E" label={{ value: 'your target', position: 'right', fill: '#C1502E', fontSize: 11 }} />
            )}
            <Line
              type="monotone" dataKey="price_mad" stroke="#C1502E" strokeWidth={2}
              dot={<CustomDot />} activeDot={{ r: 6, fill: '#C1502E' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
