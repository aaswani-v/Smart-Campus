"""
Attendify - Professional Desktop Attendance System
Exact replica of the React frontend design
Built with PySide6 + YOLO + OpenCV

Run: python attendify_desktop.py
"""

import sys
import cv2
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import random

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QProgressBar, QMessageBox, QSizePolicy, QSpacerItem,
    QGraphicsDropShadowEffect, QScrollArea, QComboBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QBrush, QPen, QIcon, QFontDatabase, QPainterPath

# Check for LBPH
try:
    _ = cv2.face.LBPHFaceRecognizer_create()
    LBPH_AVAILABLE = True
except:
    LBPH_AVAILABLE = False
    print("[WARN] opencv-contrib-python needed for face recognition")


# ============= DESIGN TOKENS (from React frontend) =============
COLORS = {
    # Light Theme
    'bg_main': '#F5F5F3',
    'bg_card': '#FFFFFF',
    'bg_header': '#FFFFFF',
    'bg_input': '#F9FAFB',
    
    # Accent Colors
    'accent_orange': '#FF6B35',
    'accent_orange_hover': '#E85D04',
    'accent_grey': '#9CA3AF',
    'accent_green': '#22C55E',
    'accent_blue': '#3B82F6',
    'accent_red': '#EF4444',
    'accent_purple': '#8B5CF6',
    'accent_pink': '#EC4899',
    
    # Text Colors
    'text_primary': '#1A1A1A',
    'text_secondary': '#6B7280',
    'text_muted': '#9CA3AF',
    
    # Borders
    'border': '#E5E7EB',
    'border_light': '#F3F4F6',
}

FONTS = {
    'primary': 'Inter',
    'fallback': 'Segoe UI, Arial',
}

RADIUS = {
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 20,
    'xxl': 24,
    'pill': 9999,
}

SHADOWS = {
    'card': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)',
    'lg': '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)',
}


