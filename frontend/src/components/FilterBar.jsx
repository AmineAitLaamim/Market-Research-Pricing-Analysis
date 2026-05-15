import { PLATFORMS, SORT_OPTIONS } from '../utils/constants'

export default function FilterBar({ filters, onChange }) {
  function update(key, value) {
    onChange({ ...filters, [key]: value, page: 1 })
  }

  return (
    <div className="filter-bar">
      {/* Platform */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>Platform</label>
        <select
          id="filter-platform"
          className="filter-select"
          value={filters.platform || ''}
          onChange={(e) => update('platform', e.target.value)}
        >
          <option value="">All Platforms</option>
          {PLATFORMS.map((p) => (
            <option key={p.id} value={p.id}>{p.icon} {p.name}</option>
          ))}
        </select>
      </div>

      {/* Sort */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>Sort</label>
        <select
          id="filter-sort"
          className="filter-select"
          value={filters.sort || 'default'}
          onChange={(e) => update('sort', e.target.value)}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Anomaly */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>Anomalies</label>
        <select
          id="filter-anomaly"
          className="filter-select"
          value={filters.anomaly || 'all'}
          onChange={(e) => update('anomaly', e.target.value)}
        >
          <option value="all">Show All</option>
          <option value="false">Hide Anomalies</option>
          <option value="true">Show only anomalies</option>
        </select>
      </div>

      {/* Reset */}
      {(filters.platform || filters.sort !== 'default' || filters.anomaly !== 'all') && (
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => onChange({ platform: '', sort: 'default', anomaly: 'all', page: 1 })}
          style={{ marginLeft: 'auto' }}
        >
          ✕ Reset filters
        </button>
      )}
    </div>
  )
}
