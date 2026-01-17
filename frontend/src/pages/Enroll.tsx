import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, CheckCircle, Loader2, ArrowRight, ArrowLeft, MoreHorizontal, User } from 'lucide-react'
import FaceRecognition from '../components/FaceRecognition'
import BiometricPanel from '../components/BiometricPanel'

export default function Enroll() {
  const [step, setStep] = useState(1)
  const [studentData, setStudentData] = useState({ studentId: '', name: '', email: '', department: '', year: 1 })
  const [capturedPhotos, setCapturedPhotos] = useState<string[]>([])  // Changed to string[] for base64
  const [isEnrolling, setIsEnrolling] = useState(false)
  const [enrollError, setEnrollError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setStudentData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleEnroll = async () => {
    setIsEnrolling(true)
    setEnrollError(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/face-recognition/enroll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentData.studentId,
          name: studentData.name,
          images: capturedPhotos
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setStep(4)
      } else {
        setEnrollError(result.error || 'Enrollment failed')
      }
    } catch (error) {
      setEnrollError('Network error. Is the backend running?')
    }
    
    setIsEnrolling(false)
  }

  const reset = () => {
    setStudentData({ studentId: '', name: '', email: '', department: '', year: 1 })
    setCapturedPhotos([])
    setEnrollError(null)
    setStep(1)
  }

  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <motion.div 
        className="page-header"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="page-title">Enrollment</h1>
        <MoreHorizontal size={20} style={{ color: 'var(--text-muted)' }} />
      </motion.div>

      {/* Progress Steps */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        style={{ display: 'flex', gap: 6, marginBottom: 'var(--space-xl)' }}
      >
        {[1, 2, 3, 4].map(n => (
          <motion.div 
            key={n}
            animate={{ 
              background: step >= n ? 'var(--accent-primary)' : 'var(--border-color)',
              scale: step === n ? 1.1 : 1
            }}
            style={{ flex: 1, height: 4, borderRadius: 'var(--radius-pill)' }} 
          />
        ))}
      </motion.div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div 
            key="s1" 
            className="card"
            initial={{ opacity: 0, x: 20 }} 
            animate={{ opacity: 1, x: 0 }} 
            exit={{ opacity: 0, x: -20 }}
          >
            <div className="card-header"><span className="card-title">Student Information</span></div>
            <div className="grid grid-2" style={{ gap: 'var(--space-md)' }}>
              <div className="input-group"><label className="input-label">Student ID</label><input name="studentId" value={studentData.studentId} onChange={handleChange} className="input" placeholder="STU001" /></div>
              <div className="input-group"><label className="input-label">Full Name</label><input name="name" value={studentData.name} onChange={handleChange} className="input" placeholder="John Doe" /></div>
              <div className="input-group"><label className="input-label">Email</label><input name="email" type="email" value={studentData.email} onChange={handleChange} className="input" placeholder="john@uni.edu" /></div>
              <div className="input-group"><label className="input-label">Department</label><input name="department" value={studentData.department} onChange={handleChange} className="input" placeholder="Computer Science" /></div>
            </div>
            <div style={{ marginTop: 'var(--space-xl)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setStep(2)} disabled={!studentData.studentId || !studentData.name}>
                Continue <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div 
            key="s2" 
            className="card"
            initial={{ opacity: 0, x: 20 }} 
            animate={{ opacity: 1, x: 0 }} 
            exit={{ opacity: 0, x: -20 }}
          >
            <div className="card-header"><span className="card-title">Face Capture</span></div>
            <div className="grid grid-2" style={{ gap: 'var(--space-lg)' }}>
            <FaceRecognition mode="enrollment" onCapture={(frames) => setCapturedPhotos(frames)} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <motion.div 
                  onClick={() => fileInputRef.current?.click()}
                  whileHover={{ scale: 1.02, borderColor: 'var(--accent-primary)' }}
                  style={{ 
                    flex: 1, 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    background: 'var(--bg-elevated)', 
                    border: '2px dashed var(--border-color)', 
                    borderRadius: 'var(--radius-lg)', 
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <Upload size={28} style={{ color: 'var(--accent-primary)', marginBottom: 8 }} />
                  <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>Upload Photos</span>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>3-5 photos required</span>
                  <input ref={fileInputRef} type="file" accept="image/*" multiple style={{ display: 'none' }} onChange={async (e) => {
                    if (e.target.files) {
                      const files = Array.from(e.target.files)
                      const base64Promises = files.map(file => {
                        return new Promise<string>((resolve) => {
                          const reader = new FileReader()
                          reader.onloadend = () => resolve(reader.result as string)
                          reader.readAsDataURL(file)
                        })
                      })
                      const base64Images = await Promise.all(base64Promises)
                      setCapturedPhotos(prev => [...prev, ...base64Images].slice(0, 5))
                    }
                  }} />
                </motion.div>
                {capturedPhotos.length > 0 && (
                  <div style={{ display: 'flex', gap: 6 }}>
                    {capturedPhotos.map((_, i) => (
                      <motion.div 
                        key={i}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="avatar" 
                        style={{ width: 40, height: 40 }}
                      >
                        <User size={16} />
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div style={{ marginTop: 'var(--space-xl)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button className="btn btn-secondary" onClick={() => setStep(1)}><ArrowLeft size={16} /> Back</button>
              <button className="btn btn-primary" onClick={() => setStep(3)} disabled={capturedPhotos.length < 3}>Continue <ArrowRight size={16} /></button>
            </div>
            {enrollError && (
              <div style={{ marginTop: 'var(--space-md)', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--radius-md)', color: '#ef4444', fontSize: '0.875rem', textAlign: 'center' }}>
                {enrollError}
              </div>
            )}
          </motion.div>
        )}

        {step === 3 && (
          <motion.div 
            key="s3" 
            className="card"
            initial={{ opacity: 0, x: 20 }} 
            animate={{ opacity: 1, x: 0 }} 
            exit={{ opacity: 0, x: -20 }}
          >
            <BiometricPanel mode="register" />
            <div style={{ marginTop: 'var(--space-xl)', display: 'flex', justifyContent: 'space-between' }}>
              <button className="btn btn-secondary" onClick={() => setStep(2)}><ArrowLeft size={16} /> Back</button>
              <button className="btn btn-success btn-lg" onClick={handleEnroll} disabled={isEnrolling}>
                {isEnrolling ? <><Loader2 size={18} className="animate-spin" /> Enrolling...</> : <><CheckCircle size={18} /> Complete</>}
              </button>
            </div>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div 
            key="s4" 
            className="card"
            initial={{ opacity: 0, scale: 0.95 }} 
            animate={{ opacity: 1, scale: 1 }}
            style={{ textAlign: 'center', padding: 'var(--space-2xl)' }}
          >
            <motion.div 
              initial={{ scale: 0 }} 
              animate={{ scale: 1 }} 
              transition={{ type: 'spring', delay: 0.2 }}
              style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--accent-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto var(--space-lg)' }}
            >
              <CheckCircle size={28} color="#fff" />
            </motion.div>
            <h2 style={{ marginBottom: 8 }}>Successfully Enrolled!</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: 'var(--space-xl)' }}>
              {studentData.name} has been registered in the system.
            </p>
            <button className="btn btn-primary btn-lg" onClick={reset}>Enroll Another Student</button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
