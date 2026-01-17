
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Calendar,
  Clock,
  Radio,
  Plus,
  Monitor,
  FileText,
  Upload,
  Download,
  Trash2,
  Bell,
  Play,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import "./FacultyDashboard.css";

const subjects = [
    { code: "CS301", name: "Artificial Intelligence" },
    { code: "CS302", name: "Database Management" },
    { code: "CS303", name: "Computer Networks" },
    { code: "CS304", name: "Operating Systems" },
    { code: "CS305", name: "Software Engineering" },
    { code: "CS306", name: "Cyber Security" }
];

const initialMaterials = [
    { id: 1, title: "Lecture 1: Intro to AI", subject: "CS301", type: "PDF", size: "2.4 MB", date: "2024-03-10" },
    { id: 2, title: "Normalization Rules", subject: "CS302", type: "DOCX", size: "1.1 MB", date: "2024-03-12" },
    { id: 3, title: "TCP/IP Protocol Stack", subject: "CS303", type: "PDF", size: "3.5 MB", date: "2024-03-14" },
];

export default function FacultyDashboard() {
  const [isScanning, setIsScanning] = useState(false);
  const [attendanceCount, setAttendanceCount] = useState(0);
  const [scanProgress, setScanProgress] = useState(0);
  const [materials, setMaterials] = useState(initialMaterials);
  
  // Upload Form
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadSub, setUploadSub] = useState("CS301");

  // Classroom Tools State
  const [quizActive, setQuizActive] = useState(false);
  const [reminderInput, setReminderInput] = useState("");
  const [reminders, setReminders] = useState([
      { id: 1, text: "Check Assignment 3", date: "Today", urgent: true },
      { id: 2, text: "Submit Grading Report", date: "Tomorrow", urgent: false }
  ]);

  const startRadar = () => {
      setIsScanning(true);
      setScanProgress(0);
      setAttendanceCount(0);
      const interval = setInterval(() => {
          setScanProgress(prev => {
              if(prev >= 100) {
                  clearInterval(interval);
                  setIsScanning(false);
                  setAttendanceCount(Math.floor(Math.random() * (45 - 28 + 1)) + 28);
                  return 100;
              }
              return prev + 2;
          });
      }, 50);
  };

  useEffect(() => {
      // Load materials from storage or set initial
      const saved = localStorage.getItem('shared_materials');
      if (saved) {
          setMaterials(JSON.parse(saved));
      } else {
          localStorage.setItem('shared_materials', JSON.stringify(initialMaterials));
      }
  }, []);

  const handleUpload = () => {
      if(!uploadTitle) return;
      const newItem = {
          id: Date.now(),
          title: uploadTitle,
          subject: uploadSub,
          type: "PDF", // Mock type
          size: (Math.random() * (5 - 0.5) + 0.5).toFixed(1) + " MB",
          date: new Date().toISOString().split('T')[0]
      };
      const updated = [newItem, ...materials];
      setMaterials(updated);
      localStorage.setItem('shared_materials', JSON.stringify(updated));
      setUploadTitle("");
      alert("File Uploaded & Published to Students!");
  };

  const deleteMaterial = (id: number) => {
      const updated = materials.filter(m => m.id !== id);
      setMaterials(updated);
      localStorage.setItem('shared_materials', JSON.stringify(updated));
  }

  const addReminder = () => {
      if (!reminderInput) return;
      const newRem = { id: Date.now(), text: reminderInput, date: 'Today', urgent: false };
      setReminders([...reminders, newRem]);
      setReminderInput("");
  }

  return (
    <div className="dashboard-container">
      <header className="dash-header">
        <h1>Faculty Dashboard</h1>
        <div className="user-badge">Dr. Alan Turing</div>
      </header>

      <div className="dash-grid">
        {/* Radar Section */}
        <motion.div className="dash-card radar-card" layout>
            <h2><Radio className="icon-pulse" /> Live Attendance Radar</h2>
            <div className="radar-display">
                <div className={`radar-circle ${isScanning ? 'scanning' : ''}`}>
                    <div className="radar-sweep"></div>
                    <div className="radar-stat">
                        {isScanning ? (
                            <span className="scan-text">SCANNING... {scanProgress}%</span>
                        ) : (
                            <div className="stat-content">
                                <span className="stat-num">{attendanceCount}</span>
                                <span className="stat-label">Students Detected</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            <button className="btn-primary" onClick={startRadar} disabled={isScanning}>
                {isScanning ? "Scanning Area..." : "Start Radar Scan"}
            </button>
        </motion.div>

        {/* Classroom Management (New) */}
        <motion.div className="dash-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <h2><Monitor size={20} /> Classroom Tools</h2>
            
            {/* Host Quiz */}
            <div style={{ background: 'var(--bg-elevated)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Quick Quiz</h3>
                    {quizActive && <span className="badge" style={{ background: '#ef4444', color: '#fff' }}>LIVE</span>}
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>Host an instant pop-quiz for connected students.</p>
                <button 
                    className={`btn-primary ${quizActive ? 'active' : ''}`} 
                    onClick={() => setQuizActive(!quizActive)}
                    style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem', background: quizActive ? '#ef4444' : 'var(--accent-primary)' }}
                >
                    {quizActive ? <><Radio size={16} /> Stop Quiz session</> : <><Play size={16} /> Host New Quiz</>}
                </button>
            </div>

            {/* Reminders */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                     <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Reminders</h3>
                </div>
                <div className="form-row" style={{ marginBottom: '1rem' }}>
                    <input 
                        placeholder="Add task (e.g. Check Assignments)" 
                        value={reminderInput}
                        onChange={(e) => setReminderInput(e.target.value)}
                        style={{ fontSize: '0.8rem' }}
                    />
                    <button className="btn-secondary" onClick={addReminder} style={{ padding: '0.5rem' }}><Plus size={16}/></button>
                </div>
                <div className="reminder-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
                    {reminders.map(r => (
                        <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)' }}>
                            <Bell size={14} color={r.urgent ? '#ef4444' : 'var(--text-secondary)'} />
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '0.8rem', fontWeight: 500 }}>{r.text}</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{r.date}</div>
                            </div>
                            <button onClick={() => setReminders(reminders.filter(x => x.id !== r.id))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-success)' }}>
                                <CheckCircle size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>

        {/* Course Materials Manager */}
        <motion.div className="dash-card timetable-card" style={{ gridColumn: 'span 2' }}>
            <div className="card-header-row">
                <h2><FileText /> Course Materials</h2>
                <span className="badge">Synced</span>
            </div>
            
            <div className="add-schedule-form" style={{ marginBottom: '1.5rem' }}>
                <h3>Upload New Material</h3>
                <div className="form-row">
                    <select value={uploadSub} onChange={e => setUploadSub(e.target.value)}>
                        {subjects.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
                    </select>
                    <input 
                        type="text" 
                        placeholder="Document Title (e.g. Lecture Notes 5)" 
                        value={uploadTitle} 
                        onChange={e => setUploadTitle(e.target.value)} 
                        style={{ flex: 2 }}
                    />
                </div>
                <button className="btn-secondary" onClick={handleUpload}>
                    <Upload size={16}/> Upload PDF
                </button>
            </div>

            <div className="materials-list">
                {materials.map(mat => (
                    <div key={mat.id} className="time-slot">
                        <div className="time-col">
                            <FileText size={16} /> 
                            <div>
                                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{mat.title}</div>
                                <div style={{ fontSize: '0.75em' }}>{mat.subject} • {mat.size} • {mat.date}</div>
                            </div>
                        </div>
                        <button className="btn-icon" onClick={() => deleteMaterial(mat.id)} style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#ef4444' }}>
                            <Trash2 size={16} />
                        </button>
                    </div>
                ))}
            </div>
        </motion.div>
      </div>
    </div>
  );
}
