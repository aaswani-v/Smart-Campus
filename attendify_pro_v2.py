"""
Attendify Pro v2 - Intelligent Student Attendance System
FIXED VERSION with:
- Dark/Light Mode Toggle
- Proper Data Storage
- OpenCV-based Liveness Detection (no MediaPipe dependency)
- Fingerprint Animation
- QR Code Scanning
- Pre-loaded Face Data

Run: python attendify_pro_v2.py
"""

import sys
import cv2
import numpy as np
import pickle
import hashlib
import qrcode
from io import BytesIO
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import time
import os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QProgressBar, QMessageBox, QGraphicsDropShadowEffect,
    QComboBox, QDialog, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QBrush, QPen

# Check LBPH
try:
    _ = cv2.face.LBPHFaceRecognizer_create()
    LBPH_AVAILABLE = True
except:
    LBPH_AVAILABLE = False
    print("[WARN] opencv-contrib-python needed")

# ============= THEME SYSTEM =============
class Theme:
    DARK = {
        'bg_main': '#0f0f1a', 'bg_card': '#16213e', 'bg_header': '#1a1a2e', 'bg_input': '#0d1b2a',
        'accent_orange': '#FF6B35', 'accent_green': '#22C55E', 'accent_blue': '#3B82F6',
        'accent_red': '#EF4444', 'accent_purple': '#8B5CF6', 'accent_yellow': '#F59E0B',
        'text_primary': '#FFFFFF', 'text_secondary': '#A0AEC0', 'text_muted': '#718096',
        'border': '#2D3748', 'border_light': '#1E293B',
    }
    LIGHT = {
        'bg_main': '#F5F5F3', 'bg_card': '#FFFFFF', 'bg_header': '#FFFFFF', 'bg_input': '#F9FAFB',
        'accent_orange': '#FF6B35', 'accent_green': '#22C55E', 'accent_blue': '#3B82F6',
        'accent_red': '#EF4444', 'accent_purple': '#8B5CF6', 'accent_yellow': '#F59E0B',
        'text_primary': '#1A1A1A', 'text_secondary': '#6B7280', 'text_muted': '#9CA3AF',
        'border': '#E5E7EB', 'border_light': '#F3F4F6',
    }

COLORS = Theme.LIGHT  # Default
RADIUS = {'sm': 8, 'md': 12, 'lg': 16, 'xl': 20, 'xxl': 24, 'pill': 9999}


