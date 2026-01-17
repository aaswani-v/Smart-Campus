import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, User, Plus, Trash2, Megaphone, Calendar } from "lucide-react";
import "../index.css";

const initialNotices = [
    { id: 1, title: "Mid-Semester Exam Schedule", content: "The exams will commence from 15th April. Check your timetable.", date: "2024-03-20", author: "Dr. Alan Turing", urgency: "high" },
    { id: 2, title: "Hackathon Registration Open", content: "Register for the annual Smart Campus Hackathon by Friday!", date: "2024-03-22", author: "Student Council", urgency: "normal" }
];

export default function Notices() {
  const [notices, setNotices] = useState(initialNotices);
  const [role, setRole] = useState("student");
  
  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [isUrgent, setIsUrgent] = useState(false);
  const [isPosting, setIsPosting] = useState(false);

  useEffect(() => {
      const userRole = localStorage.getItem('user_role') || 'student';
      setRole(userRole);

      const saved = localStorage.getItem('campus_notices');
      if (saved) {
          setNotices(JSON.parse(saved));
      } else {
          localStorage.setItem('campus_notices', JSON.stringify(initialNotices));
      }

      // Live sync
      const interval = setInterval(() => {
          const current = localStorage.getItem('campus_notices');
          if(current && current !== JSON.stringify(notices)) {
              setNotices(JSON.parse(current));
          }
      }, 2000);
      return () => clearInterval(interval);
  }, []);

  const handlePost = () => {
      if(!newTitle || !newContent) return;
      
      const newNotice = {
          id: Date.now(),
          title: newTitle,
          content: newContent,
          date: new Date().toISOString().split('T')[0],
          author: localStorage.getItem('user_name') || "Faculty",
          urgency: isUrgent ? "high" : "normal"
      };

      const updated = [newNotice, ...notices];
      setNotices(updated);
      localStorage.setItem('campus_notices', JSON.stringify(updated));
      
      // Reset
      setNewTitle("");
      setNewContent("");
      setIsUrgent(false);
      setIsPosting(false);
  };

  const handleDelete = (id: number) => {
      if(role !== 'faculty') return;
      const updated = notices.filter(n => n.id !== id);
      setNotices(updated);
      localStorage.setItem('campus_notices', JSON.stringify(updated));
  }

  return (
    <div className="dashboard-container" style={{ maxWidth: 900, margin: '0 auto', paddingBottom: '2rem' }}>
      <header className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
           <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
               <Megaphone className="icon-pulse" color="var(--accent-primary)" /> Campus Notices
           </h1>
           <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Official announcements and updates.</p>
        </div>
        
        {role === 'faculty' && (
            <button className="btn-primary" onClick={() => setIsPosting(!isPosting)}>
                <Plus size={18} /> Post Notice
            </button>
        )}
      </header>

      {/* Post Form (Faculty Only) */}
      <AnimatePresence>
          {role === 'faculty' && isPosting && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                style={{ overflow: 'hidden', marginBottom: '2rem' }}
              >
                  <div className="card" style={{ padding: '1.5rem', background: 'var(--bg-elevated)', border: '1px solid var(--accent-primary)' }}>
                      <h3 style={{ marginTop: 0 }}>Create New Announcement</h3>
                      <div style={{ display: 'grid', gap: '1rem' }}>
                          <input 
                              placeholder="Notice Title" 
                              value={newTitle}
                              onChange={e => setNewTitle(e.target.value)}
                              style={{ padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
                          />
                          <textarea 
                              placeholder="Notice Content..." 
                              rows={3}
                              value={newContent}
                              onChange={e => setNewContent(e.target.value)}
                              style={{ padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontFamily: 'inherit' }}
                          />
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                                  <input type="checkbox" checked={isUrgent} onChange={e => setIsUrgent(e.target.checked)} />
                                  <span style={{ color: isUrgent ? '#ef4444' : 'var(--text-primary)', fontWeight: isUrgent ? 600 : 400 }}>Mark as High Priority</span>
                              </label>
                              <div style={{ display: 'flex', gap: '1rem' }}>
                                  <button className="btn-secondary" onClick={() => setIsPosting(false)}>Cancel</button>
                                  <button className="btn-primary" onClick={handlePost}>Post Announcement</button>
                              </div>
                          </div>
                      </div>
                  </div>
              </motion.div>
          )}
      </AnimatePresence>

      {/* Notices List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {notices.map((notice, index) => (
              <motion.div 
                  key={notice.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="card"
                  style={{ 
                      padding: '1.5rem', 
                      borderLeft: notice.urgency === 'high' ? '4px solid #ef4444' : '4px solid var(--accent-primary)',
                      position: 'relative' 
                  }}
              >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                          <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <Bell size={18} color={notice.urgency === 'high' ? '#ef4444' : 'var(--text-primary)'} />
                          </div>
                          <div>
                              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{notice.title}</h3>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <User size={12} /> {notice.author}
                                  <span>•</span>
                                  <Calendar size={12} /> {notice.date}
                              </div>
                          </div>
                      </div>
                      {notice.urgency === 'high' && (
                          <span className="badge" style={{ background: '#ef4444', color: 'white' }}>URGENT</span>
                      )}
                      
                      {role === 'faculty' && (
                          <button 
                              onClick={() => handleDelete(notice.id)}
                              style={{ position: 'absolute', right: '1.5rem', top: '1.5rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                              title="Delete Notice"
                          >
                              <Trash2 size={16} />
                          </button>
                      )}
                  </div>
                  
                  <p style={{ lineHeight: 1.6, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                      {notice.content}
                  </p>
              </motion.div>
          ))}
          
          {notices.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                  <p>No notices for now.</p>
              </div>
          )}
      </div>
    </div>
  );
}
