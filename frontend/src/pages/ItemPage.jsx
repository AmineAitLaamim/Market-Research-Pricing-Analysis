import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, ExternalLink, Trophy, AlertTriangle, CheckCircle, Info } from 'lucide-react'
import { searchApi } from '../api/search'
import { PLATFORMS, CONDITION_LABELS } from '../utils/constants'

function PlatformBadge({ platform }) {
  const p = PLATFORMS.find((x) => x.id === platform)
  return <span className={`badge badge-${platform}`}>{p ? `${p.icon} ${p.name}` : platform}</span>
}

export default function ItemPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [item, setItem] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchItem() {
      try {
        const res = await searchApi.getItem(id)
        setItem(res.data)
      } catch (err) {
        console.error("Failed to load item", err)
      } finally {
        setLoading(false)
      }
    }
    fetchItem()
  }, [id])

  if (loading) {
    return (
      <div className="page-container">
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 20 }} />
        <div className="card" style={{ padding: 40 }}>
          <div className="skeleton" style={{ height: 300, width: '100%', marginBottom: 20 }} />
        </div>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <h2>Item not found</h2>
          <button className="btn btn-secondary" onClick={() => navigate(-1)}>Go back</button>
        </div>
      </div>
    )
  }

  const analysis = item.analysis ?? {}
  const isAnomaly = analysis.is_anomaly
  const dealScore = analysis.deal_score != null ? `${(analysis.deal_score * 100).toFixed(1)}%` : null
  const cluster = analysis.cluster_kmeans != null ? `#${analysis.cluster_kmeans}` : '—'

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} style={{ marginBottom: '20px', color: 'var(--text-secondary)' }}>
          <ArrowLeft size={14} /> Back to results
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <PlatformBadge platform={item.platform} />
          {isAnomaly && <span className="badge badge-warning"><AlertTriangle size={12} style={{ marginRight: 4 }} /> Anomaly Detected</span>}
          {dealScore && !isAnomaly && <span className="badge badge-success"><Trophy size={12} style={{ marginRight: 4 }} /> {dealScore} Deal Score</span>}
        </div>
        <h1 className="page-title" style={{ marginTop: '16px', lineHeight: 1.3 }}>{item.title}</h1>
      </div>

      <div className="grid-2" style={{ gap: '32px' }}>
        {/* Left Column: Image */}
        <div className="card" style={{ padding: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fff' }}>
          {item.image_url ? (
            <img src={item.image_url} alt={item.title} style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain' }} />
          ) : (
            <div className="empty-state" style={{ minHeight: '300px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--surface-sunken)', borderRadius: '8px' }}>
              <span style={{ color: 'var(--text-muted)' }}>No image available</span>
            </div>
          )}
        </div>

        {/* Right Column: Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className="card" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '16px' }}>Price Details</h2>
            <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--brand)', marginBottom: '8px' }}>
              {Number(item.price_mad).toFixed(2)} <span style={{ fontSize: '18px', fontWeight: 600 }}>MAD</span>
            </div>
            {item.currency !== 'MAD' && (
              <div style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                Original: {Number(item.price).toFixed(2)} {item.currency} (Exchange rate: {item.exchange_rate})
              </div>
            )}
            
            <div style={{ marginTop: '24px' }}>
              {item.url && (
                <a href={item.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
                  View on {PLATFORMS.find(p => p.id === item.platform)?.name || item.platform} <ExternalLink size={16} style={{ marginLeft: '8px' }} />
                </a>
              )}
            </div>
          </div>

          <div className="card" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '16px' }}>Item Attributes</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Condition</span>
                <span style={{ fontWeight: 600 }}>{item.condition ? (CONDITION_LABELS[item.condition] ?? item.condition) : 'Unknown'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Seller Rating</span>
                <span style={{ fontWeight: 600 }}>{item.seller_rating != null ? `${Number(item.seller_rating).toFixed(1)} / 5.0 ★` : 'No rating'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Market Cluster</span>
                <span style={{ fontWeight: 600 }}>{cluster}</span>
              </div>
            </div>
          </div>
          
          {item.analysis && (
            <div className={`card ${isAnomaly ? 'anomaly-card' : ''}`} style={{ padding: '24px', border: isAnomaly ? '1px solid var(--color-danger)' : '1px solid var(--border)', background: isAnomaly ? '#fff5f5' : 'var(--surface-sunken)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Info size={16} color={isAnomaly ? 'var(--color-danger)' : 'var(--text-secondary)'} />
                <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: isAnomaly ? 'var(--color-danger)' : 'var(--text-primary)' }}>AI Analysis</h3>
              </div>
              <p style={{ fontSize: '14px', lineHeight: 1.5, color: 'var(--text-secondary)', margin: 0 }}>
                {isAnomaly ? (
                  "This item's price significantly deviates from the market average. It has been flagged as an anomaly by the Isolation Forest algorithm."
                ) : (
                  `This item belongs to market cluster ${cluster}. Based on the price distribution within this cluster, it has a relative deal score of ${dealScore ?? 'N/A'}.`
                )}
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
