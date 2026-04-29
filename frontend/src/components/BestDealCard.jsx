import { ExternalLink, Trophy } from 'lucide-react'
import { PLATFORMS } from '../utils/constants'

function PlatformBadge({ platform }) {
  const p = PLATFORMS.find((x) => x.id === platform)
  return (
    <span className={`badge badge-${platform}`}>
      {p ? `${p.icon} ${p.name}` : platform}
    </span>
  )
}

export default function BestDealCard({ deal, loading = false }) {
  if (loading) {
    return (
      <div className="best-deal-card">
        <div className="skeleton" style={{ height: '13px', width: '100px', marginBottom: '16px' }} />
        <div className="skeleton" style={{ height: '18px', width: '75%', marginBottom: '12px' }} />
        <div className="skeleton" style={{ height: '28px', width: '130px', marginBottom: '12px' }} />
        <div className="skeleton" style={{ height: '34px', width: '140px' }} />
      </div>
    )
  }

  if (!deal) {
    return (
      <div className="best-deal-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Trophy size={16} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
            Best Deal
          </span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          No deal available — all items were flagged as anomalous.
        </p>
      </div>
    )
  }

  const score = deal.deal_score != null ? `${(deal.deal_score * 100).toFixed(1)}%` : null

  return (
    <div className="best-deal-card animate-scale-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
        <Trophy size={16} style={{ color: 'var(--brand)' }} />
        <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
          Best Deal Found
        </span>
        {score && (
          <span className="badge badge-success" style={{ marginLeft: 'auto' }}>
            {score} deal score
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', marginBottom: '14px' }}>
        {deal.image_url && (
          <img src={deal.image_url} alt="" style={{ width: 64, height: 64, objectFit: 'contain', borderRadius: 6, background: '#fff', padding: '4px', border: '1px solid var(--border)' }} />
        )}
        <p style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-primary)', lineHeight: 1.45, margin: 0 }}>
          {deal.title}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '18px' }}>
        <PlatformBadge platform={deal.platform} />
        <span style={{
          fontFamily: "'Source Serif 4', serif",
          fontSize: '26px',
          fontWeight: 700,
          color: 'var(--brand)',
          letterSpacing: '-0.01em',
        }}>
          {Number(deal.price).toFixed(2)} MAD
        </span>
      </div>

      {deal.url && (
        <a
          href={deal.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary btn-sm"
          style={{ display: 'inline-flex' }}
        >
          <ExternalLink size={13} />
          View listing
        </a>
      )}
    </div>
  )
}
