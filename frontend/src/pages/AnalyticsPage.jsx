import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { analyticsApi } from '../api/analytics'
import { useToast } from '../context/ToastContext'
import ProductDetail from '../components/analytics/ProductDetail'
import { Search, Clock, TrendingDown, Package } from 'lucide-react'

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export default function AnalyticsPage() {
  const location = useLocation()
  const [selectedProduct, setSelectedProduct] = useState(location.state?.product || null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [topDrops, setTopDrops] = useState([])
  const [recentProducts, setRecentProducts] = useState([])
  const [searching, setSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef(null)

  // Load recent products and top drops on mount
  useEffect(() => {
    Promise.all([
      analyticsApi.getRecentProducts().catch(() => ({ data: [] })),
      analyticsApi.getTopDrops().catch(() => ({ data: [] }))
    ]).then(([recentRes, dropsRes]) => {
      setRecentProducts(recentRes.data)
      setTopDrops(dropsRes.data)
    })
  }, [])

  // Debounced search
  useEffect(() => {
    if (query.length < 2) { setResults([]); setShowDropdown(false); return }
    setSearching(true)
    const timer = setTimeout(() => {
      analyticsApi.searchProducts(query)
        .then(res => { setResults(res.data); setShowDropdown(true) })
        .catch(() => {})
        .finally(() => setSearching(false))
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function selectProduct(product) {
    setSelectedProduct(product)
    setShowDropdown(false)
    setQuery('')
  }

  if (selectedProduct) {
    return <ProductDetail product={selectedProduct} onBack={() => setSelectedProduct(null)} onSelectProduct={setSelectedProduct} />
  }

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 120px)' }}>
      <div style={{ width: '100%', maxWidth: '800px', textAlign: 'center' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <Package size={32} style={{ color: '#C1502E', marginBottom: '12px' }} />
          <h1 style={{ fontSize: '22px', fontWeight: 500, margin: '0 0 6px' }}>Product Intelligence</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', margin: 0 }}>Search any product you've scraped to see price trends, comparisons, and buy recommendations</p>
        </div>

        {/* Search input */}
        <div ref={dropdownRef} style={{ position: 'relative', marginBottom: '40px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onFocus={() => results.length > 0 && setShowDropdown(true)}
              placeholder="Search a product you've scraped before…"
              style={{
                width: '100%', height: '46px', paddingLeft: '40px', paddingRight: '16px',
                borderRadius: '12px', border: '0.5px solid var(--border)',
                fontSize: '14px', background: 'var(--surface)', color: 'var(--text-primary)',
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Dropdown */}
          {showDropdown && (
            <div style={{
              position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0,
              background: '#fff', border: '0.5px solid var(--border)', borderRadius: '12px',
              zIndex: 100, overflow: 'hidden', maxHeight: '360px', overflowY: 'auto',
            }}>
              {results.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                  No results. Try scraping this keyword first.
                </div>
              ) : results.map((p, i) => (
                <div
                  key={`${p.normalized_title}-${p.platform}-${i}`}
                  onClick={() => selectProduct(p)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '12px 16px', cursor: 'pointer', borderBottom: '0.5px solid var(--border)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-muted)'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '3px' }}>
                      <span style={{ fontSize: '11px', background: 'var(--bg-muted)', padding: '1px 6px', borderRadius: '4px', textTransform: 'capitalize' }}>{p.platform}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{p.scrape_count} scrapes</span>
                    </div>
                  </div>
                  <span style={{ fontWeight: 500, fontSize: '14px', color: '#C1502E', flexShrink: 0, marginLeft: '12px' }}>
                    {p.latest_price_mad.toFixed(0)} MAD
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Drops */}
        <div style={{ textAlign: 'left', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '14px' }}>
            <TrendingDown size={14} style={{ color: '#2e7d32' }} />
            <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-secondary)' }}>Biggest recent price drops</span>
          </div>
          {topDrops.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {topDrops.map((p, i) => (
                <div
                  key={`drop-${i}`}
                  onClick={() => selectProduct(p)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '16px',
                    padding: '16px', borderRadius: '12px', border: '0.5px solid var(--border)',
                    background: 'var(--surface)', cursor: 'pointer', transition: 'border-color 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#C1502E'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  {/* Product Image */}
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.title} style={{ width: '64px', height: '64px', objectFit: 'contain', borderRadius: '8px', background: '#fff', border: '0.5px solid var(--border)' }} />
                  ) : (
                    <div style={{ width: '64px', height: '64px', borderRadius: '8px', background: 'var(--bg-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Package size={24} color="var(--text-muted)" />
                    </div>
                  )}

                  {/* Title and Platform */}
                  <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '11px', background: 'var(--bg-muted)', padding: '2px 6px', borderRadius: '4px', textTransform: 'capitalize' }}>{p.platform}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{timeAgo(p.last_scraped)}</span>
                    </div>
                  </div>

                  {/* Prices & Drop */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0, marginLeft: '12px' }}>
                    <span style={{ fontSize: '12px', background: '#e8f5e9', color: '#2e7d32', padding: '2px 6px', borderRadius: '4px', fontWeight: 500 }}>
                      -{p.drop_percent.toFixed(0)}%
                    </span>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                      <span style={{ fontSize: '16px', fontWeight: 500, color: '#C1502E' }}>{p.latest_price_mad.toFixed(0)}</span>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>{p.old_price_mad.toFixed(0)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '24px', textAlign: 'center', background: 'var(--bg-muted)', borderRadius: '12px', border: '1px dashed var(--border)', color: 'var(--text-muted)', fontSize: '13px' }}>
              No price drops detected yet. Scrape keywords multiple times over a few days to catch drops!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
