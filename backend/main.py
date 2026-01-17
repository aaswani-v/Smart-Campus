"""
Smart Campus - Main Application
FastAPI server with WebSocket support for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime
from typing import List
import os

from api.routes import router as api_router
from models.database import init_db

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: dict = {}  # session_id -> list of websockets
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if session_id:
            if session_id not in self.session_connections:
                self.session_connections[session_id] = []
            self.session_connections[session_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if session_id and session_id in self.session_connections:
            if websocket in self.session_connections[session_id]:
                self.session_connections[session_id].remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast to clients watching a specific session"""
        if session_id in self.session_connections:
            for connection in self.session_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Smart Campus Backend Starting...")
    init_db()
    
    # === DEMO DATA SEEDING ===
    from models.database import SessionLocal, Student, Course, AttendanceSession, TimetableSlot
    db = SessionLocal()
    try:
        # Create Demo Student
        demo_student = db.query(Student).filter_by(student_id="unknown_1").first()
        if not demo_student:
            demo_student = Student(
                student_id="unknown_1",
                name="Unknown 1",
                email="unknown1@example.com",
                department="Computer Science",
                year=3
            )
            db.add(demo_student)
            
            # Create a few more demo students
            students_data = [
                ("S101", "Alice Smith", "alice@test.com"),
                ("S102", "Bob Jones", "bob@test.com"),
                ("S103", "Charlie Brown", "charlie@test.com")
            ]
            for sid, name, email in students_data:
                s = Student(student_id=sid, name=name, email=email, department="CS", year=3)
                db.add(s)
            
            db.commit()
            print("✅ Demo students created")

        # Create Demo Courses & Sessions
        if db.query(Course).count() == 0:
            courses_data = [
                ("CS301", "Artificial Intelligence", "Dr. Alan Turing"),
                ("CS302", "Database Systems", "Dr. E.F. Codd"),
                ("CS303", "Computer Networks", "Dr. Vint Cerf"),
                ("CS304", "Operating Systems", "Dr. Linus Torvalds"),
                ("CS305", "Software Engineering", "Dr. Grace Hopper")
            ]
            
            for code, name, faculty in courses_data:
                course = Course(course_code=code, name=name, department="CS", faculty_name=faculty, credits=4)
                db.add(course)
                db.flush() # get ID
                
                # Active Session
                session = AttendanceSession(
                    session_id=f"sess_{code.lower()}",
                    course_id=course.id,
                    room="Lab 301",
                    is_active=True
                )
                db.add(session)
            
            db.commit()
            print("✅ Demo courses & sessions created")
            
    except Exception as e:
        print(f"⚠️ Seeding error: {e}")
    finally:
        db.close()
    
    print("✅ Database initialized & seeded")
    
    yield
    
    # Shutdown
    print("👋 Smart Campus Backend Shutting Down...")


# Create FastAPI app
app = FastAPI(
    title="Smart Campus API",
    description="Intelligent Attendance & Attention Tracking System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")



from services.face_recognition import get_face_service
from pydantic import BaseModel
from fastapi import Form, File, UploadFile
from typing import Optional
import numpy as np
import cv2

class EnrollRequest(BaseModel):
    student_id: str
    name: str
    images: list  # List of base64 encoded images

# ============= FACE RECOGNITION API ENDPOINTS =============

@app.post("/api/face-recognition/enroll")
async def enroll_student(request: EnrollRequest):
    """Enroll a new student with face images"""
    face_service = get_face_service()
    
    try:
        # Decode images
        decoded_images = []
        for img_base64 in request.images:
            img = face_service.decode_base64_image(img_base64)
            if img is not None:
                decoded_images.append(img)
        
        if len(decoded_images) < 3:
            return JSONResponse(
                status_code=400, 
                content={"error": f"Need at least 3 valid images, got {len(decoded_images)}"}
            )
        
        result = face_service.enroll_student(
            student_id=request.student_id,
            name=request.name,
            images=decoded_images
        )
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

class RecognizeRequest(BaseModel):
    image: str  # Base64 encoded image

@app.post("/api/face-recognition/recognize")
async def recognize_faces(request: RecognizeRequest):
    """Recognize faces in a single image"""
    face_service = get_face_service()
    
    try:
        image = face_service.decode_base64_image(request.image)
        if image is None:
            return JSONResponse(status_code=400, content={"error": "Invalid image"})
        
        results = face_service.recognize_from_image(image)
        
        return {
            "success": True,
            "faces": results
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/face-recognition/enrolled")
async def get_enrolled_students():
    """Get list of enrolled students"""
    face_service = get_face_service()
    return {
        "count": face_service.get_enrolled_count(),
        "students": face_service.get_enrolled_students()
    }

# ============= WEBSOCKET ENDPOINTS =============

@app.websocket("/api/face-recognition/ws")
async def face_rec_websocket(websocket: WebSocket):
    """WebSocket for live face recognition"""
    await websocket.accept()
    face_service = get_face_service()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle both {type: 'frame', image: ...} and {image: ...}
            image_data = message.get("image")
            
            if image_data:
                try:
                    # Decode and process frame
                    image = face_service.decode_base64_image(image_data)
                    
                    # Detect and Recognize
                    # This will use YOLO/Haar for detection and LBPH for ID
                    results = face_service.recognize_from_image(image)
                    
                    # Log for debugging
                    if results:
                        print(f"[WS] Recognized {len(results)} faces: {[r.get('name', 'Unknown') for r in results]}")
                    
                    await websocket.send_json({
                        "type": "result", 
                        "faces": results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    import traceback
                    traceback.print_exc()
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """General WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/session/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for real-time session updates"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo message type for debugging
            if message.get("type") == "subscribe":
                await websocket.send_json({
                    "type": "subscribed",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)


# ============= HEALTH & STATUS ENDPOINTS =============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Smart Campus API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "database": "ok",
            "face_recognition": "ok",
            "attention_tracking": "ok"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============= UTILITY FUNCTION FOR BROADCASTING =============

async def broadcast_attendance_update(session_id: str, data: dict):
    """Broadcast attendance update to session subscribers"""
    await manager.broadcast_to_session(session_id, {
        "type": "attendance_update",
        "session_id": session_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_attention_update(session_id: str, data: dict):
    """Broadcast attention metrics to session subscribers"""
    await manager.broadcast_to_session(session_id, {
        "type": "attention_update",
        "session_id": session_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