# ============= MAIN STYLESHEET =============
STYLE_SHEET = f"""
    QMainWindow, QWidget#mainContainer {{
        background-color: {COLORS['bg_main']};
    }}
    QWidget {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        color: {COLORS['text_primary']};
    }}
    QLabel {{
        background: transparent;
    }}
    
    /* Cards */
    QFrame#card {{
        background-color: {COLORS['bg_card']};
        border-radius: {RADIUS['xxl']}px;
        border: 1px solid {COLORS['border_light']};
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {COLORS['accent_orange']};
        color: white;
        border: none;
        border-radius: {RADIUS['pill']}px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_orange_hover']};
    }}
    QPushButton:pressed {{
        background-color: #d45500;
    }}
    QPushButton#secondary {{
        background-color: {COLORS['text_primary']};
        color: white;
    }}
    QPushButton#secondary:hover {{
        background-color: #333333;
    }}
    QPushButton#outline {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
    }}
    QPushButton#outline:hover {{
        background-color: {COLORS['bg_input']};
    }}
    QPushButton#navActive {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
        font-weight: 600;
    }}
    QPushButton#nav {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
    }}
    QPushButton#nav:hover {{
        background-color: {COLORS['bg_input']};
        color: {COLORS['text_primary']};
    }}
    
    /* Inputs */
    QLineEdit, QComboBox {{
        background-color: {COLORS['bg_input']};
        border: 1px solid {COLORS['border']};
        border-radius: {RADIUS['md']}px;
        padding: 14px 18px;
        font-size: 14px;
        color: {COLORS['text_primary']};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {COLORS['accent_orange']};
    }}
    QLineEdit::placeholder {{
        color: {COLORS['text_muted']};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 15px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border: none;
    }}
    
    /* List Widget */
    QListWidget {{
        background: transparent;
        border: none;
    }}
    QListWidget::item {{
        background-color: {COLORS['bg_card']};
        border-radius: {RADIUS['lg']}px;
        padding: 16px;
        margin: 6px 0;
        border: 1px solid {COLORS['border_light']};
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['accent_orange']};
        color: white;
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {COLORS['bg_input']};
        border-radius: 6px;
        height: 8px;
        text-align: center;
        border: none;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent_orange']};
        border-radius: 6px;
    }}
    
    /* Scroll Area */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""


# ============= FACE RECOGNITION SYSTEM =============
class FaceSystem:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create() if LBPH_AVAILABLE else None
        
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
            self.recognizer.write(str(self.data_dir / "face_model.yml"))
    
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
                return sid, self.student_names.get(sid, "Unknown"), int(max(0, 100 - conf))
        except:
            pass
        return None, "Unknown", 0
    
    def mark_attendance(self, student_id, name):
        if student_id in self.attendance_today:
            return False
        self.attendance_today[student_id] = {'name': name, 'time': datetime.now().strftime("%H:%M:%S")}
        today = datetime.now().strftime("%Y-%m-%d")
        with open(self.data_dir / f"attendance_{today}.csv", 'a') as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')},{student_id},{name}\n")
        return True
    
    def get_enrolled_count(self):
        return len(self.label_map)


# ============= VIDEO WORKER =============
class VideoWorker(QThread):
    frame_ready = Signal(np.ndarray, list)
    
    def __init__(self, face_system):
        super().__init__()
        self.face_system = face_system
        self.running = False
        self.mode = "recognition"
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
            faces = self.face_system.detect_faces(frame)
            
            results = []
            for (x, y, w, h) in faces:
                if self.mode == "recognition":
                    sid, name, conf = self.face_system.recognize(frame, (x, y, w, h))
                    results.append({'bbox': (x, y, w, h), 'student_id': sid, 'name': name, 'confidence': conf, 'recognized': sid is not None})
                else:
                    results.append({'bbox': (x, y, w, h), 'name': 'Enrollment', 'confidence': 100, 'recognized': False})
            
            self.frame_ready.emit(frame, results)
            self.msleep(30)
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        self.running = False
        self.wait()
    
    def get_current_frame(self):
        return self.current_frame


# ============= CUSTOM WIDGETS =============

class Card(QFrame):
    """Modern card with shadow and rounded corners"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 28, 28, 28)
        self._layout.setSpacing(20)
    
    def addWidget(self, widget):
        self._layout.addWidget(widget)
    
    def addLayout(self, layout):
        self._layout.addLayout(layout)


class NavPill(QPushButton):
    """Navigation pill button"""
    def __init__(self, text, active=False, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setMinimumWidth(100)
        self.update_style()
        self.toggled.connect(self.update_style)
    
    def update_style(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 20px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 20px;
                    padding: 10px 20px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    color: {COLORS['text_primary']};
                }}
            """)


class StatBadge(QFrame):
    """Stat display with colored accent"""
    def __init__(self, value, label, color=COLORS['accent_orange'], parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: {RADIUS['xl']}px;
                border: 1px solid {COLORS['border_light']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)
        
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {color};
        """)
        layout.addWidget(self.value_label)
        
        desc = QLabel(label)
        desc.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(desc)
    
    def set_value(self, val):
        self.value_label.setText(str(val))


