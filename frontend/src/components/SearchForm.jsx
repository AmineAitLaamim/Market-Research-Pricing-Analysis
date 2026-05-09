import { useState, useRef, useEffect } from 'react'
import { PLATFORMS } from '../utils/constants'
import { ChevronDown, Search } from 'lucide-react'

export default function SearchForm({ onSubmit, loading = false, initialQuery = '' }) {
  const [query, setQuery]       = useState(initialQuery)
  const [selected, setSelected] = useState(PLATFORMS.map((p) => p.id))
  const [qError, setQError]     = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function togglePlatform(id) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    )
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!query.trim()) { setQError('Please enter a search query'); return }
    if (!selected.length) { setQError('Select at least one platform'); return }
    setQError('')
    setDropdownOpen(false)
    onSubmit(query.trim(), selected)
  }

  const selectedNames = selected.length === PLATFORMS.length 
    ? 'All websites' 
    : selected.length === 0 
      ? 'Select websites' 
      : `${selected.length} selected`

  return (
    <div style={{ position: 'relative' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '12px', 
          alignItems: 'stretch',
          background: '#fff',
          padding: '8px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          
          {/* Query input */}
          <div style={{ flex: '1 1 250px', position: 'relative' }}>
            <Search size={20} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              id="search-query"
              type="text"
              className={`form-input ${qError ? 'error' : ''}`}
              placeholder="What are you looking for?"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setQError('') }}
              style={{ 
                width: '100%', 
                height: '100%', 
                border: 'none', 
                background: 'transparent',
                padding: '12px 16px 12px 48px',
                fontSize: '16px',
                boxShadow: 'none'
              }}
            />
          </div>

          <div style={{ width: '1px', background: 'var(--border-color)', margin: '8px 0' }} className="hide-mobile" />

          {/* Platform Dropdown */}
          <div ref={dropdownRef} style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <button
              type="button"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'transparent',
                border: 'none',
                padding: '12px 16px',
                cursor: 'pointer',
                fontSize: '15px',
                color: 'var(--text-primary)',
                fontWeight: 500,
                whiteSpace: 'nowrap'
              }}
            >
              {selectedNames}
              <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
            </button>

            {dropdownOpen && (
              <div style={{
                position: 'absolute',
                top: 'calc(100% + 12px)',
                right: 0,
                background: '#fff',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '8px',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 100,
                minWidth: '200px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px'
              }}>
                <div style={{ padding: '8px 12px', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Websites to scrape
                </div>
                {PLATFORMS.map((p) => (
                  <label key={p.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 12px',
                    cursor: 'pointer',
                    borderRadius: '6px',
                    background: selected.includes(p.id) ? 'var(--brand-light)' : 'transparent',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => { if (!selected.includes(p.id)) e.currentTarget.style.background = 'var(--bg-base)' }}
                  onMouseLeave={(e) => { if (!selected.includes(p.id)) e.currentTarget.style.background = 'transparent' }}
                  >
                    <input
                      type="checkbox"
                      checked={selected.includes(p.id)}
                      onChange={() => togglePlatform(p.id)}
                      style={{ accentColor: 'var(--brand)', width: '16px', height: '16px' }}
                    />
                    <span style={{ fontSize: '16px' }}>{p.icon}</span>
                    <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>{p.name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Submit */}
          <button
            id="search-submit"
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ padding: '12px 24px', whiteSpace: 'nowrap' }}
          >
            {loading ? <><span className="spinner" /> Scraping…</> : 'Start Scraping'}
          </button>
        </div>
      </form>
      
      {qError && (
        <div style={{ color: 'var(--danger)', fontSize: '13px', marginTop: '8px', paddingLeft: '16px' }}>
          ⚠ {qError}
        </div>
      )}
    </div>
  )
}
