
import { motion } from "framer-motion";
import {
  Users,
  GraduationCap,
  School,
  TrendingUp,
  Calendar,
  MoreHorizontal,
  ChevronDown
} from "lucide-react";

// Mock Data for Campus Overview
const stats = {
  totalStudents: "2,845",
  attendanceRate: "94.2%",
  activeClasses: "42",
  departments: "8"
};

const departmentData = [
    { name: "Computer Science", attendance: 96, status: "increase" },
    { name: "Electrical Eng.", attendance: 88, status: "decrease" },
    { name: "Business Admin", attendance: 92, status: "stable" }
];

export default function Home() {
  return (
    <div className="home-container" style={{ padding: '0 1rem' }}>
      
      {/* Top Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 800, letterSpacing: '0.02em', marginBottom: '0.5rem' }}>CAMPUS METRICS</h1>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
            <div className="filter-pill">
                 <span>Term: <strong>Fall 2025</strong></span> <ChevronDown size={14} />
            </div>
             <div className="filter-pill">
                 <span>View: <strong>All Depts</strong></span> <ChevronDown size={14} />
            </div>
             <div className="filter-pill">
                 <span>Role: <strong>Admin</strong></span> <ChevronDown size={14} />
            </div>
        </div>
      </div>

      {/* Main Grid - Restored Complex Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Weekly Attendance (Waterfall Style) */}
        <motion.div className="card" style={{ gridColumn: 'span 4' }} whileHover={{ y: -5 }}>
            <div className="card-header">
                <span className="card-title">WEEKLY ATTENDANCE</span>
                <div className="card-menu"><MoreHorizontal size={18} /></div>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '1rem' }}>
                 <span className="stat-value">94.2%</span>
                 <span className="stat-badge up"><TrendingUp size={12} /> +2.4%</span>
            </div>
            <div className="waterfall-chart">
                {[60, 45, 75, 50, 80, 65, 90, 55, 70, 40, 85, 60, 75, 50, 95].map((h, i) => (
                     <div key={i} className={`waterfall-bar ${i > 10 ? 'active' : ''}`} style={{ height: `${h}%` }} />
                ))}
            </div>
        </motion.div>

        {/* Pass Rate Trends (Line Chart Style) */}
        <motion.div className="card" style={{ gridColumn: 'span 4' }} whileHover={{ y: -5 }}>
             <div className="card-header">
                <span className="card-title">PASS RATE TRENDS</span>
                <div className="card-menu"><MoreHorizontal size={18} /></div>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '1rem' }}>
                 <span className="stat-value">88.5%</span>
                 <span className="stat-badge down"><TrendingUp size={12} style={{ transform: 'rotate(180deg)' }} /> -1.2%</span>
            </div>
            {/* Simulated Line Chart using multiple divs for "efficiency" look */}
            <div style={{ display: 'flex', alignItems: 'flex-end', height: 120, gap: 4 }}>
                 {[30, 40, 35, 50, 45, 60, 55, 70, 65, 80, 75, 90, 85, 70, 75, 60, 65, 50, 55, 40, 45, 30].map((h, i) => (
                      <div key={i} style={{ width: '100%', height: `${h}%`, background: 'var(--accent-primary)', opacity: 0.2 + (i/25), borderRadius: 2 }} />
                 ))}
            </div>
        </motion.div>

        {/* Course Completion (Horizontal Bars) */}
        <motion.div className="card" style={{ gridColumn: 'span 4' }} whileHover={{ y: -5 }}>
             <div className="card-header">
                <span className="card-title">SEMESTER PROGRESS</span>
                <div className="card-menu"><MoreHorizontal size={18} /></div>
            </div>
             <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                {[
                    { date: '30.09', val: 92, label: 'Finals Prep' },
                    { date: '29.09', val: 85, label: 'Proposals' },
                    { date: '28.09', val: 64, label: 'Mid-Terms' },
                    { date: '27.09', val: 45, label: 'Assignments' },
                    { date: '26.09', val: 23, label: 'Lectures' }
                ].map((item, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', width: 40 }}>{item.date}</span>
                        <div style={{ flex: 1, height: 24, background: 'var(--bg-elevated)', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
                             <div style={{ width: `${item.val}%`, height: '100%', background: i===0 ? 'var(--accent-orange)' : 'var(--accent-secondary)', borderRadius: 4, display: 'flex', alignItems: 'center', paddingLeft: 8, fontSize: '0.7rem', color: '#fff', fontWeight: 600 }}>
                                 {item.val}%
                             </div>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>

      </div>

      {/* Bottom Bar Chart - Department Stats */}
      <motion.div className="card" layout>
          <div className="card-header">
              <span className="card-title">DEPARTMENT PERFORMANCE</span>
              <div className="filter-pill">Sort By: <strong>Attendance</strong></div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'flex-end', height: 220, paddingBottom: '1rem' }}>
              {['CS', 'Mech', 'Civil', 'Elec', 'Bio', 'Arts', 'Bus', 'Law', 'Med', 'Arch', 'Des', 'Chem'].map((dept, i) => {
                  const h = [55, 45, 95, 75, 35, 85, 60, 40, 70, 50, 80, 65][i];
                  const val = [52, 44, 96, 72, 34, 84, 58, 38, 68, 48, 78, 63][i];
                  return (
                      <div key={dept} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', width: '6%' }}>
                           <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>{val}</span>
                           <div style={{ display: 'flex', gap: 4, alignItems: 'flex-end' }}>
                                <motion.div 
                                    initial={{ height: 0 }}
                                    animate={{ height: h * 1.5 }}
                                    transition={{ duration: 0.5, delay: i * 0.05 }}
                                    style={{ 
                                        width: 8, 
                                        background: i % 3 === 0 ? 'var(--accent-secondary)' : 'var(--accent-primary)',
                                        borderRadius: '4px 4px 0 0',
                                        opacity: i % 3 === 0 ? 0.5 : 1
                                    }}
                                />
                                 {i % 4 === 0 && (
                                     <motion.div 
                                        initial={{ height: 0 }}
                                        animate={{ height: h }}
                                        style={{ width: 8, background: 'var(--accent-orange)', borderRadius: '4px 4px 0 0' }} 
                                     />
                                 )}
                           </div>
                           <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: 4 }}>{dept}</span>
                      </div>
                  )
              })}
          </div>
      </motion.div>

    </div>
  );
}
