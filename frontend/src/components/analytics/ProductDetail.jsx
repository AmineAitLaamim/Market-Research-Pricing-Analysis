import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyticsApi } from '../../api/analytics'
import PriceChart from './PriceChart'
import PriceCalendar from './PriceCalendar'
import {
  ArrowLeft, CheckCircle, Tag, Clock, HelpCircle, Minus,
  TrendingDown, TrendingUp, ArrowUpDown, ExternalLink, Bell,
  AlertCircle, Search as SearchIcon
} from 'lucide-react'

const VERDICT_CONFIG = {
  buy_now:   { icon: CheckCircle,  label: 'Buy now',         bg: '#e8f5e9', color: '#2e7d32' },
  good_deal: { icon: Tag,          label: 'Good deal',        bg: '#e0f2f1', color: '#00796b' },
  wait:      { icon: Clock,        label: 'Wait',             bg: '#fff8e1', color: '#f57f17' },
  uncertain: { icon: HelpCircle,   label: 'Not enough data',  bg: 'var(--bg-muted)', color: 'var(--text-muted)' },
  neutral:   { icon: Minus,        label: 'No strong signal',  bg: '#e3f2fd', color: '#1565c0' },
}

const TREND_CONFIG = {
  dropping:    { icon: TrendingDown, label: 'Price is dropping',    bg: '#e8f5e9', color: '#2e7d32' },
  rising:      { icon: TrendingUp,   label: 'Price is rising',      bg: '#ffebee', color: '#c62828' },
  stable:      { icon: Minus,        label: 'Price is stable',      bg: '#e3f2fd', color: '#1565c0' },
  fluctuating: { icon: ArrowUpDown,  label: 'Price is fluctuating', bg: '#fff8e1', color: '#f57f17' },
  uncertain:   { icon: HelpCircle,   label: 'Not enough data yet',  bg: 'var(--bg-muted)', color: 'var(--text-muted)' },
}

