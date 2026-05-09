import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { searchApi } from '../api/search'
import { useToast } from '../context/ToastContext'
import SearchForm from '../components/SearchForm'
import { connectWebSocket } from '../utils/websocket'
import ProgressIndicator from '../components/ProgressIndicator'
import AnalyticsDashboard from '../components/AnalyticsDashboard'

function SearchProgressCard({ id, onRemove }) {
  const navigate = useNavigate()
  const [search, setSearch] = useState(() => {
    try {
      const saved = localStorage.getItem(`search_meta_${id}`)
      return saved ? JSON.parse(saved) : { id, status: 'pending' }
    } catch { return { id, status: 'pending' } }
  })
  const [events, setEvents] = useState(() => {
    try {
      const saved = localStorage.getItem(`search_events_${id}`)
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const disconnectRef = useRef(null)

  function persistSearch(data) {
    setSearch(data)
    localStorage.setItem(`search_meta_${id}`, JSON.stringify(data))
  }

  function addEvent(msg) {
    setEvents(prev => {
      const next = [...prev, msg]
      localStorage.setItem(`search_events_${id}`, JSON.stringify(next))
      return next
    })
  }

  useEffect(() => {
    searchApi.getSearchStatus(id).then(res => persistSearch(res.data)).catch(console.error)

    disconnectRef.current = connectWebSocket(id,
      (msg) => {
        addEvent(msg)
        if (msg.type === 'done' || msg.status === 'completed') {
          searchApi.getSearchStatus(id).then(res => persistSearch(res.data)).catch(console.error)
        }
      },
      () => { }
    )
    return () => disconnectRef.current?.()
  }, [id])


  return (
    <div className="card" style={{ padding: '24px', background: 'var(--surface-sunken)', borderRadius: '16px', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
          {search.query ? `Searching: "${search.query}"` : 'Initializing search...'}
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`badge badge-${search.status === 'completed' ? 'success' : search.status === 'failed' ? 'danger' : 'info'}`}>
            {search.status}
          </span>
          <button
            onClick={onRemove}
            title="Dismiss"
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1, padding: '2px 4px', borderRadius: '4px', transition: 'color 0.15s, background 0.15s' }}
            onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.background = 'var(--bg-muted)' }}
            onMouseLeave={e => { e.target.style.color = 'var(--text-muted)'; e.target.style.background = 'none' }}
          >✕</button>
        </div>
      </div>

      <ProgressIndicator events={events} status={search.status} />

      {search.status === 'completed' && (
        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={() => navigate(`/results/${id}`)}>
            View Full Results
          </button>
        </div>
      )}

      {search.status === 'failed' && (
        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={() => navigate(`/results/${id}`)}>
            View Error Details
          </button>
        </div>
      )}
    </div>
  )
}

export default function SearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const initialQuery = searchParams.get('q') || ''
  const [activeSearches, setActiveSearches] = useState(() => {
    try {
      const saved = localStorage.getItem('activeSearches')
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  function updateSearches(updater) {
    setActiveSearches(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      localStorage.setItem('activeSearches', JSON.stringify(next))
      return next
    })
  }

  async function handleSearch(query, platforms) {
    setLoading(true)
    try {
      const res = await searchApi.createSearch(query, platforms)
      updateSearches(prev => [res.data.id, ...prev])
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start search. Please try again.'
      showToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', paddingTop: '24px', paddingRight: '340px' }}>
      <div style={{ maxWidth: '800px', width: '100%', margin: '0 auto' }}>
        <div style={{ marginBottom: '40px' }}>
          <SearchForm onSubmit={handleSearch} loading={loading} initialQuery={initialQuery} />
        </div>
        
        <AnalyticsDashboard />
      </div>

      <div style={{
          position: 'fixed',
          right: 0,
          top: '60px',
          bottom: 0,
          width: '320px',
          borderLeft: '1px solid var(--border)',
          background: 'var(--bg-surface)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 50,
          overflowY: 'auto',
          padding: '16px',
          gap: '12px',
        }}>
          {activeSearches.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '10px', color: 'var(--text-muted)' }}>
              <span style={{ fontSize: '28px', opacity: 0.4 }}>🔍</span>
              <span style={{ fontSize: '12px', textAlign: 'center' }}>No active searches</span>
            </div>
          ) : (
            activeSearches.map(id => (
              <SearchProgressCard key={id} id={id} onRemove={() => {
                localStorage.removeItem(`search_meta_${id}`)
                localStorage.removeItem(`search_events_${id}`)
                updateSearches(prev => prev.filter(s => s !== id))
              }} />
            ))
          )}
        </div>
    </div>
  )
}
