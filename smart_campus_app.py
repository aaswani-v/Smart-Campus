"""
Smart Campus - Professional Desktop Attendance System
Built with PySide6 + YOLO + OpenCV

Run: python smart_campus_app.py
"""

import sys
import cv2
import numpy as np
import pickle
import os
from datetime import datetime
from pathlib import Path
from collections import deque

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QProgressBar, QMessageBox, QSizePolicy, QSpacerItem,
    QGraphicsDropShadowEffect, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QBrush, QPen, QIcon

# Check for LBPH
try:
    _ = cv2.face.LBPHFaceRecognizer_create()
    LBPH_AVAILABLE = True
except:
    LBPH_AVAILABLE = False
    print("[WARN] opencv-contrib-python needed for face recognition")


# ============= STYLE CONSTANTS =============
COLORS = {
    'bg_dark': '#0f0f1a',
    'bg_card': '#16213e',
    'bg_elevated': '#1a1a2e',
    'accent_orange': '#ff6b35',
    'accent_green': '#22c55e',
    'accent_blue': '#3b82f6',
    'accent_red': '#ef4444',
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0a0',
    'text_muted': '#666666',
    'border': '#2a2a4a',
}

STYLE_SHEET = f"""
    QMainWindow {{
        background-color: {COLORS['bg_dark']};
    }}
    QWidget {{
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QLabel {{
        color: {COLORS['text_primary']};
    }}
    QPushButton {{
        background-color: {COLORS['accent_orange']};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: bold;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: #e85d04;
    }}
    QPushButton:pressed {{
        background-color: #d45500;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['text_muted']};
    }}
    QPushButton#secondary {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
    }}
    QPushButton#secondary:hover {{
        background-color: {COLORS['bg_elevated']};
    }}
    QPushButton#success {{
        background-color: {COLORS['accent_green']};
    }}
    QPushButton#danger {{
        background-color: {COLORS['accent_red']};
    }}
    QLineEdit {{
        background-color: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 12px 16px;
        color: {COLORS['text_primary']};
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border-color: {COLORS['accent_orange']};
    }}
    QListWidget {{
        background-color: {COLORS['bg_dark']};
        border: none;
        border-radius: 12px;
        padding: 8px;
    }}
    QListWidget::item {{
        background-color: {COLORS['bg_card']};
        border-radius: 8px;
        padding: 12px;
        margin: 4px 0;
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['accent_orange']};
    }}
    QProgressBar {{
        background-color: {COLORS['bg_card']};
        border-radius: 6px;
        height: 12px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent_green']};
        border-radius: 6px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
"""


# ============= FACE RECOGNITION SYSTEM =============
class FaceSystem:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Face Detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Face Recognition
        self.recognizer = cv2.face.LBPHFaceRecognizer_create() if LBPH_AVAILABLE else None
        
        # Data
        self.label_map = {}
        self.student_names = {}
        self.attendance_today = {}
        self._load_data()
    
    def _load_data(self):
        data_path = self.data_dir / "face_data.pkl"
        model_path = self.data_dir / "face_model.yml"
        
        if data_path.exists():
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.label_map = data.get('labels', {})
                self.student_names = data.get('names', {})
        
        if self.recognizer and model_path.exists():
            try:
                self.recognizer.read(str(model_path))
            except:
                pass
    
    def _save_data(self):
        with open(self.data_dir / "face_data.pkl", 'wb') as f:
            pickle.dump({'labels': self.label_map, 'names': self.student_names}, f)
        
        if self.recognizer:
            try:
                self.recognizer.write(str(self.data_dir / "face_model.yml"))
            except:
                pass
    
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    
    def preprocess_face(self, frame, rect):
        x, y, w, h = rect
        face = frame[y:y+h, x:x+w]
        if len(face.shape) == 3:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        return cv2.equalizeHist(cv2.resize(face, (200, 200)))
    
    def enroll(self, student_id, name, frames):
        if not self.recognizer:
            return False, "Recognition not available"
        
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
        
        self.label_map[label] = student_id
        self.student_names[student_id] = name
        self._save_data()
        return True, f"Enrolled {name}!"
    
    def recognize(self, frame, rect):
        if not self.recognizer or not self.label_map:
            return None, "Unknown", 0
        
        try:
            face = self.preprocess_face(frame, rect)
            label, conf = self.recognizer.predict(face)
            
            if label in self.label_map and conf < 85:
                sid = self.label_map[label]
                name = self.student_names.get(sid, "Unknown")
                return sid, name, int(max(0, 100 - conf))
        except:
            pass
        
        return None, "Unknown", 0
    
    def mark_attendance(self, student_id, name):
        today = datetime.now().strftime("%Y-%m-%d")
        
        if student_id in self.attendance_today:
            return False
        
        self.attendance_today[student_id] = {
            'name': name,
            'time': datetime.now().strftime("%H:%M:%S")
        }
        
        # Save to file
        log_path = self.data_dir / f"attendance_{today}.csv"
        with open(log_path, 'a') as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')},{student_id},{name}\n")
        
        return True
    
    def get_enrolled_count(self):
        return len(self.label_map)
    
    def get_today_attendance(self):
        return list(self.attendance_today.values())


