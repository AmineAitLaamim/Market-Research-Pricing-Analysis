import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyticsApi } from '../api/analytics'
import { Database, Search, Package } from 'lucide-react'
import ProductDetail from '../components/analytics/ProductDetail'
import { PLATFORMS } from '../utils/constants'

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

export default function DatabasePage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState(null)
  
  // Load initial products
  useEffect(() => {
    loadProducts('')
  }, [])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadProducts(query)
    }, 400)
    return () => clearTimeout(timer)
  }, [query])

  function loadProducts(searchQuery) {
    setSearching(true)
    analyticsApi.searchProducts(searchQuery, 100) // Get up to 100 results for the grid
      .then(res => setResults(res.data))
      .catch(() => {})
      .finally(() => setSearching(false))
  }

  if (selectedProduct) {
    return <ProductDetail product={selectedProduct} onBack={() => setSelectedProduct(null)} onSelectProduct={setSelectedProduct} />
  }

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '40px', paddingBottom: '60px' }}>
      <div style={{ width: '100%', maxWidth: '1000px' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px', textAlign: 'center' }}>
          <Database size={32} style={{ color: '#10b981', marginBottom: '12px' }} />
          <h1 style={{ fontSize: '24px', fontWeight: 600, margin: '0 0 8px' }}>Local Database</h1>
          <p style={{ fontSize: '15px', color: 'var(--text-muted)', margin: 0 }}>
            Search through products you have already scraped without making new online requests.
          </p>
        </div>

        {/* Search Input */}
        <div style={{ display: 'flex', gap: '12px', maxWidth: '600px', margin: '0 auto 40px auto' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && loadProducts(query)}
              placeholder="Search your scraped products..."
              style={{
                width: '100%', height: '52px', paddingLeft: '46px', paddingRight: '16px',
                borderRadius: '16px', border: '1px solid var(--border)',
                fontSize: '15px', background: 'var(--surface)', color: 'var(--text-primary)',
                outline: 'none', boxSizing: 'border-box',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)'
              }}
            />
            {searching && (
              <div style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)' }}>
                <span className="spinner" style={{ borderColor: 'var(--text-muted)', borderTopColor: 'transparent', width: '16px', height: '16px' }} />
              </div>
            )}
          </div>
          <button 
            className="btn btn-primary" 
            onClick={() => loadProducts(query)}
            style={{ height: '52px', padding: '0 24px', borderRadius: '16px', fontWeight: 600 }}
          >
            Search
          </button>
        </div>

        {/* Results Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '16px'
        }}>
          {results.length === 0 && !searching ? (
            <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', background: 'var(--bg-muted)', borderRadius: '12px', border: '1px dashed var(--border)', color: 'var(--text-muted)' }}>
              No products found in your database.
            </div>
          ) : (
            results.map((p, i) => (
              <div
                key={`${p.normalized_title}-${p.platform}-${i}`}
                onClick={() => setSelectedProduct(p)}
                style={{
                  display: 'flex', flexDirection: 'column',
                  padding: '16px', borderRadius: '12px', border: '1px solid var(--border)',
                  background: 'var(--surface)', cursor: 'pointer', transition: 'all 0.15s ease',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = '#10b981'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.05)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                  e.currentTarget.style.transform = 'none'
                  e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)'
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '14px', lineHeight: '1.4', marginBottom: '8px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {p.title}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <span style={{ fontSize: '11px', background: 'var(--bg-muted)', padding: '2px 8px', borderRadius: '6px', textTransform: 'capitalize', fontWeight: 500, color: 'var(--text-secondary)' }}>
                      {PLATFORMS.find(pl => pl.id === p.platform)?.icon || '🌐'} {p.platform}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {p.scrape_count} {p.scrape_count === 1 ? 'scrape' : 'scrapes'}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', borderTop: '1px solid var(--border)', paddingTop: '12px', marginTop: 'auto' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    Last seen {timeAgo(p.last_scraped)}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '16px', color: '#10b981' }}>
                    {p.latest_price_mad.toFixed(0)} MAD
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
