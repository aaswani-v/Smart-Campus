"""
Smart Campus - Database Models
SQLAlchemy ORM models for the attendance system
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'data', 'smart_campus.db')}")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Student(Base):
    """Student model with biometric data"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    department = Column(String(50))
    year = Column(Integer)
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    
    # Biometric data (simulated)
    fingerprint_hash = Column(String(64))  # SHA256 hash for demo
    rfid_tag = Column(String(32))  # RFID tag ID
    face_encoding_path = Column(String(255))  # Path to face data
    
    is_active = Column(Boolean, default=True)
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    attention_logs = relationship("AttentionLog", back_populates="student")


class Course(Base):
    """Course/Subject model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(50))
    credits = Column(Integer)
    faculty_name = Column(String(100))
    
    # Relationships
    sessions = relationship("AttendanceSession", back_populates="course")
    timetable_slots = relationship("TimetableSlot", back_populates="course")


class TimetableSlot(Base):
    """Timetable slot for scheduling"""
    __tablename__ = "timetable_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time = Column(String(5))  # HH:MM format
    end_time = Column(String(5))
    room = Column(String(20))
    
    course = relationship("Course", back_populates="timetable_slots")


class AttendanceSession(Base):
    """Attendance session for a class"""
    __tablename__ = "attendance_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True)  # UUID
    course_id = Column(Integer, ForeignKey("courses.id"))
    room = Column(String(20))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    
    # Relationships
    course = relationship("Course", back_populates="sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session")
    attention_logs = relationship("AttentionLog", back_populates="session")


class AttendanceRecord(Base):
    """Individual attendance record"""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    marked_at = Column(DateTime, default=datetime.utcnow)
    
    # Verification factors
    face_verified = Column(Boolean, default=False)
    face_confidence = Column(Float, default=0.0)
    fingerprint_verified = Column(Boolean, default=False)
    rfid_verified = Column(Boolean, default=False)
    
    # Multi-factor result
    factors_passed = Column(Integer, default=0)
    is_valid = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("Student", back_populates="attendance_records")


class AttentionLog(Base):
    """Attention tracking logs"""
    __tablename__ = "attention_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Attention metrics
    attention_score = Column(Float, default=0.0)  # 0-100
    head_yaw = Column(Float, default=0.0)  # Left/Right
    head_pitch = Column(Float, default=0.0)  # Up/Down
    head_roll = Column(Float, default=0.0)  # Tilt
    eye_aspect_ratio = Column(Float, default=0.0)
    is_drowsy = Column(Boolean, default=False)
    is_distracted = Column(Boolean, default=False)
    gaze_direction = Column(String(20))  # 'forward', 'left', 'right', 'down'
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="attention_logs")
    student = relationship("Student", back_populates="attention_logs")


class SystemLog(Base):
    """System audit logs"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))  # 'enroll', 'attendance', 'error', etc
    user_id = Column(String(20))
    details = Column(Text)
    ip_address = Column(String(45))
    success = Column(Boolean, default=True)


# Database initialization
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize on import
init_db()