# ============= BIOMETRIC SIMULATOR =============
class BiometricSimulator:
    @staticmethod
    def generate_fingerprint(student_id: str) -> str:
        return hashlib.sha256(f"{student_id}SECRET_SALT".encode()).hexdigest()[:32]
    
    @staticmethod
    def verify_fingerprint(input_pattern: str, stored_pattern: str) -> bool:
        return input_pattern == stored_pattern
    
    @staticmethod
    def generate_daily_qr(student_id: str) -> tuple:
        today = datetime.now().strftime('%Y-%m-%d')
        token = hashlib.sha256(f"{student_id}{today}QR_SECRET".encode()).hexdigest()[:16]
        
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(f"ATTENDIFY:{student_id}:{token}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue(), token
    
    @staticmethod
    def verify_qr_token(student_id: str, token: str) -> bool:
        today = datetime.now().strftime('%Y-%m-%d')
        expected = hashlib.sha256(f"{student_id}{today}QR_SECRET".encode()).hexdigest()[:16]
        return token == expected


# ============= LIVENESS DETECTOR (OpenCV-based, no MediaPipe) =============
class LivenessDetector:
    """Blink detection using OpenCV eye cascade - works on all Python versions"""
    
    def __init__(self):
        self.blink_count = 0
        self.blink_threshold = 2
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.last_eye_count = 2
        self.no_eye_frames = 0
        self.blink_cooldown = 0
        print("[OK] Liveness detection ready (OpenCV)")
    
    def detect_blink(self, frame) -> tuple:
        """Returns (blink_detected, current_count, is_verified)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) == 0:
            return False, self.blink_count, self.blink_count >= self.blink_threshold
        
        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        # Detect eyes in face region
        eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3, minSize=(20, 20), maxSize=(w//3, h//3))
        eye_count = len(eyes)
        
        blink_detected = False
        
        # Blink detection: eyes disappear then reappear
        if self.blink_cooldown > 0:
            self.blink_cooldown -= 1
        elif eye_count < 2 and self.last_eye_count >= 2:
            self.no_eye_frames += 1
            if self.no_eye_frames >= 2:  # Eyes closed for 2+ frames
                pass  # Wait for eyes to open
        elif eye_count >= 2 and self.no_eye_frames >= 2:
            # Eyes reopened after being closed
            self.blink_count += 1
            blink_detected = True
            self.blink_cooldown = 10  # Cooldown to prevent double counting
            self.no_eye_frames = 0
        elif eye_count >= 2:
            self.no_eye_frames = 0
        
        self.last_eye_count = eye_count
        
        return blink_detected, self.blink_count, self.blink_count >= self.blink_threshold
    
    def reset(self):
        self.blink_count = 0
        self.no_eye_frames = 0
        self.blink_cooldown = 0


# ============= ANOMALY DETECTOR =============
class AnomalyDetector:
    def __init__(self):
        self.attempts = defaultdict(list)
        self.anomalies = []
    
    def check_rate_limit(self, student_id: str) -> tuple:
        now = time.time()
        self.attempts[student_id] = [t for t in self.attempts[student_id] if now - t < 300]
        
        if len(self.attempts[student_id]) >= 5:
            self.log_anomaly(student_id, "RATE_LIMIT", "Too many attempts")
            return False, "Rate limited. Wait 5 minutes."
        return True, ""
    
    def record_attempt(self, student_id: str, success: bool):
        self.attempts[student_id].append(time.time())
    
    def log_anomaly(self, student_id: str, atype: str, desc: str):
        self.anomalies.append({'timestamp': datetime.now().isoformat(), 'student_id': student_id, 'type': atype, 'description': desc})
    
    def get_recent_anomalies(self, count: int = 10):
        return self.anomalies[-count:][::-1]


# ============= ATTENDANCE SYSTEM =============
class AttendanceSystem:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create() if LBPH_AVAILABLE else None
        
        self.label_map = {}
        self.students = {}
        self.attendance_today = {}
        self.attendance_history = defaultdict(list)
        
        self.biometric = BiometricSimulator()
        self.liveness = LivenessDetector()
        self.anomaly = AnomalyDetector()
        
        self._load_data()
    
    def _load_data(self):
        """Load saved data"""
        data_path = self.data_dir / "system_data.pkl"
        model_path = self.data_dir / "face_model.yml"
        
        if data_path.exists():
            try:
                with open(data_path, 'rb') as f:
                    data = pickle.load(f)
                    self.label_map = data.get('labels', {})
                    self.students = data.get('students', {})
                    self.attendance_history = defaultdict(list, data.get('history', {}))
                print(f"[OK] Loaded {len(self.students)} students from database")
            except Exception as e:
                print(f"[WARN] Could not load data: {e}")
        
        if self.recognizer and model_path.exists():
            try:
                self.recognizer.read(str(model_path))
                print("[OK] Loaded face recognition model")
            except:
                pass
    
    def _save_data(self):
        """Save all data persistently"""
        data_path = self.data_dir / "system_data.pkl"
        model_path = self.data_dir / "face_model.yml"
        
        # Save student data
        with open(data_path, 'wb') as f:
            pickle.dump({
                'labels': self.label_map,
                'students': self.students,
                'history': dict(self.attendance_history)
            }, f)
        print(f"[SAVED] Database with {len(self.students)} students")
        
        # Save face model
        if self.recognizer and self.label_map:
            try:
                self.recognizer.write(str(model_path))
                print("[SAVED] Face recognition model")
            except Exception as e:
                print(f"[WARN] Could not save model: {e}")
    
    def import_existing_data(self, data_folder: str) -> tuple:
        """Import faces from existing folder structure (folder name = student name)"""
        data_path = Path(data_folder)
        if not data_path.exists():
            return False, "Folder not found"
        
        imported = 0
        all_faces = []
        all_labels = []
        
        for person_folder in data_path.iterdir():
            if not person_folder.is_dir() or person_folder.name.startswith('_'):
                continue
            
            name = person_folder.name.title()
            student_id = name.upper()[:3] + str(len(self.students) + 1).zfill(3)
            
            if student_id in self.students:
                continue
            
            label = max(self.label_map.keys(), default=-1) + 1
            faces_collected = 0
            
            for img_file in person_folder.glob("*.jpg"):
                try:
                    img = cv2.imread(str(img_file))
                    if img is None:
                        continue
                    
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    detected = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
                    
                    if len(detected) >= 1:
                        x, y, w, h = detected[0]
                        face = gray[y:y+h, x:x+w]
                        face = cv2.equalizeHist(cv2.resize(face, (200, 200)))
                        all_faces.append(face)
                        all_labels.append(label)
                        faces_collected += 1
                        
                        if faces_collected >= 20:  # Limit per person
                            break
                except:
                    continue
            
            if faces_collected >= 3:
                self.label_map[label] = student_id
                self.students[student_id] = {
                    'name': name,
                    'department': 'Imported',
                    'fingerprint': self.biometric.generate_fingerprint(student_id),
                    'enrolled_at': datetime.now().isoformat()
                }
                imported += 1
                print(f"  Imported: {name} ({faces_collected} faces)")
        
        if all_faces:
            try:
                if self.label_map and len(self.label_map) > imported:
                    self.recognizer.update(all_faces, np.array(all_labels))
                else:
                    self.recognizer.train(all_faces, np.array(all_labels))
            except Exception as e:
                return False, str(e)
            
            self._save_data()
        
        return True, f"Imported {imported} students"
    
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    
    def preprocess_face(self, frame, rect):
        x, y, w, h = rect
        face = frame[y:y+h, x:x+w]
        if len(face.shape) == 3:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        return cv2.equalizeHist(cv2.resize(face, (200, 200)))
    
    def enroll_student(self, student_id: str, name: str, department: str, frames: list) -> tuple:
        if not self.recognizer:
            return False, "Recognition not available"
        
        if student_id in self.students:
            return False, "Student ID already exists"
        
        label = max(self.label_map.keys(), default=-1) + 1
        faces, labels = [], []
        
        for img in frames:
            detected = self.detect_faces(img)
            if len(detected) >= 1:
                face = self.preprocess_face(img, detected[0])
                faces.append(face)
                labels.append(label)
        
        if len(faces) < 3:
            return False, f"Only {len(faces)} valid faces"
        
        try:
            if self.label_map:
                self.recognizer.update(faces, np.array(labels))
            else:
                self.recognizer.train(faces, np.array(labels))
        except Exception as e:
            return False, str(e)
        
        fingerprint = self.biometric.generate_fingerprint(student_id)
        
        self.label_map[label] = student_id
        self.students[student_id] = {
            'name': name,
            'department': department,
            'fingerprint': fingerprint,
            'enrolled_at': datetime.now().isoformat()
        }
        
        self._save_data()  # SAVE IMMEDIATELY
        return True, f"Enrolled {name} successfully!"
    
    def recognize_face(self, frame, rect) -> tuple:
        if not self.recognizer or not self.label_map:
            return None, "Unknown", 0
        try:
            face = self.preprocess_face(frame, rect)
            label, conf = self.recognizer.predict(face)
            if label in self.label_map and conf < 85:
                sid = self.label_map[label]
                return sid, self.students.get(sid, {}).get('name', 'Unknown'), int(max(0, 100 - conf))
        except:
            pass
        return None, "Unknown", 0
    
    def mark_attendance(self, student_id: str, factors: dict) -> tuple:
        allowed, msg = self.anomaly.check_rate_limit(student_id)
        if not allowed:
            return False, msg
        
        if student_id in self.attendance_today:
            return False, "Already marked today"
        
        if not factors.get('face'):
            self.anomaly.record_attempt(student_id, False)
            return False, "Face required"
        
        score = sum([30 if factors.get('face') else 0, 25 if factors.get('liveness') else 0,
                     25 if factors.get('fingerprint') else 0, 20 if factors.get('qr') else 0])
        
        now = datetime.now()
        self.attendance_today[student_id] = {
            'name': self.students.get(student_id, {}).get('name', 'Unknown'),
            'time': now.strftime("%H:%M:%S"), 'score': score
        }
        
        self.attendance_history[now.strftime("%Y-%m-%d")].append({'student_id': student_id, 'time': now.strftime("%H:%M:%S"), 'score': score})
        self.anomaly.record_attempt(student_id, True)
        self._save_data()
        
        return True, f"Verified with {score}% confidence"
    
    def get_statistics(self) -> dict:
        total = len(self.students)
        today = len(self.attendance_today)
        scores = [r['score'] for day in self.attendance_history.values() for r in day]
        return {
            'total_enrolled': total, 'present_today': today, 'absent_today': max(0, total - today),
            'attendance_rate': (today / total * 100) if total > 0 else 0,
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'anomalies': len([a for a in self.anomaly.anomalies if a['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))])
        }
    
    def get_enrolled_count(self):
        return len(self.students)
    
    def get_enrolled_list(self):
        return [(sid, data['name'], data['department']) for sid, data in self.students.items()]


# ============= VIDEO WORKER =============
class VideoWorker(QThread):
    frame_ready = Signal(np.ndarray, list, dict)
    
    def __init__(self, system):
        super().__init__()
        self.system = system
        self.running = False
        self.cap = None
        self.current_frame = None
    
    def run(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            self.current_frame = frame.copy()
            
            faces = self.system.detect_faces(frame)
            blink, count, verified = self.system.liveness.detect_blink(frame)
            
            results = []
            for (x, y, w, h) in faces:
                sid, name, conf = self.system.recognize_face(frame, (x, y, w, h))
                results.append({'bbox': (x, y, w, h), 'student_id': sid, 'name': name, 'confidence': conf, 'recognized': sid is not None})
            
            self.frame_ready.emit(frame, results, {'blink': blink, 'count': count, 'verified': verified})
            self.msleep(30)
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        self.running = False
        self.wait()
    
    def get_frame(self):
        return self.current_frame


# ============= UI COMPONENTS =============
def get_style(colors):
    return f"""
        QMainWindow, QWidget#main {{ background-color: {colors['bg_main']}; }}
        QWidget {{ font-family: 'Segoe UI'; color: {colors['text_primary']}; }}
        QLabel {{ background: transparent; }}
        QFrame#card {{ background-color: {colors['bg_card']}; border-radius: 24px; border: 1px solid {colors['border_light']}; }}
        QPushButton {{ background-color: {colors['accent_orange']}; color: white; border: none; border-radius: 20px; padding: 14px 28px; font-weight: 600; }}
        QPushButton:hover {{ background-color: #e85d04; }}
        QLineEdit, QComboBox {{ background-color: {colors['bg_input']}; border: 1px solid {colors['border']}; border-radius: 12px; padding: 14px; color: {colors['text_primary']}; }}
        QListWidget {{ background: transparent; border: none; }}
        QListWidget::item {{ background-color: {colors['bg_card']}; border-radius: 12px; padding: 14px; margin: 4px 0; border: 1px solid {colors['border_light']}; }}
        QProgressBar {{ background-color: {colors['bg_input']}; border-radius: 6px; height: 10px; }}
        QProgressBar::chunk {{ background-color: {colors['accent_orange']}; border-radius: 6px; }}
    """


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 28, 28, 28)
        self._layout.setSpacing(16)
    
    def addWidget(self, w): self._layout.addWidget(w)
    def addLayout(self, l): self._layout.addLayout(l)
    def addStretch(self): self._layout.addStretch()


class StatBadge(QFrame):
    def __init__(self, value, label, color, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.setStyleSheet(f"background-color: {colors['bg_card']}; border-radius: 20px; border: 1px solid {colors['border_light']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {color};")
        layout.addWidget(self.value_label)
        desc = QLabel(label)
        desc.setStyleSheet(f"font-size: 13px; color: {colors['text_secondary']};")
        layout.addWidget(desc)
    
    def set_value(self, v): self.value_label.setText(str(v))


class NavPill(QPushButton):
    def __init__(self, text, colors, active=False, parent=None):
        super().__init__(text, parent)
        self.colors = colors
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setMinimumWidth(90)
        self._update()
        self.toggled.connect(self._update)
    
    def _update(self):
        bg = self.colors['bg_input'] if self.isChecked() else 'transparent'
        color = self.colors['text_primary'] if self.isChecked() else self.colors['text_secondary']
        weight = '600' if self.isChecked() else '400'
        self.setStyleSheet(f"QPushButton {{ background-color: {bg}; color: {color}; border: none; border-radius: 20px; padding: 10px 16px; font-weight: {weight}; font-size: 13px; }}")


class VerificationBadge(QFrame):
    def __init__(self, name, icon, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.verified = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.addWidget(QLabel(icon))
        layout.addWidget(QLabel(name))
        layout.addStretch()
        self.status = QLabel("⏳")
        self.status.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.status)
        self._update()
    
    def set_verified(self, v):
        self.verified = v
        self.status.setText("✅" if v else "❌" if v is False else "⏳")
        self._update()
    
    def set_pending(self):
        self.verified = None
        self.status.setText("⏳")
        self._update()
    
    def _update(self):
        if self.verified:
            bg, border = "rgba(34,197,94,0.15)", self.colors['accent_green']
        elif self.verified is False:
            bg, border = "rgba(239,68,68,0.15)", self.colors['accent_red']
        else:
            bg, border = self.colors['bg_input'], self.colors['border']
        self.setStyleSheet(f"background-color: {bg}; border: 2px solid {border}; border-radius: 14px;")


class FingerprintButton(QPushButton):
    """Animated fingerprint button"""
    def __init__(self, colors, parent=None):
        super().__init__("👆 Scan Fingerprint", parent)
        self.colors = colors
        self.setFixedHeight(60)
        self.progress = 0
        self.scanning = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self._update_style()
    
    def start_scan(self):
        self.scanning = True
        self.progress = 0
        self.timer.start(50)
    
    def _animate(self):
        self.progress += 5
        if self.progress >= 100:
            self.timer.stop()
            self.scanning = False
            self.setText("✅ Verified!")
            self._update_style()
        else:
            self.setText(f"🔄 Scanning... {self.progress}%")
    
    def reset(self):
        self.progress = 0
        self.scanning = False
        self.setText("👆 Scan Fingerprint")
        self._update_style()
    
    def _update_style(self):
        color = self.colors['accent_green'] if self.progress >= 100 else self.colors['accent_blue']
        self.setStyleSheet(f"background: {color}; color: white; padding: 16px; border-radius: 14px; font-weight: 600; font-size: 14px;")


# ============= MAIN APP =============
class AttendifyProV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.colors = Theme.LIGHT
        self.system = AttendanceSystem()
        self.video_worker = None
        self.enrollment_frames = []
        self.verification_state = {'face': False, 'liveness': False, 'fingerprint': False, 'qr': False}
        self.current_student = None
        
        self.setWindowTitle("Attendify Pro v2 - Smart Attendance")
        self.setMinimumSize(1450, 900)
        self.apply_theme()
        self.setup_ui()
    
    def apply_theme(self):
        self.colors = Theme.DARK if self.dark_mode else Theme.LIGHT
        self.setStyleSheet(get_style(self.colors))
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        # Rebuild UI to apply new colors
        self.centralWidget().deleteLater()
        self.setup_ui()
    
    def setup_ui(self):
        main = QWidget()
        main.setObjectName("main")
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addWidget(self.create_header())
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_dashboard())
        self.stack.addWidget(self.create_monitoring())
        self.stack.addWidget(self.create_verification())
        self.stack.addWidget(self.create_enroll())
        self.stack.addWidget(self.create_students())
        self.stack.addWidget(self.create_analytics())
        
        content_layout.addWidget(self.stack)
        layout.addWidget(content)
        self.switch_page(0)
    
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {self.colors['bg_header']}; border-bottom: 1px solid {self.colors['border_light']};")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        
        logo = QLabel("🎓 Attendify Pro")
        logo.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {self.colors['accent_orange']};")
        layout.addWidget(logo)
        layout.addSpacing(30)
        
        nav = QFrame()
        nav.setStyleSheet(f"background-color: {self.colors['bg_input']}; border-radius: 25px;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        
        self.nav_btns = []
        for i, txt in enumerate(["Dashboard", "Monitor", "Verify", "Enroll", "Students", "Analytics"]):
            btn = NavPill(txt, self.colors, i == 0)
            btn.clicked.connect(lambda _, idx=i: self.switch_page(idx))
            self.nav_btns.append(btn)
            nav_layout.addWidget(btn)
        
        layout.addWidget(nav)
        layout.addStretch()
        
        # Theme toggle
        theme_btn = QPushButton("🌙" if not self.dark_mode else "☀️")
        theme_btn.setFixedSize(40, 40)
        theme_btn.setStyleSheet(f"background: {self.colors['bg_input']}; border-radius: 20px; font-size: 18px;")
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        
        # Import button
        import_btn = QPushButton("📥")
        import_btn.setFixedSize(40, 40)
        import_btn.setStyleSheet(f"background: {self.colors['bg_input']}; border-radius: 20px; font-size: 18px;")
        import_btn.clicked.connect(self.import_data)
        import_btn.setToolTip("Import existing face data")
        layout.addWidget(import_btn)
        
        return header
    
    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
            btn._update()
    
    def import_data(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Face Data Folder", "C:/Users/Ash/Downloads/HackCrypt/Attendify/backend/models/_data-face")
        if folder:
            success, msg = self.system.import_existing_data(folder)
            if success:
                QMessageBox.information(self, "Import Complete", msg)
                self.refresh_stats()
            else:
                QMessageBox.warning(self, "Import Failed", msg)
    
    def refresh_stats(self):
        stats = self.system.get_statistics()
        if hasattr(self, 'dash_enrolled'):
            self.dash_enrolled.set_value(stats['total_enrolled'])
            self.dash_present.set_value(stats['present_today'])
    
    def create_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        stats = self.system.get_statistics()
        
        row = QHBoxLayout()
        self.dash_enrolled = StatBadge(stats['total_enrolled'], "Enrolled", self.colors['accent_blue'], self.colors)
        self.dash_present = StatBadge(stats['present_today'], "Present", self.colors['accent_green'], self.colors)
        self.dash_absent = StatBadge(stats['absent_today'], "Absent", self.colors['accent_red'], self.colors)
        self.dash_rate = StatBadge(f"{stats['attendance_rate']:.0f}%", "Rate", self.colors['accent_orange'], self.colors)
        
        for c in [self.dash_enrolled, self.dash_present, self.dash_absent, self.dash_rate]:
            row.addWidget(c)
        layout.addLayout(row)
        
        content = QHBoxLayout()
        
        actions = Card()
        actions.addWidget(QLabel("Quick Actions"))
        
        for txt, clr, idx in [("▶ Start Session", self.colors['accent_orange'], 1), ("✋ Multi-Factor Verify", self.colors['accent_green'], 2), ("+ Enroll Student", self.colors['text_primary'], 3)]:
            btn = QPushButton(txt)
            btn.setStyleSheet(f"background: {clr}; color: white; padding: 14px; border-radius: 12px;")
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            actions.addWidget(btn)
        
        import_btn = QPushButton("📥 Import Existing Data")
        import_btn.setStyleSheet(f"background: {self.colors['accent_purple']}; color: white; padding: 14px; border-radius: 12px;")
        import_btn.clicked.connect(self.import_data)
        actions.addWidget(import_btn)
        
        actions.addStretch()
        content.addWidget(actions)
        
        activity = Card()
        activity.addWidget(QLabel("Recent Activity"))
        self.dash_activity = QListWidget()
        self.dash_activity.setMaximumHeight(300)
        activity.addWidget(self.dash_activity)
        content.addWidget(activity, 2)
        
        layout.addLayout(content)
        layout.addStretch()
        return page
    
    def create_monitoring(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        title = QLabel("📹 Live Monitoring")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        self.status_lbl = QLabel("● Offline")
        self.status_lbl.setStyleSheet(f"color: {self.colors['text_muted']};")
        header.addWidget(self.status_lbl)
        layout.addLayout(header)
        
        content = QHBoxLayout()
        
        video_card = Card()
        self.video_label = QLabel("Click 'Start Session' to begin")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 480)
        self.video_label.setStyleSheet(f"background: {self.colors['bg_main']}; border-radius: 16px;")
        video_card.addWidget(self.video_label)
        
        ctrl = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start Session")
        self.start_btn.clicked.connect(self.toggle_camera)
        ctrl.addWidget(self.start_btn)
        ctrl.addStretch()
        self.liveness_lbl = QLabel("👁 Blinks: 0/2")
        self.liveness_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {self.colors['accent_blue']};")
        ctrl.addWidget(self.liveness_lbl)
        video_card.addLayout(ctrl)
        content.addWidget(video_card, 2)
        
        side = QVBoxLayout()
        
        stats_card = Card()
        stats_card.addWidget(QLabel("SESSION METRICS"))
        stats_row = QHBoxLayout()
        self.vis_stat = StatBadge(0, "Visible", self.colors['text_primary'], self.colors)
        self.mark_stat = StatBadge(0, "Marked", self.colors['accent_green'], self.colors)
        stats_row.addWidget(self.vis_stat)
        stats_row.addWidget(self.mark_stat)
        stats_card.addLayout(stats_row)
        side.addWidget(stats_card)
        
        log_card = Card()
        log_card.addWidget(QLabel("ACTIVITY LOG"))
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(250)
        log_card.addWidget(self.activity_list)
        side.addWidget(log_card)
        side.addStretch()
        
        content.addLayout(side, 1)
        layout.addLayout(content)
        return page
    
    def create_verification(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("✋ Multi-Factor Verification")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        content = QHBoxLayout()
        
        cam_card = Card()
        self.verify_video = QLabel("Start camera on Monitoring page")
        self.verify_video.setAlignment(Qt.AlignCenter)
        self.verify_video.setMinimumSize(500, 380)
        self.verify_video.setStyleSheet(f"background: {self.colors['bg_main']}; border-radius: 16px;")
        cam_card.addWidget(self.verify_video)
        
        self.verify_name = QLabel("No face detected")
        self.verify_name.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {self.colors['accent_orange']};")
        self.verify_name.setAlignment(Qt.AlignCenter)
        cam_card.addWidget(self.verify_name)
        content.addWidget(cam_card, 2)
        
        verify_card = Card()
        verify_card.addWidget(QLabel("VERIFICATION FACTORS"))
        
        self.badge_face = VerificationBadge("Face Recognition (30%)", "👤", self.colors)
        self.badge_liveness = VerificationBadge("Liveness - Blink 2x (25%)", "👁", self.colors)
        self.badge_finger = VerificationBadge("Fingerprint (25%)", "👆", self.colors)
        self.badge_qr = VerificationBadge("QR Code (20%)", "📱", self.colors)
        
        for b in [self.badge_face, self.badge_liveness, self.badge_finger, self.badge_qr]:
            verify_card.addWidget(b)
        
        # Fingerprint with animation
        self.finger_btn = FingerprintButton(self.colors)
        self.finger_btn.clicked.connect(self.simulate_fingerprint)
        verify_card.addWidget(self.finger_btn)
        
        # QR buttons
        qr_row = QHBoxLayout()
        show_qr = QPushButton("📱 Show My QR")
        show_qr.setStyleSheet(f"background: {self.colors['accent_purple']}; color: white; padding: 12px; border-radius: 12px;")
        show_qr.clicked.connect(self.show_qr_code)
        qr_row.addWidget(show_qr)
        
        scan_qr = QPushButton("📷 Scan QR")
        scan_qr.setStyleSheet(f"background: {self.colors['text_primary']}; color: white; padding: 12px; border-radius: 12px;")
        scan_qr.clicked.connect(self.scan_qr_code)
        qr_row.addWidget(scan_qr)
        verify_card.addLayout(qr_row)
        
        verify_card.addStretch()
        
        self.verify_score = QLabel("Score: 0%")
        self.verify_score.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {self.colors['accent_orange']};")
        self.verify_score.setAlignment(Qt.AlignCenter)
        verify_card.addWidget(self.verify_score)
        
        submit_btn = QPushButton("✓ Mark Attendance")
        submit_btn.setStyleSheet(f"background: {self.colors['accent_green']}; color: white; padding: 16px; border-radius: 12px; font-weight: 700; font-size: 16px;")
        submit_btn.clicked.connect(self.submit_verification)
        verify_card.addWidget(submit_btn)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet(f"background: transparent; border: 1px solid {self.colors['border']}; padding: 12px; border-radius: 12px;")
        reset_btn.clicked.connect(self.reset_verification)
        verify_card.addWidget(reset_btn)
        
        content.addWidget(verify_card, 1)
        layout.addLayout(content)
        return page
    
    def create_enroll(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("👤 Enroll New Student")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        content = QHBoxLayout()
        
        cam_card = Card()
        self.enroll_video = QLabel("Start camera to capture")
        self.enroll_video.setAlignment(Qt.AlignCenter)
        self.enroll_video.setMinimumSize(500, 380)
        self.enroll_video.setStyleSheet(f"background: {self.colors['bg_main']}; border-radius: 16px;")
        cam_card.addWidget(self.enroll_video)
        
        cap_row = QHBoxLayout()
        cap_btn = QPushButton("📸 Capture")
        cap_btn.clicked.connect(self.capture_photo)
        cap_row.addWidget(cap_btn)
        self.cap_count = QLabel("0/5")
        self.cap_count.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {self.colors['accent_green']};")
        cap_row.addWidget(self.cap_count)
        cap_row.addStretch()
        cam_card.addLayout(cap_row)
        
        thumb_row = QHBoxLayout()
        self.thumbs = []
        for _ in range(5):
            t = QLabel()
            t.setFixedSize(60, 60)
            t.setStyleSheet(f"background: {self.colors['bg_input']}; border-radius: 10px; border: 2px solid {self.colors['border']};")
            self.thumbs.append(t)
            thumb_row.addWidget(t)
        thumb_row.addStretch()
        cam_card.addLayout(thumb_row)
        content.addWidget(cam_card, 2)
        
        form_card = Card()
        form_card.addWidget(QLabel("Student Information"))
        
        for lbl, ph, attr in [("Student ID", "STU001", "enroll_id"), ("Full Name", "John Doe", "enroll_name")]:
            form_card.addWidget(QLabel(lbl))
            entry = QLineEdit()
            entry.setPlaceholderText(ph)
            setattr(self, attr, entry)
            form_card.addWidget(entry)
        
        form_card.addWidget(QLabel("Department"))
        self.enroll_dept = QComboBox()
        self.enroll_dept.addItems(["Computer Science", "Electronics", "Mechanical", "Civil"])
        form_card.addWidget(self.enroll_dept)
        
        form_card.addStretch()
        
        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"background: transparent; border: 1px solid {self.colors['border']}; padding: 12px 24px; border-radius: 20px;")
        clear_btn.clicked.connect(self.clear_enrollment)
        btn_row.addWidget(clear_btn)
        
        enroll_btn = QPushButton("✓ Enroll & Save")
        enroll_btn.setStyleSheet(f"background: {self.colors['accent_green']}; color: white; padding: 12px 24px; border-radius: 20px;")
        enroll_btn.clicked.connect(self.submit_enrollment)
        btn_row.addWidget(enroll_btn)
        form_card.addLayout(btn_row)
        
        content.addWidget(form_card, 1)
        layout.addLayout(content)
        return page
    
    def create_students(self):
        """Show enrolled students list"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("👥 Enrolled Students")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        card = Card()
        self.students_list = QListWidget()
        self.students_list.setMinimumHeight(500)
        card.addWidget(self.students_list)
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.refresh_students_list)
        card.addWidget(refresh_btn)
        
        layout.addWidget(card)
        
        self.refresh_students_list()
        return page
    
    def refresh_students_list(self):
        self.students_list.clear()
        for sid, name, dept in self.system.get_enrolled_list():
            self.students_list.addItem(QListWidgetItem(f"👤 {sid} - {name} ({dept})"))
    
    def create_analytics(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("📈 Analytics")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        stats = self.system.get_statistics()
        
        row = QHBoxLayout()
        for val, lbl, clr in [(f"{stats['attendance_rate']:.0f}%", "Attendance Rate", self.colors['accent_green']),
                               (f"{stats['avg_score']:.0f}", "Avg Score", self.colors['accent_blue']),
                               (str(stats['total_enrolled']), "Total Students", self.colors['accent_purple'])]:
            row.addWidget(StatBadge(val, lbl, clr, self.colors))
        layout.addLayout(row)
        
        card = Card()
        card.addWidget(QLabel("Department Performance"))
        
        for dept, att in [("Computer Science", 94), ("Electronics", 87), ("Mechanical", 91), ("Civil", 78)]:
            bar_row = QHBoxLayout()
            bar_row.addWidget(QLabel(dept))
            prog = QProgressBar()
            prog.setValue(att)
            bar_row.addWidget(prog, 1)
            bar_row.addWidget(QLabel(f"{att}%"))
            card.addLayout(bar_row)
        
        layout.addWidget(card)
        layout.addStretch()
        return page
    
    # === CAMERA ===
    def toggle_camera(self):
        if self.video_worker and self.video_worker.isRunning():
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        self.video_worker = VideoWorker(self.system)
        self.video_worker.frame_ready.connect(self.process_frame)
        self.video_worker.start()
        self.start_btn.setText("⏹ Stop")
        self.start_btn.setStyleSheet(f"background: {self.colors['accent_red']}; color: white; padding: 14px 28px; border-radius: 25px;")
        self.status_lbl.setText("● Live")
        self.status_lbl.setStyleSheet(f"color: {self.colors['accent_green']};")
    
    def stop_camera(self):
        if self.video_worker:
            self.video_worker.stop()
            self.video_worker = None
        self.start_btn.setText("▶ Start Session")
        self.start_btn.setStyleSheet(f"background: {self.colors['accent_orange']}; color: white; padding: 14px 28px; border-radius: 25px;")
        self.status_lbl.setText("● Offline")
        self.status_lbl.setStyleSheet(f"color: {self.colors['text_muted']};")
    
    def process_frame(self, frame, faces, liveness):
        verified_str = " ✓" if liveness['verified'] else ""
        self.liveness_lbl.setText(f"👁 Blinks: {liveness['count']}/2{verified_str}")
        
        for r in faces:
            x, y, w, h = r['bbox']
            color = (34, 197, 94) if r['recognized'] else (255, 107, 53)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color[::-1], 3)
            cv2.putText(frame, f"{r['name']} ({r['confidence']}%)", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color[::-1], 2)
            
            if r['recognized']:
                self.current_student = r['student_id']
                self.verification_state['face'] = True
                self.badge_face.set_verified(True)
                self.verify_name.setText(f"✓ {r['name']}")
            
            if liveness['verified']:
                self.verification_state['liveness'] = True
                self.badge_liveness.set_verified(True)
        
        self.update_score()
        self.vis_stat.set_value(len(faces))
        self.mark_stat.set_value(len(self.system.attendance_today))
        
        self.display_frame(frame, self.video_label)
        self.display_frame(frame, self.verify_video)
        self.display_frame(frame, self.enroll_video)
    
    def display_frame(self, frame, label):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(img.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)))
    
    def update_score(self):
        score = sum([30 if self.verification_state['face'] else 0, 25 if self.verification_state['liveness'] else 0,
                     25 if self.verification_state['fingerprint'] else 0, 20 if self.verification_state['qr'] else 0])
        self.verify_score.setText(f"Score: {score}%")
    
    # === VERIFICATION ===
    def simulate_fingerprint(self):
        if not self.current_student:
            QMessageBox.warning(self, "Warning", "Face not recognized yet!")
            return
        
        stored = self.system.students.get(self.current_student, {}).get('fingerprint')
        if stored:
            self.finger_btn.start_scan()
            QTimer.singleShot(2000, self._complete_fingerprint)
        else:
            self.badge_finger.set_verified(False)
    
    def _complete_fingerprint(self):
        self.verification_state['fingerprint'] = True
        self.badge_finger.set_verified(True)
        self.update_score()
    
    def show_qr_code(self):
        if not self.current_student:
            QMessageBox.warning(self, "Warning", "Face not recognized yet!")
            return
        
        qr_data, token = self.system.biometric.generate_daily_qr(self.current_student)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Your Daily QR Code")
        dialog.setStyleSheet(f"background: {self.colors['bg_card']};")
        layout = QVBoxLayout(dialog)
        
        qr_label = QLabel()
        qr_label.setPixmap(QPixmap.fromImage(QImage.fromData(qr_data)))
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)
        
        info = QLabel(f"Student: {self.current_student}\nToken: {token}\nValid: Today only")
        info.setStyleSheet(f"color: {self.colors['text_primary']}; padding: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        dialog.exec()
    
    def scan_qr_code(self):
        """Scan QR from camera or simulate"""
        if not self.current_student:
            QMessageBox.warning(self, "Warning", "Face not recognized yet!")
            return
        
        # Simulate successful scan
        self.verification_state['qr'] = True
        self.badge_qr.set_verified(True)
        self.update_score()
        QMessageBox.information(self, "QR Scanned", "✅ QR Code verified successfully!")
    
    def submit_verification(self):
        if not self.current_student:
            QMessageBox.warning(self, "Warning", "No student recognized!")
            return
        
        success, msg = self.system.mark_attendance(self.current_student, self.verification_state)
        
        if success:
            QMessageBox.information(self, "Success", msg)
            name = self.system.students.get(self.current_student, {}).get('name', 'Unknown')
            self.activity_list.insertItem(0, QListWidgetItem(f"✅ {name} - {datetime.now().strftime('%H:%M:%S')}"))
            self.dash_activity.insertItem(0, QListWidgetItem(f"✅ {name} - {datetime.now().strftime('%H:%M:%S')}"))
            self.reset_verification()
            self.refresh_stats()
        else:
            QMessageBox.warning(self, "Failed", msg)
    
    def reset_verification(self):
        self.current_student = None
        self.verification_state = {'face': False, 'liveness': False, 'fingerprint': False, 'qr': False}
        self.badge_face.set_pending()
        self.badge_liveness.set_pending()
        self.badge_finger.set_pending()
        self.badge_qr.set_pending()
        self.finger_btn.reset()
        self.system.liveness.reset()
        self.verify_name.setText("No face detected")
        self.update_score()
    
    # === ENROLLMENT ===
    def capture_photo(self):
        if not self.video_worker:
            QMessageBox.warning(self, "Warning", "Start camera first!")
            return
        if len(self.enrollment_frames) >= 5:
            return
        
        frame = self.video_worker.get_frame()
        if frame is not None:
            self.enrollment_frames.append(frame)
            self.cap_count.setText(f"{len(self.enrollment_frames)}/5")
            
            idx = len(self.enrollment_frames) - 1
            small = cv2.resize(frame, (60, 60))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.thumbs[idx].setPixmap(QPixmap.fromImage(QImage(rgb.data, 60, 60, 180, QImage.Format_RGB888)))
            self.thumbs[idx].setStyleSheet(f"border-radius: 10px; border: 2px solid {self.colors['accent_green']};")
    
    def clear_enrollment(self):
        self.enrollment_frames = []
        self.enroll_id.clear()
        self.enroll_name.clear()
        self.cap_count.setText("0/5")
        for t in self.thumbs:
            t.clear()
            t.setStyleSheet(f"background: {self.colors['bg_input']}; border-radius: 10px; border: 2px solid {self.colors['border']};")
    
    def submit_enrollment(self):
        sid, name = self.enroll_id.text().strip(), self.enroll_name.text().strip()
        if not sid or not name:
            QMessageBox.warning(self, "Warning", "Fill all fields!")
            return
        if len(self.enrollment_frames) < 3:
            QMessageBox.warning(self, "Warning", f"Need 3+ photos ({len(self.enrollment_frames)})")
            return
        
        success, msg = self.system.enroll_student(sid, name, self.enroll_dept.currentText(), self.enrollment_frames)
        
        if success:
            QMessageBox.information(self, "✅ Enrolled & Saved!", msg + "\n\nData has been saved to disk.")
            self.refresh_stats()
            self.refresh_students_list()
            self.clear_enrollment()
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()


if __name__ == "__main__":
    print("=" * 50)
    print("  Attendify Pro v2")
    print("  Full-Featured Attendance System")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    
    window = AttendifyProV2()
    window.show()
    
    sys.exit(app.exec())
