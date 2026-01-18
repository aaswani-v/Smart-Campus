import { useRef, useState, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Camera, CameraOff, CheckCircle, XCircle, Loader2, User } from 'lucide-react'
import { API_BASE } from '../config'

interface RecognitionResult {
  recognized: boolean
  student_id: string | null
  name: string
  confidence: number
  bbox: { x: number; y: number; w: number; h: number }
}

interface FaceRecognitionProps {
  sessionId?: string
  onRecognition?: (results: RecognitionResult[]) => void
  onCapture?: (frames: string[]) => void  // NEW: Pass captured frames to parent
  mode?: 'recognition' | 'enrollment'
}

export default function FaceRecognition({ sessionId, onRecognition, onCapture, mode = 'recognition' }: FaceRecognitionProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<RecognitionResult[]>([])
  const [capturedFrames, setCapturedFrames] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' } })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
        setIsStreaming(true)
        setError(null)
      }
    } catch (err) {
      setError('Camera access denied')
    }
  }, [])

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop())
      videoRef.current.srcObject = null
    }
    setIsStreaming(false)
  }, [])

  const captureFrame = useCallback((): string | null => {
    if (!videoRef.current || !canvasRef.current) return null
    const ctx = canvasRef.current.getContext('2d')
    if (!ctx) return null
    canvasRef.current.width = videoRef.current.videoWidth
    canvasRef.current.height = videoRef.current.videoHeight
    ctx.drawImage(videoRef.current, 0, 0)
    return canvasRef.current.toDataURL('image/jpeg', 0.8)
  }, [])

  const processFrame = useCallback(async () => {
    if (!isStreaming || isProcessing) return
    const frameData = captureFrame()
    if (!frameData) return
    setIsProcessing(true)
    try {
      // Call Python face recognition API
      const response = await fetch(`${API_BASE}/api/face-recognition/recognize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: frameData })
      })
      if (response.ok) {
        const data = await response.json()
        if (data.success && data.faces) {
          const mapped = data.faces.map((f: {x: number, y: number, w: number, h: number, student_id: string | null, name: string, confidence: number}) => ({
            recognized: f.student_id !== null,
            student_id: f.student_id,
            name: f.name,
            confidence: f.confidence,
            bbox: { x: f.x, y: f.y, w: f.w, h: f.h }
          }))
          setResults(mapped)
          onRecognition?.(mapped)
        }
      }
    } catch (err) {
      console.error('Python API error:', err)
    }
    setIsProcessing(false)
  }, [isStreaming, isProcessing, captureFrame, onRecognition])

  useEffect(() => {
    if (mode !== 'recognition' || !isStreaming) return
    const interval = setInterval(processFrame, 1500)
    return () => clearInterval(interval)
  }, [mode, isStreaming, processFrame])

  const captureForEnrollment = useCallback(() => {
    const frameData = captureFrame()
    if (frameData && capturedFrames.length < 5) {
      const newFrames = [...capturedFrames, frameData]
      setCapturedFrames(newFrames)
      onCapture?.(newFrames)  // Pass frames to parent
    }
  }, [captureFrame, capturedFrames, onCapture])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
      {/* Camera View */}
      <div style={{ position: 'relative', borderRadius: 'var(--radius-xl)', overflow: 'hidden', background: 'var(--bg-elevated)', aspectRatio: '4/3' }}>
        <video ref={videoRef} style={{ width: '100%', height: '100%', objectFit: 'cover', display: isStreaming ? 'block' : 'none', transform: 'scaleX(-1)' }} playsInline muted />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {!isStreaming && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <CameraOff size={36} style={{ marginBottom: 8 }} />
            <span style={{ fontSize: '0.875rem' }}>Camera off</span>
          </div>
        )}

        {isProcessing && (
          <div style={{ position: 'absolute', top: 12, right: 12, background: 'rgba(0,0,0,0.8)', borderRadius: 'var(--radius-pill)', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Loader2 size={14} className="animate-spin" style={{ color: 'var(--accent-orange)' }} />
            <span style={{ fontSize: '0.75rem' }}>Processing</span>
          </div>
        )}

        {isStreaming && (
          <div style={{ position: 'absolute', top: 12, left: 12, background: 'var(--accent-danger)', borderRadius: 'var(--radius-pill)', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', fontWeight: 600, zIndex: 10 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />
            LIVE
          </div>
        )}

        {/* Face Bounding Boxes */}
        {mode === 'recognition' && results.map((result, i) => {
          const videoWidth = videoRef.current?.videoWidth || 640
          const videoHeight = videoRef.current?.videoHeight || 480
          const clientWidth = videoRef.current?.clientWidth || 0
          const clientHeight = videoRef.current?.clientHeight || 0
          
          // Calculate visual coordinates for mirrored video
          // Logical X is from left, but visual is mirrored, so visual X = width - x - w
          const logicalX = result.bbox.x
          const featureWidth = result.bbox.w
          const visualX = videoWidth - logicalX - featureWidth
          
          return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${visualX * clientWidth / videoWidth}px`,
              top: `${result.bbox.y * clientHeight / videoHeight}px`,
              width: `${result.bbox.w * clientWidth / videoWidth}px`,
              height: `${result.bbox.h * clientHeight / videoHeight}px`,
              border: `2px solid ${result.recognized ? '#22c55e' : '#ef4444'}`,
              borderRadius: '4px',
              pointerEvents: 'none',
              zIndex: 5
            }}
          >
            <div style={{
              position: 'absolute',
              top: -24,
              left: 0,
              background: result.recognized ? '#22c55e' : '#ef4444',
              color: '#fff',
              fontSize: '12px',
              padding: '2px 6px',
              borderRadius: '4px',
              whiteSpace: 'nowrap'
            }}>
              {result.name}
            </div>
          </div>
        )})}
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 'var(--space-md)' }}>
        <button className={`btn ${isStreaming ? 'btn-danger' : 'btn-primary'}`} onClick={isStreaming ? stopCamera : startCamera} style={{ flex: 1 }}>
          {isStreaming ? <><CameraOff size={18} /> Stop</> : <><Camera size={18} /> Start Camera</>}
        </button>
        {mode === 'enrollment' && isStreaming && (
          <button className="btn btn-secondary" onClick={captureForEnrollment} disabled={capturedFrames.length >= 5}>
            Capture ({capturedFrames.length}/5)
          </button>
        )}
      </div>

      {/* Connection Indicator */}
      <div style={{ position: 'absolute', bottom: 12, right: 12, display: 'flex', gap: 6 }}>
           {isProcessing && <div style={{width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-orange)'}} />}
      </div>

      {error && <div style={{ padding: '8px 12px', background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)', borderRadius: 'var(--radius-md)', fontSize: '0.8125rem', color: 'var(--accent-danger)', textAlign: 'center' }}>{error} - Try restarting app</div>}

      {/* Results */}
      {mode === 'recognition' && results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          {results.map((result, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--space-sm) var(--space-md)', background: 'var(--bg-elevated)', border: `1px solid ${result.recognized ? 'rgba(163,230,53,0.2)' : 'rgba(248,113,113,0.2)'}`, borderRadius: 'var(--radius-xl)' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                <div className="avatar">{result.name.charAt(0)}</div>
                <div>
                  <div style={{ fontWeight: 500 }}>{result.name}</div>
                  {result.student_id && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{result.student_id}</div>}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                <span className={`badge ${result.recognized ? 'badge-success' : 'badge-danger'}`}>{Math.round(result.confidence)}%</span>
                {result.recognized ? <CheckCircle size={18} style={{ color: 'var(--accent-lime)' }} /> : <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Enrollment captures */}
      {mode === 'enrollment' && capturedFrames.length > 0 && (
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8 }}>Captured ({capturedFrames.length}/5)</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {capturedFrames.map((frame, i) => (
              <img key={i} src={frame} style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 'var(--radius-md)', border: '2px solid var(--accent-lime)' }} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
