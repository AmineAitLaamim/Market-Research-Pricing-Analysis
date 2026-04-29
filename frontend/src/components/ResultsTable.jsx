import { ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { PLATFORMS, CONDITION_LABELS } from '../utils/constants'

function PlatformBadge({ platform }) {
  const p = PLATFORMS.find((x) => x.id === platform)
  return <span className={`badge badge-${platform}`}>{p ? `${p.icon} ${p.name}` : platform}</span>
}

export default function ResultsTable({ results = [], loading = false, total = 0, page = 1, pageSize = 20, onPageChange }) {
  const navigate = useNavigate()
  const totalPages = Math.ceil(total / pageSize) || 1

  if (loading) {
    return (
      <div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton" style={{ height: '48px', borderRadius: '8px', marginBottom: '8px' }} />
        ))}
      </div>
    )
  }

  if (!results.length) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon">🔍</span>
        <p className="empty-state-title">No results match your filters</p>
        <p className="empty-state-desc">Try adjusting the platform or sort options</p>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '20px' }}>
        {results.map((r, i) => {
          const analysis   = r.analysis ?? {}
          const isAnomaly  = analysis.is_anomaly
          const dealScore  = analysis.deal_score != null ? `${(analysis.deal_score * 100).toFixed(1)}%` : '—'
          const cluster    = analysis.cluster_kmeans != null ? `#${analysis.cluster_kmeans}` : '—'

          return (
            <div 
              key={r.id ?? i} 
              className={`card animate-scale-in`} 
              onClick={() => navigate(`/item/${r.id}`)}
              style={{ 
                padding: '16px', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '12px',
                border: isAnomaly ? '1px solid #ffcdd2' : '1px solid var(--border)',
                background: isAnomaly ? '#fff5f5' : '#fff',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}
            >
              {/* Image Container */}
              <div style={{ width: '100%', height: '180px', position: 'relative', background: '#fff', borderRadius: '6px', overflow: 'hidden' }}>
                {r.image_url ? (
                  <img src={r.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                ) : (
                  <div style={{ width: '100%', height: '100%', background: 'var(--surface-sunken)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No image</div>
                )}
                <div style={{ position: 'absolute', top: 8, right: 8 }}>
                  <PlatformBadge platform={r.platform} />
                </div>
              </div>

              {/* Text Info */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ 
                  fontSize: '14px', 
                  fontWeight: 600, 
                  margin: '0 0 8px 0', 
                  display: '-webkit-box', 
                  WebkitLineClamp: 2, 
                  WebkitBoxOrient: 'vertical', 
                  overflow: 'hidden',
                  lineHeight: '1.4'
                }} title={r.title}>
                  {r.title}
                </h3>
                
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--brand)', marginBottom: '12px' }}>
                  {Number(r.price_mad ?? r.price ?? 0).toFixed(2)} <span style={{ fontSize: '13px', fontWeight: 600 }}>MAD</span>
                </div>
                
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', marginBottom: 'auto' }}>
                  <span>{r.condition ? (CONDITION_LABELS[r.condition] ?? r.condition) : 'Condition N/A'}</span>
                  <span>{r.seller_rating != null ? `${Number(r.seller_rating).toFixed(1)} ★` : 'No rating'}</span>
                </div>
              </div>

              {/* Footer */}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {cluster !== '—' && <span className="badge badge-info" title="Cluster ID">{cluster}</span>}
                  {isAnomaly 
                    ? <span className="badge badge-warning">⚠️ Anomaly</span>
                    : (dealScore !== '—' && <span className="badge badge-success">{dealScore}</span>)
                  }
                </div>
                {r.url && (
                  <a href={r.url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-sm" style={{ padding: '6px 10px' }} onClick={(e) => e.stopPropagation()}>
                    View <ExternalLink size={14} style={{ marginLeft: '4px' }} />
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          className="btn btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          ← Prev
        </button>
        <span className="pagination-info">Page {page} of {totalPages} &nbsp;·&nbsp; {total} results</span>
        <button
          className="btn btn-secondary btn-sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next →
        </button>
      </div>
    </div>
  )
}