# ============= VIDEO WORKER THREAD =============
class VideoWorker(QThread):
    frame_ready = Signal(np.ndarray, list)  # frame, detected faces
    
    def __init__(self, face_system):
        super().__init__()
        self.face_system = face_system
        self.running = False
        self.mode = "recognition"
        self.cap = None
    
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
            faces = self.face_system.detect_faces(frame)
            
            results = []
            for (x, y, w, h) in faces:
                if self.mode == "recognition":
                    sid, name, conf = self.face_system.recognize(frame, (x, y, w, h))
                    results.append({
                        'bbox': (x, y, w, h),
                        'student_id': sid,
                        'name': name,
                        'confidence': conf,
                        'recognized': sid is not None
                    })
                else:
                    results.append({
                        'bbox': (x, y, w, h),
                        'name': 'Enrollment',
                        'confidence': 100,
                        'recognized': False
                    })
            
            self.frame_ready.emit(frame, results)
            self.msleep(30)
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        self.running = False
        self.wait()
    
    def capture_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return cv2.flip(frame, 1)
        return None


# ============= CUSTOM WIDGETS =============
class CardWidget(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {COLORS['bg_card']};
                border-radius: 20px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 11px;
                font-weight: bold;
                color: {COLORS['text_muted']};
                text-transform: uppercase;
                letter-spacing: 2px;
            """)
            self.layout.addWidget(title_label)


class StatCard(QFrame):
    def __init__(self, value="0", label="Label", color=COLORS['accent_orange'], parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {COLORS['bg_elevated']};
                border-radius: 16px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 800;
            color: {color};
        """)
        layout.addWidget(self.value_label)
        
        desc_label = QLabel(label)
        desc_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(desc_label)
    
    def set_value(self, value):
        self.value_label.setText(str(value))


