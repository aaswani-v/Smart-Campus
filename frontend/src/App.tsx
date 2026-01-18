import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Enroll from './pages/Enroll'
import Session from './pages/Session'
import Timetable from './pages/Timetable'
import Analytics from './pages/Analytics'
import FaceRecognition from './pages/FaceRecognition'
import Login from './pages/Login'
import Signup from './pages/Signup'
import StudentDashboard from './pages/StudentDashboard'
import FacultyDashboard from './pages/FacultyDashboard'
import StudentRecords from './pages/StudentRecords'
import StudyMaterials from './pages/StudyMaterials'
import Notices from './pages/Notices'
import AttendanceReport from './pages/AttendanceReport'

import { AnimatePresence, motion } from 'framer-motion'
import './index.css'

function AppRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<PageTransition><Login /></PageTransition>} />
        <Route path="/signup" element={<PageTransition><Signup /></PageTransition>} />
        
        {/* Protected Routes with Layout */}
        <Route path="/student-dashboard" element={<Layout><PageTransition><StudentDashboard /></PageTransition></Layout>} />
        <Route path="/faculty-dashboard" element={<Layout><PageTransition><FacultyDashboard /></PageTransition></Layout>} />
        <Route path="/home" element={<Layout><PageTransition><Home /></PageTransition></Layout>} />
        <Route path="/enroll" element={<Layout><PageTransition><Enroll /></PageTransition></Layout>} />
        <Route path="/session" element={<Layout><PageTransition><Session /></PageTransition></Layout>} />
        <Route path="/session/:sessionId" element={<Layout><PageTransition><Session /></PageTransition></Layout>} />
        <Route path="/timetable" element={<Layout><PageTransition><Timetable /></PageTransition></Layout>} />
        <Route path="/analytics" element={<Layout><PageTransition><Analytics /></PageTransition></Layout>} />
        <Route path="/face-recognition" element={<Layout><PageTransition><FaceRecognition /></PageTransition></Layout>} />
        <Route path="/records" element={<Layout><PageTransition><StudentRecords /></PageTransition></Layout>} />
        <Route path="/materials" element={<Layout><PageTransition><StudyMaterials /></PageTransition></Layout>} />
        <Route path="/notices" element={<Layout><PageTransition><Notices /></PageTransition></Layout>} />
        <Route path="/attendance-report" element={<Layout><PageTransition><AttendanceReport /></PageTransition></Layout>} />

      </Routes>
    </AnimatePresence>
  )
}

function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
    >
      {children}
    </motion.div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ThemeProvider>
  )
}
