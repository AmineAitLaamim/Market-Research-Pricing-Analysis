import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, RefreshCw } from 'lucide-react'

import { searchApi }        from '../api/search'
import { connectWebSocket } from '../utils/websocket'
import { useToast }         from '../context/ToastContext'

import ProgressIndicator  from '../components/ProgressIndicator'
import StatsCards         from '../components/StatsCards'
import BestDealCard       from '../components/BestDealCard'
import PriceHistogram     from '../components/PriceHistogram'
import BoxPlot            from '../components/BoxPlot'
import ClusterScatter     from '../components/ClusterScatter'
import AssociationRules   from '../components/AssociationRules'
import FilterBar          from '../components/FilterBar'
import ResultsTable       from '../components/ResultsTable'
import ExportButton       from '../components/ExportButton'

const POLL_INTERVAL = 3000

export default function ResultsPage({ searchId, isEmbedded = false }) {
  const params        = useParams()
  const id            = searchId || params.id
  const navigate      = useNavigate()
  const { showToast } = useToast()

  const [search,        setSearch]        = useState(null)
  const [loadingSearch, setLoadingSearch] = useState(true)
  const [events,        setEvents]        = useState([])
  const [analysisData,  setAnalysisData]  = useState(null)
  const [allResults,    setAllResults]    = useState([])
  const [pcaPoints,     setPcaPoints]     = useState([])
  const [rules,         setRules]         = useState([])
  const [loadingData,   setLoadingData]   = useState(false)
  const [filters, setFilters] = useState({ platform: '', sort: 'default', anomaly_only: false, page: 1 })
  const [tableResults,  setTableResults]  = useState([])
  const [tableTotal,    setTableTotal]    = useState(0)
  const [loadingTable,  setLoadingTable]  = useState(false)

  const disconnectRef = useRef(null)
  const pollRef       = useRef(null)

  const fetchSearch = useCallback(async () => {
    try {
      const res = await searchApi.getSearchStatus(id)
      setSearch(res.data)
      return res.data
    } catch { showToast('Failed to load search', 'error'); return null }
    finally { setLoadingSearch(false) }
  }, [id])

  const fetchAnalysisData = useCallback(async () => {
    setLoadingData(true)
    try {
      const [resAll, resPca, resRules] = await Promise.allSettled([
        searchApi.getResults(id, { page: 1, page_size: 1000 }),
        searchApi.getPCA(id),
        searchApi.getRules(id),
      ])
      if (resAll.status === 'fulfilled') {
        const data = resAll.value.data
        setAllResults(data.results ?? data ?? [])
        setAnalysisData({ stats: data.meta?.stats, best_deal: data.meta?.best_deal })
      }
      if (resPca.status   === 'fulfilled') setPcaPoints(resPca.value.data ?? [])
      if (resRules.status === 'fulfilled') setRules(resRules.value.data ?? [])
    } finally { setLoadingData(false) }
  }, [id])

  const fetchTableResults = useCallback(async () => {
    setLoadingTable(true)
    try {
      const params = {
        page:       filters.page,
        platform:   filters.platform || undefined,
        is_anomaly: filters.anomaly_only ? true : undefined,
        ordering:   filters.sort === 'price_asc'  ? 'price'
                  : filters.sort === 'price_desc' ? '-price'
                  : filters.sort === 'deal_desc'  ? '-analysis__deal_score'
                  : undefined,
      }
      const res  = await searchApi.getResults(id, params)
      const data = res.data
      setTableResults(data.results ?? data ?? [])
      setTableTotal(data.count ?? (data.results?.length ?? 0))
    } catch { showToast('Failed to load results', 'error') }
    finally { setLoadingTable(false) }
  }, [id, filters])

  function startWebSocket() {
    if (disconnectRef.current) return
    disconnectRef.current = connectWebSocket(id,
      (msg) => {
        setEvents((prev) => [...prev, msg])
        if (msg.type === 'done' || msg.status === 'completed') {
          stopPolling(); fetchSearch().then(() => fetchAnalysisData())
        }
      },
      () => startPolling()
    )
  }
  function stopWebSocket() {
    disconnectRef.current?.(); disconnectRef.current = null
  }
  function startPolling() {
    if (pollRef.current) return
    pollRef.current = setInterval(async () => {
      const s = await fetchSearch()
      if (s?.status === 'completed' || s?.status === 'failed') {
        stopPolling(); fetchAnalysisData()
      }
    }, POLL_INTERVAL)
  }
  function stopPolling() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  useEffect(() => {
    fetchSearch().then((s) => {
      if (!s) return
      if (s.status === 'completed') fetchAnalysisData()
      else if (s.status !== 'failed') startWebSocket()
    })
    return () => { stopWebSocket(); stopPolling() }
  }, [id])

  useEffect(() => {
    if (search?.status === 'completed') fetchTableResults()
  }, [filters, search?.status])

  const isLive     = search?.status === 'pending' || search?.status === 'processing'
  const isComplete = search?.status === 'completed'
  const isFailed   = search?.status === 'failed'

  return (
    <div className={isEmbedded ? "" : "page-container"}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          {!isEmbedded && (
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/search')} style={{ marginBottom: '10px', color: 'var(--text-secondary)' }}>
              <ArrowLeft size={14} /> Back to search
            </button>
          )}
          <h1 className="page-title">
            {loadingSearch
              ? <span className="skeleton" style={{ width: '220px', display: 'inline-block', height: '26px' }} />
              : <>Results: "{search?.query}"</>
            }
          </h1>
          {search && (
            <p className="page-subtitle" style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
              <span>{search.platforms?.join(', ')}</span>
              <span>·</span>
              <span className={`badge badge-${
                search.status === 'completed' ? 'success'
                : search.status === 'failed'  ? 'danger'
                : 'info'
              }`}>{search.status}</span>
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-start', paddingTop: '40px' }}>
          <ExportButton searchId={id} disabled={!isComplete} />
          {isComplete && (
            <button className="btn btn-secondary btn-sm" onClick={() => { fetchAnalysisData(); fetchTableResults() }}>
              <RefreshCw size={13} /> Refresh
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      {(isLive || isFailed) && (
        <div className="card" style={{ padding: '28px', marginBottom: '32px', boxShadow: 'var(--shadow-sm)' }}>
          <h2 className="section-title">Processing</h2>
          <ProgressIndicator events={events} status={search?.status} />
          {isFailed && (
            <div style={{ marginTop: '20px' }}>
              <button className="btn btn-primary" onClick={() => navigate('/search')}>
                Try a new search
              </button>
            </div>
          )}
        </div>
      )}

      {/* Dashboard */}
      {isComplete && (
        <>
          {/* Stats */}
          <section style={{ marginBottom: '32px' }}>
            <h2 className="section-title">Price Statistics</h2>
            <StatsCards stats={analysisData?.stats} loading={loadingData} />
          </section>

          {/* Best Deal */}
          <section style={{ marginBottom: '32px' }}>
            <h2 className="section-title">Best Deal</h2>
            <BestDealCard deal={analysisData?.best_deal} loading={loadingData} />
          </section>

          {/* Charts */}
          <section style={{ marginBottom: '32px' }}>
            <div className="grid-2">
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '20px 20px 0' }}>
                  <h2 className="section-title" style={{ marginBottom: '2px' }}>Price Histogram</h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Full dataset · unaffected by table filters</p>
                </div>
                <PriceHistogram results={allResults} />
              </div>
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '20px 20px 0' }}>
                  <h2 className="section-title" style={{ marginBottom: '2px' }}>Price Distribution</h2>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Outliers shown in red</p>
                </div>
                <BoxPlot results={allResults} stats={analysisData?.stats} />
              </div>
            </div>
          </section>

          {/* PCA + Rules */}
          <section style={{ marginBottom: '32px' }}>
            <div className="grid-2">
              <div className="card" style={{ padding: '24px' }}>
                <h2 className="section-title">Cluster Visualization (PCA)</h2>
                <ClusterScatter points={pcaPoints} />
              </div>
              <div className="card" style={{ padding: '24px' }}>
                <h2 className="section-title">Association Rules</h2>
                <AssociationRules rules={rules} />
              </div>
            </div>
          </section>

          {/* Table */}
          <section>
            <div className="card" style={{ padding: '24px' }}>
              <h2 className="section-title">All Listings</h2>
              <FilterBar filters={filters} onChange={setFilters} />
              <ResultsTable
                results={tableResults}
                loading={loadingTable}
                total={tableTotal}
                page={filters.page}
                pageSize={20}
                onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
              />
            </div>
          </section>
        </>
      )}
    </div>
  )
}
