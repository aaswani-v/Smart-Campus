
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, Link } from 'react-router-dom'
import { User, Lock, Mail, School, ArrowRight } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [role, setRole] = useState<'student' | 'faculty'>('student')
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
        // Save simulated session
        if (role === 'student') {
            const randomNames = ["Emma Watson", "John Doe", "Alex Smith", "Sarah Connor", "Michael Scott"]
            const randomName = randomNames[Math.floor(Math.random() * randomNames.length)]
            localStorage.setItem('user_role', 'student')
            localStorage.setItem('user_name', randomName)
            window.location.href = '/student-dashboard'
        } else {
            localStorage.setItem('user_role', 'faculty')
            localStorage.setItem('user_name', 'Dr. Alan Turing')
            window.location.href = '/faculty-dashboard'
        }
    }, 1500)
  }

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      background: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Left Decoration Side */}
      <div style={{ 
          flex: 1, 
          background: 'linear-gradient(135deg, #3e6345 0%, #5a8262 100%)', 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          padding: '4rem',
          position: 'relative',
          overflow: 'hidden'
      }} className="hidden-mobile">
          <div style={{ position: 'relative', zIndex: 2 }}>
            <h1 style={{ fontSize: '3.5rem', fontWeight: 800, color: 'white', marginBottom: '1rem', lineHeight: 1.1 }}>
                Attendify<br/>Campus
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '1.2rem', maxWidth: '400px' }}>
                Join the future of campus management. AI-powered attendance tracking with face recognition and biometric security.
            </p>
          </div>
          
          {/* Decorative Circles */}
          <motion.div 
            animate={{ scale: [1, 1.1, 1], rotate: [0, 90, 0] }}
            transition={{ duration: 20, repeat: Infinity }}
            style={{ 
                position: 'absolute', top: -100, right: -100, 
                width: 400, height: 400, 
                borderRadius: '50%', 
                background: 'rgba(255,255,255,0.1)' 
            }} 
          />
          <motion.div 
            animate={{ y: [0, 20, 0] }}
            transition={{ duration: 5, repeat: Infinity }}
            style={{ 
                position: 'absolute', bottom: 50, left: 50, 
                width: 200, height: 200, 
                borderRadius: '50%', 
                background: 'rgba(255,255,255,0.1)' 
            }} 
          />
      </div>

      {/* Right Form Side */}
      <div style={{ 
          flex: 1, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          padding: '2rem'
      }}>
        <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            style={{ width: '100%', maxWidth: '420px' }}
        >
            <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
                <img src="/logo.png" alt="Attendify Logo" style={{ width: 80, height: 80, borderRadius: 16, marginBottom: '1rem' }} />
                <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Welcome Back</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Please enter your details to sign in.</p>
            </div>

            {/* Role Switcher */}
            <div style={{ 
                display: 'flex', 
                background: 'var(--bg-elevated)', 
                padding: '4px', 
                borderRadius: '8px',
                marginBottom: '2rem'
            }}>
                <button 
                    onClick={() => setRole('student')}
                    style={{
                        flex: 1,
                        padding: '10px',
                        border: 'none',
                        background: role === 'student' ? 'var(--bg-card)' : 'transparent',
                        color: role === 'student' ? 'var(--accent-primary)' : 'var(--text-secondary)',
                        fontWeight: 600,
                        borderRadius: '6px',
                        cursor: 'pointer',
                        boxShadow: role === 'student' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
                        transition: 'all 0.2s'
                    }}
                >
                    Student
                </button>
                <button 
                    onClick={() => setRole('faculty')}
                    style={{
                        flex: 1,
                        padding: '10px',
                        border: 'none',
                        background: role === 'faculty' ? 'var(--bg-card)' : 'transparent',
                        color: role === 'faculty' ? '#34d399' : 'var(--text-secondary)',
                        fontWeight: 600,
                        borderRadius: '6px',
                        cursor: 'pointer',
                        boxShadow: role === 'faculty' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
                        transition: 'all 0.2s'
                    }}
                >
                    Faculty
                </button>
            </div>

            <form onSubmit={handleLogin}>
                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Email Address</label>
                    <div style={{ position: 'relative' }}>
                        <Mail size={18} style={{ position: 'absolute', left: 12, top: 14, color: 'var(--text-muted)' }} />
                        <input 
                            type="email" 
                            required
                            placeholder={role === 'student' ? 'student@university.edu' : 'faculty@university.edu'}
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '12px 12px 12px 40px',
                                background: 'var(--bg-elevated)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)',
                                outline: 'none'
                            }}
                        />
                    </div>
                </div>

                <div style={{ marginBottom: '2rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Password</label>
                    <div style={{ position: 'relative' }}>
                        <Lock size={18} style={{ position: 'absolute', left: 12, top: 14, color: 'var(--text-muted)' }} />
                        <input 
                            type="password" 
                            required
                            placeholder="••••••••"
                            style={{
                                width: '100%',
                                padding: '12px 12px 12px 40px',
                                background: 'var(--bg-elevated)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)',
                                outline: 'none'
                            }}
                        />
                    </div>
                    <div style={{ textAlign: 'right', marginTop: '0.5rem' }}>
                        <a href="#" style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', textDecoration: 'none' }}>Forgot Password?</a>
                    </div>
                </div>

                <button 
                    type="submit"
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '14px',
                        background: role === 'student' ? 'var(--accent-primary)' : '#34d399',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        opacity: loading ? 0.7 : 1
                    }}
                >
                    {loading ? (
                        'Signing In...'
                    ) : (
                        <>Sign In <ArrowRight size={18} /></>
                    )}
                </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '2rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Don't have an account? <Link to="/signup" style={{ color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>Sign up for free</Link>
            </div>
        </motion.div>
      </div>

      <style>{`
        @media (max-width: 900px) {
            .hidden-mobile { display: none !important; }
        }
      `}</style>
    </div>
  )
}
