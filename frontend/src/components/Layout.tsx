
import { ReactNode, useLayoutEffect, useRef, useState, useEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Sun, Moon, User, LogOut, Mail } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { motion, AnimatePresence } from 'framer-motion'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { theme, toggleTheme } = useTheme()
  const navRef = useRef<HTMLDivElement | null>(null)
  const indicatorRef = useRef<HTMLDivElement | null>(null)
  const location = useLocation()
  const navigate = useNavigate()
  
  // Profile Menu State
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const profileRef = useRef<HTMLDivElement | null>(null)

  // Handle click outside to close menu
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [profileRef]);

  const handleSignOut = () => {
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    navigate('/');
  }

  // Profile Logic
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [requestSent, setRequestSent] = useState(false);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);

  useEffect(() => {
    // Sync Requests
    const syncRequests = () => {
        const stored = localStorage.getItem('profile_requests');
        if(stored) setPendingRequests(JSON.parse(stored));
    };
    syncRequests();
    
    // Polling for live updates
    const interval = setInterval(syncRequests, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleProfileUpdate = (newName: string) => {
      if(!newName) return;
      
      const newRequest = {
          id: Date.now(),
          oldName: localStorage.getItem('user_name') || 'Student',
          newName: newName,
          status: 'pending'
      };
      
      const updatedRequests = [...pendingRequests, newRequest];
      localStorage.setItem('profile_requests', JSON.stringify(updatedRequests));
      setPendingRequests(updatedRequests); // Optimistic update
      
      setRequestSent(true);
      setIsEditingProfile(false);
      setTimeout(() => setRequestSent(false), 5000); // Reset badge after 5s
  }

  const handleApprove = (id: number, newName: string) => {
      // 1. Remove request
      const updated = pendingRequests.filter(r => r.id !== id);
      setPendingRequests(updated);
      localStorage.setItem('profile_requests', JSON.stringify(updated));
      
      // 2. Mock Database Update (Simulated by updating localStorage if it was this user)
      // in a real app, this would happen on the server. here we just simulate it.
      // We will assume the Faculty is approving strictly for demo purposes.
      alert(`Approved change to "${newName}"`);
  }

  const handleReject = (id: number) => {
       const updated = pendingRequests.filter(r => r.id !== id);
       setPendingRequests(updated);
       localStorage.setItem('profile_requests', JSON.stringify(updated));
  }

  const handleContact = () => {
      alert("Opening Faculty Support Ticket #2938...");
      setShowProfileMenu(false);
  }

  useLayoutEffect(() => {
    const nav = navRef.current
    const indicator = indicatorRef.current
    if (!nav || !indicator) return

    const active = nav.querySelector('.nav-link.active') as HTMLElement | null
    if (active) {
      const navRect = nav.getBoundingClientRect()
      const rect = active.getBoundingClientRect()
      const left = rect.left - navRect.left + nav.scrollLeft
      indicator.style.width = `${rect.width}px`
      indicator.style.transform = `translateX(${left}px)`
      indicator.style.opacity = '1'
    } else {
      indicator.style.opacity = '0'
      indicator.style.width = '0px'
    }

    const handleResize = () => {
      const act = nav.querySelector('.nav-link.active') as HTMLElement | null
      if (act) {
        const navRect = nav.getBoundingClientRect()
        const rect = act.getBoundingClientRect()
        const left = rect.left - navRect.left + nav.scrollLeft
        indicator.style.width = `${rect.width}px`
        indicator.style.transform = `translateX(${left}px)`
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [location.pathname])

  return (
    <>
      {/* Header */}
      <header className="header">
        {/* Logo */}
        <div className="header-logo">
          <img src="/logo.png" alt="Logo" style={{ width: 40, height: 40, borderRadius: 8 }} />
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>ATTENDIFY</span>
        </div>

        {/* Navigation */}
        <nav className="nav" ref={navRef}>
          {localStorage.getItem('user_role') === 'faculty' ? (
            <>
              <NavLink to="/home" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Overview
              </NavLink>
              <NavLink to="/faculty-dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Dashboard
              </NavLink>
              <NavLink to="/session" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                 Monitor
              </NavLink>
              <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Analytics
              </NavLink>
              <NavLink to="/notices" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Notices
              </NavLink>
            </>
          ) : (
            <>
              <NavLink to="/student-dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Dashboard
              </NavLink>
              <NavLink to="/records" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                 My Records
              </NavLink>
              <NavLink to="/materials" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                 Study Notes
              </NavLink>
              <NavLink to="/notices" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                Notices
              </NavLink>
            </>
          )}
          <div ref={indicatorRef} className="nav-indicator" aria-hidden="true" />
        </nav>

        {/* Right Section */}
        <div className="header-right">
          <button className="header-icon" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className="user-avatar" ref={profileRef} onClick={() => setShowProfileMenu(!showProfileMenu)}>
            <div className="user-avatar-inner">
                <User size={24} color="var(--text-primary)" />
            </div>
            {/* Pop-up Menu */}
            <AnimatePresence>
                {showProfileMenu && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.1 }}
                        style={{
                            position: 'absolute',
                            top: '120%',
                            right: 0,
                            width: 320,
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-color)',
                            borderRadius: 12,
                            boxShadow: 'var(--shadow-lg)',
                            padding: '1rem',
                            zIndex: 1000,
                            overflow: 'hidden'
                        }}
                    >
                        {/* Profile Header */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--accent-primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem', fontWeight: 600 }}>
                                {localStorage.getItem('user_name')?.charAt(0) || 'U'}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontWeight: 700, fontSize: '1rem' }}>{localStorage.getItem('user_name') || 'Guest User'}</div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                    {localStorage.getItem('user_role') || 'User'}
                                </div>
                            </div>
                        </div>

                        {/* Student Details & Edit */}
                        {localStorage.getItem('user_role') !== 'faculty' && (
                            <div style={{ marginBottom: '1rem' }}>
                                {!isEditingProfile ? (
                                    <>
                                        <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Roll No:</span> <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>CS21B1038</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Class:</span> <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>CS-A</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Email:</span> <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>ash@student.edu</span>
                                            </div>
                                        </div>
                                        
                                        {requestSent ? (
                                            <div className="badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', width: '100%', justifyContent: 'center', padding: '0.5rem' }}>
                                                Profile Update Pending Approval
                                            </div>
                                        ) : (
                                            <button 
                                                onClick={() => setIsEditingProfile(true)}
                                                className="btn-secondary" 
                                                style={{ width: '100%', fontSize: '0.8rem', padding: '0.5rem' }}
                                            >
                                                Edit Profile Details
                                            </button>
                                        )}
                                    </>
                                ) : (
                                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                                        <input 
                                            placeholder="Full Name"
                                            defaultValue={localStorage.getItem('user_name') || ''}
                                            id="edit-name"
                                            style={{ padding: '0.5rem', width: '100%', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: '0.85rem' }}
                                        />
                                        <input 
                                            placeholder="Email Address"
                                            defaultValue="ash@student.edu"
                                            style={{ padding: '0.5rem', width: '100%', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: '0.85rem' }}
                                        />
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button 
                                                onClick={() => setIsEditingProfile(false)}
                                                style={{ flex: 1, padding: '0.5rem', background: 'none', border: '1px solid var(--border-color)', borderRadius: 6, cursor: 'pointer', fontSize: '0.8rem' }}
                                            >
                                                Cancel
                                            </button>
                                            <button 
                                                onClick={() => {
                                                    const newName = (document.getElementById('edit-name') as HTMLInputElement).value;
                                                    handleProfileUpdate(newName);
                                                }}
                                                style={{ flex: 1, padding: '0.5rem', background: 'var(--accent-primary)', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: '0.8rem' }}
                                            >
                                                Save Request
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Faculty Details & Approvals */}
                        {localStorage.getItem('user_role') === 'faculty' && (
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ display: 'grid', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span>Faculty ID:</span> <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>FAC-992</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span>Department:</span> <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Computer Science</span>
                                    </div>
                                </div>

                                {pendingRequests.length > 0 ? (
                                    <div style={{ background: 'var(--bg-elevated)', borderRadius: 8, padding: '0.75rem' }}>
                                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444' }} />
                                            Pending Approvals ({pendingRequests.length})
                                        </div>
                                        {pendingRequests.map((req: any) => (
                                            <div key={req.id} style={{ marginBottom: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                                                <div style={{ fontSize: '0.8rem' }}>
                                                    <span style={{ fontWeight: 600 }}>{req.oldName}</span> wants to change name to <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{req.newName}</span>
                                                </div>
                                                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                                    <button 
                                                        onClick={() => handleApprove(req.id, req.newName)}
                                                        style={{ padding: '2px 8px', fontSize: '0.7rem', background: '#22c55e', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                                                    >
                                                        Approve
                                                    </button>
                                                    <button 
                                                        onClick={() => handleReject(req.id)}
                                                        style={{ padding: '2px 8px', fontSize: '0.7rem', background: '#ef4444', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                                                    >
                                                        Reject
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0.5rem', background: 'var(--bg-elevated)', borderRadius: 6 }}>
                                        No pending requests
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Actions */}
                        <div style={{ paddingTop: '0.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                             <button onClick={handleContact} style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', borderRadius: 6, color: 'var(--text-primary)', fontSize: '0.85rem' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'} onMouseLeave={(e) => e.currentTarget.style.background = 'none'}>
                                <Mail size={16} /> Contact Support
                            </button>
                            <button onClick={handleSignOut} style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', borderRadius: 6, color: '#ef4444', fontSize: '0.85rem' }} onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-elevated)'} onMouseLeave={(e) => e.currentTarget.style.background = 'none'}>
                                <LogOut size={16} /> Sign Out
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {children}
      </main>
    </>
  )
}
