import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface RadarPoint {
  student_id: string
  name: string
  angle: number
  radius: number
  attention: number
  is_drowsy: boolean
  is_distracted: boolean
}

interface RadarViewProps {
  points: RadarPoint[]
  sessionActive?: boolean
}

export default function RadarView({ points, sessionActive = true }: RadarViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [sweepAngle, setSweepAngle] = useState(0)
  const [hoveredPoint, setHoveredPoint] = useState<RadarPoint | null>(null)

  useEffect(() => {
    if (!sessionActive) return
    const interval = setInterval(() => {
      setSweepAngle(prev => (prev + 1.5) % 360)
    }, 50)
    return () => clearInterval(interval)
  }, [sessionActive])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const size = canvas.width
    const center = size / 2
    const maxRadius = size / 2 - 24

    ctx.clearRect(0, 0, size, size)

    // Draw concentric circles
    ctx.strokeStyle = 'rgba(163, 230, 53, 0.08)'
    ctx.lineWidth = 1
    for (let i = 1; i <= 4; i++) {
      ctx.beginPath()
      ctx.arc(center, center, maxRadius * (i / 4), 0, Math.PI * 2)
      ctx.stroke()
    }

    // Draw cross lines
    ctx.strokeStyle = 'rgba(163, 230, 53, 0.05)'
    ctx.beginPath()
    ctx.moveTo(center, 24)
    ctx.lineTo(center, size - 24)
    ctx.moveTo(24, center)
    ctx.lineTo(size - 24, center)
    ctx.stroke()

    // Draw sweep line
    if (sessionActive) {
      const sweepRad = (sweepAngle * Math.PI) / 180
      const gradient = ctx.createLinearGradient(
        center, center,
        center + Math.cos(sweepRad) * maxRadius,
        center + Math.sin(sweepRad) * maxRadius
      )
      gradient.addColorStop(0, 'rgba(163, 230, 53, 0)')
      gradient.addColorStop(1, 'rgba(163, 230, 53, 0.6)')

      ctx.beginPath()
      ctx.moveTo(center, center)
      ctx.lineTo(
        center + Math.cos(sweepRad) * maxRadius,
        center + Math.sin(sweepRad) * maxRadius
      )
      ctx.strokeStyle = gradient
      ctx.lineWidth = 2
      ctx.stroke()
    }
  }, [sweepAngle, sessionActive])

  const getPointColor = (attention: number, isDrowsy: boolean, isDistracted: boolean) => {
    if (isDrowsy) return '#52525b'
    if (isDistracted || attention < 60) return '#fb923c'
    return '#a3e635'
  }

  const polarToCartesian = (angle: number, radius: number, size: number) => {
    const rad = (angle * Math.PI) / 180
    const center = size / 2
    const maxR = size / 2 - 32
    return {
      x: center + Math.cos(rad) * radius * maxR,
      y: center + Math.sin(rad) * radius * maxR
    }
  }

  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '1', maxWidth: 280, margin: '0 auto' }}>
      <canvas
        ref={canvasRef}
        width={280}
        height={280}
        style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-xl)', background: 'var(--bg-elevated)' }}
      />

      {/* Student Points */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {points.map((point) => {
          const pos = polarToCartesian(point.angle, point.radius, 280)
          const color = getPointColor(point.attention, point.is_drowsy, point.is_distracted)
          return (
            <motion.div
              key={point.student_id}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              style={{
                position: 'absolute',
                left: `${(pos.x / 280) * 100}%`,
                top: `${(pos.y / 280) * 100}%`,
                transform: 'translate(-50%, -50%)',
                pointerEvents: 'auto',
                cursor: 'pointer'
              }}
              onMouseEnter={() => setHoveredPoint(point)}
              onMouseLeave={() => setHoveredPoint(null)}
            >
              <motion.div
                animate={{ boxShadow: [`0 0 0 0 ${color}40`, `0 0 0 6px transparent`] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: color,
                  border: '2px solid rgba(0,0,0,0.5)'
                }}
              />
            </motion.div>
          )
        })}
      </div>

      {/* Tooltip */}
      <AnimatePresence>
        {hoveredPoint && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'absolute',
              bottom: 8,
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 12px',
              fontSize: '0.75rem',
              whiteSpace: 'nowrap',
              zIndex: 10
            }}
          >
            <div style={{ fontWeight: 600 }}>{hoveredPoint.name}</div>
            <div style={{ color: getPointColor(hoveredPoint.attention, hoveredPoint.is_drowsy, hoveredPoint.is_distracted) }}>
              {hoveredPoint.attention}% attention
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Center */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: 'var(--accent-lime)',
        boxShadow: '0 0 8px var(--accent-lime)'
      }} />
    </div>
  )
}
