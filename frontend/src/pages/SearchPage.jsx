import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchApi } from '../api/search'
import { useToast } from '../context/ToastContext'
import SearchForm from '../components/SearchForm'
import { connectWebSocket } from '../utils/websocket'
import ProgressIndicator from '../components/ProgressIndicator'

function SearchProgressCard({ id }) {
  const navigate = useNavigate()
  const [search, setSearch] = useState({ id, status: 'pending' })
  const [events, setEvents] = useState([])
  const disconnectRef = useRef(null)

  useEffect(() => {
    searchApi.getSearchStatus(id).then(res => setSearch(res.data)).catch(console.error)

    disconnectRef.current = connectWebSocket(id,
      (msg) => {
        setEvents((prev) => [...prev, msg])
        if (msg.type === 'done' || msg.status === 'completed') {
          searchApi.getSearchStatus(id).then(res => setSearch(res.data)).catch(console.error)
        }
      },
      () => {}
    )
    return () => disconnectRef.current?.()
  }, [id])

  return (
    <div className="card" style={{ padding: '24px', background: 'var(--surface-sunken)', borderRadius: '16px', border: '1px solid var(--border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
          {search.query ? `Searching: "${search.query}"` : 'Initializing search...'}
        </h3>
        <span className={`badge badge-${search.status === 'completed' ? 'success' : search.status === 'failed' ? 'danger' : 'info'}`}>
          {search.status}
        </span>
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
  const navigate    = useNavigate()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [activeSearches, setActiveSearches] = useState([])

  async function handleSearch(query, platforms) {
    setLoading(true)
    try {
      const res = await searchApi.createSearch(query, platforms)
      setActiveSearches(prev => [res.data.id, ...prev])
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start search. Please try again.'
      showToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', paddingTop: '24px' }}>
      <div style={{ maxWidth: '720px', width: '100%', margin: '0 auto', marginBottom: '40px' }}>
        <SearchForm onSubmit={handleSearch} loading={loading} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {activeSearches.map(id => (
          <SearchProgressCard key={id} id={id} />
        ))}
      </div>
    </div>
  )
}
