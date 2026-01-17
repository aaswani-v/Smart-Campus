import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { MoreHorizontal, Download, ChevronDown, Calendar, TrendingUp } from 'lucide-react'

function AnimatedNumber({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    const duration = 800
    const startTime = Date.now()
    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(value * eased))
      if (progress < 1) requestAnimationFrame(animate)
    }
    requestAnimationFrame(animate)
  }, [value])
  return <>{display.toLocaleString()}{suffix}</>
}

export default function Analytics() {
  const [range, setRange] = useState<'week' | 'month'>('week')



  return (
    <div style={{ paddingBottom: '2rem', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Page Header - Compact & Centered */}
      <motion.div 
        className="page-header" 
        initial={{ opacity: 0, y: -10 }} 
        animate={{ opacity: 1, y: 0 }} 
        style={{ marginBottom: '1rem', paddingBottom: '0.5rem' }}
      >
        <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, letterSpacing: '0.02em', margin: 0 }}>ANALYTICS OVERVIEW</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '0.2rem' }}>Real-time performance metrics and AI insights.</p>
        </div>
        <div className="filters">
          <div className="filter-pill" style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem' }} onClick={() => setRange(range === 'week' ? 'month' : 'week')}>
             <Calendar size={12} /> <span>Range: <strong>{range === 'week' ? 'This Week' : 'This Month'}</strong></span> <ChevronDown size={12} />
          </div>
          <button className="btn btn-secondary" style={{ padding: '0.3rem 0.7rem', fontSize: '0.75rem' }}><Download size={12} /> Export</button>
        </div>
      </motion.div>

      {/* Grid Container with Staggered Animation */}
      <motion.div 
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
          }
        }}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gridTemplateRows: 'auto auto auto', gap: '0.75rem' }}
      >

        {/* 1. Key Metrics (Top Row - 4 Columns) */}
        {[
          { label: 'Avg Attendance', value: 92, suffix: '%' },
          { label: 'Avg Attention', value: 78, suffix: '%' },
          { label: 'Engagement', value: 8.5, suffix: '/10' },
          { label: 'Classes', value: 24, suffix: '' },
        ].map((stat, i) => (
          <motion.div 
            key={i} 
            className="card" 
            variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
            whileHover={{ y: -2, boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}
            style={{ padding: '0.75rem 1rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
          >
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>{stat.label}</div>
            <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
                <AnimatedNumber value={stat.value} suffix={stat.suffix} />
            </span>
          </motion.div>
        ))}

        {/* 2. Main Trend Chart (Spans 3 Columns) */}
        <motion.div 
          className="card" 
          variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
          style={{ gridColumn: 'span 3', height: 200, display: 'flex', flexDirection: 'column', padding: '1rem' }}
        >
            <div className="card-header" style={{ marginBottom: '0.25rem', paddingBottom: '0.25rem' }}>
              <span className="card-title" style={{ fontSize: '0.75rem' }}>ATTENDANCE TRENDS</span>
              <div className="card-menu"><MoreHorizontal size={14} /></div>
            </div>
            <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 6, padding: '0 0.5rem' }}>
                {[65, 70, 75, 72, 80, 85, 82, 88, 90, 85, 80, 85, 92, 95, 90, 88, 92, 94, 91, 95].map((h, i) => (
                    <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', gap: 2, height: '100%' }}>
                        <motion.div 
                          initial={{ height: 0 }}
                          animate={{ height: `${h * 0.6}%` }}
                          transition={{ duration: 0.8, delay: i * 0.03, ease: 'easeOut' }}
                          style={{ background: 'var(--accent-secondary)', borderRadius: 1, width: '100%', opacity: 0.4 }}
                        />
                        <motion.div 
                          initial={{ height: 0 }}
                          animate={{ height: `${h}%` }}
                          transition={{ duration: 0.8, delay: i * 0.03, ease: 'easeOut' }}
                          style={{ background: 'var(--accent-primary)', borderRadius: '2px 2px 0 0', width: '100%' }}
                        />
                    </div>
                ))}
            </div>
             <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '0.25rem', fontSize: '0.65rem', borderTop: '1px solid var(--bg-primary)', paddingTop: '0.25rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: 2, background: 'var(--accent-primary)' }} /> Actual</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: 2, background: 'var(--accent-secondary)' }} /> Predicted</span>
            </div>
        </motion.div>

        {/* 3. AI Insights (Side Panel - Spans 1 Column) */}
        <motion.div 
          className="card" 
          variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
          style={{ gridColumn: 'span 1', height: 200, background: 'linear-gradient(160deg, var(--accent-primary) 0%, #1e2923 100%)', color: '#fff', padding: '1rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
        >
             <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                   <span style={{ fontSize: '0.65rem', fontWeight: 600, opacity: 0.9, letterSpacing: '0.05em' }}>AI INSIGHTS</span>
                   <span style={{ fontSize: '0.6rem', background: 'rgba(255,255,255,0.2)', padding: '1px 5px', borderRadius: 3 }}>Live</span>
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, lineHeight: 1, marginBottom: '0.2rem' }}>+15%</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>Engagement Spike</div>
                <p style={{ fontSize: '0.7rem', opacity: 0.8, marginTop: '0.25rem', lineHeight: 1.3 }}>Morning classes showing higher focus.</p>
             </div>
             <div style={{ background: 'rgba(0,0,0,0.25)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', marginTop: '0.5rem' }}>
                 <div style={{ fontSize: '0.65rem', fontWeight: 600, marginBottom: 2, display: 'flex', alignItems: 'center', gap: 4 }}>💡 Recommendation</div>
                 <p style={{ fontSize: '0.7rem', opacity: 0.9, lineHeight: 1.2 }}>Schedule core subjects 9-11 AM.</p>
             </div>
        </motion.div>

        {/* 4. Top Performers (Spans 2 Columns) - Indian Names */}
        <motion.div 
          className="card" 
          variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
          style={{ gridColumn: 'span 2', padding: '0.75rem 1rem' }}
        >
            <div className="card-header" style={{ marginBottom: '0.5rem' }}>
                <span className="card-title" style={{ fontSize: '0.75rem' }}>TOP PERFORMERS</span>
                <div className="filter-pill" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>View All</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {[
                  { name: 'Ananya Sharma', score: 98 },
                  { name: 'Rohan Verma', score: 95 },
                  { name: 'Aditya Patel', score: 94 }
                ].map((s, i) => (
                    <motion.div whileHover={{ x: 2 }} key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)', fontSize: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                             <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--accent-primary)', width: 16 }}>#{i+1}</span>
                             <span style={{ fontWeight: 500 }}>{s.name}</span>
                        </div>
                        <span style={{ fontWeight: 700 }}>{s.score}%</span>
                    </motion.div>
                ))}
            </div>
        </motion.div>

        {/* 5. Needs Attention (Spans 2 Columns) - Indian Names */}
        <motion.div 
          className="card" 
          variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}
          style={{ gridColumn: 'span 2', padding: '0.75rem 1rem' }}
        >
            <div className="card-header" style={{ marginBottom: '0.5rem' }}>
                <span className="card-title" style={{ fontSize: '0.75rem' }}>NEEDS ATTENTION</span>
                <div className="filter-pill" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>View All</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {[
                    { name: 'Vihaan Gupta', issue: 'Low Attendance', val: '65%' },
                    { name: 'Kavya Singh', issue: 'Declining Focus', val: '58%' },
                    { name: 'Arjun Nair', issue: 'Missed Quiz', val: '-' },
                ].map((s, i) => (
                    <motion.div whileHover={{ x: 2 }} key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)', fontSize: '0.75rem' }}>
                         <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                             <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#ef4444' }} />
                             <span style={{ fontWeight: 500 }}>{s.name}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                             <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{s.issue}</span>
                             <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.val}</span>
                        </div>
                    </motion.div>
                ))}
            </div>
        </motion.div>

      </motion.div>
    </div>
  )
}
