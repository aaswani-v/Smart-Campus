import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FileText, Download, Search, BookOpen } from "lucide-react";
import "../index.css";

const initialMaterials = [
    { id: 1, title: "Lecture 1: Intro to AI", subject: "CS301", type: "PDF", size: "2.4 MB", date: "2024-03-10" },
    { id: 2, title: "Normalization Rules", subject: "CS302", type: "DOCX", size: "1.1 MB", date: "2024-03-12" },
    { id: 3, title: "TCP/IP Protocol Stack", subject: "CS303", type: "PDF", size: "3.5 MB", date: "2024-03-14" },
];

export default function StudyMaterials() {
  const [materials, setMaterials] = useState(initialMaterials);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
     // Sync materials from localStorage
     const saved = localStorage.getItem('shared_materials');
     if(saved) setMaterials(JSON.parse(saved));
     
     // Listen for updates slightly less frequently as it's a full page
     const interval = setInterval(() => {
         const current = localStorage.getItem('shared_materials');
         if(current && current !== JSON.stringify(materials)) {
             setMaterials(JSON.parse(current));
         }
     }, 2000);
     return () => clearInterval(interval);
  }, []);

  const filteredMaterials = materials.filter(m => 
      m.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
      m.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="dashboard-container" style={{ maxWidth: 1000, margin: '0 auto', paddingBottom: '2rem' }}>
      <header className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
           <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0 }}>Study Materials</h1>
           <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Access lecture notes, assignments, and reference documents.</p>
        </div>
        <div style={{ position: 'relative' }}>
            <Search className="search-icon" size={18} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input 
                type="text" 
                placeholder="Search notes..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                style={{ 
                    padding: '0.6rem 1rem 0.6rem 2.5rem', 
                    borderRadius: 'var(--radius-md)', 
                    border: '1px solid var(--border-color)', 
                    background: 'var(--bg-elevated)',
                    color: 'var(--text-primary)',
                    width: 250
                }}
            />
        </div>
      </header>

      {filteredMaterials.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
              <BookOpen size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
              <p>No materials found.</p>
          </div>
      ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
              {filteredMaterials.map((mat: any, i) => (
                  <motion.div 
                      key={mat.id} 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      whileHover={{ y: -5 }}
                      className="card" 
                      style={{ 
                          padding: '1.25rem', 
                          display: 'flex', 
                          flexDirection: 'column', 
                          gap: '1rem',
                          border: '1px solid var(--border-color)'
                      }}
                  >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div style={{ width: 40, height: 40, borderRadius: 8, background: 'rgba(34, 197, 94, 0.1)', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <FileText size={20} />
                          </div>
                          <span className="badge" style={{ fontSize: '0.7rem' }}>{mat.type}</span>
                      </div>
                      
                      <div style={{ flex: 1 }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.25rem', lineHeight: 1.3 }}>{mat.title}</h3>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {mat.subject} • {mat.size}
                          </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{mat.date}</span>
                          <button className="btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', gap: 6 }}>
                              <Download size={14} /> Download
                          </button>
                      </div>
                  </motion.div>
              ))}
          </div>
      )}
    </div>
  );
}