class NavButton(QPushButton):
    def __init__(self, text, icon_text="", active=False, parent=None):
        super().__init__(parent)
        self.setText(f"{icon_text}  {text}" if icon_text else text)
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.set_active(active)
    
    def set_active(self, active):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_orange']};
                    color: white;
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: bold;
                    font-size: 14px;
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-size: 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card']};
                    color: white;
                }}
            """)


# ============= MAIN WINDOW =============
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.face_system = FaceSystem()
        self.video_worker = None
        self.enrollment_frames = []
        
        self.setWindowTitle("Smart Campus - Attendance System")
        self.setMinimumSize(1400, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_card']};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(8)
        
        # Logo
        logo = QLabel("🎓 Smart Campus")
        logo.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {COLORS['accent_orange']};
            padding: 10px 0 30px 0;
        """)
        sidebar_layout.addWidget(logo)
        
        # Navigation
        self.nav_buttons = []
        nav_items = [
            ("Dashboard", "📊", 0),
            ("Monitoring", "📹", 1),
            ("Enroll", "👤", 2),
            ("Attendance", "📋", 3),
        ]
        
        for text, icon, idx in nav_items:
            btn = NavButton(text, icon, active=(idx == 1))
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)
        
        sidebar_layout.addStretch()
        
        # Stats
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            background-color: {COLORS['bg_elevated']};
            border-radius: 16px;
            padding: 16px;
        """)
        stats_layout = QVBoxLayout(stats_frame)
        
        self.enrolled_stat = QLabel(f"👥 Enrolled: {self.face_system.get_enrolled_count()}")
        self.enrolled_stat.setStyleSheet("font-size: 13px; padding: 8px;")
        stats_layout.addWidget(self.enrolled_stat)
        
        self.present_stat = QLabel(f"✅ Present: {len(self.face_system.attendance_today)}")
        self.present_stat.setStyleSheet("font-size: 13px; padding: 8px;")
        stats_layout.addWidget(self.present_stat)
        
        sidebar_layout.addWidget(stats_frame)
        
        main_layout.addWidget(sidebar)
        
        # === MAIN CONTENT ===
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        self.stack.addWidget(self.create_dashboard_page())
        self.stack.addWidget(self.create_monitoring_page())
        self.stack.addWidget(self.create_enroll_page())
        self.stack.addWidget(self.create_attendance_page())
        
        self.stack.setCurrentIndex(1)  # Start on Monitoring
        
        main_layout.addWidget(self.stack)
    
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.set_active(i == index)
    
    # === PAGE BUILDERS ===
    
    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("📊 Dashboard")
        header.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(header)
        
        # Stats Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        self.dash_enrolled = StatCard("0", "Students Enrolled", COLORS['accent_blue'])
        self.dash_present = StatCard("0", "Present Today", COLORS['accent_green'])
        self.dash_absent = StatCard("0", "Absent", COLORS['accent_red'])
        self.dash_rate = StatCard("0%", "Attendance Rate", COLORS['accent_orange'])
        
        for card in [self.dash_enrolled, self.dash_present, self.dash_absent, self.dash_rate]:
            stats_row.addWidget(card)
        
        layout.addLayout(stats_row)
        
        # Quick Actions
        actions_card = CardWidget("Quick Actions")
        actions_layout = QHBoxLayout()
        
        start_btn = QPushButton("▶ Start Monitoring")
        start_btn.setFixedHeight(50)
        start_btn.clicked.connect(lambda: self.switch_page(1))
        actions_layout.addWidget(start_btn)
        
        enroll_btn = QPushButton("👤 Enroll Student")
        enroll_btn.setFixedHeight(50)
        enroll_btn.setObjectName("secondary")
        enroll_btn.clicked.connect(lambda: self.switch_page(2))
        actions_layout.addWidget(enroll_btn)
        
        actions_card.layout.addLayout(actions_layout)
        layout.addWidget(actions_card)
        
        layout.addStretch()
        
        return page
    
    def create_monitoring_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)
        
        # Left - Video Feed
        left = QVBoxLayout()
        left.setSpacing(16)
        
        # Header
        header_row = QHBoxLayout()
        title = QLabel("📹 Live Monitoring")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_row.addWidget(title)
        
        self.status_indicator = QLabel("● Offline")
        self.status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        header_row.addStretch()
        header_row.addWidget(self.status_indicator)
        left.addLayout(header_row)
        
        # Video Frame
        video_card = CardWidget()
        video_card.setMinimumHeight(500)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            border-radius: 16px;
            min-height: 400px;
        """)
        self.video_label.setText("Click 'Start Camera' to begin")
        video_card.layout.addWidget(self.video_label)
        
        left.addWidget(video_card)
        
        # Controls
        controls = QHBoxLayout()
        
        self.start_cam_btn = QPushButton("▶ Start Camera")
        self.start_cam_btn.setFixedSize(180, 50)
        self.start_cam_btn.clicked.connect(self.toggle_camera)
        controls.addWidget(self.start_cam_btn)
        
        controls.addStretch()
        left.addLayout(controls)
        
        layout.addLayout(left, 2)
        
        # Right - Info Panel
        right = QVBoxLayout()
        right.setSpacing(16)
        
        # Stats
        stats_card = CardWidget("ATTENDANCE METRICS")
        stats_grid = QHBoxLayout()
        
        self.visible_stat = StatCard("0", "Visible", COLORS['text_primary'])
        self.marked_stat = StatCard("0", "Marked", COLORS['accent_green'])
        
        stats_grid.addWidget(self.visible_stat)
        stats_grid.addWidget(self.marked_stat)
        stats_card.layout.addLayout(stats_grid)
        right.addWidget(stats_card)
        
        # Log
        log_card = CardWidget("RECENT ACTIVITY")
        self.activity_list = QListWidget()
        self.activity_list.setMinimumHeight(300)
        log_card.layout.addWidget(self.activity_list)
        right.addWidget(log_card)
        
        layout.addLayout(right, 1)
        
        return page
    
    def create_enroll_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(24)
        
        # Left - Camera
        left = QVBoxLayout()
        
        title = QLabel("👤 Enroll New Student")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        left.addWidget(title)
        
        # Enroll Video
        self.enroll_video_label = QLabel()
        self.enroll_video_label.setAlignment(Qt.AlignCenter)
        self.enroll_video_label.setMinimumSize(640, 480)
        self.enroll_video_label.setStyleSheet(f"""
            background-color: {COLORS['bg_card']};
            border-radius: 20px;
            border: 2px solid {COLORS['border']};
        """)
        self.enroll_video_label.setText("Start camera to capture photos")
        left.addWidget(self.enroll_video_label)
        
        # Capture controls
        cap_row = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture Photo")
        self.capture_btn.setFixedHeight(50)
        self.capture_btn.clicked.connect(self.capture_enrollment_photo)
        cap_row.addWidget(self.capture_btn)
        
        self.capture_count = QLabel("0/5 photos")
        self.capture_count.setStyleSheet("font-size: 16px; font-weight: bold;")
        cap_row.addWidget(self.capture_count)
        
        left.addLayout(cap_row)
        
        layout.addLayout(left, 2)
        
        # Right - Form
        right_card = CardWidget("STUDENT INFORMATION")
        right_card.setMaximumWidth(400)
        
        # Form fields
        id_label = QLabel("Student ID")
        id_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']}; margin-top: 10px;")
        right_card.layout.addWidget(id_label)
        
        self.enroll_id = QLineEdit()
        self.enroll_id.setPlaceholderText("e.g. STU001")
        right_card.layout.addWidget(self.enroll_id)
        
        name_label = QLabel("Full Name")
        name_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']}; margin-top: 10px;")
        right_card.layout.addWidget(name_label)
        
        self.enroll_name = QLineEdit()
        self.enroll_name.setPlaceholderText("e.g. John Doe")
        right_card.layout.addWidget(self.enroll_name)
        
        # Preview thumbnails
        preview_label = QLabel("Captured Photos")
        preview_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']}; margin-top: 20px;")
        right_card.layout.addWidget(preview_label)
        
        self.preview_row = QHBoxLayout()
        for i in range(5):
            thumb = QLabel()
            thumb.setFixedSize(50, 50)
            thumb.setStyleSheet(f"""
                background-color: {COLORS['bg_elevated']};
                border-radius: 8px;
                border: 1px solid {COLORS['border']};
            """)
            self.preview_row.addWidget(thumb)
        right_card.layout.addLayout(self.preview_row)
        
        right_card.layout.addSpacing(20)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self.clear_enrollment)
        btn_row.addWidget(clear_btn)
        
        enroll_btn = QPushButton("✅ Enroll Student")
        enroll_btn.setObjectName("success")
        enroll_btn.clicked.connect(self.submit_enrollment)
        btn_row.addWidget(enroll_btn)
        
        right_card.layout.addLayout(btn_row)
        right_card.layout.addStretch()
        
        layout.addWidget(right_card)
        
        return page
    
    def create_attendance_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        title = QLabel("📋 Today's Attendance")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # Attendance list
        list_card = CardWidget()
        self.attendance_list = QListWidget()
        self.attendance_list.setMinimumHeight(500)
        list_card.layout.addWidget(self.attendance_list)
        layout.addWidget(list_card)
        
        # Export button
        export_btn = QPushButton("📥 Export to CSV")
        export_btn.setFixedWidth(200)
        export_btn.setObjectName("secondary")
        layout.addWidget(export_btn)
        
        return page
    
    # === CAMERA FUNCTIONS ===
    
    def toggle_camera(self):
        if self.video_worker and self.video_worker.isRunning():
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        self.video_worker = VideoWorker(self.face_system)
        self.video_worker.frame_ready.connect(self.process_frame)
        self.video_worker.start()
        
        self.start_cam_btn.setText("⏹ Stop Camera")
        self.start_cam_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_red']};
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }}
        """)
        self.status_indicator.setText("● Live")
        self.status_indicator.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px;")
    
    def stop_camera(self):
        if self.video_worker:
            self.video_worker.stop()
            self.video_worker = None
        
        self.start_cam_btn.setText("▶ Start Camera")
        self.start_cam_btn.setStyleSheet("")
        self.status_indicator.setText("● Offline")
        self.status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        self.video_label.clear()
        self.video_label.setText("Click 'Start Camera' to begin")
    
    def process_frame(self, frame, results):
        # Draw detections
        for r in results:
            x, y, w, h = r['bbox']
            color = (0, 255, 0) if r['recognized'] else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
            
            label = f"{r['name']} ({r['confidence']}%)" if r['recognized'] else "Unknown"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Mark attendance
            if r['recognized'] and r.get('student_id'):
                if self.face_system.mark_attendance(r['student_id'], r['name']):
                    self.add_activity(f"✅ {r['name']} marked present")
        
        # Update stats
        self.visible_stat.set_value(len(results))
        self.marked_stat.set_value(len(self.face_system.attendance_today))
        
        # Display frame
        self.display_frame(frame, self.video_label)
        
        # Also show on enroll page if active
        if self.stack.currentIndex() == 2:
            self.display_frame(frame, self.enroll_video_label)
    
    def display_frame(self, frame, label):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        
        scaled = img.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(QPixmap.fromImage(scaled))
    
    def add_activity(self, text):
        item = QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - {text}")
        self.activity_list.insertItem(0, item)
        
        # Update sidebar stats
        self.present_stat.setText(f"✅ Present: {len(self.face_system.attendance_today)}")
    
    # === ENROLLMENT FUNCTIONS ===
    
    def capture_enrollment_photo(self):
        if not self.video_worker or not self.video_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Start the camera first!")
            return
        
        if len(self.enrollment_frames) >= 5:
            QMessageBox.information(self, "Info", "Already captured 5 photos!")
            return
        
        frame = self.video_worker.capture_frame()
        if frame is not None:
            self.enrollment_frames.append(frame)
            self.capture_count.setText(f"{len(self.enrollment_frames)}/5 photos")
            
            # Update thumbnail
            idx = len(self.enrollment_frames) - 1
            thumb = self.preview_row.itemAt(idx).widget()
            if thumb:
                small = cv2.resize(frame, (50, 50))
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                img = QImage(rgb.data, 50, 50, 150, QImage.Format_RGB888)
                thumb.setPixmap(QPixmap.fromImage(img))
    
    def clear_enrollment(self):
        self.enrollment_frames = []
        self.enroll_id.clear()
        self.enroll_name.clear()
        self.capture_count.setText("0/5 photos")
        
        for i in range(5):
            thumb = self.preview_row.itemAt(i).widget()
            if thumb:
                thumb.clear()
    
    def submit_enrollment(self):
        sid = self.enroll_id.text().strip()
        name = self.enroll_name.text().strip()
        
        if not sid or not name:
            QMessageBox.warning(self, "Warning", "Please enter Student ID and Name!")
            return
        
        if len(self.enrollment_frames) < 3:
            QMessageBox.warning(self, "Warning", f"Need at least 3 photos. Have {len(self.enrollment_frames)}")
            return
        
        success, msg = self.face_system.enroll(sid, name, self.enrollment_frames)
        
        if success:
            QMessageBox.information(self, "Success", msg)
            self.enrolled_stat.setText(f"👥 Enrolled: {self.face_system.get_enrolled_count()}")
            self.clear_enrollment()
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()


# ============= MAIN =============
if __name__ == "__main__":
    print("=" * 50)
    print("  Smart Campus - Desktop Attendance System")
    print("  Version 1.0")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
