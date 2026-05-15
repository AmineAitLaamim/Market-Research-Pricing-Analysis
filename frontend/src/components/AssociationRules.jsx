import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'

const MIN_SUPPORT = 0.1
const MAX_SUPPORT = 50
const SUPPORT_STEP = 0.1

export default function AssociationRules({
  rules = [],
  totalResults = 0,
  loading = false,
  minSupport = 3,
  onSupportChange,
}) {
  const [sortKey, setSortKey]   = useState('lift')
  const [sortDir, setSortDir]   = useState('desc')

  const supportControl = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '18px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
        <label htmlFor="association-support" style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Minimum support
        </label>
        <span className="badge badge-neutral">{minSupport.toFixed(1)}%</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <input
          id="association-support"
          type="range"
          min={MIN_SUPPORT}
          max={MAX_SUPPORT}
          step={SUPPORT_STEP}
          value={minSupport}
          onChange={(e) => onSupportChange?.(Number(e.target.value))}
          style={{ flex: 1 }}
        />
        <input
          type="number"
          min={MIN_SUPPORT}
          max={MAX_SUPPORT}
          step={SUPPORT_STEP}
          value={minSupport}
          onChange={(e) => {
            const next = Number(e.target.value)
            if (!Number.isNaN(next)) onSupportChange?.(Math.min(MAX_SUPPORT, Math.max(MIN_SUPPORT, next)))
          }}
          style={{
            width: '84px',
            padding: '8px 10px',
            borderRadius: '10px',
            border: '1px solid var(--border-light)',
            background: 'var(--surface-primary)',
            color: 'var(--text-primary)',
          }}
        />
      </div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {[0.5, 1, 3, 5, 10, 20].map((value) => (
          <button
            key={value}
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => onSupportChange?.(value)}
            style={{
              padding: '6px 10px',
              borderColor: Math.abs(minSupport - value) < 0.001 ? 'var(--accent)' : undefined,
              background: Math.abs(minSupport - value) < 0.001 ? 'var(--surface-secondary)' : undefined,
            }}
          >
            {value}%
          </button>
        ))}
      </div>
    </div>
  )

  if (loading) {
    return (
      <>
        {supportControl}
        <div className="empty-state" style={{ minHeight: '160px' }}>
          <span className="empty-state-icon">⏳</span>
          <p className="empty-state-title">Loading association rules</p>
          <p className="empty-state-desc">Applying the selected support threshold.</p>
        </div>
      </>
    )
  }

  if (!rules.length) {
    const notEnoughData = totalResults > 0 && totalResults < 30
    return (
      <>
        {supportControl}
        <div className="empty-state" style={{ minHeight: '160px' }}>
          <span className="empty-state-icon">🔗</span>
          <p className="empty-state-title">
            {notEnoughData ? 'Not enough data for association rules' : 'No association rules found'}
          </p>
          <p className="empty-state-desc">
            {notEnoughData
              ? 'Minimum 30 results required'
              : `No rules met the current thresholds. Try lowering support below ${minSupport.toFixed(1)}%.`}
          </p>
        </div>
      </>
    )
  }

  function handleSort(key) {
    if (key === sortKey) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...rules].sort((a, b) => {
    const va = a[sortKey], vb = b[sortKey]
    if (typeof va === 'number') return sortDir === 'asc' ? va - vb : vb - va
    return sortDir === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va))
  })

  function SortIcon({ col }) {
    if (col !== sortKey) return null
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  const cols = [
    { key: 'antecedent', label: 'Antecedent' },
    { key: 'consequent', label: 'Consequent' },
    { key: 'support',    label: 'Support %' },
    { key: 'confidence', label: 'Confidence %' },
    { key: 'lift',       label: 'Lift' },
  ]

  return (
    <>
      {supportControl}
      <div
        style={{
          maxHeight: '420px',
          overflow: 'auto',
          border: '1px solid var(--border-light)',
          borderRadius: '14px',
          background: 'var(--surface-primary)',
        }}
      >
        <table
          className="data-table"
          style={{
            borderCollapse: 'separate',
            borderSpacing: 0,
          }}
        >
          <thead>
            <tr>
              {cols.map((c) => (
                <th
                  key={c.key}
                  onClick={() => handleSort(c.key)}
                  style={{
                    whiteSpace: 'nowrap',
                    position: 'sticky',
                    top: 0,
                    background: 'var(--surface-primary)',
                    zIndex: 3,
                    boxShadow: '0 1px 0 var(--border)',
                  }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    {c.label} <SortIcon col={c.key} />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r, i) => {
              const antecedentValue = r.antecedent ?? r.antecedents
              const consequentValue = r.consequent ?? r.consequents
              const ant = Array.isArray(antecedentValue) ? antecedentValue.join(', ') : antecedentValue
              const con = Array.isArray(consequentValue) ? consequentValue.join(', ') : consequentValue
              return (
                <tr key={i}>
                  <td><span className="badge badge-neutral">{ant}</span></td>
                  <td><span className="badge badge-info">{con}</span></td>
                  <td>{(r.support * 100).toFixed(1)}%</td>
                  <td>{(r.confidence * 100).toFixed(1)}%</td>
                  <td style={{ fontWeight: 600, color: r.lift > 1.5 ? 'var(--color-success)' : 'var(--text-secondary)' }}>
                    {r.lift.toFixed(3)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </>
  )
}
