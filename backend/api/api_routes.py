"""
Smart Campus - API Routes
RESTful API endpoints for the attendance system
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import json
import base64
import cv2
import numpy as np

from models.database import (
    get_db, Student, Course, TimetableSlot, 
    AttendanceSession, AttendanceRecord, AttentionLog, SystemLog
)
from services.face_recognition import get_face_service
from services.biometric import get_biometric_service
from services.attention import get_attention_tracker

router = APIRouter()


# ============= STUDENT ENDPOINTS =============

@router.post("/students/enroll")
async def enroll_student(
    student_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(None),
    department: str = Form(None),
    year: int = Form(None),
    photos: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Enroll a new student with face photos
    Requires at least 3 photos for reliable recognition
    """
    face_service = get_face_service()
    bio_service = get_biometric_service()
    
    # Check if student already exists
    existing = db.query(Student).filter(Student.student_id == student_id).first()
    if existing:
        raise HTTPException(400, f"Student {student_id} already enrolled")
    
    # Read and decode images
    images = []
    for photo in photos:
        contents = await photo.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            images.append(img)
    
    if len(images) < 3:
        raise HTTPException(400, "Need at least 3 valid photos")
    
    # Enroll face
    result = face_service.enroll_student(student_id, name, images)
    
    if not result['success']:
        raise HTTPException(400, result.get('error', 'Enrollment failed'))
    
    # Generate biometric data
    fp_result = bio_service.register_fingerprint(student_id)
    rfid_result = bio_service.register_rfid(student_id)
    
    # Save to database
    student = Student(
        student_id=student_id,
        name=name,
        email=email,
        department=department,
        year=year,
        fingerprint_hash=fp_result['fingerprint_hash'],
        rfid_tag=rfid_result['rfid_tag'],
        face_encoding_path=f"data/faces/{student_id}"
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return {
        "success": True,
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "faces_enrolled": result['faces_enrolled']
        },
        "biometrics": {
            "fingerprint_registered": True,
            "rfid_tag": rfid_result['rfid_tag']
        }
    }


@router.get("/students")
async def list_students(db: Session = Depends(get_db)):
    """List all enrolled students"""
    students = db.query(Student).filter(Student.is_active == True).all()
    
    return {
        "count": len(students),
        "students": [
            {
                "id": s.id,
                "student_id": s.student_id,
                "name": s.name,
                "department": s.department,
                "year": s.year,
                "enrolled_at": s.enrollment_date.isoformat() if s.enrollment_date else None
            }
            for s in students
        ]
    }


@router.get("/students/{student_id}")
async def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get student details"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")
    
    # Get attendance stats
    total_sessions = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id
    ).count()
    
    present_sessions = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        AttendanceRecord.is_valid == True
    ).count()
    
    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "department": student.department,
            "year": student.year
        },
        "attendance": {
            "total_sessions": total_sessions,
            "present": present_sessions,
            "percentage": round(present_sessions / total_sessions * 100, 1) if total_sessions > 0 else 0
        }
    }


# ============= COURSE ENDPOINTS =============

