import { useState } from 'react'
import { motion } from 'framer-motion'
import { Fingerprint, CreditCard, CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface BiometricPanelProps {
  mode?: 'verify' | 'register'
}

export default function BiometricPanel({ mode = 'verify' }: BiometricPanelProps) {
  const [fingerprintStatus, setFingerprintStatus] = useState<'idle' | 'scanning' | 'success' | 'failed'>('idle')
  const [rfidStatus, setRfidStatus] = useState<'idle' | 'scanning' | 'success' | 'failed'>('idle')

  const scan = async (type: 'fingerprint' | 'rfid') => {
    const setStatus = type === 'fingerprint' ? setFingerprintStatus : setRfidStatus
    setStatus('scanning')
    await new Promise(r => setTimeout(r, type === 'fingerprint' ? 2000 : 1500))
    setStatus(Math.random() > 0.15 ? 'success' : 'failed')
  }

  const getColor = (status: string) => {
    if (status === 'success') return 'var(--accent-lime)'
    if (status === 'failed') return 'var(--accent-danger)'
    if (status === 'scanning') return 'var(--accent-orange)'
    return 'var(--text-muted)'
  }

  const getBorder = (status: string) => {
    if (status === 'success') return '1px solid rgba(163, 230, 53, 0.3)'
    if (status === 'failed') return '1px solid rgba(248, 113, 113, 0.3)'
    if (status === 'scanning') return '1px solid rgba(251, 146, 60, 0.3)'
    return '1px solid var(--border-color)'
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      <div>
        <h3 style={{ marginBottom: 4 }}>{mode === 'register' ? 'Register Biometrics' : 'Biometric Verification'}</h3>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Scan to {mode === 'register' ? 'register' : 'verify'}</p>
      </div>

      {/* Fingerprint */}
      <motion.div
        style={{ background: 'var(--bg-elevated)', border: getBorder(fingerprintStatus), borderRadius: 'var(--radius-xl)', padding: 'var(--space-md)' }}
        whileHover={{ scale: 1.01 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-pill)', background: fingerprintStatus === 'success' ? 'var(--accent-lime)' : 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Fingerprint size={24} style={{ color: fingerprintStatus === 'success' ? '#000' : 'var(--accent-lime)' }} />
            </div>
            <div>
              <div style={{ fontWeight: 500 }}>Fingerprint</div>
              <div style={{ fontSize: '0.75rem', color: getColor(fingerprintStatus) }}>
                {fingerprintStatus === 'idle' && 'Not scanned'}
                {fingerprintStatus === 'scanning' && 'Scanning...'}
                {fingerprintStatus === 'success' && 'Verified'}
                {fingerprintStatus === 'failed' && 'Failed'}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            {fingerprintStatus === 'scanning' && <Loader2 size={18} className="animate-spin" style={{ color: 'var(--accent-orange)' }} />}
            {fingerprintStatus === 'success' && <CheckCircle size={18} style={{ color: 'var(--accent-lime)' }} />}
            {fingerprintStatus === 'failed' && <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />}
            <button className={`btn ${fingerprintStatus === 'idle' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => scan('fingerprint')} disabled={fingerprintStatus === 'scanning'}>
              {fingerprintStatus === 'idle' ? 'Scan' : 'Retry'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* RFID */}
      <motion.div
        style={{ background: 'var(--bg-elevated)', border: getBorder(rfidStatus), borderRadius: 'var(--radius-xl)', padding: 'var(--space-md)' }}
        whileHover={{ scale: 1.01 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-pill)', background: rfidStatus === 'success' ? 'var(--accent-lime)' : 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CreditCard size={24} style={{ color: rfidStatus === 'success' ? '#000' : 'var(--accent-orange)' }} />
            </div>
            <div>
              <div style={{ fontWeight: 500 }}>RFID Card</div>
              <div style={{ fontSize: '0.75rem', color: getColor(rfidStatus) }}>
                {rfidStatus === 'idle' && 'Not tapped'}
                {rfidStatus === 'scanning' && 'Waiting...'}
                {rfidStatus === 'success' && 'Verified'}
                {rfidStatus === 'failed' && 'Not recognized'}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            {rfidStatus === 'scanning' && <Loader2 size={18} className="animate-spin" style={{ color: 'var(--accent-orange)' }} />}
            {rfidStatus === 'success' && <CheckCircle size={18} style={{ color: 'var(--accent-lime)' }} />}
            {rfidStatus === 'failed' && <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />}
            <button className={`btn ${rfidStatus === 'idle' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => scan('rfid')} disabled={rfidStatus === 'scanning'}>
              {rfidStatus === 'idle' ? 'Tap' : 'Retry'}
            </button>
          </div>
        </div>
      </motion.div>

      {/* Success Summary */}
      {(fingerprintStatus === 'success' || rfidStatus === 'success') && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ background: 'rgba(163, 230, 53, 0.1)', border: '1px solid rgba(163, 230, 53, 0.2)', borderRadius: 'var(--radius-xl)', padding: 'var(--space-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}
        >
          <CheckCircle size={20} style={{ color: 'var(--accent-lime)' }} />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--accent-lime)' }}>
              {fingerprintStatus === 'success' && rfidStatus === 'success' ? 'Full Verification' : 'Partial Verification'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {[fingerprintStatus === 'success' && 'Fingerprint', rfidStatus === 'success' && 'RFID'].filter(Boolean).join(' + ')}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