class ProgressBarHorizontal(QWidget):
    """Horizontal progress bar with label"""
    def __init__(self, label, value, max_value=100, color=COLORS['accent_orange'], parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(16)
        
        # Label
        lbl = QLabel(label)
        lbl.setFixedWidth(150)
        lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text_primary']};")
        layout.addWidget(lbl)
        
        # Progress bar container
        bar_container = QWidget()
        bar_container.setFixedHeight(10)
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        # Calculate width percentage
        pct = min(1, value / max_value) if max_value > 0 else 0
        
        # Filled part
        filled = QFrame()
        filled.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        bar_layout.addWidget(filled, int(pct * 100))
        
        # Empty part
        if pct < 1:
            empty = QFrame()
            empty.setStyleSheet(f"background-color: {COLORS['bg_input']}; border-radius: 5px;")
            bar_layout.addWidget(empty, int((1 - pct) * 100))
        
        layout.addWidget(bar_container, 1)
        
        # Value
        val_lbl = QLabel(f"{value}%")
        val_lbl.setFixedWidth(50)
        val_lbl.setAlignment(Qt.AlignRight)
        val_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_primary']};")
        layout.addWidget(val_lbl)


# ============= MAIN WINDOW =============
class AttendifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.face_system = FaceSystem()
        self.video_worker = None
        self.enrollment_frames = []
        
        self.setWindowTitle("Attendify - Smart Attendance System")
        self.setMinimumSize(1400, 850)
        self.setStyleSheet(STYLE_SHEET)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        self.setCentralWidget(main_container)
        
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === HEADER ===
        header = self.create_header()
        main_layout.addWidget(header)
        
        # === CONTENT STACK ===
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(40, 30, 40, 30)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_home_page())
        self.stack.addWidget(self.create_monitoring_page())
        self.stack.addWidget(self.create_enroll_page())
        self.stack.addWidget(self.create_schedule_page())
        self.stack.addWidget(self.create_analytics_page())
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_container)
        
        # Start on Home
        self.switch_page(0)
    
    def create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_header']};
                border-bottom: 1px solid {COLORS['border_light']};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo
        logo = QLabel("A  attendify")
        logo.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        # Make the A orange
        layout.addWidget(logo)
        
        layout.addSpacing(60)
        
        # Navigation Pills
        nav_container = QFrame()
        nav_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border-radius: 25px;
                padding: 4px;
            }}
        """)
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(4)
        
        self.nav_buttons = []
        nav_items = ["Home", "Monitoring", "Enroll", "Schedule", "Analytics"]
        
        for i, text in enumerate(nav_items):
            btn = NavPill(text, active=(i == 0))
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        
        layout.addWidget(nav_container)
        layout.addStretch()
        
        # Right side icons (placeholder)
        icons_container = QHBoxLayout()
        icons_container.setSpacing(16)
        
        for icon in ["🔍", "🌙", "🔔"]:
            lbl = QLabel(icon)
            lbl.setStyleSheet(f"font-size: 18px; color: {COLORS['text_secondary']};")
            icons_container.addWidget(lbl)
        
        # Profile avatar
        avatar = QLabel("👤")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            border-radius: 18px;
            font-size: 16px;
        """)
        icons_container.addWidget(avatar)
        
        layout.addLayout(icons_container)
        
        return header
    
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.update_style()
    
    # === PAGE BUILDERS ===
    
    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        header_row.addWidget(title)
        header_row.addStretch()
        
        # Filters
        filter_btn = QPushButton("Facial Recognition")
        filter_btn.setObjectName("outline")
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 13px;
            }}
        """)
        header_row.addWidget(filter_btn)
        
        layout.addLayout(header_row)
        
        # Stats Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        self.home_enrolled = StatBadge(self.face_system.get_enrolled_count() if hasattr(self, 'face_system') else 0, "Students Enrolled", COLORS['accent_blue'])
        self.home_present = StatBadge(0, "Present Today", COLORS['accent_green'])
        self.home_sessions = StatBadge(0, "Active Sessions", COLORS['accent_purple'])
        self.home_rate = StatBadge("0%", "Attendance Rate", COLORS['accent_orange'])
        
        for card in [self.home_enrolled, self.home_present, self.home_sessions, self.home_rate]:
            stats_row.addWidget(card)
        
        layout.addLayout(stats_row)
        
        # Main content grid
        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        
        # Left card - Recent Activity
        activity_card = Card()
        activity_title = QLabel("Recent Activity")
        activity_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        activity_card.addWidget(activity_title)
        
        self.home_activity_list = QListWidget()
        self.home_activity_list.setMaximumHeight(300)
        activity_card.addWidget(self.home_activity_list)
        
        content_row.addWidget(activity_card, 2)
        
        # Right card - Quick Actions
        actions_card = Card()
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: 600;")
        actions_card.addWidget(actions_title)
        
        start_btn = QPushButton("▶  Start Session")
        start_btn.setFixedHeight(50)
        start_btn.clicked.connect(lambda: self.switch_page(1))
        actions_card.addWidget(start_btn)
        
        enroll_btn = QPushButton("+ Enroll Student")
        enroll_btn.setObjectName("secondary")
        enroll_btn.setFixedHeight(50)
        enroll_btn.clicked.connect(lambda: self.switch_page(2))
        actions_card.addWidget(enroll_btn)
        
        content_row.addWidget(actions_card, 1)
        
        layout.addLayout(content_row)
        layout.addStretch()
        
        return page
    
    def create_monitoring_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header
        header_row = QHBoxLayout()
        title = QLabel("Live Monitoring")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        header_row.addWidget(title)
        header_row.addStretch()
        
        self.status_indicator = QLabel("● Offline")
        self.status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        header_row.addWidget(self.status_indicator)
        
        layout.addLayout(header_row)
        
        # Main content
        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        
        # Video Card
        video_card = Card()
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet(f"""
            background-color: {COLORS['bg_main']};
            border-radius: {RADIUS['xl']}px;
        """)
        self.video_label.setText("Click 'Start Session' to begin monitoring")
        video_card.addWidget(self.video_label)
        
        # Controls
        ctrl_row = QHBoxLayout()
        
        self.start_btn = QPushButton("▶  Start Session")
        self.start_btn.setFixedSize(180, 50)
        self.start_btn.clicked.connect(self.toggle_camera)
        ctrl_row.addWidget(self.start_btn)
        
        ctrl_row.addStretch()
        video_card.addLayout(ctrl_row)
        
        content_row.addWidget(video_card, 2)
        
        # Side Panel
        side_panel = QVBoxLayout()
        side_panel.setSpacing(16)
        
        # Stats
        stats_card = Card()
        stats_title = QLabel("SESSION METRICS")
        stats_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        stats_card.addWidget(stats_title)
        
        stats_grid = QHBoxLayout()
        self.visible_stat = StatBadge(0, "Visible", COLORS['text_primary'])
        self.marked_stat = StatBadge(0, "Marked", COLORS['accent_green'])
        stats_grid.addWidget(self.visible_stat)
        stats_grid.addWidget(self.marked_stat)
        stats_card.addLayout(stats_grid)
        
        side_panel.addWidget(stats_card)
        
        # Activity Log
        log_card = Card()
        log_title = QLabel("ACTIVITY LOG")
        log_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 1px;")
        log_card.addWidget(log_title)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(250)
        log_card.addWidget(self.activity_list)
        
        side_panel.addWidget(log_card)
        side_panel.addStretch()
        
        content_row.addLayout(side_panel, 1)
        layout.addLayout(content_row)
        
        return page
    
    def create_enroll_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header
        title = QLabel("Enroll New Student")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        # Progress steps
        steps_row = QHBoxLayout()
        steps = ["Student Information", "Face Capture", "Biometrics", "Complete"]
        for i, step in enumerate(steps):
            step_widget = QFrame()
            step_layout = QHBoxLayout(step_widget)
            step_layout.setContentsMargins(0, 0, 0, 0)
            
            # Number circle
            num = QLabel(str(i + 1))
            num.setFixedSize(28, 28)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(f"""
                background-color: {COLORS['accent_orange'] if i == 1 else COLORS['bg_input']};
                color: {'white' if i == 1 else COLORS['text_secondary']};
                border-radius: 14px;
                font-weight: 600;
                font-size: 12px;
            """)
            step_layout.addWidget(num)
            
            # Label
            lbl = QLabel(step)
            lbl.setStyleSheet(f"color: {COLORS['text_primary'] if i == 1 else COLORS['text_secondary']}; font-size: 14px;")
            step_layout.addWidget(lbl)
            
            steps_row.addWidget(step_widget)
            if i < len(steps) - 1:
                line = QFrame()
                line.setFixedHeight(2)
                line.setStyleSheet(f"background-color: {COLORS['border']};")
                steps_row.addWidget(line, 1)
        
        layout.addLayout(steps_row)
        
        # Main content
        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        
        # Left - Camera
        camera_card = Card()
        
        cam_title = QLabel("Face Capture")
        cam_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        camera_card.addWidget(cam_title)
        
        self.enroll_video = QLabel()
        self.enroll_video.setAlignment(Qt.AlignCenter)
        self.enroll_video.setMinimumSize(500, 380)
        self.enroll_video.setStyleSheet(f"""
            background-color: {COLORS['bg_main']};
            border-radius: {RADIUS['xl']}px;
            border: 2px solid {COLORS['border']};
        """)
        self.enroll_video.setText("Start camera to capture photos")
        camera_card.addWidget(self.enroll_video)
        
        # Capture controls
        cap_row = QHBoxLayout()
        
        self.capture_btn = QPushButton("📸 Capture")
        self.capture_btn.setFixedHeight(45)
        self.capture_btn.clicked.connect(self.capture_photo)
        cap_row.addWidget(self.capture_btn)
        
        self.capture_count = QLabel("0/5")
        self.capture_count.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['accent_green']};")
        cap_row.addWidget(self.capture_count)
        
        cap_row.addStretch()
        camera_card.addLayout(cap_row)
        
        # Thumbnails
        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(10)
        self.thumb_labels = []
        for i in range(5):
            thumb = QLabel()
            thumb.setFixedSize(60, 60)
            thumb.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                border-radius: 10px;
                border: 2px solid {COLORS['border']};
            """)
            thumb.setAlignment(Qt.AlignCenter)
            self.thumb_labels.append(thumb)
            thumb_row.addWidget(thumb)
        thumb_row.addStretch()
        camera_card.addLayout(thumb_row)
        
        content_row.addWidget(camera_card, 2)
        
        # Right - Form
        form_card = Card()
        
        form_title = QLabel("Student Information")
        form_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        form_card.addWidget(form_title)
        
        # Form fields
        id_lbl = QLabel("Student ID")
        id_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; margin-top: 10px;")
        form_card.addWidget(id_lbl)
        
        self.enroll_id = QLineEdit()
        self.enroll_id.setPlaceholderText("e.g. STU001")
        form_card.addWidget(self.enroll_id)
        
        name_lbl = QLabel("Full Name")
        name_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; margin-top: 10px;")
        form_card.addWidget(name_lbl)
        
        self.enroll_name = QLineEdit()
        self.enroll_name.setPlaceholderText("e.g. John Doe")
        form_card.addWidget(self.enroll_name)
        
        dept_lbl = QLabel("Department")
        dept_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; margin-top: 10px;")
        form_card.addWidget(dept_lbl)
        
        self.enroll_dept = QComboBox()
        self.enroll_dept.addItems(["Computer Science", "Electronics", "Mechanical", "Civil"])
        form_card.addWidget(self.enroll_dept)
        
        # Spacer
        form_card._layout.addStretch()
        
        # Buttons
        btn_row = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("outline")
        clear_btn.clicked.connect(self.clear_enrollment)
        btn_row.addWidget(clear_btn)
        
        enroll_btn = QPushButton("✓ Enroll Student")
        enroll_btn.clicked.connect(self.submit_enrollment)
        btn_row.addWidget(enroll_btn)
        
        form_card.addLayout(btn_row)
        
        content_row.addWidget(form_card, 1)
        layout.addLayout(content_row)
        
        return page
    
    def create_schedule_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header
        header_row = QHBoxLayout()
        title = QLabel("Class Schedule")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        header_row.addWidget(title)
        header_row.addStretch()
        
        add_btn = QPushButton("+ Add Class")
        add_btn.setObjectName("secondary")
        header_row.addWidget(add_btn)
        
        layout.addLayout(header_row)
        
        # Calendar Card
        cal_card = Card()
        
        # Days header
        days_row = QHBoxLayout()
        days = ["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            lbl = QLabel(day)
            lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLORS['text_secondary']};")
            lbl.setAlignment(Qt.AlignCenter)
            days_row.addWidget(lbl, 1)
        cal_card.addLayout(days_row)
        
        # Time slots
        times = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
        
        # Sample classes
        classes = {
            (0, 1): ("CS101", "Data Structures", COLORS['accent_blue']),
            (1, 2): ("CS201", "Algorithms", COLORS['accent_orange']),
            (2, 3): ("CS301", "Database", COLORS['accent_green']),
            (3, 4): ("CS102", "Networks", COLORS['accent_purple']),
            (4, 0): ("CS202", "OS", COLORS['accent_pink']),
        }
        
        for row, time in enumerate(times):
            row_layout = QHBoxLayout()
            
            # Time label
            time_lbl = QLabel(time)
            time_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
            time_lbl.setAlignment(Qt.AlignCenter)
            row_layout.addWidget(time_lbl, 1)
            
            # Day cells
            for col in range(5):
                cell = QFrame()
                cell.setFixedHeight(50)
                cell.setStyleSheet(f"""
                    background-color: {COLORS['bg_input']};
                    border-radius: 8px;
                    margin: 2px;
                """)
                
                # Check if there's a class
                if (row, col) in classes:
                    code, name, color = classes[(row, col)]
                    cell.setStyleSheet(f"""
                        background-color: {color};
                        border-radius: 8px;
                        margin: 2px;
                    """)
                    cell_layout = QVBoxLayout(cell)
                    cell_layout.setContentsMargins(8, 4, 8, 4)
                    
                    code_lbl = QLabel(code)
                    code_lbl.setStyleSheet("color: white; font-weight: 600; font-size: 12px;")
                    cell_layout.addWidget(code_lbl)
                    
                    name_lbl = QLabel(name)
                    name_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 10px;")
                    cell_layout.addWidget(name_lbl)
                
                row_layout.addWidget(cell, 1)
            
            cal_card.addLayout(row_layout)
        
        layout.addWidget(cal_card)
        layout.addStretch()
        
        return page
    
    def create_analytics_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Header
        title = QLabel("Analytics")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        
        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        stats = [
            ("92%", "Avg Attendance", COLORS['accent_green']),
            ("78%", "Avg Attention", COLORS['accent_blue']),
            ("12", "Active Courses", COLORS['accent_purple']),
            ("156", "Total Students", COLORS['accent_orange']),
        ]
        
        for val, label, color in stats:
            card = StatBadge(val, label, color)
            stats_row.addWidget(card)
        
        layout.addLayout(stats_row)
        
        # Content row
        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        
        # Course Performance Card
        perf_card = Card()
        perf_title = QLabel("Course Performance")
        perf_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        perf_card.addWidget(perf_title)
        
        courses = [
            ("CS101 - Data Structures", 94),
            ("CS201 - Algorithms", 87),
            ("CS301 - Database", 91),
            ("CS102 - Networks", 76),
            ("CS202 - Operating Systems", 82),
        ]
        
        for course, attendance in courses:
            bar = ProgressBarHorizontal(course, attendance, color=COLORS['accent_orange'])
            perf_card.addWidget(bar)
        
        content_row.addWidget(perf_card, 2)
        
        # Attention Card
        attn_card = Card()
        attn_title = QLabel("Attention Metrics")
        attn_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        attn_card.addWidget(attn_title)
        
        metrics = [
            ("High Attention", 45),
            ("Medium Attention", 32),
            ("Low Attention", 23),
        ]
        
        for metric, val in metrics:
            bar = ProgressBarHorizontal(metric, val, max_value=100, color=COLORS['accent_blue'])
            attn_card.addWidget(bar)
        
        attn_card._layout.addStretch()
        content_row.addWidget(attn_card, 1)
        
        layout.addLayout(content_row)
        layout.addStretch()
        
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
        
        self.start_btn.setText("⏹  Stop Session")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_red']};
                color: white;
                border-radius: 25px;
                font-weight: 600;
            }}
        """)
        self.status_indicator.setText("● Live")
        self.status_indicator.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 14px;")
    
    def stop_camera(self):
        if self.video_worker:
            self.video_worker.stop()
            self.video_worker = None
        
        self.start_btn.setText("▶  Start Session")
        self.start_btn.setStyleSheet("")
        self.status_indicator.setText("● Offline")
        self.status_indicator.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
    
    def process_frame(self, frame, results):
        # Draw detections
        for r in results:
            x, y, w, h = r['bbox']
            color = (34, 197, 94) if r['recognized'] else (255, 107, 53)  # RGB
            cv2.rectangle(frame, (x, y), (x+w, y+h), color[::-1], 3)  # BGR
            
            label = f"{r['name']} ({r['confidence']}%)" if r['recognized'] else "Unknown"
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color[::-1], 2)
            
            if r['recognized'] and r.get('student_id'):
                if self.face_system.mark_attendance(r['student_id'], r['name']):
                    self.add_activity(f"✅ {r['name']} marked present")
        
        self.visible_stat.set_value(len(results))
        self.marked_stat.set_value(len(self.face_system.attendance_today))
        
        self.display_frame(frame, self.video_label)
        
        if self.stack.currentIndex() == 2:
            self.display_frame(frame, self.enroll_video)
    
    def display_frame(self, frame, label):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        scaled = img.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(QPixmap.fromImage(scaled))
    
    def add_activity(self, text):
        item = QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - {text}")
        self.activity_list.insertItem(0, item)
        if hasattr(self, 'home_activity_list'):
            self.home_activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - {text}"))
    
    # === ENROLLMENT ===
    
    def capture_photo(self):
        if not self.video_worker or not self.video_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Start the camera first on the Monitoring page!")
            return
        
        if len(self.enrollment_frames) >= 5:
            QMessageBox.information(self, "Info", "Already captured 5 photos!")
            return
        
        frame = self.video_worker.get_current_frame()
        if frame is not None:
            self.enrollment_frames.append(frame)
            self.capture_count.setText(f"{len(self.enrollment_frames)}/5")
            
            # Update thumbnail
            idx = len(self.enrollment_frames) - 1
            if idx < len(self.thumb_labels):
                small = cv2.resize(frame, (60, 60))
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                img = QImage(rgb.data, 60, 60, 180, QImage.Format_RGB888)
                self.thumb_labels[idx].setPixmap(QPixmap.fromImage(img))
                self.thumb_labels[idx].setStyleSheet(f"""
                    border-radius: 10px;
                    border: 2px solid {COLORS['accent_green']};
                """)
    
    def clear_enrollment(self):
        self.enrollment_frames = []
        self.enroll_id.clear()
        self.enroll_name.clear()
        self.capture_count.setText("0/5")
        for thumb in self.thumb_labels:
            thumb.clear()
            thumb.setStyleSheet(f"""
                background-color: {COLORS['bg_input']};
                border-radius: 10px;
                border: 2px solid {COLORS['border']};
            """)
    
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
            if hasattr(self, 'home_enrolled'):
                self.home_enrolled.set_value(self.face_system.get_enrolled_count())
            self.clear_enrollment()
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def closeEvent(self, event):
        self.stop_camera()
        event.accept()


# ============= MAIN =============
if __name__ == "__main__":
    print("=" * 50)
    print("  Attendify - Smart Attendance System")
    print("  Professional Desktop Application")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = AttendifyApp()
    window.show()
    
    sys.exit(app.exec())
