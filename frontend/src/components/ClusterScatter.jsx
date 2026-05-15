import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

// Warm cluster palette for light background
const CLUSTER_COLORS = [
  '#C96442', '#1D6FA4', '#2E7D52', '#B45309',
  '#7C3AED', '#0891B2', '#DC2626', '#059669',
]

export default function ClusterScatter({ points = [] }) {
  const svgRef = useRef(null)

  const hasData = points.length > 0 && points.some((p) => p.pca_x !== 0 || p.pca_y !== 0)

  useEffect(() => {
    if (!svgRef.current || !hasData) return

    const el     = svgRef.current
    const width  = el.clientWidth  || 560
    const height = el.clientHeight || 300
    const margin = { top: 16, right: 16, bottom: 36, left: 48 }
    const innerW = width  - margin.left - margin.right
    const innerH = height - margin.top  - margin.bottom

    d3.select(el).selectAll('*').remove()

    const svg = d3.select(el)
      .attr('width', width)
      .attr('height', height)
      .style('background', 'transparent')

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    const xScale = d3.scaleLinear()
      .domain(d3.extent(points, (d) => d.pca_x)).nice().range([0, innerW])
    const yScale = d3.scaleLinear()
      .domain(d3.extent(points, (d) => d.pca_y)).nice().range([innerH, 0])
    const maxScore = Math.max(...points.map((d) => d.deal_score ?? 0), 1)
    const rScale = d3.scaleSqrt().domain([0, maxScore]).range([4, 11])

    // Grid lines
    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-innerW).tickFormat(''))
      .call((ax) => { ax.select('.domain').remove(); ax.selectAll('line').attr('stroke', '#ECEAE5') })

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(5).tickFormat((d) => d.toFixed(1)))
      .call((ax) => { ax.select('.domain').attr('stroke', '#DDD9D0') })
      .selectAll('text').attr('fill', '#9B978F').style('font-size', '10px')

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5).tickFormat((d) => d.toFixed(1)))
      .call((ax) => { ax.select('.domain').attr('stroke', '#DDD9D0') })
      .selectAll('text').attr('fill', '#9B978F').style('font-size', '10px')

    // Tooltip
    const tooltip = d3.select('body').append('div')
      .style('position', 'fixed')
      .style('display', 'none')
      .style('background', '#FFFFFF')
      .style('border', '1px solid #DDD9D0')
      .style('border-radius', '8px')
      .style('padding', '10px 14px')
      .style('font-size', '12px')
      .style('color', '#66635B')
      .style('box-shadow', '0 4px 18px rgba(26,23,20,0.12)')
      .style('pointer-events', 'none')
      .style('z-index', '9999')
      .style('max-width', '220px')
      .style('line-height', '1.6')
      .style('font-family', 'Inter, sans-serif')

    points.forEach((d) => {
      // Aggressively check multiple keys just in case, and avoid ?? operator to prevent transpilation bugs
      let cluster = null;
      if (d.cluster !== undefined && d.cluster !== null) cluster = d.cluster;
      else if (d.cluster_dbscan !== undefined && d.cluster_dbscan !== null) cluster = d.cluster_dbscan;
      else if (d.cluster_id !== undefined && d.cluster_id !== null) cluster = d.cluster_id;

      // For DBSCAN, -1 is noise
      const isNoise   = cluster === -1;
      const color     = (cluster !== null && !isNoise) ? CLUSTER_COLORS[cluster % CLUSTER_COLORS.length] : '#9B978F';
      const r         = rScale(d.deal_score ?? 0);
      const cx        = xScale(d.pca_x);
      const cy        = yScale(d.pca_y);
      const isAnomaly = d.is_anomaly;

      const shape = g.append('g')
        .attr('transform', `translate(${cx},${cy})`)
        .style('cursor', 'pointer')

      if (isAnomaly) {
        const s = r * 0.85
        shape.append('line').attr('x1', -s).attr('y1', -s).attr('x2', s).attr('y2', s)
          .attr('stroke', '#C0392B').attr('stroke-width', 2).attr('stroke-linecap', 'round')
        shape.append('line').attr('x1', s).attr('y1', -s).attr('x2', -s).attr('y2', s)
          .attr('stroke', '#C0392B').attr('stroke-width', 2).attr('stroke-linecap', 'round')
        shape.append('circle').attr('r', r + 4).attr('fill', 'transparent')
      } else {
        shape.append('circle')
          .attr('r', r)
          .attr('fill', color + '44')
          .attr('stroke', color)
          .attr('stroke-width', 1.5)
      }

      shape
        .on('mouseover', () => {
          tooltip.style('display', 'block').html(`
            <strong style="color:#1A1714">${d.title ?? 'Item'}</strong><br/>
            Platform: ${d.platform ?? '—'}<br/>
            Price: ${d.price_mad != null ? Number(d.price_mad).toFixed(2) + ' MAD' : '—'}<br/>
            Deal score: ${d.deal_score != null ? (d.deal_score * 100).toFixed(1) + '%' : '—'}<br/>
            Cluster: ${isNoise ? 'Noise' : (cluster !== null && cluster !== undefined ? cluster : (isAnomaly ? '⚠ Anomaly' : '—'))}
          `)
        })
        .on('mousemove', (event) => {
          tooltip.style('left', (event.clientX + 14) + 'px').style('top', (event.clientY - 10) + 'px')
        })
        .on('mouseout', () => tooltip.style('display', 'none'))
    })

    return () => { tooltip.remove() }
  }, [points, hasData])

  if (!hasData) {
    return (
      <div className="empty-state" style={{ minHeight: '300px' }}>
        <span className="empty-state-icon">🔵</span>
        <p className="empty-state-title">Not enough data for cluster visualization</p>
        <p className="empty-state-desc">Minimum 10 results required</p>
      </div>
    )
  }

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
}
