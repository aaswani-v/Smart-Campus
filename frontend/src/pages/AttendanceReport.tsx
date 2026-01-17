import { useState, useEffect } from 'react';
import { ArrowLeft, Calendar, Download, Search, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

interface AttendanceRecord {
  name: string;
  date: string;
  time: string;
}

interface AttendanceSummary {
  month: string;
  people: string[];
  dates: string[];
  matrix: { [person: string]: { [date: string]: boolean } };
}

const API_BASE = 'http://localhost:8000';

export function AttendanceReport() {
  const navigate = useNavigate();
  const [view, setView] = useState<'list' | 'matrix'>('matrix');
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [searchName, setSearchName] = useState('');
  const [loading, setLoading] = useState(true);

  // Fetch attendance data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        if (view === 'matrix') {
          const res = await fetch(`${API_BASE}/api/simple-attendance/summary?month=${selectedMonth}`);
          const data = await res.json();
          setSummary(data);
        } else {
          const res = await fetch(`${API_BASE}/api/simple-attendance/history`);
          const data = await res.json();
          setRecords(data.records || []);
        }
      } catch (error) {
        console.error('Failed to fetch attendance:', error);
      }
      setLoading(false);
    };
    fetchData();
  }, [view, selectedMonth]);

  // Filter records by search
  const filteredRecords = records.filter(r => 
    r.name.toLowerCase().includes(searchName.toLowerCase())
  );

  return (
    <div style={{ padding: 'var(--space-md) var(--space-lg)', minHeight: 'calc(100vh - 80px)' }}>
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-lg)' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <button 
            onClick={() => navigate(-1)}
            style={{ 
              width: 40, height: 40, 
              border: '1px solid var(--border-color)', 
              background: 'var(--bg-elevated)',
              color: 'var(--text-primary)',
              borderRadius: '12px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Attendance Report
            </h1>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Monthly attendance overview
            </div>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          {/* Month Selector */}
          <input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{
              padding: '8px 12px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontSize: '0.875rem'
            }}
          />
          
          {/* View Toggle */}
          <div style={{ display: 'flex', background: 'var(--bg-card)', borderRadius: '8px', padding: '4px' }}>
            <button
              onClick={() => setView('matrix')}
              style={{
                padding: '8px 16px',
                background: view === 'matrix' ? 'var(--accent-orange)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: view === 'matrix' ? '#fff' : 'var(--text-muted)',
                fontWeight: 600,
                fontSize: '0.8125rem',
                cursor: 'pointer'
              }}
            >
              Grid View
            </button>
            <button
              onClick={() => setView('list')}
              style={{
                padding: '8px 16px',
                background: view === 'list' ? 'var(--accent-orange)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: view === 'list' ? '#fff' : 'var(--text-muted)',
                fontWeight: 600,
                fontSize: '0.8125rem',
                cursor: 'pointer'
              }}
            >
              List View
            </button>
          </div>

          {/* Export */}
          <button
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              fontWeight: 600,
              fontSize: '0.8125rem',
              cursor: 'pointer'
            }}
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </motion.div>

      {/* Content */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px', color: 'var(--text-muted)' }}>
          Loading...
        </div>
      ) : view === 'matrix' && summary ? (
        /* Matrix/Grid View - Excel-like */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            background: 'var(--bg-elevated)',
            borderRadius: '16px',
            border: '1px solid var(--border-color)',
            overflow: 'auto'
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-card)' }}>
                <th style={{ 
                  padding: '12px 16px', 
                  textAlign: 'left', 
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  borderBottom: '1px solid var(--border-color)',
                  position: 'sticky',
                  left: 0,
                  background: 'var(--bg-card)',
                  zIndex: 10
                }}>
                  Name
                </th>
                {summary.dates.map(date => (
                  <th 
                    key={date} 
                    style={{ 
                      padding: '12px 8px', 
                      textAlign: 'center',
                      fontWeight: 600,
                      color: 'var(--text-muted)',
                      borderBottom: '1px solid var(--border-color)',
                      minWidth: '40px'
                    }}
                  >
                    {new Date(date).getDate()}
                  </th>
                ))}
                <th style={{ 
                  padding: '12px 16px', 
                  textAlign: 'center',
                  fontWeight: 700,
                  color: 'var(--accent-green)',
                  borderBottom: '1px solid var(--border-color)'
                }}>
                  Total
                </th>
              </tr>
            </thead>
            <tbody>
              {summary.people.map(person => {
                const presentDays = summary.dates.filter(d => summary.matrix[person]?.[d]).length;
                return (
                  <tr key={person} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ 
                      padding: '12px 16px',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      position: 'sticky',
                      left: 0,
                      background: 'var(--bg-elevated)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ 
                          width: 28, height: 28, 
                          borderRadius: '50%', 
                          background: 'rgba(255, 107, 53, 0.1)',
                          color: 'var(--accent-orange)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>
                          <User size={14} />
                        </div>
                        {person}
                      </div>
                    </td>
                    {summary.dates.map(date => {
                      const present = summary.matrix[person]?.[date];
                      return (
                        <td 
                          key={date}
                          style={{ 
                            padding: '8px',
                            textAlign: 'center'
                          }}
                        >
                          <div style={{
                            width: 24, height: 24,
                            borderRadius: '6px',
                            background: present ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.1)',
                            color: present ? 'var(--accent-green)' : '#ef4444',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            margin: '0 auto',
                            fontSize: '0.75rem',
                            fontWeight: 700
                          }}>
                            {present ? '✓' : '—'}
                          </div>
                        </td>
                      );
                    })}
                    <td style={{ 
                      padding: '12px 16px',
                      textAlign: 'center',
                      fontWeight: 700,
                      color: 'var(--accent-green)'
                    }}>
                      {presentDays}/{summary.dates.length}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          
          {summary.people.length === 0 && (
            <div style={{ 
              padding: '48px', 
              textAlign: 'center', 
              color: 'var(--text-muted)' 
            }}>
              <Calendar size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
              <div>No attendance records for this month</div>
            </div>
          )}
        </motion.div>
      ) : (
        /* List View */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            background: 'var(--bg-elevated)',
            borderRadius: '16px',
            border: '1px solid var(--border-color)',
            overflow: 'hidden'
          }}
        >
          {/* Search */}
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8,
              padding: '10px 12px',
              background: 'var(--bg-card)',
              borderRadius: '8px',
              maxWidth: '300px'
            }}>
              <Search size={16} style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search by name..."
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem'
                }}
              />
            </div>
          </div>

          {/* Records Table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-card)' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: 'var(--text-muted)' }}>Name</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: 'var(--text-muted)' }}>Date</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: 'var(--text-muted)' }}>Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.map((record, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border-light)' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ 
                        width: 28, height: 28, 
                        borderRadius: '50%', 
                        background: 'rgba(34, 197, 94, 0.1)',
                        color: 'var(--accent-green)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center'
                      }}>
                        <User size={14} />
                      </div>
                      {record.name}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{record.date}</td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>{record.time}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredRecords.length === 0 && (
            <div style={{ 
              padding: '48px', 
              textAlign: 'center', 
              color: 'var(--text-muted)' 
            }}>
              <User size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
              <div>No attendance records found</div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

export default AttendanceReport;
