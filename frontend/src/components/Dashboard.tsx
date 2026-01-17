import { useState } from 'react'
import { motion } from 'framer-motion'
import { MoreHorizontal, TrendingUp } from 'lucide-react'

interface DashboardProps {
  sessionId?: string
}

export default function Dashboard({ sessionId }: DashboardProps) {
  const [stats] = useState({ present: 28, total: 32, attention: 78, drowsy: 2, distracted: 5 })

  return (
    <div className="grid grid-2">
      {/* Stats */}
      <motion.div className="glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <div className="card-header"><span className="card-title">TODAY'S SUMMARY</span><MoreHorizontal size={16} className="card-menu" /></div>
        <div className="grid grid-2" style={{ gap: 'var(--space-xl)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span className="stat-value lime">{stats.present}</span>
              <span style={{ fontSize: '1.125rem', color: 'var(--text-muted)', marginLeft: 4 }}>/{stats.total}</span>
            </div>
            <div className="stat-label">Present</div>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span className="stat-value" style={{ color: stats.attention >= 70 ? 'var(--accent-lime)' : 'var(--accent-orange)' }}>{stats.attention}%</span>
              <span className="stat-trend up"><TrendingUp size={10} /> +5</span>
            </div>
            <div className="stat-label">Avg Attention</div>
          </div>
          <div>
            <span className="stat-value orange">{stats.distracted}</span>
            <div className="stat-label">Distracted</div>
          </div>
          <div>
            <span className="stat-value" style={{ color: 'var(--accent-danger)' }}>{stats.drowsy}</span>
            <div className="stat-label">Drowsy</div>
          </div>
        </div>
      </motion.div>

      {/* Activity */}
      <motion.div className="glass-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
        <div className="card-header"><span className="card-title">WEEKLY ACTIVITY</span><MoreHorizontal size={16} className="card-menu" /></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          {[
            { label: 'CS101', value: 92 },
            { label: 'CS201', value: 85 },
            { label: 'MTH101', value: 78 },
            { label: 'PHY101', value: 65 },
          ].map((item, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', width: 50 }}>{item.label}</span>
              <div style={{ flex: 1, height: 6, background: 'var(--bg-elevated)', borderRadius: 'var(--radius-pill)', overflow: 'hidden' }}>
                <motion.div initial={{ width: 0 }} animate={{ width: `${item.value}%` }} transition={{ delay: 0.7 + i * 0.1, duration: 0.5 }} style={{ height: '100%', background: item.value >= 80 ? 'var(--accent-lime)' : item.value >= 70 ? 'var(--accent-orange)' : 'var(--accent-danger)', borderRadius: 'var(--radius-pill)' }} />
              </div>
              <span style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', width: 30 }}>{item.value}%</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
