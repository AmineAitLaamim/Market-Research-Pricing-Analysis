import { useState, useEffect, useCallback, useRef } from 'react'
import { alertsApi } from '../api/alerts'

export function useAlerts() {
  const [alerts, setAlerts]           = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading]         = useState(true)
  const wsRef                         = useRef(null)

  const fetch = useCallback(async () => {
    try {
      const res = await alertsApi.getAlerts()
      setAlerts(res.data.results ?? [])
      setUnreadCount(res.data.unread_count ?? 0)
    } catch {
      // Silently ignore — alerts are non-critical
    } finally {
      setLoading(false)
    }
  }, [])

  // Connect to the per-user alerts WebSocket
  useEffect(() => {
    fetch()

    const url = `ws://${window.location.host}/ws/alerts/`
    let ws
    let stopped = false
    let retries = 0
    const MAX_RETRIES = 5

    function connect() {
      if (stopped) return
      ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => { retries = 0 }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'new_alerts') {
            // Refresh the full list so the dropdown shows the real alerts
            fetch()
          }
        } catch { /* ignore malformed */ }
      }

      ws.onclose = () => {
        if (stopped) return
        if (retries < MAX_RETRIES) {
          const delay = 1500 * Math.pow(2, retries)
          retries++
          setTimeout(connect, delay)
        }
      }
    }

    connect()

    return () => {
      stopped = true
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [fetch])

  const markRead = useCallback(async (id) => {
    try {
      await alertsApi.markAlertRead(id)
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch { /* noop */ }
  }, [])

  const markAllRead = useCallback(async () => {
    try {
      await alertsApi.markAllRead()
      setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))
      setUnreadCount(0)
    } catch { /* noop */ }
  }, [])

  return { alerts, unreadCount, markRead, markAllRead, loading, refresh: fetch }
}
