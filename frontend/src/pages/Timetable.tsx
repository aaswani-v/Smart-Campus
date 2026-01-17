import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, MapPin, X, Check, MoreHorizontal, Clock } from 'lucide-react'

interface TimetableSlot { id: number; course: { id: number; code: string; name: string }; day_index: number; start_time: string; room: string }

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const TIMES = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']

const COLORS = ['#4a90d9', '#22c55e', '#f97316', '#ec4899', '#8b5cf6']

export default function Timetable() {
  const [slots] = useState<TimetableSlot[]>([
    { id: 1, course: { id: 1, code: 'CS101', name: 'Programming' }, day_index: 0, start_time: '09:00', room: '301' },
    { id: 2, course: { id: 2, code: 'CS201', name: 'Data Structures' }, day_index: 0, start_time: '11:00', room: '302' },
    { id: 3, course: { id: 3, code: 'MTH101', name: 'Calculus' }, day_index: 2, start_time: '09:00', room: '401' },
    { id: 4, course: { id: 2, code: 'CS201', name: 'Data Structures' }, day_index: 3, start_time: '14:00', room: '302' },
    { id: 5, course: { id: 4, code: 'PHY101', name: 'Physics' }, day_index: 4, start_time: '10:00', room: '201' },
  ])
  const [courses] = useState([{ id: 1, code: 'CS101', name: 'Programming' }, { id: 2, code: 'CS201', name: 'Data Structures' }, { id: 3, code: 'MTH101', name: 'Calculus' }, { id: 4, code: 'PHY101', name: 'Physics' }])
  const [showModal, setShowModal] = useState(false)
  const [selectedDay, setSelectedDay] = useState<number | null>(null)
  const [newSlot, setNewSlot] = useState({ courseId: '', startTime: '', room: '' })

  const getSlot = (day: number, time: string) => slots.find(s => s.day_index === day && s.start_time === time)
  const getColor = (courseId: number) => COLORS[(courseId - 1) % COLORS.length]

  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">Schedule</h1>
        <motion.button 
          className="btn btn-primary" 
          onClick={() => setShowModal(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Plus size={16} /> Add Class
        </motion.button>
      </motion.div>

      <motion.div 
        className="card" 
        initial={{ opacity: 0, y: 20 }} 
        animate={{ opacity: 1, y: 0 }}
        style={{ padding: 0, overflow: 'hidden' }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '70px repeat(6, 1fr)', minHeight: 480 }}>
          {/* Header Row */}
          <div style={{ background: 'var(--bg-elevated)', padding: 'var(--space-md)', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Clock size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          {DAYS.map((d, i) => (
            <motion.div 
              key={d}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              style={{ background: 'var(--bg-elevated)', padding: 'var(--space-md)', borderBottom: '1px solid var(--border-color)', borderLeft: '1px solid var(--border-color)', fontWeight: 600, fontSize: '0.8125rem', textAlign: 'center' }}
            >
              {d}
            </motion.div>
          ))}

          {/* Time Rows */}
          {TIMES.map((time, ti) => (
            <>
              <div 
                key={`t-${time}`}
                style={{ padding: 'var(--space-sm)', borderBottom: '1px solid var(--border-light)', fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                {time}
              </div>
              {DAYS.map((_, di) => {
                const slot = getSlot(di, time)
                return (
                  <motion.div 
                    key={`${di}-${time}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 + ti * 0.02 + di * 0.01 }}
                    onClick={() => !slot && (setSelectedDay(di), setNewSlot(p => ({ ...p, startTime: time })), setShowModal(true))}
                    style={{ 
                      borderBottom: '1px solid var(--border-light)', 
                      borderLeft: '1px solid var(--border-light)', 
                      padding: 4, 
                      minHeight: 48, 
                      cursor: slot ? 'default' : 'pointer',
                      transition: 'background 0.15s'
                    }}
                    whileHover={!slot ? { background: 'var(--bg-elevated)' } : {}}
                  >
                    {slot && (
                      <motion.div 
                        initial={{ scale: 0.8, opacity: 0 }} 
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: 'spring', stiffness: 300 }}
                        whileHover={{ scale: 1.02 }}
                        style={{ 
                          background: getColor(slot.course.id), 
                          borderRadius: 'var(--radius-md)', 
                          padding: '8px 10px', 
                          height: '100%', 
                          color: '#fff',
                          cursor: 'pointer'
                        }}
                      >
                        <div style={{ fontWeight: 600, fontSize: '0.75rem' }}>{slot.course.code}</div>
                        <div style={{ fontSize: '0.5625rem', opacity: 0.9, display: 'flex', alignItems: 'center', gap: 3, marginTop: 2 }}>
                          <MapPin size={8} /> {slot.room}
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                )
              })}
            </>
          ))}
        </div>
      </motion.div>

      {/* Legend */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        style={{ display: 'flex', gap: 'var(--space-lg)', marginTop: 'var(--space-lg)', fontSize: '0.75rem' }}
      >
        {courses.map((c) => (
          <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 12, height: 12, borderRadius: 'var(--radius-sm)', background: getColor(c.id) }} />
            <span style={{ color: 'var(--text-secondary)' }}>{c.code}</span>
          </div>
        ))}
      </motion.div>

      {/* Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            onClick={() => setShowModal(false)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
          >
            <motion.div 
              className="card"
              initial={{ scale: 0.9, y: 20 }} 
              animate={{ scale: 1, y: 0 }} 
              exit={{ scale: 0.9, y: 20 }}
              onClick={e => e.stopPropagation()}
              style={{ width: 360 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-lg)' }}>
                <span className="card-title">Add Class</span>
                <motion.button 
                  className="card-menu"
                  onClick={() => setShowModal(false)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <X size={16} />
                </motion.button>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <div className="input-group">
                  <label className="input-label">Course</label>
                  <select className="input" value={newSlot.courseId} onChange={e => setNewSlot(p => ({ ...p, courseId: e.target.value }))}>
                    <option value="">Select course...</option>
                    {courses.map(c => <option key={c.id} value={c.id}>{c.code} - {c.name}</option>)}
                  </select>
                </div>
                <div className="grid grid-2" style={{ gap: 'var(--space-md)' }}>
                  <div className="input-group">
                    <label className="input-label">Day</label>
                    <select className="input" value={selectedDay ?? ''} onChange={e => setSelectedDay(Number(e.target.value))}>
                      <option value="">Select day...</option>
                      {DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Room</label>
                    <input className="input" value={newSlot.room} onChange={e => setNewSlot(p => ({ ...p, room: e.target.value }))} placeholder="301" />
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">Time</label>
                  <select className="input" value={newSlot.startTime} onChange={e => setNewSlot(p => ({ ...p, startTime: e.target.value }))}>
                    <option value="">Select time...</option>
                    {TIMES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: 'var(--space-md)', marginTop: 'var(--space-xl)' }}>
                <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowModal(false)}>Cancel</button>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => setShowModal(false)}><Check size={14} /> Add Class</button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
