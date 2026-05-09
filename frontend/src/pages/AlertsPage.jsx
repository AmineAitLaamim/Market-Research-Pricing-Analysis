import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, TrendingDown, Search, Filter, CheckCheck, ExternalLink } from 'lucide-react'
import { useAlerts } from '../hooks/useAlerts'

const PLATFORMS = ['avito', 'jumia']

export default function AlertsPage() {
  const navigate = useNavigate()
  const { alerts, unreadCount, markRead, markAllRead, loading } = useAlerts()

  const [searchQuery, setSearchQuery]     = useState('')
  const [platformFilter, setPlatformFilter] = useState('all')
  const [statusFilter, setStatusFilter]   = useState('all') // all | unread | read
  const [sortBy, setSortBy]               = useState('newest') // newest | drop_amount | drop_percent

  const filtered = useMemo(() => {
    let result = [...alerts]

    // Filter by keyword
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        a => a.product_title.toLowerCase().includes(q) || a.search_query.toLowerCase().includes(q)
      )
    }

    // Filter by platform
    if (platformFilter !== 'all') {
      result = result.filter(a => a.platform === platformFilter)
    }

    // Filter by read status
    if (statusFilter === 'unread') result = result.filter(a => !a.is_read)
    if (statusFilter === 'read')   result = result.filter(a => a.is_read)

    // Sort
    if (sortBy === 'drop_amount')  result.sort((a, b) => parseFloat(b.drop_amount) - parseFloat(a.drop_amount))
    if (sortBy === 'drop_percent') result.sort((a, b) => parseFloat(b.drop_percent) - parseFloat(a.drop_percent))
    // 'newest' is default from server

    return result
  }, [alerts, searchQuery, platformFilter, statusFilter, sortBy])

  function formatDate(iso) {
    return new Date(iso).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bell size={22} />
            Price Alerts
            {unreadCount > 0 && (
              <span style={{
                background: '#C1502E', color: '#fff', fontSize: '12px',
                fontWeight: 700, borderRadius: '99px', padding: '2px 8px',
              }}>
                {unreadCount} unread
              </span>
            )}
          </h1>
          <p className="page-subtitle">All detected price drops across your searches</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {unreadCount > 0 && (
            <button className="btn btn-secondary btn-sm" onClick={markAllRead} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCheck size={14} /> Mark all read
            </button>
          )}
          <button className="btn btn-primary" onClick={() => navigate('/search')}>
            New Search
          </button>
        </div>
      </div>

      {/* Filters bar */}
      <div style={{
        display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center',
        marginBottom: '20px', padding: '14px 16px',
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: '12px',
      }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by product or keyword…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{
              width: '100%', paddingLeft: '32px', paddingRight: '12px',
              height: '34px', borderRadius: '8px', fontSize: '13px',
              border: '1px solid var(--border)', background: 'var(--bg)',
              color: 'var(--text-primary)', outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        {/* Platform */}
        <select
          value={platformFilter}
          onChange={e => setPlatformFilter(e.target.value)}
          style={{ height: '34px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-primary)', fontSize: '13px', padding: '0 10px' }}
        >
          <option value="all">All platforms</option>
          {PLATFORMS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
        </select>

        {/* Status */}
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ height: '34px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-primary)', fontSize: '13px', padding: '0 10px' }}
        >
          <option value="all">All statuses</option>
          <option value="unread">Unread</option>
          <option value="read">Read</option>
        </select>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          style={{ height: '34px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-primary)', fontSize: '13px', padding: '0 10px' }}
        >
          <option value="newest">Newest first</option>
          <option value="drop_amount">Largest drop (MAD)</option>
          <option value="drop_percent">Largest drop (%)</option>
        </select>

        <span style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
          <Filter size={12} style={{ marginRight: '4px' }} />
          {filtered.length} of {alerts.length}
        </span>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '88px', borderRadius: '12px' }} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card empty-state" style={{ padding: '64px 24px' }}>
          <span className="empty-state-icon">🔔</span>
          <p className="empty-state-title">
            {alerts.length === 0 ? 'No price drops yet' : 'No alerts match your filters'}
          </p>
          <p className="empty-state-desc">
            {alerts.length === 0
              ? 'Re-scrape a keyword you\'ve searched before to start tracking price changes.'
              : 'Try adjusting your search or filter criteria.'}
          </p>
          {alerts.length === 0 && (
            <button className="btn btn-primary" onClick={() => navigate('/search')} style={{ marginTop: '8px' }}>
              Start searching
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {filtered.map(alert => (
            <div
              key={alert.id}
              onClick={() => markRead(alert.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '14px',
                padding: '16px 20px',
                background: alert.is_read ? 'var(--surface)' : '#F5F4F0',
                border: `1px solid ${alert.is_read ? 'var(--border)' : '#ddd8cf'}`,
                borderRadius: '12px', cursor: 'pointer',
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateX(2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = ''}
            >
              {/* Icon */}
              <div style={{
                flexShrink: 0, width: '40px', height: '40px', borderRadius: '10px',
                background: '#EAF3DE', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <TrendingDown size={18} color="#3B6D11" />
              </div>

              {/* Main content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {alert.product_title}
                  </span>
                  {!alert.is_read && (
                    <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#C1502E', flexShrink: 0 }} />
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>
                    {parseFloat(alert.old_price).toFixed(0)} MAD
                  </span>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {parseFloat(alert.new_price).toFixed(0)} MAD
                  </span>
                  <span style={{ background: '#EAF3DE', color: '#27500A', borderRadius: '4px', fontSize: '12px', fontWeight: 600, padding: '2px 7px' }}>
                    -{parseFloat(alert.drop_amount).toFixed(0)} MAD · -{parseFloat(alert.drop_percent).toFixed(1)}%
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  <span style={{ textTransform: 'capitalize' }}>{alert.platform}</span>
                  {' · keyword: '}
                  <strong>{alert.search_query}</strong>
                  {' · '}
                  {formatDate(alert.created_at)}
                </div>
              </div>

              {/* View button */}
              <a
                href={alert.product_url}
                target="_blank"
                rel="noreferrer"
                onClick={e => e.stopPropagation()}
                style={{
                  flexShrink: 0, display: 'flex', alignItems: 'center', gap: '4px',
                  fontSize: '12px', color: '#C1502E', fontWeight: 600, textDecoration: 'none',
                  padding: '6px 10px', border: '1px solid #C1502E', borderRadius: '6px',
                  whiteSpace: 'nowrap', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = '#C1502E'; e.currentTarget.style.color = '#fff' }}
                onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#C1502E' }}
              >
                <ExternalLink size={12} /> View
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
