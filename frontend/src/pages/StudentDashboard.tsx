
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Fingerprint,
  ScanFace,
  CheckCircle,
  FileWarning,
  ClipboardList,
  Megaphone,
  User
} from "lucide-react";
import "./FacultyDashboard.css"; // Reuse CSS

export default function StudentDashboard() {
  const [userName, setUserName] = useState("Student");
  const [notices, setNotices] = useState([]);
  const [showBiometric, setShowBiometric] = useState(false);
  const [bioStep, setBioStep] = useState(0);

  useEffect(() => {
     setUserName(localStorage.getItem('user_name') || "Student");
     
     // Sync Notices
     const savedNotices = localStorage.getItem('campus_notices');
     if(savedNotices) setNotices(JSON.parse(savedNotices));
     
     // Listen for updates
     const interval = setInterval(() => {
         const currentNotices = localStorage.getItem('campus_notices');
         if(currentNotices && currentNotices !== JSON.stringify(notices)) {
             setNotices(JSON.parse(currentNotices));
         }
     }, 1000);
     return () => clearInterval(interval);
  }, []);

  const handleDispute = () => {
    alert("Dispute Report Submitted Successfully (Ticket #9382)");
  };

  const startBioSim = () => {
    setBioStep(1);
    setTimeout(() => setBioStep(2), 2500);
  };

  return (
    <div className="dashboard-container">
      <header className="dash-header">
        <h1>Student Portal</h1>
        <div className="user-badge">{userName}</div>
      </header>

      <div className="dash-grid">
        
        {/* Attendance Score Card */}
        <motion.div className="dash-card">
            <h2>My Attendance</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', marginTop: '1rem' }}>
                <div style={{ position: 'relative', width: 100, height: 100 }}>
                    <svg viewBox="0 0 36 36">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#333" strokeWidth="4" />
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#34d399" strokeWidth="4" strokeDasharray="85, 100" />
                    </svg>
                    <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontWeight: 'bold' }}>85%</div>
                </div>
                <div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 600 }}>Good Standing</div>
                    <div style={{ color: 'var(--text-secondary)' }}>You are present in most classes.</div>
                </div>
            </div>
            <button className="btn-secondary" style={{ marginTop: '1.5rem', width: '100%', borderColor: '#ef4444', color: '#ef4444' }} onClick={handleDispute}>
                <FileWarning size={16} /> Raise Attendance Dispute
            </button>
        </motion.div>

        {/* Biometric Verification */}
        <motion.div className="dash-card">
            <h2><Fingerprint size={20}/> Biometric Access</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Verify your identity for exam entry.</p>
            
            {!showBiometric ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <button className="btn-secondary" onClick={() => { setShowBiometric(true); setBioStep(0); }}>
                        <Fingerprint size={24} style={{ marginBottom: 5 }} /> <br/> Touch ID
                    </button>
                    <button className="btn-secondary" onClick={() => { setShowBiometric(true); setBioStep(0); }}>
                        <ScanFace size={24} style={{ marginBottom: 5 }} /> <br/> Face ID
                    </button>
                </div>
            ) : (
                <div style={{ textAlign: 'center', padding: '1rem', background: 'var(--bg-elevated)', borderRadius: 8 }}>
                    {bioStep === 0 && (
                        <div onClick={startBioSim} style={{ cursor: 'pointer' }}>
                            <Fingerprint size={48} className="icon-pulse" color="#ff6b35" />
                            <p>Tap to Scan</p>
                        </div>
                    )}
                    {bioStep === 1 && (
                        <div>
                            <div className="radar-circle scanning" style={{ width: 80, height: 80, margin: '0 auto' }}></div>
                            <p>Verifying Identity...</p>
                        </div>
                    )}
                    {bioStep === 2 && (
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                            <CheckCircle size={48} color="#34d399" style={{ margin: '0 auto' }} />
                            <p style={{ color: '#34d399', fontWeight: 'bold' }}>Verified Successfully!</p>
                            <button className="btn-secondary" onClick={() => setShowBiometric(false)} style={{ marginTop: 10 }}>Done</button>
                        </motion.div>
                    )}
                </div>
            )}
        </motion.div>

        {/* Assignments Section */}
        <motion.div className="dash-card">
            <h2><ClipboardList size={20}/> Pending Assignments</h2>
            <div className="status-indicators">
                <div className="indicator" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>AI Theory Project</div>
                        <span style={{ fontSize: '0.75rem', color: '#ef4444' }}>Due: Tomorrow, 11:59 PM</span>
                    </div>
                    <button className="btn-secondary" style={{ fontSize: '0.75rem' }}>Submit</button>
                </div>
                <div className="indicator" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600 }}>Database Schema Design</div>
                        <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>Due: 3 Days left</span>
                    </div>
                     <button className="btn-secondary" style={{ fontSize: '0.75rem' }}>Submit</button>
                </div>
            </div>
        </motion.div>

        {/* Important Notices - Replaces Study Resources */}
        <div className="dash-card timetable-card" style={{ gridColumn: '1 / -1' }}>
            <div className="card-header-row">
                <h2><Megaphone size={20} className="icon-pulse" color="#ef4444" /> Important Updates</h2>
                <div style={{ display: 'flex', gap: '1rem' }}>
                     <span className="badge" style={{ background: '#ef4444', color: '#fff' }}>Priority</span>
                </div>
            </div>
            
            {notices.filter((n: any) => n.urgency === 'high').length === 0 ? (
                <p>No urgent notices at the moment.</p>
            ) : (
                <div className="timetable-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
                    {notices.filter((n: any) => n.urgency === 'high').slice(0, 3).map((notice: any) => (
                        <motion.div 
                            key={notice.id} 
                            whileHover={{ y: -5 }}
                            className="time-slot" 
                            style={{ 
                                display: 'flex', 
                                flexDirection: 'column', 
                                alignItems: 'flex-start',
                                background: 'var(--bg-elevated)',
                                borderRadius: '8px',
                                borderLeft: '4px solid #ef4444',
                                padding: '1rem'
                            }}
                        >
                            <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <div className="badge" style={{ background: '#ef444422', color: '#ef4444', fontWeight: 700 }}>URGENT</div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{notice.date}</span>
                            </div>
                            <h3 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>{notice.title}</h3>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.4 }}>
                                {notice.content.substring(0, 80)}...
                            </p>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                                <User size={12} /> {notice.author}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
             <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                <a href="/notices" className="btn-secondary" style={{ display: 'inline-flex', textDecoration: 'none' }}>View All Notices</a>
            </div>
        </div>

      </div>
    </div>
  );
}
