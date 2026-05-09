/**
 * ProgressIndicator — shows only scraping results per platform.
 */
export default function ProgressIndicator({ events = [], status = 'pending' }) {
  const scrapingEvents = events.filter((e) => e.type === 'scraping')

  // Keep latest count per platform
  const latestScraped = Object.values(
    scrapingEvents.reduce((acc, e) => {
      if (e.platform) acc[e.platform] = e;
      return acc;
    }, {})
  )

  const isActive = status === 'processing'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {latestScraped.length === 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isActive && <span className="spinner" style={{ width: 10, height: 10, borderWidth: 1.5 }} />}
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {isActive ? 'Scraping…' : '—'}
          </span>
        </div>
      ) : (
        latestScraped.map((e) => (
          <div key={e.platform} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
              {e.platform}
            </span>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-primary)', background: 'var(--bg-muted)', borderRadius: '4px', padding: '1px 6px' }}>
              {e.count ?? 0} items
            </span>
          </div>
        ))
      )}
    </div>
  )
}

