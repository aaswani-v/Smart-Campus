import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Square, Users, Eye, AlertTriangle, Camera, Fingerprint, CheckCircle, MoreHorizontal, Radio } from 'lucide-react'
import RadarView from '../components/RadarView'
import FaceRecognition from '../components/FaceRecognition'
import BiometricPanel from '../components/BiometricPanel'

interface Course { id: number; code: string; name: string }
interface ActiveSession { session_id: string; course: string; room: string; started_at: string }

export default function Session() {
  const [tab, setTab] = useState<'radar' | 'camera' | 'biometric'>('radar')
  const [courses] = useState<Course[]>([{ id: 1, code: 'CS101', name: 'Intro to Programming' }, { id: 2, code: 'CS201', name: 'Data Structures' }])
  const [selectedCourse, setSelectedCourse] = useState<number | null>(null)
  const [room, setRoom] = useState('')
  const [session, setSession] = useState<ActiveSession | null>(null)
  const [radarPoints, setRadarPoints] = useState<any[]>([])
  const [isStarting, setIsStarting] = useState(false)
  const [attendanceLog, setAttendanceLog] = useState<any[]>([])

  useEffect(() => {
    if (!session) return
    const fetchRadar = () => fetch(`/api/analytics/radar/${session.session_id}`).then(r => r.ok && r.json()).then(d => setRadarPoints(d?.points || [])).catch(() => {})
    fetchRadar()
    const interval = setInterval(fetchRadar, 3000)
    return () => clearInterval(interval)
  }, [session])

  const startSession = async () => {
    if (!selectedCourse || !room) return
    setIsStarting(true)
    await new Promise(r => setTimeout(r, 800))
    setSession({ session_id: 'demo-session', course: courses.find(c => c.id === selectedCourse)?.code || '', room, started_at: new Date().toISOString() })
    setIsStarting(false)
  }

  const endSession = () => {
    setSession(null)
    setRadarPoints([])
    setAttendanceLog([])
  }

  if (!session) {
    return (
      <div style={{ maxWidth: 480, margin: '0 auto' }}>
        <motion.div className="page-header" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="page-title">START SESSION</h1>
        </motion.div>
        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ marginBottom: 'var(--space-md)' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Select Course</label>
            <select className="input" value={selectedCourse || ''} onChange={e => setSelectedCourse(Number(e.target.value))}>
              <option value="">Choose a course...</option>
              {courses.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
            </select>
          </div>
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: 8 }}>Room Number</label>
            <input className="input" value={room} onChange={e => setRoom(e.target.value)} placeholder="e.g., Room 301" />
          </div>
          <motion.button 
            className="btn btn-primary btn-lg w-full" 
            onClick={startSession} 
            disabled={!selectedCourse || !room || isStarting}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{ background: '#ff6b35' }}
          >
            {isStarting ? 'Starting...' : <><Play size={18} /> Start Session</>}
          </motion.button>
        </motion.div>
      </div>
    )
  }

  const avgAttention = radarPoints.length > 0 ? Math.round(radarPoints.reduce((a, p) => a + p.attention, 0) / radarPoints.length) : 78

  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <motion.div 
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }} 
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} 
            />
            <h1 className="page-title">{session.course} - {session.room}</h1>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>Started {new Date(session.started_at).toLocaleTimeString()}</p>
        </div>
        <button className="btn btn-secondary" onClick={endSession} style={{ borderColor: '#ef4444', color: '#ef4444' }}><Square size={16} /> End Session</button>
      </motion.div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-lg)', marginBottom: 'var(--space-lg)' }}>
        {[
          { icon: Users, value: radarPoints.length || 28, label: 'Present', color: '#ff6b35' },
          { icon: Eye, value: `${avgAttention}%`, label: 'Attention', color: '#ff6b35' },
          { icon: AlertTriangle, value: radarPoints.filter(p => p.is_distracted).length || 5, label: 'Distracted', color: '#a1a1aa' },
          { icon: AlertTriangle, value: radarPoints.filter(p => p.is_drowsy).length || 2, label: 'Drowsy', color: '#ef4444' }
        ].map((s, i) => (
          <motion.div key={i} className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 * i }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
              <s.icon size={20} style={{ color: s.color }} />
              <div>
                <span style={{ fontSize: '2rem', fontWeight: 600 }}>{s.value}</span>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.label}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Tab Nav */}
      <div className="nav" style={{ marginBottom: 'var(--space-lg)', width: 'fit-content' }}>
        {[{ id: 'radar', icon: Radio, label: 'Radar' }, { id: 'camera', icon: Camera, label: 'Camera' }, { id: 'biometric', icon: Fingerprint, label: 'Biometric' }].map(t => (
          <button key={t.id} className={`nav-link ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id as any)}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-lg)' }}>
        <AnimatePresence mode="wait">
          {tab === 'radar' && (
            <motion.div key="r" className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="card-header"><span className="card-title">LIVE RADAR</span><div className="card-menu"><MoreHorizontal size={16} /></div></div>
              <RadarView points={radarPoints.length ? radarPoints : [{ student_id: 'demo', name: 'Demo', angle: 45, radius: 0.7, attention: 85, is_drowsy: false, is_distracted: false }]} sessionActive />
            </motion.div>
          )}
          {tab === 'camera' && (
            <motion.div key="c" className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="card-header"><span className="card-title">FACE RECOGNITION</span><div className="card-menu"><MoreHorizontal size={16} /></div></div>
              <FaceRecognition sessionId={session.session_id} onRecognition={r => r.filter(x => x.recognized).forEach(x => setAttendanceLog(prev => prev.some(l => l.student_id === x.student_id) ? prev : [...prev, { ...x, timestamp: new Date().toISOString() }]))} mode="recognition" />
            </motion.div>
          )}
          {tab === 'biometric' && (
            <motion.div key="b" className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <BiometricPanel mode="verify" />
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="card-header"><span className="card-title">ATTENDANCE LOG</span><div className="card-menu"><MoreHorizontal size={16} /></div></div>
          {attendanceLog.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--space-xl)', color: 'var(--text-muted)', fontSize: '0.875rem' }}>No attendance recorded yet</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', maxHeight: 300, overflow: 'auto' }}>
              {attendanceLog.map((log) => (
                <motion.div 
                  key={log.student_id} 
                  initial={{ opacity: 0, x: -10 }} 
                  animate={{ opacity: 1, x: 0 }}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-sm) var(--space-md)', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid #ff6b35' }}
                >
                  <div>
                    <div style={{ fontWeight: 500, fontSize: '0.875rem' }}>{log.name}</div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>{log.student_id}</div>
                  </div>
                  <CheckCircle size={16} style={{ color: '#ff6b35' }} />
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
