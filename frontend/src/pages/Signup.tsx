
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, Link } from 'react-router-dom'
import { User, Lock, Mail, School, Check, ArrowLeft } from 'lucide-react'

export default function Signup() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setTimeout(() => {
       setSuccess(true)
       setTimeout(() => {
           navigate('/')
       }, 2000)
    }, 1500)
  }

  if (success) {
      return (
          <div style={{ flex: 1, height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
              <motion.div 
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                style={{ textAlign: 'center' }}
              >
                  <div style={{ width: 80, height: 80, background: '#34d399', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', boxShadow: '0 10px 25px rgba(52, 211, 153, 0.4)' }}>
                      <Check size={40} color="white" strokeWidth={3} />
                  </div>
                  <h1 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Account Created!</h1>
                  <p style={{ color: 'var(--text-secondary)' }}>Redirecting you to login...</p>
              </motion.div>
          </div>
      )
  }

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      background: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Left Decoration Side (Darker for signup) */}
      <div style={{ 
          flex: 1, 
          background: 'linear-gradient(135deg, #2d3748 0%, #1a202c 100%)', 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          padding: '4rem',
          position: 'relative',
          overflow: 'hidden'
      }} className="hidden-mobile">
          <div style={{ position: 'relative', zIndex: 2 }}>
            <h1 style={{ fontSize: '3.5rem', fontWeight: 800, color: 'white', marginBottom: '1rem', lineHeight: 1.1 }}>
                Join<br/>Attendify
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.2rem', maxWidth: '400px' }}>
                Create your student or faculty profile to get started with the smart attendance ecosystem.
            </p>
          </div>
          
          {/* Decorative Circles */}
          <motion.div 
            animate={{ scale: [1, 1.2, 1], x: [0, 50, 0] }}
            transition={{ duration: 15, repeat: Infinity }}
            style={{ 
                position: 'absolute', top: 50, right: 50, 
                width: 300, height: 300, 
                borderRadius: '50%', 
                background: 'rgba(52, 211, 153, 0.1)' 
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
            <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--text-muted)', textDecoration: 'none', marginBottom: '2rem', fontSize: '0.9rem' }}>
                <ArrowLeft size={16} /> Back to Login
            </Link>

            <div style={{ marginBottom: '2rem' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>Create Account</h2>
                <p style={{ color: 'var(--text-secondary)' }}>Fill in your details to register.</p>
            </div>

            <form onSubmit={handleSignup}>
                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Full Name</label>
                    <div style={{ position: 'relative' }}>
                        <User size={18} style={{ position: 'absolute', left: 12, top: 14, color: 'var(--text-muted)' }} />
                        <input 
                            type="text" 
                            required
                            placeholder="John Doe"
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

                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>Email Address</label>
                    <div style={{ position: 'relative' }}>
                        <Mail size={18} style={{ position: 'absolute', left: 12, top: 14, color: 'var(--text-muted)' }} />
                        <input 
                            type="email" 
                            required
                            placeholder="you@university.edu"
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
                            placeholder="Create a strong password"
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

                <button 
                    type="submit"
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '14px',
                        background: 'var(--text-primary)',
                        color: 'var(--bg-primary)',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        opacity: loading ? 0.7 : 1
                    }}
                >
                    {loading ? 'Creating Account...' : 'Sign Up'}
                </button>
            </form>
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
