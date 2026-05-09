import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { searchApi } from '../api/search'
import { useToast } from '../context/ToastContext'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { ArrowDown, ArrowUp, Minus, AlertCircle } from 'lucide-react'

export default function ComparisonPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { showToast } = useToast()
  
  const aId = searchParams.get('a')
  const bId = searchParams.get('b')

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!aId || !bId) {
      showToast('Missing search IDs for comparison', 'error')
      navigate('/history')
      return
    }

    let mounted = true
    setLoading(true)

    searchApi.getComparison(aId, bId)
      .then(res => {
        if (mounted) {
          setData(res.data)
          setLoading(false)
        }
      })
      .catch(err => {
        console.error(err)
        showToast(err.response?.data?.detail || 'Failed to load comparison', 'error')
        if (mounted) {
          setLoading(false)
          navigate('/history')
        }
      })

    return () => { mounted = false }
  }, [aId, bId, navigate, showToast])

  if (loading) {
    return (
      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div className="skeleton" style={{ height: '80px', borderRadius: '12px' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: '100px', borderRadius: '12px' }} />)}
        </div>
        <div className="skeleton" style={{ height: '300px', borderRadius: '12px' }} />
        <div className="skeleton" style={{ height: '400px', borderRadius: '12px' }} />
      </div>
    )
  }

  if (!data) return null

  const { query, date_a, date_b, summary, matched, new_items, gone_items, prices_a, prices_b } = data

  // Process histogram data
  const minPrice = Math.min(...prices_a, ...prices_b, 0)
  const maxPrice = Math.max(...prices_a, ...prices_b, 1)
  const binCount = 10
  const binSize = (maxPrice - minPrice) / binCount
  
  const bins = Array.from({ length: binCount }, (_, i) => ({
    name: `${Math.round(minPrice + i * binSize)}-${Math.round(minPrice + (i + 1) * binSize)}`,
    min: minPrice + i * binSize,
    max: minPrice + (i + 1) * binSize,
    DateA: 0,
    DateB: 0,
  }))

  prices_a.forEach(p => {
    const bin = bins.find(b => p >= b.min && p <= b.max) || bins[bins.length - 1]
    bin.DateA++
  })
  
  prices_b.forEach(p => {
    const bin = bins.find(b => p >= b.min && p <= b.max) || bins[bins.length - 1]
    bin.DateB++
  })

  // Format diff for metric card
  const priceDiff = summary.avg_price_b - summary.avg_price_a
  const priceDiffPct = summary.avg_price_a ? (priceDiff / summary.avg_price_a) * 100 : 0
  const isPriceDrop = priceDiff < 0
  const isPriceUp = priceDiff > 0

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
          <button className="btn btn-secondary btn-sm" style={{ marginBottom: '16px' }} onClick={() => navigate('/history')}>
            ← Back to History
          </button>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span>{query}</span>
            <span style={{ fontSize: '16px', color: 'var(--text-muted)', fontWeight: 400 }}>
              {date_a} vs {date_b}
            </span>
          </h1>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        
        {/* Avg Price */}
        <div className="card" style={{ padding: '20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Avg Price
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {summary.avg_price_b.toFixed(2)} MAD
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '8px', fontSize: '13px', fontWeight: 600, color: isPriceDrop ? 'var(--color-success)' : isPriceUp ? 'var(--color-danger)' : 'var(--text-muted)' }}>
            {isPriceDrop ? <ArrowDown size={14} /> : isPriceUp ? <ArrowUp size={14} /> : <Minus size={14} />}
            {Math.abs(priceDiff).toFixed(2)} MAD ({Math.abs(priceDiffPct).toFixed(1)}%)
          </div>
        </div>

        {/* Total Items */}
        <div className="card" style={{ padding: '20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Total Items
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {summary.total_items_b}
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            was {summary.total_items_a} on {date_a}
          </div>
        </div>

        {/* Cheapest Item */}
        <div className="card" style={{ padding: '20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Cheapest Found
          </div>
          <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
            {summary.cheapest_b !== null ? summary.cheapest_b.toFixed(2) : '—'} MAD
          </div>
          <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            was {summary.cheapest_a !== null ? summary.cheapest_a.toFixed(2) : '—'} MAD
          </div>
        </div>

        {/* Market Churn */}
        <div className="card" style={{ padding: '20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Market Changes
          </div>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-success)' }}>+{summary.new_items_count}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>New Listings</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-danger)' }}>-{summary.gone_items_count}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Gone Listings</div>
            </div>
          </div>
        </div>

      </div>

      {/* Distribution Chart */}
      <div className="card" style={{ padding: '24px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
        <h3 style={{ margin: '0 0 24px 0', fontSize: '16px' }}>Price Distribution Comparison</h3>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bins} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} tickLine={false} axisLine={false} dy={10} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'var(--bg-muted)' }}
                contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Bar dataKey="DateA" name={date_a} fill="var(--text-muted)" opacity={0.6} radius={[4, 4, 0, 0]} />
              <Bar dataKey="DateB" name={date_b} fill="var(--brand)" opacity={0.9} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Product Table */}
      <div className="card" style={{ background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)', overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h3 style={{ margin: 0, fontSize: '16px' }}>Product Level Comparison</h3>
          <span className="badge badge-neutral">{matched.length + new_items.length + gone_items.length} items total</span>
        </div>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: 'var(--bg-muted)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Product Title</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Platform</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>{date_a} (MAD)</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>{date_b} (MAD)</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Difference</th>
              </tr>
            </thead>
            <tbody>
              {/* Matched Items */}
              {matched.map((m, i) => (
                <tr key={`match-${i}`} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '16px 24px', maxWidth: '300px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      <a href={m.url_b || m.url_a} target="_blank" rel="noreferrer" style={{ color: 'var(--text-primary)', textDecoration: 'none' }} onMouseEnter={e => e.target.style.textDecoration='underline'} onMouseLeave={e => e.target.style.textDecoration='none'}>
                        {m.title}
                      </a>
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textTransform: 'capitalize', color: 'var(--text-muted)' }}>{m.platform}</td>
                  <td style={{ padding: '16px 24px' }}>{m.price_a.toFixed(2)}</td>
                  <td style={{ padding: '16px 24px', fontWeight: 500 }}>{m.price_b.toFixed(2)}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <span style={{ 
                      color: m.diff < 0 ? 'var(--color-success)' : m.diff > 0 ? 'var(--color-danger)' : 'var(--text-muted)',
                      fontWeight: m.diff !== 0 ? 600 : 400
                    }}>
                      {m.diff > 0 ? '+' : ''}{m.diff.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}

              {/* New Items */}
              {new_items.map((m, i) => (
                <tr key={`new-${i}`} style={{ borderBottom: '1px solid var(--border)', background: 'rgba(46, 125, 82, 0.03)' }}>
                  <td style={{ padding: '16px 24px', maxWidth: '300px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      <a href={m.url_b} target="_blank" rel="noreferrer" style={{ color: 'var(--text-primary)', textDecoration: 'none' }} onMouseEnter={e => e.target.style.textDecoration='underline'} onMouseLeave={e => e.target.style.textDecoration='none'}>
                        {m.title}
                      </a>
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textTransform: 'capitalize', color: 'var(--text-muted)' }}>{m.platform}</td>
                  <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>—</td>
                  <td style={{ padding: '16px 24px', fontWeight: 500 }}>{m.price_b.toFixed(2)}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <span className="badge badge-success">New</span>
                  </td>
                </tr>
              ))}

              {/* Gone Items */}
              {gone_items.map((m, i) => (
                <tr key={`gone-${i}`} style={{ borderBottom: '1px solid var(--border)', background: 'rgba(220, 53, 69, 0.03)' }}>
                  <td style={{ padding: '16px 24px', maxWidth: '300px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', opacity: 0.6 }}>
                      {m.title}
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', textTransform: 'capitalize', color: 'var(--text-muted)' }}>{m.platform}</td>
                  <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>{m.price_a.toFixed(2)}</td>
                  <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>—</td>
                  <td style={{ padding: '16px 24px' }}>
                    <span className="badge badge-danger">Gone</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