@router.post("/courses")
async def create_course(
    course_code: str = Form(...),
    name: str = Form(...),
    department: str = Form(None),
    credits: int = Form(3),
    faculty_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    existing = db.query(Course).filter(Course.course_code == course_code).first()
    if existing:
        raise HTTPException(400, f"Course {course_code} already exists")
    
    course = Course(
        course_code=course_code,
        name=name,
        department=department,
        credits=credits,
        faculty_name=faculty_name
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    
    return {"success": True, "course": {"id": course.id, "code": course.course_code, "name": course.name}}


@router.get("/courses")
async def list_courses(db: Session = Depends(get_db)):
    """List all courses"""
    courses = db.query(Course).all()
    
    return {
        "count": len(courses),
        "courses": [
            {
                "id": c.id,
                "code": c.course_code,
                "name": c.name,
                "department": c.department,
                "faculty": c.faculty_name
            }
            for c in courses
        ]
    }


# ============= TIMETABLE ENDPOINTS =============

@router.post("/timetable/slots")
async def create_timetable_slot(
    course_id: int = Form(...),
    day_of_week: int = Form(...),  # 0=Monday
    start_time: str = Form(...),  # HH:MM
    end_time: str = Form(...),
    room: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a timetable slot"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    
    slot = TimetableSlot(
        course_id=course_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        room=room
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    return {"success": True, "slot_id": slot.id}


@router.get("/timetable")
async def get_timetable(db: Session = Depends(get_db)):
    """Get full timetable"""
    slots = db.query(TimetableSlot).all()
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return {
        "slots": [
            {
                "id": s.id,
                "course": {
                    "id": s.course.id,
                    "code": s.course.course_code,
                    "name": s.course.name
                } if s.course else None,
                "day": days[s.day_of_week],
                "day_index": s.day_of_week,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "room": s.room
            }
            for s in slots
        ]
    }


# ============= SESSION ENDPOINTS =============

@router.post("/sessions/start")
async def start_session(
    course_id: int = Form(...),
    room: str = Form(...),
    db: Session = Depends(get_db)
):
    """Start a new attendance session"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    
    session_uuid = str(uuid.uuid4())
    
    session = AttendanceSession(
        session_id=session_uuid,
        course_id=course_id,
        room=room,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "success": True,
        "session": {
            "id": session.id,
            "session_id": session.session_id,
            "course": course.course_code,
            "room": room,
            "started_at": session.start_time.isoformat()
        }
    }


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str, db: Session = Depends(get_db)):
    """End an active session"""
    session = db.query(AttendanceSession).filter(
        AttendanceSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    session.is_active = False
    session.end_time = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "session_id": session_id,
        "ended_at": session.end_time.isoformat(),
        "total_present": session.present_count
    }


@router.get("/sessions/active")
async def get_active_sessions(db: Session = Depends(get_db)):
    """Get all currently active sessions"""
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.is_active == True
    ).all()
    
    return {
        "count": len(sessions),
        "sessions": [
            {
                "id": s.id,
                "session_id": s.session_id,
                "course": s.course.course_code if s.course else None,
                "room": s.room,
                "started_at": s.start_time.isoformat(),
                "present_count": s.present_count
            }
            for s in sessions
        ]
    }


# ============= ATTENDANCE ENDPOINTS =============

@router.post("/attendance/mark")
async def mark_attendance(
    session_id: str = Form(...),
    image_base64: str = Form(None),
    fingerprint_hash: str = Form(None),
    rfid_tag: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Mark attendance using multi-factor verification
    Requires face recognition + at least one of: fingerprint or RFID
    """
    session = db.query(AttendanceSession).filter(
        AttendanceSession.session_id == session_id,
        AttendanceSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, "Active session not found")
    
    face_service = get_face_service()
    bio_service = get_biometric_service()
    
    results = []
    
    # Process face recognition if image provided
    if image_base64:
        image = face_service.decode_base64_image(image_base64)
        recognitions = face_service.recognize_face(image)
        
        for rec in recognitions:
            if not rec['recognized']:
                continue
            
            student = db.query(Student).filter(
                Student.student_id == rec['student_id']
            ).first()
            
            if not student:
                continue
            
            # Check if already marked
            existing = db.query(AttendanceRecord).filter(
                AttendanceRecord.session_id == session.id,
                AttendanceRecord.student_id == student.id
            ).first()
            
            if existing:
                results.append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "status": "already_marked",
                    "marked_at": existing.marked_at.isoformat()
                })
                continue
            
            # Multi-factor verification
            mf_result = bio_service.multi_factor_verify(
                student_id=student.student_id,
                face_verified=True,
                face_confidence=rec['confidence'],
                fingerprint_hash=fingerprint_hash,
                stored_fingerprint=student.fingerprint_hash,
                rfid_tag=rfid_tag,
                stored_rfid=student.rfid_tag
            )
            
            # Create attendance record
            record = AttendanceRecord(
                session_id=session.id,
                student_id=student.id,
                face_verified=True,
                face_confidence=rec['confidence'],
                fingerprint_verified=any(
                    f['method'] == 'fingerprint' and f['verified'] 
                    for f in mf_result['factors']
                ),
                rfid_verified=any(
                    f['method'] == 'rfid' and f['verified'] 
                    for f in mf_result['factors']
                ),
                factors_passed=mf_result['factors_passed'],
                is_valid=mf_result['is_valid']
            )
            db.add(record)
            
            if mf_result['is_valid']:
                session.present_count += 1
            
            db.commit()
            
            results.append({
                "student_id": student.student_id,
                "name": student.name,
                "status": "marked" if mf_result['is_valid'] else "failed",
                "factors_passed": mf_result['factors_passed'],
                "face_confidence": rec['confidence'],
                "is_valid": mf_result['is_valid']
            })
    
    return {
        "session_id": session_id,
        "processed": len(results),
        "results": results
    }


@router.post("/attendance/recognize")
async def recognize_faces(
    image_base64: str = Form(...),
):
    """
    Recognize faces in an image without marking attendance
    Used for preview/testing
    """
    face_service = get_face_service()
    
    try:
        image = face_service.decode_base64_image(image_base64)
        results = face_service.recognize_face(image)
        
        return {
            "faces_detected": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(400, f"Image processing error: {str(e)}")


@router.get("/attendance/session/{session_id}")
async def get_session_attendance(session_id: str, db: Session = Depends(get_db)):
    """Get attendance records for a session"""
    session = db.query(AttendanceSession).filter(
        AttendanceSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id
    ).all()
    
    return {
        "session": {
            "id": session.session_id,
            "course": session.course.course_code if session.course else None,
            "room": session.room,
            "started_at": session.start_time.isoformat(),
            "is_active": session.is_active
        },
        "attendance": [
            {
                "student_id": r.student.student_id,
                "name": r.student.name,
                "marked_at": r.marked_at.isoformat(),
                "face_confidence": r.face_confidence,
                "factors_passed": r.factors_passed,
                "is_valid": r.is_valid
            }
            for r in records
        ],
        "summary": {
            "total": len(records),
            "valid": sum(1 for r in records if r.is_valid),
            "invalid": sum(1 for r in records if not r.is_valid)
        }
    }


# ============= ATTENTION ENDPOINTS =============

@router.post("/attention/analyze")
async def analyze_attention(
    session_id: str = Form(...),
    image_base64: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Analyze attention from a classroom frame
    """
    session = db.query(AttendanceSession).filter(
        AttendanceSession.session_id == session_id,
        AttendanceSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(404, "Active session not found")
    
    face_service = get_face_service()
    attention_tracker = get_attention_tracker()
    
    # Decode image
    image = face_service.decode_base64_image(image_base64)
    
    # Get attention metrics
    metrics = attention_tracker.analyze_frame(image)
    
    # Match with recognized students
    recognitions = face_service.recognize_face(image)
    
    results = []
    for i, m in enumerate(metrics):
        student_id = None
        student_name = "Unknown"
        
        # Try to match with recognition results
        if i < len(recognitions) and recognitions[i]['recognized']:
            student_id = recognitions[i]['student_id']
            student_name = recognitions[i]['name']
            
            # Save to database
            student = db.query(Student).filter(
                Student.student_id == student_id
            ).first()
            
            if student:
                log = AttentionLog(
                    session_id=session.id,
                    student_id=student.id,
                    attention_score=m.attention_score,
                    head_yaw=m.head_yaw,
                    head_pitch=m.head_pitch,
                    head_roll=m.head_roll,
                    eye_aspect_ratio=m.avg_ear,
                    is_drowsy=m.is_drowsy,
                    is_distracted=m.is_distracted,
                    gaze_direction=m.gaze_direction
                )
                db.add(log)
        
        results.append({
            "student_id": student_id,
            "name": student_name,
            "attention_score": m.attention_score,
            "head_pose": {
                "yaw": m.head_yaw,
                "pitch": m.head_pitch,
                "roll": m.head_roll
            },
            "eye_aspect_ratio": m.avg_ear,
            "is_drowsy": m.is_drowsy,
            "is_distracted": m.is_distracted,
            "gaze": m.gaze_direction
        })
    
    db.commit()
    
    # Calculate class summary
    class_metrics = attention_tracker.get_class_attention(metrics)
    
    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "individual": results,
        "class_summary": class_metrics
    }


# ============= ANALYTICS ENDPOINTS =============

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(db: Session = Depends(get_db)):
    """Get dashboard analytics data"""
    # Total stats
    total_students = db.query(Student).filter(Student.is_active == True).count()
    total_courses = db.query(Course).count()
    total_sessions = db.query(AttendanceSession).count()
    
    # Today's stats
    today = datetime.utcnow().date()
    today_sessions = db.query(AttendanceSession).filter(
        AttendanceSession.start_time >= datetime.combine(today, datetime.min.time())
    ).all()
    
    today_present = sum(s.present_count for s in today_sessions)
    
    # Active sessions
    active_sessions = db.query(AttendanceSession).filter(
        AttendanceSession.is_active == True
    ).count()
    
    # Recent attention
    recent_attention = db.query(AttentionLog).order_by(
        AttentionLog.timestamp.desc()
    ).limit(100).all()
    
    avg_attention = 0
    if recent_attention:
        avg_attention = sum(a.attention_score for a in recent_attention) / len(recent_attention)
    
    return {
        "overview": {
            "total_students": total_students,
            "total_courses": total_courses,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions
        },
        "today": {
            "sessions": len(today_sessions),
            "attendance_marked": today_present
        },
        "attention": {
            "average_score": round(avg_attention, 1),
            "recent_logs": len(recent_attention)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/analytics/radar/{session_id}")
async def get_radar_data(session_id: str, db: Session = Depends(get_db)):
    """
    Get radar visualization data for a session
    Returns student positions and attention levels for the radar display
    """
    session = db.query(AttendanceSession).filter(
        AttendanceSession.session_id == session_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Get attendance with latest attention
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.is_valid == True
    ).all()
    
    radar_points = []
    for i, record in enumerate(records):
        # Get latest attention for this student
        latest_attention = db.query(AttentionLog).filter(
            AttentionLog.session_id == session.id,
            AttentionLog.student_id == record.student_id
        ).order_by(AttentionLog.timestamp.desc()).first()
        
        # Generate position (in real system, this would come from seating chart)
        angle = (i / max(len(records), 1)) * 360
        radius = 0.6 + (i % 3) * 0.15  # Vary radius slightly
        
        radar_points.append({
            "student_id": record.student.student_id,
            "name": record.student.name,
            "angle": angle,
            "radius": radius,
            "attention": latest_attention.attention_score if latest_attention else 75,
            "is_drowsy": latest_attention.is_drowsy if latest_attention else False,
            "is_distracted": latest_attention.is_distracted if latest_attention else False,
            "gaze": latest_attention.gaze_direction if latest_attention else "forward"
        })
    
    return {
        "session_id": session_id,
        "course": session.course.course_code if session.course else None,
        "room": session.room,
        "points": radar_points,
        "summary": {
            "total": len(radar_points),
            "attentive": sum(1 for p in radar_points if p['attention'] >= 70),
            "distracted": sum(1 for p in radar_points if p['is_distracted']),
            "drowsy": sum(1 for p in radar_points if p['is_drowsy'])
        }
    }
