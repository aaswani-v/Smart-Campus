import { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import { ArrowLeft, User, UserPlus, X, Camera, Check, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
// @ts-ignore
import { FaceDetection } from '@mediapipe/face_detection';
// @ts-ignore
import { Camera as MediaPipeCamera } from '@mediapipe/camera_utils';

interface DetectedFace {
  bbox: { x: number; y: number; w: number; h: number };
  name: string;
  confidence: number;
  recognized: boolean;
  student_id: string | null;
}

export function FaceRecognition() {
  const navigate = useNavigate();
  const webcamRef = useRef<Webcam>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [detectedFaces, setDetectedFaces] = useState<DetectedFace[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const lastSentTime = useRef<number>(0);
  const RECOGNITION_INTERVAL = 500;

  // Enrollment State
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollName, setEnrollName] = useState('');
  const [enrollId, setEnrollId] = useState('');
  const [capturedFrames, setCapturedFrames] = useState<string[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [enrollStatus, setEnrollStatus] = useState<'idle' | 'capturing' | 'submitting' | 'success' | 'error'>('idle');
  const [enrollMessage, setEnrollMessage] = useState('');
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Capture frames for enrollment
  const captureFrames = useCallback(async () => {
    if (!webcamRef.current) return;
    
    setIsCapturing(true);
    setEnrollStatus('capturing');
    setEnrollMessage('Look at the camera... capturing 5 photos');
    
    const frames: string[] = [];
    
    for (let i = 0; i < 5; i++) {
      await new Promise(resolve => setTimeout(resolve, 600)); // Wait 600ms between captures
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
      const response = await fetch('http://localhost:8000/api/face-recognition/enroll', {
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

  // Initialize WebSocket for Recognition Only
  useEffect(() => {
    ws.current = new WebSocket('ws://localhost:8000/api/face-recognition/ws');
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.faces && data.faces.length > 0) {
        setDetectedFaces(data.faces); 
      }
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  // Initialize MediaPipe - waits for camera to be ready
  useEffect(() => {
    if (!cameraReady || !webcamRef.current?.video) {
      return;
    }

    const faceDetection = new FaceDetection({
      locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`
    });

    faceDetection.setOptions({
      model: 'short',
      minDetectionConfidence: 0.5
    });

    faceDetection.onResults((results: any) => {
        const videoWidth = webcamRef.current?.video?.videoWidth;
        const videoHeight = webcamRef.current?.video?.videoHeight;
        const canvas = canvasRef.current;
        
        if (canvas && videoWidth && videoHeight && results.detections) {
            canvas.width = videoWidth;
            canvas.height = videoHeight;
            const ctx = canvas.getContext('2d');
            
            if (ctx) {
                ctx.clearRect(0, 0, videoWidth, videoHeight);
                
                results.detections.forEach((detection: any) => {
                    const bbox = detection.boundingBox;
                    const x = bbox.xCenter * videoWidth - (bbox.width * videoWidth) / 2;
                    const y = bbox.yCenter * videoHeight - (bbox.height * videoHeight) / 2;
                    const w = bbox.width * videoWidth;
                    const h = bbox.height * videoHeight;

                    ctx.strokeStyle = '#22c55e';
                    ctx.lineWidth = 3;
                    ctx.strokeRect(x, y, w, h);
                });
            }
        }

        const now = Date.now();
        if (results.detections.length > 0 && now - lastSentTime.current > RECOGNITION_INTERVAL) {
             if (webcamRef.current && ws.current && ws.current.readyState === WebSocket.OPEN) {
                const imageSrc = webcamRef.current.getScreenshot();
                if (imageSrc) {
                    ws.current.send(JSON.stringify({ image: imageSrc }));
                    lastSentTime.current = now;
                }
             }
        }
    });

    const camera = new MediaPipeCamera(webcamRef.current.video, {
        onFrame: async () => {
            if (webcamRef.current?.video) {
                await faceDetection.send({image: webcamRef.current.video});
            }
        },
        width: 640,
        height: 480
    });
    camera.start();
    
    return () => {
      camera.stop();
    };
  }, [cameraReady]);

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
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)', boxShadow: '0 0 8px var(--accent-green)' }}></div>
                    Client-Side AI Active
                </div>
            </div>
        </div>

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
              {/* Modal Header */}
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

              {/* Form */}
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

              {/* Captured Frames Preview */}
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

              {/* Status Message */}
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

              {/* Action Buttons */}
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
                videoConstraints={{ width: 640, height: 480, facingMode: "user" }}
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
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }}
            />
            
            {detectedFaces.map((face, i) => (
                 <div
                    key={i}
                    style={{
                        position: 'absolute',
                        left: `${face.bbox.x}px`, 
                        top: `${face.bbox.y - 40}px`,
                        transform: 'translateX(0)',
                        background: 'rgba(0,0,0,0.8)',
                        backdropFilter: 'blur(8px)',
                        padding: '6px 16px',
                        borderRadius: '20px',
                        border: `1px solid ${face.recognized ? 'var(--accent-green)' : 'var(--accent-orange)'}`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        whiteSpace: 'nowrap',
                        zIndex: 30
                    }}
                 >
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: face.recognized ? 'var(--accent-green)' : 'var(--accent-orange)' }}></div>
                    <span style={{ color: '#fff', fontSize: '0.875rem', fontWeight: 600 }}>{face.name}</span>
                    <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: 8, marginLeft: 4 }}>
                        {Math.round(face.confidence)}%
                    </span>
                 </div>
            ))}
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
                    Attendance Metrics
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                     <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '16px', border: '1px solid var(--border-light)' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1, marginBottom: 4 }}>
                            {detectedFaces.length}
                        </div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Visible</div>
                     </div>
                     <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: '16px', border: '1px solid var(--border-light)' }}>
                        <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', lineHeight: 1, marginBottom: 4 }}>
                            {detectedFaces.filter(f => f.recognized).length}
                        </div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Marked</div>
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
                        Attendance Log
                    </div>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
                    {detectedFaces.length === 0 ? (
                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', opacity: 0.5, textAlign: 'center' }}>
                            <User size={32} strokeWidth={1.5} style={{ marginBottom: 12, opacity: 0.5 }} />
                            <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>No Attendance to Mark</div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {detectedFaces.map((face, i) => (
                                <motion.div 
                                    key={i}
                                    style={{ padding: '12px 16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: '12px' }}
                                >
                                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: face.recognized ? 'rgba(34, 197, 94, 0.1)' : 'rgba(255, 107, 53, 0.1)', color: face.recognized ? 'var(--accent-green)' : 'var(--accent-orange)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <User size={16} />
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>{face.name}</div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {face.recognized ? 'Marked Present' : 'Unknown ID'}
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
    </div>
  );
}
export default FaceRecognition;

