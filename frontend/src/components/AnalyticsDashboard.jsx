import { useState, useEffect } from 'react'
import { searchApi } from '../api/search'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts'
import { Activity, Database, ShoppingCart, Search as SearchIcon } from 'lucide-react'

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    searchApi.getAnalytics()
      .then(res => {
        if (mounted) {
          setData(res.data)
          setLoading(false)
        }
      })
      .catch(err => {
        console.error("Failed to fetch analytics:", err)
        if (mounted) setLoading(false)
      })

    return () => { mounted = false }
  }, [])

  if (loading) {
    return (
      <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          {[1,2,3,4].map(i => (
            <div key={i} style={{ height: '100px', background: 'var(--bg-muted)', borderRadius: '12px', animation: 'pulse 1.5s infinite' }} />
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          <div style={{ height: '300px', background: 'var(--bg-muted)', borderRadius: '12px', animation: 'pulse 1.5s infinite' }} />
          <div style={{ height: '300px', background: 'var(--bg-muted)', borderRadius: '12px', animation: 'pulse 1.5s infinite' }} />
        </div>
      </div>
    )
  }

  if (!data || data.summary.total_searches === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 24px', color: 'var(--text-muted)' }}>
        <Activity size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
        <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-primary)' }}>No search history yet</h3>
        <p style={{ marginTop: '8px', fontSize: '14px' }}>Run some searches to populate your analytics dashboard.</p>
      </div>
    )
  }

  const { summary, price_trends, top_cheap_products, keyword_frequency } = data

  const metricCards = [
    { label: 'Total Searches', value: summary.total_searches, icon: <SearchIcon size={20} /> },
    { label: 'Items Scraped', value: summary.total_items, icon: <Database size={20} /> },
    { label: 'Avg Items / Search', value: summary.avg_items_per_search, icon: <Activity size={20} /> },
    { label: 'Top Keyword', value: summary.most_searched_keyword, icon: <ShoppingCart size={20} /> },
  ]

  // Dynamic lines for platforms
  const platforms = new Set()
  price_trends.forEach(d => {
    Object.keys(d).forEach(k => {
      if (k !== 'date') platforms.add(k)
    })
  })
  const platformArray = Array.from(platforms)
  const colors = ['#C1502E', '#2E5B82', '#E2A03F', '#4A7C59', '#6B4A7C']

  return (
    <div style={{ padding: '24px 0', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* 1. Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        {metricCards.map((card, i) => (
          <div key={i} className="card" style={{ padding: '20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'var(--bg-muted)', color: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {card.icon}
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {card.label}
              </div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                {card.value}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', alignItems: 'start' }}>
        
        {/* 2. Price Trend Chart */}
        <div className="card" style={{ padding: '24px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 24px 0', fontSize: '16px' }}>Average Price Trends (MAD)</h3>
          {price_trends.length > 0 ? (
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={price_trends} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} tickLine={false} axisLine={false} tickFormatter={(val) => `DH ${val}`} />
                  <Tooltip 
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                  {platformArray.map((plat, i) => (
                    <Line 
                      key={plat}
                      type="monotone" 
                      dataKey={plat} 
                      name={plat.charAt(0).toUpperCase() + plat.slice(1)}
                      stroke={colors[i % colors.length]} 
                      strokeWidth={3}
                      dot={{ r: 4, strokeWidth: 2 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
              Not enough data for trends
            </div>
          )}
        </div>

        {/* 3. Keyword Frequency */}
        <div className="card" style={{ padding: '24px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 24px 0', fontSize: '16px' }}>Top Searches</h3>
          {keyword_frequency.length > 0 ? (
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={keyword_frequency} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="keyword" type="category" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} width={80} />
                  <Tooltip 
                    cursor={{ fill: 'var(--bg-muted)' }}
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px' }}
                  />
                  <Bar dataKey="count" fill="var(--brand)" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
             <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
              No keyword data
            </div>
          )}
        </div>

      </div>

      {/* 4. Top Cheapest Products */}
      <div className="card" style={{ padding: '24px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px' }}>Top 5 Cheapest Products Found</h3>
        {top_cheap_products.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {top_cheap_products.map(p => (
              <a 
                key={p.id} 
                href={p.url} 
                target="_blank" 
                rel="noreferrer"
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center', 
                  padding: '12px 16px', 
                  background: 'var(--bg-surface)', 
                  borderRadius: '8px',
                  textDecoration: 'none',
                  color: 'inherit',
                  border: '1px solid transparent',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--brand)'; e.currentTarget.style.background = 'var(--bg-muted)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'transparent'; e.currentTarget.style.background = 'var(--bg-surface)' }}
              >
                <div style={{ flex: 1, minWidth: 0, marginRight: '16px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {p.title}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', textTransform: 'capitalize' }}>
                    {p.platform}
                  </div>
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--brand)', whiteSpace: 'nowrap' }}>
                  {p.price_mad} MAD
                </div>
              </a>
            ))}
          </div>
        ) : (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '14px' }}>
            No products found yet
          </div>
        )}
      </div>

    </div>
  )
}
