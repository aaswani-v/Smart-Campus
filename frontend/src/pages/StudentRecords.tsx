import { motion } from "framer-motion";
import { BookOpen, CheckCircle, AlertCircle } from "lucide-react";
import "../index.css";

const subjects = [
  { code: "CS301", name: "Artificial Intelligence", attendance: 92, completion: 85, status: "On Track" },
  { code: "CS302", name: "Database Management", attendance: 88, completion: 70, status: "On Track" },
  { code: "CS303", name: "Computer Networks", attendance: 75, completion: 60, status: "Lagging" },
  { code: "CS304", name: "Operating Systems", attendance: 95, completion: 90, status: "Excellent" },
  { code: "CS305", name: "Software Engineering", attendance: 82, completion: 75, status: "On Track" },
  { code: "CS306", name: "Cyber Security", attendance: 60, completion: 40, status: "Risk" },
];

export default function StudentRecords() {
  const overallAttendance = Math.round(subjects.reduce((acc, s) => acc + s.attendance, 0) / subjects.length);
  const overallCompletion = Math.round(subjects.reduce((acc, s) => acc + s.completion, 0) / subjects.length);

  return (
    <div className="dashboard-container" style={{ maxWidth: 1000, margin: '0 auto', paddingBottom: '2rem' }}>
      <header className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
           <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>My Academic Records</h1>
           <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Detailed breakdown of your attendance and course progress.</p>
        </div>
        <div className="badge" style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}>
           Semester 5
        </div>
      </header>
      
      {/* Top Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}
          >
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(34, 197, 94, 0.1)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <CheckCircle size={24} />
              </div>
              <div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Overall Attendance</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>{overallAttendance}%</div>
              </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}
          >
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <BookOpen size={24} />
              </div>
              <div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Course Completion</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>{overallCompletion}%</div>
              </div>
          </motion.div>

          <motion.div 
             initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
             className="card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}
          >
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <AlertCircle size={24} />
              </div>
              <div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Pending Actions</div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>3</div>
              </div>
          </motion.div>
      </div>

      {/* Detailed Table */}
      <motion.div 
         initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
         className="card" style={{ padding: 0, overflow: 'hidden' }}
      >
          <div style={{ padding: '1.25rem', borderBottom: '1px solid var(--border-color)' }}>
              <h3 style={{ margin: 0, fontSize: '1rem' }}>Subject Performance</h3>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '1rem' }}>Subject Code</th>
                      <th style={{ padding: '1rem' }}>Subject Name</th>
                      <th style={{ padding: '1rem' }}>Attendance</th>
                      <th style={{ padding: '1rem' }}>Completion</th>
                      <th style={{ padding: '1rem' }}>Status</th>
                  </tr>
              </thead>
              <tbody>
                  {subjects.map((sub, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                          <td style={{ padding: '1rem', fontWeight: 600 }}>{sub.code}</td>
                          <td style={{ padding: '1rem' }}>{sub.name}</td>
                          <td style={{ padding: '1rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                  <div style={{ flex: 1, height: 6, background: 'var(--bg-primary)', borderRadius: 3, width: 80 }}>
                                      <div style={{ width: `${sub.attendance}%`, height: '100%', background: sub.attendance > 75 ? 'var(--accent-primary)' : '#ef4444', borderRadius: 3 }} />
                                  </div>
                                  <span style={{ fontSize: '0.85rem', width: 30 }}>{sub.attendance}%</span>
                              </div>
                          </td>
                          <td style={{ padding: '1rem' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                  <div style={{ flex: 1, height: 6, background: 'var(--bg-primary)', borderRadius: 3, width: 80 }}>
                                      <div style={{ width: `${sub.completion}%`, height: '100%', background: '#3b82f6', borderRadius: 3 }} />
                                  </div>
                                  <span style={{ fontSize: '0.85rem', width: 30 }}>{sub.completion}%</span>
                              </div>
                          </td>
                          <td style={{ padding: '1rem' }}>
                              <span className="badge" style={{ 
                                  background: sub.status === 'Risk' ? 'rgba(239, 68, 68, 0.2)' : sub.status === 'Excellent' ? 'rgba(34, 197, 94, 0.2)' : 'var(--bg-elevated)',
                                  color: sub.status === 'Risk' ? '#ef4444' : sub.status === 'Excellent' ? 'var(--accent-primary)' : 'var(--text-primary)'
                              }}>
                                  {sub.status}
                              </span>
                          </td>
                      </tr>
                  ))}
              </tbody>
          </table>
      </motion.div>
    </div>
  );
}
