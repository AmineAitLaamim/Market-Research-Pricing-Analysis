import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, TrendingDown } from 'lucide-react'
import { useAlerts } from '../hooks/useAlerts'

export default function AlertBell() {
  const { alerts, unreadCount, markRead, markAllRead } = useAlerts()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const navigate = useNavigate()

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function formatDrop(alert) {
    const pct = parseFloat(alert.drop_percent).toFixed(1)
    const amt = parseFloat(alert.drop_amount).toFixed(0)
    return `-${amt} MAD · -${pct}%`
  }

  function timeAgo(iso) {
    const diff = Date.now() - new Date(iso).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      {/* Bell button */}
      <button
        id="alert-bell-btn"
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          position: 'relative',
          padding: '6px',
          borderRadius: '8px',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          transition: 'color 0.15s',
        }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-secondary)'}
        title="Price drop alerts"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '1px',
            right: '1px',
            background: '#C1502E',
            color: '#fff',
            fontSize: '10px',
            fontWeight: 700,
            borderRadius: '99px',
            minWidth: '16px',
            height: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 3px',
            lineHeight: 1,
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 10px)',
          right: 0,
          width: '340px',
          background: '#fff',
          border: '0.5px solid #e0ddd6',
          borderRadius: '12px',
          zIndex: 9999,
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 16px 10px',
            borderBottom: '0.5px solid #e0ddd6',
          }}>
            <span style={{ fontWeight: 700, fontSize: '14px', color: '#111' }}>
              Price drops
            </span>
            {unreadCount > 0 && (
              <button
                onClick={markAllRead}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#C1502E',
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: 0,
                }}
              >
                Mark all as read
              </button>
            )}
          </div>

          {/* Alert list */}
          <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
            {alerts.length === 0 ? (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '36px 16px',
                color: '#888',
                gap: '10px',
              }}>
                <Bell size={28} strokeWidth={1.5} />
                <span style={{ fontSize: '13px', textAlign: 'center' }}>
                  No price drops yet.<br />Run a search to start tracking.
                </span>
              </div>
            ) : (
              alerts.map(alert => (
                <div
                  key={alert.id}
                  id={`alert-${alert.id}`}
                  onClick={() => markRead(alert.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    background: alert.is_read ? '#fff' : '#F5F4F0',
                    borderBottom: '0.5px solid #e0ddd6',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#f0ede8'}
                  onMouseLeave={e => e.currentTarget.style.background = alert.is_read ? '#fff' : '#F5F4F0'}
                >
                  {/* Icon */}
                  <div style={{
                    flexShrink: 0,
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: '#EAF3DE',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <TrendingDown size={16} color="#3B6D11" />
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '13px',
                      fontWeight: 500,
                      color: '#111',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      marginBottom: '3px',
                    }}>
                      {alert.product_title}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '12px', color: '#888', textDecoration: 'line-through' }}>
                        {parseFloat(alert.old_price).toFixed(0)} MAD
                      </span>
                      <span style={{ fontSize: '13px', fontWeight: 700, color: '#111' }}>
                        {parseFloat(alert.new_price).toFixed(0)} MAD
                      </span>
                      <span style={{
                        background: '#EAF3DE',
                        color: '#27500A',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        padding: '1px 5px',
                      }}>
                        {formatDrop(alert)}
                      </span>
                    </div>

                    <div style={{ fontSize: '11px', color: '#999' }}>
                      {alert.platform} · keyword: {alert.search_query} · {timeAgo(alert.created_at)}
                    </div>
                  </div>

                  {/* Right side */}
                  <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                    <a
                      href={alert.product_url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={e => e.stopPropagation()}
                      style={{
                        fontSize: '11px',
                        color: '#C1502E',
                        fontWeight: 600,
                        textDecoration: 'none',
                        padding: '2px 6px',
                        border: '0.5px solid #C1502E',
                        borderRadius: '4px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      View
                    </a>
                    {!alert.is_read && (
                      <span style={{
                        width: '7px',
                        height: '7px',
                        borderRadius: '50%',
                        background: '#C1502E',
                        display: 'block',
                      }} />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div style={{
            padding: '10px 16px',
            borderTop: '0.5px solid #e0ddd6',
            textAlign: 'center',
          }}>
            <button
              onClick={() => { setOpen(false); navigate('/alerts') }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#C1502E',
                fontSize: '12px',
                fontWeight: 600,
                padding: 0,
              }}
            >
              View all alerts →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
