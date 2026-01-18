import { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { ArrowLeft, User, UserPlus, X, Camera, Check, Loader2, FileSpreadsheet } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import faceRecognitionService from '../services/FaceRecognitionService';
import { API_BASE } from '../config';

interface DetectedFace {
  name: string;
  confidence: number;
  box: { x: number; y: number; width: number; height: number };
  recognized: boolean;
}

export function FaceRecognition() {
  const navigate = useNavigate();
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [detectedFaces, setDetectedFaces] = useState<DetectedFace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState('Initializing...');
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [videoConstraints, setVideoConstraints] = useState<MediaTrackConstraints>({ facingMode: 'user' });
  
  // Attendance tracking - debounce to avoid duplicate marks
  const markedAttendance = useRef<Set<string>>(new Set());
  const [attendanceLog, setAttendanceLog] = useState<{name: string; time: string}[]>([]);

  // Enumerate available cameras on mount
  useEffect(() => {
    const setupCamera = async () => {
      try {
        // First, request permission
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop()); // Stop immediately, we just needed permission
        
        // Now enumerate devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        console.log('[Camera] Found video devices:', videoDevices);
        
        if (videoDevices.length > 0) {
          // Use the first available device
          setVideoConstraints({ 
            deviceId: { exact: videoDevices[0].deviceId },
            width: { ideal: 640 },
            height: { ideal: 480 }
          });
        } else {
          setCameraError('No camera devices found on this system.');
        }
      } catch (err) {
        console.error('[Camera] Setup error:', err);
        // Fallback to basic constraints
        setVideoConstraints({ facingMode: 'user' });
      }
    };
    setupCamera();
  }, []);

  // Enrollment State
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollName, setEnrollName] = useState('');
  const [enrollId, setEnrollId] = useState('');
  const [capturedFrames, setCapturedFrames] = useState<string[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [enrollStatus, setEnrollStatus] = useState<'idle' | 'capturing' | 'submitting' | 'success' | 'error'>('idle');
  const [enrollMessage, setEnrollMessage] = useState('');

  // Initialize face-api.js service
  useEffect(() => {
    const initService = async () => {
      try {
        setLoadingStatus('Loading AI models...');
        await faceRecognitionService.loadModels();
        
        setLoadingStatus('Loading face database...');
        await faceRecognitionService.loadFaceDatabase();
        
        setIsLoading(false);
        setLoadingStatus('Ready!');
      } catch (error) {
        console.error('Failed to initialize face service:', error);
        setLoadingStatus('Failed to load. Check console.');
      }
    };
    initService();
  }, []);

  // Detection loop - runs when camera is ready and service is loaded
  useEffect(() => {
    if (!cameraReady || isLoading || !webcamRef.current?.video) return;
    
    let animationId: number;
    let lastDetectionTime = 0;
    const DETECTION_INTERVAL = 300; // ms between detections
    
    const detectLoop = async (timestamp: number) => {
      if (timestamp - lastDetectionTime > DETECTION_INTERVAL) {
        lastDetectionTime = timestamp;
        
        if (webcamRef.current?.video && faceRecognitionService.isReady()) {
          setIsDetecting(true);
          
          try {
            const matches = await faceRecognitionService.detectFaces(webcamRef.current.video);
            
            // Convert to our format and draw
            const faces: DetectedFace[] = matches.map(m => ({
              name: m.name,
              confidence: Math.round((1 - m.distance) * 100),
              box: m.box,
              recognized: m.name !== 'Unknown'
            }));
            
            setDetectedFaces(faces);
            drawDetections(faces);
            
            // Mark attendance for recognized faces (debounced)
            for (const face of faces) {
              if (face.recognized && !markedAttendance.current.has(face.name)) {
                markedAttendance.current.add(face.name);
                const success = await faceRecognitionService.markAttendance(face.name);
                if (success) {
                  setAttendanceLog(prev => [...prev, { 
                    name: face.name, 
                    time: new Date().toLocaleTimeString() 
                  }]);
                }
              }
            }
          } catch (e) {
            console.error('Detection error:', e);
          }
          
          setIsDetecting(false);
        }
      }
      
      animationId = requestAnimationFrame(detectLoop);
    };
    
    animationId = requestAnimationFrame(detectLoop);
    
    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [cameraReady, isLoading]);

  // Draw bounding boxes on canvas
  const drawDetections = (faces: DetectedFace[]) => {
    const canvas = canvasRef.current;
    const video = webcamRef.current?.video;
    if (!canvas || !video) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    faces.forEach(face => {
      const { x, y, width, height } = face.box;
      
      // Draw box
      ctx.strokeStyle = face.recognized ? '#22c55e' : '#ff6b35';
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);
      
      // Draw label background
      const label = `${face.name} (${face.confidence}%)`;
      ctx.font = 'bold 14px Inter, sans-serif';
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(x, y - 28, textWidth + 16, 24);
      
      // Draw label text
      ctx.fillStyle = '#fff';
      ctx.fillText(label, x + 8, y - 10);
    });
  };

  // Capture frames for enrollment
  const captureFrames = useCallback(async () => {
    if (!webcamRef.current) return;
    
    setIsCapturing(true);
    setEnrollStatus('capturing');
    setEnrollMessage('Look at the camera... capturing 5 photos');
    
    const frames: string[] = [];
    
    for (let i = 0; i < 5; i++) {
      await new Promise(resolve => setTimeout(resolve, 600));
      const imageSrc = webcamRef.current?.getScreenshot();
      if (imageSrc) {
        frames.push(imageSrc);
        setCapturedFrames([...frames]);
      }
    }
    
    setIsCapturing(false);
    setCapturedFrames(frames);
    setEnrollStatus('idle');
    setEnrollMessage(`Captured ${frames.length} photos. Click "Enroll" to save.`);
  }, []);

  // Submit enrollment
  const submitEnrollment = useCallback(async () => {
    if (capturedFrames.length < 3) {
      setEnrollMessage('Need at least 3 photos. Please capture again.');
      return;
    }
    
    if (!enrollName.trim() || !enrollId.trim()) {
      setEnrollMessage('Please enter both Name and Student ID.');
      return;
    }
    
    setEnrollStatus('submitting');
    setEnrollMessage('Enrolling...');
    
    try {
      const response = await fetch(`${API_BASE}/api/face-recognition/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: enrollId.trim(),
          name: enrollName.trim(),
          images: capturedFrames
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setEnrollStatus('success');
        setEnrollMessage(`✅ Enrolled "${enrollName}" successfully!`);
        setTimeout(() => {
          setShowEnrollModal(false);
          resetEnrollment();
        }, 2000);
      } else {
        setEnrollStatus('error');
        setEnrollMessage(`❌ ${result.error || 'Enrollment failed'}`);
      }
    } catch (error) {
      setEnrollStatus('error');
      setEnrollMessage('❌ Network error. Is the backend running?');
    }
  }, [capturedFrames, enrollName, enrollId]);

  const resetEnrollment = () => {
    setEnrollName('');
    setEnrollId('');
    setCapturedFrames([]);
    setEnrollStatus('idle');
    setEnrollMessage('');
  };

  return (
    <div style={{ padding: 'var(--space-md) var(--space-lg)', height: 'calc(100vh - 80px)', display: 'flex', flexDirection: 'column', maxWidth: '100vw', margin: '0', overflow: 'hidden', boxSizing: 'border-box' }}>
      
      {/* Header */}
      <motion.div 
        className="page-header"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 'var(--space-sm)', flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <button 
                onClick={() => navigate('/')}
                className="card-menu"
                style={{ 
                    width: 40, height: 40, 
                    border: '1px solid var(--border-color)', 
                    background: 'var(--bg-elevated)',
                    color: 'var(--text-primary)',
                    borderRadius: '12px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer'
                }}
            >
                <ArrowLeft size={20} />
            </button>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2, color: 'var(--text-primary)' }}>
                    Facial Recognition
                </h1>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ 
                      width: 6, height: 6, borderRadius: '50%', 
                      background: isLoading ? 'var(--accent-orange)' : faceRecognitionService.isReady() ? 'var(--accent-green)' : 'var(--text-muted)', 
                      boxShadow: isLoading ? '0 0 8px var(--accent-orange)' : faceRecognitionService.isReady() ? '0 0 8px var(--accent-green)' : 'none',
                      animation: isLoading ? 'pulse 1s infinite' : 'none'
                    }}></div>
                    {isLoading ? loadingStatus : `face-api.js • ${faceRecognitionService.getEnrolledPeople().length} enrolled`}
                </div>
            </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          {/* Attendance Report Link */}
          <Link
            to="/attendance-report"
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 20px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              color: 'var(--text-primary)',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
              textDecoration: 'none'
            }}
          >
            <FileSpreadsheet size={18} />
            Attendance Report
          </Link>
          
          {/* Enroll Button */}
          <button
            onClick={() => setShowEnrollModal(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 20px',
              background: 'linear-gradient(135deg, var(--accent-orange), #e85d04)',
              border: 'none',
              borderRadius: '12px',
              color: '#fff',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(255, 107, 53, 0.3)'
            }}
          >
            <UserPlus size={18} />
            Enroll Face
          </button>
        </div>
      </motion.div>

      {/* Enrollment Modal */}
      <AnimatePresence>
        {showEnrollModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              top: 0, left: 0, right: 0, bottom: 0,
              background: 'rgba(0,0,0,0.8)',
              backdropFilter: 'blur(8px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              zIndex: 1000
            }}
            onClick={() => { setShowEnrollModal(false); resetEnrollment(); }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--bg-elevated)',
                borderRadius: '24px',
                padding: '32px',
                width: '450px',
                border: '1px solid var(--border-color)',
                boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Enroll New Face
                </h2>
                <button
                  onClick={() => { setShowEnrollModal(false); resetEnrollment(); }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                >
                  <X size={20} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', display: 'block' }}>
                    Student ID
                  </label>
                  <input
                    type="text"
                    value={enrollId}
                    onChange={(e) => setEnrollId(e.target.value)}
                    placeholder="e.g. STU001"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.9375rem',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', display: 'block' }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={enrollName}
                    onChange={(e) => setEnrollName(e.target.value)}
                    placeholder="e.g. John Doe"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.9375rem',
                      outline: 'none',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              {capturedFrames.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
                    Captured Photos ({capturedFrames.length}/5)
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {capturedFrames.map((frame, i) => (
                      <img 
                        key={i} 
                        src={frame} 
                        alt={`Capture ${i+1}`}
                        style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: '8px', border: '2px solid var(--accent-green)' }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {enrollMessage && (
                <div style={{ 
                  padding: '12px 16px', 
                  background: enrollStatus === 'success' ? 'rgba(34, 197, 94, 0.1)' : enrollStatus === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-card)',
                  borderRadius: '12px',
                  marginBottom: '16px',
                  fontSize: '0.875rem',
                  color: enrollStatus === 'success' ? 'var(--accent-green)' : enrollStatus === 'error' ? '#ef4444' : 'var(--text-secondary)'
                }}>
                  {enrollMessage}
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={captureFrames}
                  disabled={isCapturing || enrollStatus === 'submitting'}
                  style={{
                    flex: 1,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '14px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    cursor: isCapturing ? 'not-allowed' : 'pointer',
                    opacity: isCapturing ? 0.6 : 1
                  }}
                >
                  {isCapturing ? <Loader2 size={18} className="animate-spin" /> : <Camera size={18} />}
                  {isCapturing ? 'Capturing...' : 'Capture Photos'}
                </button>
                <button
                  onClick={submitEnrollment}
                  disabled={capturedFrames.length < 3 || enrollStatus === 'submitting' || !enrollName || !enrollId}
                  style={{
                    flex: 1,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                    padding: '14px',
                    background: capturedFrames.length >= 3 ? 'linear-gradient(135deg, var(--accent-green), #16a34a)' : 'var(--bg-card)',
                    border: 'none',
                    borderRadius: '12px',
                    color: capturedFrames.length >= 3 ? '#fff' : 'var(--text-muted)',
                    fontWeight: 600,
                    cursor: capturedFrames.length >= 3 ? 'pointer' : 'not-allowed',
                    opacity: capturedFrames.length >= 3 ? 1 : 0.5
                  }}
                >
                  {enrollStatus === 'submitting' ? <Loader2 size={18} /> : <Check size={18} />}
                  Enroll
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading Overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(8px)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          zIndex: 50
        }}>
          <Loader2 size={48} style={{ color: 'var(--accent-orange)', animation: 'spin 1s linear infinite' }} />
          <div style={{ marginTop: 16, color: 'var(--text-primary)', fontWeight: 600 }}>{loadingStatus}</div>
        </div>
      )}

      {/* Main Content Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 'var(--space-lg)', flex: 1, minHeight: 0 }}>
        
        {/* Camera Feed */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          style={{ 
            position: 'relative',
            background: '#000',
            borderRadius: '24px',
            overflow: 'hidden',
            border: '1px solid var(--border-color)',
            boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}
        >
            {cameraError ? (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ef4444',
                textAlign: 'center',
                padding: '40px'
              }}>
                <Camera size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
                  Camera Access Failed
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', maxWidth: '300px' }}>
                  {cameraError}
                </div>
                <button
                  onClick={() => { setCameraError(null); setCameraReady(false); }}
                  style={{
                    marginTop: '16px',
                    padding: '10px 20px',
                    background: 'var(--accent-orange)',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Retry
                </button>
              </div>
            ) : (
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={videoConstraints}
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                onUserMedia={() => {
                  console.log('Camera ready!');
                  setCameraReady(true);
                }}
                onUserMediaError={(err) => {
                  console.error('Camera error:', err);
                  setCameraError(err instanceof Error ? err.message : 'Could not access camera. Please check permissions.');
                }}
              />
            )}
            <canvas 
                ref={canvasRef}
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain', pointerEvents: 'none' }}
            />
            
            {/* Detection indicator */}
            {isDetecting && (
              <div style={{
                position: 'absolute',
                top: 16, right: 16,
                padding: '6px 12px',
                background: 'rgba(0,0,0,0.6)',
                borderRadius: '20px',
                display: 'flex', alignItems: 'center', gap: 6,
                fontSize: '0.75rem',
                color: 'var(--accent-green)'
              }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)', animation: 'pulse 1s infinite' }}></div>
                Detecting...
              </div>
            )}
        </motion.div>

        {/* Info Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', overflow: 'hidden' }}>
            <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                style={{ background: 'var(--bg-elevated)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-lg)' }}
            >
                <div style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: '16px' }}>
                    Live Detection
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                     <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '16px', border: '1px solid var(--border-light)' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1, marginBottom: 4 }}>
                            {detectedFaces.length}
                        </div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Faces</div>
                     </div>
                     <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '16px', border: '1px solid var(--border-light)' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', lineHeight: 1, marginBottom: 4 }}>
                            {detectedFaces.filter(f => f.recognized).length}
                        </div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Recognized</div>
                     </div>
                </div>
            </motion.div>

            <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                style={{ flex: 1, background: 'var(--bg-elevated)', borderRadius: '20px', padding: '24px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', color: 'var(--text-muted)' }}>
                        Session Attendance ({attendanceLog.length})
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
                    {attendanceLog.length === 0 ? (
                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', opacity: 0.5, textAlign: 'center' }}>
                            <User size={32} strokeWidth={1.5} style={{ marginBottom: 12, opacity: 0.5 }} />
                            <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>No attendance marked yet</div>
                            <div style={{ fontSize: '0.75rem', marginTop: 4 }}>Face the camera to mark attendance</div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {attendanceLog.map((entry, i) => (
                                <motion.div 
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    style={{ padding: '12px 16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: '12px' }}
                                >
                                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(34, 197, 94, 0.1)', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Check size={16} />
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{entry.name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            Marked at {entry.time}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

export default FaceRecognition;