export default function ProductDetail({ product, onBack, onSelectProduct }) {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [thresholdInput, setThresholdInput] = useState('')
  const [thresholdSaved, setThresholdSaved] = useState(false)
  const [thresholdError, setThresholdError] = useState('')

  function load() {
    setLoading(true)
    setError(null)
    Promise.all([
      analyticsApi.getProductHistory(product.normalized_title || product.title, product.platform),
      analyticsApi.getSimilarProducts(product.normalized_title || product.title, product.platform),
    ])
      .then(([histRes, simRes]) => {
        setData(histRes.data)
        setSimilar(simRes.data)
        if (histRes.data.threshold) setThresholdInput(String(histRes.data.threshold.threshold_mad))
      })
      .catch(() => setError('Something went wrong loading this product'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [product.normalized_title, product.title, product.platform])

  async function saveThreshold() {
    setThresholdError('')
    const val = parseFloat(thresholdInput)
    if (!val || val <= 0) { setThresholdError('Must be a positive number'); return }
    try {
      await analyticsApi.setThreshold(product.normalized_title, product.platform, val)
      setThresholdSaved(true)
      setTimeout(() => setThresholdSaved(false), 2000)
    } catch { setThresholdError('Failed to save') }
  }

  // Loading skeleton
  if (loading) return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="skeleton" style={{ height: '50px', borderRadius: '10px' }} />
      <div className="skeleton" style={{ height: '64px', borderRadius: '10px' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
        {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: '80px', borderRadius: '10px' }} />)}
      </div>
      <div className="skeleton" style={{ height: '40px', borderRadius: '10px' }} />
      <div className="skeleton" style={{ height: '280px', borderRadius: '10px' }} />
      <div style={{ display: 'grid', gridTemplateColumns: '60% 40%', gap: '12px' }}>
        <div className="skeleton" style={{ height: '120px', borderRadius: '10px' }} />
        <div className="skeleton" style={{ height: '120px', borderRadius: '10px' }} />
      </div>
      {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: '36px', borderRadius: '6px' }} />)}
    </div>
  )

  // Error state
  if (error) return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', gap: '12px' }}>
      <AlertCircle size={24} color="#c62828" />
      <p style={{ fontWeight: 500, fontSize: '15px' }}>{error}</p>
      <button className="btn btn-primary" onClick={load}>Try again</button>
      <button className="btn btn-secondary btn-sm" onClick={onBack} style={{ marginTop: '8px' }}>← Back</button>
    </div>
  )

  if (!data) return null

  const { summary, trend, recommendation, price_history, price_brackets, scrape_log, calendar_data, threshold } = data
  const vc = VERDICT_CONFIG[recommendation.verdict] || VERDICT_CONFIG.neutral
  const tc = TREND_CONFIG[trend] || TREND_CONFIG.uncertain
  const VerdictIcon = vc.icon
  const TrendIcon = tc.icon

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

      {/* A — Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <button onClick={onBack} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', padding: '6px' }}>
          <ArrowLeft size={18} />
        </button>
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {data.image_url && (
            <img src={data.image_url} alt={data.title} style={{ width: '200px', height: '200px', objectFit: 'contain', marginBottom: '16px', borderRadius: '12px', background: '#fff', border: '0.5px solid var(--border)' }} />
          )}
          <h1 style={{ fontSize: '18px', fontWeight: 500, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}>{data.title}</h1>
          <span style={{ fontSize: '11px', background: 'var(--bg-muted)', padding: '2px 8px', borderRadius: '4px', textTransform: 'capitalize', marginTop: '4px' }}>{data.platform}</span>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => navigate(`/search?q=${encodeURIComponent(scrape_log[0]?.search_query || '')}`)}>
          <SearchIcon size={12} /> Scrape now
        </button>
      </div>

      {/* B — Recommendation */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 18px', borderRadius: '12px', background: vc.bg }}>
        <VerdictIcon size={22} color={vc.color} />
        <div>
          <div style={{ fontWeight: 500, fontSize: '15px', color: vc.color }}>{vc.label}</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>{recommendation.reason}</div>
        </div>
      </div>

      {/* C — Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
        <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-muted)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Current price</div>
          <div style={{ fontSize: '20px', fontWeight: 500, color: '#C1502E' }}>{summary.current_price.toFixed(2)}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>MAD</div>
        </div>
        <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-muted)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>All-time low</div>
          <div style={{ fontSize: '20px', fontWeight: 500 }}>{summary.lowest_price.toFixed(2)}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{summary.lowest_price_date}</div>
        </div>
        <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-muted)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>All-time high</div>
          <div style={{ fontSize: '20px', fontWeight: 500 }}>{summary.highest_price.toFixed(2)}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{summary.highest_price_date}</div>
        </div>
        <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-muted)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Average price</div>
          <div style={{ fontSize: '20px', fontWeight: 500 }}>{summary.avg_price.toFixed(2)}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>MAD</div>
        </div>
        <div style={{ padding: '14px', borderRadius: '10px', background: 'var(--bg-muted)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Days tracked</div>
          <div style={{ fontSize: '20px', fontWeight: 500 }}>{summary.days_tracked}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{summary.total_scrapes} scrapes</div>
        </div>
      </div>

      {/* D — Trend pill */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', height: '40px', borderRadius: '10px', background: tc.bg }}>
        <TrendIcon size={16} color={tc.color} />
        <span style={{ fontSize: '13px', fontWeight: 500, color: tc.color }}>{tc.label}</span>
      </div>

      {/* E — Price chart */}
      <PriceChart priceHistory={price_history} calendarData={calendar_data} avgPrice={summary.avg_price} threshold={threshold} />

      {/* F — Calendar + Brackets */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        {/* Calendar */}
        <div style={{ padding: '16px', borderRadius: '12px', border: '0.5px solid var(--border)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 12px' }}>Price calendar</h3>
          <PriceCalendar calendarData={calendar_data} />
        </div>

        {/* Brackets */}
        <div style={{ padding: '16px', borderRadius: '12px', border: '0.5px solid var(--border)' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 14px' }}>Price distribution</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {price_brackets.map((b, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '12px', width: '120px', flexShrink: 0, color: 'var(--text-secondary)' }}>{b.label}</span>
                <div style={{ flex: 1, height: '10px', background: 'var(--bg-muted)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${b.percent}%`, height: '100%', background: '#C1502E', opacity: i === 0 ? 1 : i === 1 ? 0.65 : 0.35, borderRadius: '4px' }} />
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', flexShrink: 0, width: '90px', textAlign: 'right' }}>{b.count} times · {b.percent.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* G — Similar products */}
      {similar.length > 0 && (
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 12px' }}>Similar products in your history</h3>
          <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
            {similar.map((s, i) => (
              <div
                key={i}
                onClick={() => onSelectProduct(s)}
                style={{
                  minWidth: '200px', padding: '14px', borderRadius: '10px',
                  border: '0.5px solid var(--border)', cursor: 'pointer', flexShrink: 0,
                  transition: 'border-color 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#C1502E'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <div style={{ fontSize: '13px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', marginBottom: '6px', lineHeight: '1.3' }}>{s.title}</div>
                <span style={{ fontSize: '11px', background: 'var(--bg-muted)', padding: '1px 5px', borderRadius: '4px', textTransform: 'capitalize' }}>{s.platform}</span>
                <div style={{ fontSize: '14px', fontWeight: 500, marginTop: '8px' }}>{s.latest_price_mad.toFixed(0)} MAD</div>
                <div style={{ fontSize: '12px', fontWeight: 500, color: s.price_diff_direction === 'cheaper' ? '#2e7d32' : s.price_diff_direction === 'more_expensive' ? '#c62828' : 'var(--text-muted)', marginTop: '2px' }}>
                  {s.price_diff_direction === 'cheaper' ? `-${s.price_diff_mad.toFixed(0)} MAD` : s.price_diff_direction === 'more_expensive' ? `+${s.price_diff_mad.toFixed(0)} MAD` : 'Same price'}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>{s.scrape_count} scrapes</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* H — Scrape log */}
      <div>
        <h3 style={{ fontSize: '14px', fontWeight: 500, margin: '0 0 12px' }}>Scrape history</h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto', borderRadius: '10px', border: '0.5px solid var(--border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed', fontSize: '13px' }}>
            <colgroup>
              <col style={{ width: '130px' }} />
              <col style={{ width: '110px' }} />
              <col style={{ width: '120px' }} />
              <col style={{ width: '60px' }} />
            </colgroup>
            <thead>
              <tr style={{ background: 'var(--bg-muted)' }}>
                <th style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: 'var(--text-secondary)' }}>Date</th>
                <th style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: 'var(--text-secondary)' }}>Price (MAD)</th>
                <th style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 500, fontSize: '12px', color: 'var(--text-secondary)' }}>Keyword</th>
                <th style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 500, fontSize: '12px', color: 'var(--text-secondary)' }}>Link</th>
              </tr>
            </thead>
            <tbody>
              {scrape_log.map((entry, i) => (
                <tr key={i} style={{ background: i % 2 === 1 ? 'var(--bg-muted)' : '' }}>
                  <td style={{ padding: '10px 14px' }}>{new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                  <td style={{ padding: '10px 14px', fontWeight: 500 }}>{entry.price_mad.toFixed(2)}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{ background: 'var(--bg-muted)', padding: '2px 8px', borderRadius: '6px', fontSize: '12px' }}>{entry.search_query}</span>
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                    <a href={entry.product_url} target="_blank" rel="noreferrer" style={{ color: '#C1502E' }}><ExternalLink size={14} /></a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* I — Threshold */}
      <div style={{ padding: '16px 20px', borderRadius: '12px', border: '0.5px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <Bell size={16} color="#C1502E" />
          <span style={{ fontWeight: 500, fontSize: '14px' }}>Price alert threshold</span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 12px' }}>We'll notify you when the price drops below your target.</p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="number"
            value={thresholdInput}
            onChange={e => setThresholdInput(e.target.value)}
            placeholder="e.g. 280"
            style={{ width: '140px', height: '34px', borderRadius: '8px', border: '0.5px solid var(--border)', padding: '0 10px', fontSize: '13px', background: 'var(--surface)' }}
          />
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>MAD</span>
          <button className="btn btn-primary btn-sm" onClick={saveThreshold}>Save target</button>
          {thresholdSaved && <span style={{ fontSize: '12px', color: '#2e7d32', fontWeight: 500 }}>Target saved ✓</span>}
          {thresholdError && <span style={{ fontSize: '12px', color: '#c62828' }}>{thresholdError}</span>}
        </div>
        {threshold && <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', marginBottom: 0 }}>Current target: {threshold.threshold_mad} MAD</p>}
      </div>
    </div>
  )
}
