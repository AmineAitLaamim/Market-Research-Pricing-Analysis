import { useMemo } from 'react'

export default function PriceCalendar({ calendarData }) {
  const grid = useMemo(() => {
    if (!calendarData || calendarData.length === 0) return null

    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - 89) // last 90 days

    const prices = calendarData.map(d => d.price_mad)
    const minP = Math.min(...prices)
    const maxP = Math.max(...prices)
    const range = maxP - minP || 1

    // Map date string → calendar entry
    const dateMap = {}
    calendarData.forEach(d => { dateMap[d.date] = d })

    // Green scale — cheaper = darker
    const colorScale = (price) => {
      const t = 1 - (price - minP) / range // 1 = cheapest, 0 = most expensive
      const colors = ['#C0DD97', '#8FBE5A', '#5E9A2E', '#3B6D11', '#27500A']
      const idx = Math.min(Math.floor(t * (colors.length - 1)), colors.length - 1)
      return colors[idx]
    }

    // Build 7 rows × ~13 cols grid
    const cells = []
    const months = []
    let lastMonth = -1
    const cursor = new Date(startDate)

    // Align to start of week (Sunday)
    cursor.setDate(cursor.getDate() - cursor.getDay())
    const gridStart = new Date(cursor)

    let col = 0
    while (cursor <= today) {
      for (let row = 0; row < 7; row++) {
        const d = new Date(gridStart)
        d.setDate(gridStart.getDate() + col * 7 + row)
        if (d > today) break

        const dateStr = d.toISOString().slice(0, 10)
        const entry = dateMap[dateStr]
        const x = col * 12
        const y = row * 12

        // Month label
        if (d.getMonth() !== lastMonth && row === 0) {
          lastMonth = d.getMonth()
          months.push({ label: d.toLocaleDateString('en-US', { month: 'short' }), x })
        }

        cells.push({
          x, y, dateStr,
          fill: entry ? colorScale(entry.price_mad) : 'var(--bg-muted)',
          title: entry ? `${dateStr}: ${entry.price_mad.toFixed(0)} MAD` : dateStr,
        })
      }
      col++
      cursor.setDate(cursor.getDate() + 7)
    }

    const width = (col + 1) * 12
    return { cells, months, width }
  }, [calendarData])

  if (!grid) return <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>No calendar data</div>

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <svg width={grid.width} height={110} style={{ display: 'block' }}>
          {/* Month labels */}
          {grid.months.map((m, i) => (
            <text key={i} x={m.x} y={10} fontSize={10} fill="var(--text-muted)">{m.label}</text>
          ))}
          {/* Cells */}
          {grid.cells.map((c, i) => (
            <rect key={i} x={c.x} y={c.y + 16} width={10} height={10} rx={2} fill={c.fill}>
              <title>{c.title}</title>
            </rect>
          ))}
        </svg>
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
        <span>Higher price</span>
        <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#C0DD97' }} />
        <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#5E9A2E' }} />
        <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#27500A' }} />
        <span>Lower price</span>
      </div>
    </div>
  )
}
