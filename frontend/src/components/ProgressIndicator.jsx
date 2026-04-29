/**
 * ProgressIndicator receives live WebSocket events and renders
 * an animated step list: scraping → mining → done.
 *
 * Expected event shape from T27:
 *  { type: 'scraping', platform: 'amazon', count: 12 }
 *  { type: 'mining' }
 *  { type: 'done' }
 */
export default function ProgressIndicator({ events = [], status = 'pending' }) {
  // Derive state from events
  const scrapingEvents = events.filter((e) => e.type === 'scraping')
  
  // Get latest count per platform
  const latestScraped = Object.values(
    scrapingEvents.reduce((acc, e) => {
      if (e.platform) acc[e.platform] = e;
      return acc;
    }, {})
  );
  const isMining = events.some((e) => e.type === 'mining')
  const isDone   = status === 'completed' || status === 'failed' || events.some((e) => e.type === 'done')

  function stepState(condition, after) {
    if (after) return 'done'
    if (condition) return 'active'
    return 'pending'
  }

  const scrapingState = stepState(status === 'processing' && !isMining, isMining)
  const miningState   = stepState(isMining && !isDone, isDone)
  const doneState     = isDone ? 'done' : 'pending'

  const steps = [
    {
      key: 'scraping',
      state: scrapingState,
      icon: scrapingState === 'done' ? '✓' : scrapingState === 'active' ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : '🕷️',
      label: 'Scraping listings',
      detail: latestScraped.length
        ? latestScraped.map((e) => `${e.platform}: ${e.count ?? 0} items`).join(' · ')
        : status === 'pending' ? 'Waiting to start…' : 'Collecting data…',
    },
    {
      key: 'mining',
      state: miningState,
      icon: miningState === 'done' ? '✓' : miningState === 'active' ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : '🧠',
      label: 'Running analysis',
      detail: miningState === 'active' ? 'Clustering, anomaly detection, PCA…' : miningState === 'done' ? 'Analysis complete' : 'Waiting…',
    },
    {
      key: 'done',
      state: doneState,
      icon: status === 'failed' ? '✕' : doneState === 'done' ? '🏆' : '⏳',
      label: status === 'failed' ? 'Search failed' : 'Results ready',
      detail: status === 'failed' ? 'An error occurred during processing' : doneState === 'done' ? 'Scroll down to explore results' : 'Almost there…',
    },
  ]

  return (
    <div className="progress-steps animate-fade-in">
      {steps.map((s) => (
        <div key={s.key} className={`progress-step ${s.state}`}>
          <div className={`progress-step-icon`}>
            {typeof s.icon === 'string' ? s.icon : s.icon}
          </div>
          <div>
            <div className="progress-step-label">{s.label}</div>
            <div className="progress-step-detail">{s.detail}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
