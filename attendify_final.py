"""
Attendify - Premium Desktop Attendance System
Polished UI matching the React web version exactly

Run: python attendify_final.py
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

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QStackedWidget, QProgressBar, QMessageBox, QGraphicsDropShadowEffect,
    QComboBox, QDialog, QFileDialog, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QBrush, QPen, QPainterPath

# ============= FACE RECOGNITION =============
try:
    _ = cv2.face.LBPHFaceRecognizer_create()
    LBPH_OK = True
except:
    LBPH_OK = False
    print("[!] opencv-contrib-python needed")

# ============= DESIGN SYSTEM =============
class Colors:
    # Main backgrounds
    BG = "#F5F5F3"
    CARD = "#FFFFFF"
    INPUT = "#F9FAFB"
    
    # Accents
    ORANGE = "#FF6B35"
    ORANGE_DARK = "#E5572A"
    GREEN = "#22C55E"
    BLUE = "#3B82F6"
    RED = "#EF4444"
    PURPLE = "#8B5CF6"
    
    # Text
    TEXT = "#1A1A1A"
    TEXT_SEC = "#6B7280"
    TEXT_MUTED = "#9CA3AF"
    
    # Borders
    BORDER = "#E5E7EB"
    BORDER_LIGHT = "#F3F4F6"


MAIN_STYLE = f"""
QMainWindow {{
    background-color: {Colors.BG};
}}
QWidget {{
    font-family: 'Segoe UI', 'SF Pro Display', Arial;
    color: {Colors.TEXT};
}}
QLabel {{
    background: transparent;
}}
QPushButton {{
    background-color: {Colors.ORANGE};
    color: white;
    border: none;
    border-radius: 25px;
    padding: 16px 32px;
    font-weight: 600;
    font-size: 14px;
}}
QPushButton:hover {{
    background-color: {Colors.ORANGE_DARK};
}}
QPushButton:pressed {{
    background-color: #CC4A22;
}}
QLineEdit {{
    background-color: {Colors.INPUT};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 16px 20px;
    font-size: 14px;
    color: {Colors.TEXT};
}}
QLineEdit:focus {{
    border: 2px solid {Colors.ORANGE};
}}
QComboBox {{
    background-color: {Colors.INPUT};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 16px 20px;
    font-size: 14px;
}}
QListWidget {{
    background: transparent;
    border: none;
}}
QListWidget::item {{
    background-color: {Colors.CARD};
    border-radius: 14px;
    padding: 16px;
    margin: 6px 0;
    border: 1px solid {Colors.BORDER_LIGHT};
}}
QListWidget::item:hover {{
    background-color: {Colors.INPUT};
}}
QProgressBar {{
    background-color: {Colors.BORDER_LIGHT};
    border-radius: 5px;
    height: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {Colors.ORANGE};
    border-radius: 5px;
}}
"""


# ============= CORE SYSTEMS =============
class BiometricSim:
    @staticmethod
    def fingerprint(sid): 
        return hashlib.sha256(f"{sid}SALT".encode()).hexdigest()[:32]
    
    @staticmethod
    def daily_qr(sid):
        today = datetime.now().strftime('%Y-%m-%d')
        token = hashlib.sha256(f"{sid}{today}QR".encode()).hexdigest()[:16]
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(f"ATTENDIFY:{sid}:{token}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue(), token


class LivenessDetector:
    def __init__(self):
        self.blinks = 0
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.last_eyes = 2
        self.no_eye_frames = 0
        self.cooldown = 0
    
    def check(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        if len(faces) == 0:
            return False, self.blinks, self.blinks >= 2
        
        x, y, w, h = faces[0]
        roi = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(roi, 1.1, 3, minSize=(20, 20), maxSize=(w//3, h//3))
        n = len(eyes)
        
        blinked = False
        if self.cooldown > 0:
            self.cooldown -= 1
        elif n < 2 and self.last_eyes >= 2:
            self.no_eye_frames += 1
        elif n >= 2 and self.no_eye_frames >= 2:
            self.blinks += 1
            blinked = True
            self.cooldown = 10
            self.no_eye_frames = 0
        elif n >= 2:
            self.no_eye_frames = 0
        
        self.last_eyes = n
        return blinked, self.blinks, self.blinks >= 2
    
    def reset(self):
        self.blinks = 0
        self.no_eye_frames = 0
        self.cooldown = 0


class AttendanceDB:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create() if LBPH_OK else None
        
        self.labels = {}
        self.students = {}
        self.today = {}
        self.liveness = LivenessDetector()
        
        self._load()
    
    def _load(self):
        dp = self.data_dir / "data.pkl"
        mp = self.data_dir / "model.yml"
        
        if dp.exists():
            with open(dp, 'rb') as f:
                d = pickle.load(f)
                self.labels = d.get('labels', {})
                self.students = d.get('students', {})
            print(f"[OK] Loaded {len(self.students)} students")
        
        if self.recognizer and mp.exists():
            try:
                self.recognizer.read(str(mp))
                print("[OK] Model loaded")
            except:
                pass
    
    def _save(self):
        with open(self.data_dir / "data.pkl", 'wb') as f:
            pickle.dump({'labels': self.labels, 'students': self.students}, f)
        if self.recognizer and self.labels:
            self.recognizer.write(str(self.data_dir / "model.yml"))
        print("[SAVED]")
    
    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    
    def preprocess(self, frame, rect):
        x, y, w, h = rect
        face = frame[y:y+h, x:x+w]
        if len(face.shape) == 3:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        return cv2.equalizeHist(cv2.resize(face, (200, 200)))
    
    def enroll(self, sid, name, dept, frames):
        if sid in self.students:
            return False, "ID already exists"
        
        label = max(self.labels.keys(), default=-1) + 1
        faces, lbls = [], []
        
        for img in frames:
            det = self.detect(img)
            if len(det) >= 1:
                faces.append(self.preprocess(img, det[0]))
                lbls.append(label)
        
        if len(faces) < 3:
            return False, f"Only {len(faces)} faces found"
        
        try:
            if self.labels:
                self.recognizer.update(faces, np.array(lbls))
            else:
                self.recognizer.train(faces, np.array(lbls))
        except Exception as e:
            return False, str(e)
        
        self.labels[label] = sid
        self.students[sid] = {
            'name': name, 'dept': dept,
            'fingerprint': BiometricSim.fingerprint(sid),
            'enrolled': datetime.now().isoformat()
        }
        self._save()
        return True, f"Enrolled {name}!"
    
    def recognize(self, frame, rect):
        if not self.recognizer or not self.labels:
            return None, "Unknown", 0
        try:
            face = self.preprocess(frame, rect)
            lbl, conf = self.recognizer.predict(face)
            if lbl in self.labels and conf < 80:
                sid = self.labels[lbl]
                return sid, self.students[sid]['name'], int(100 - conf)
        except:
            pass
        return None, "Unknown", 0
    
    def mark(self, sid, factors):
        if sid in self.today:
            return False, "Already marked"
        if not factors.get('face'):
            return False, "Face required"
        
        score = (30 if factors.get('face') else 0) + (25 if factors.get('liveness') else 0) + \
                (25 if factors.get('fingerprint') else 0) + (20 if factors.get('qr') else 0)
        
        self.today[sid] = {'name': self.students[sid]['name'], 'time': datetime.now().strftime("%H:%M:%S"), 'score': score}
        
        with open(self.data_dir / f"log_{datetime.now().strftime('%Y%m%d')}.csv", 'a') as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')},{sid},{score}\n")
        
        return True, f"Marked with {score}% verification"
    
    def import_folder(self, folder):
        path = Path(folder)
        if not path.exists():
            return False, "Folder not found"
        
        count = 0
        all_faces, all_labels = [], []
        
        for person in path.iterdir():
            if not person.is_dir() or person.name.startswith('_'):
                continue
            
            name = person.name.title()
            sid = name.upper()[:3] + str(len(self.students) + 1).zfill(3)
            
            if sid in self.students:
                continue
            
            label = max(self.labels.keys(), default=-1) + 1
            faces_found = 0
            
            for img_file in person.glob("*.jpg"):
                try:
                    img = cv2.imread(str(img_file))
                    if img is None:
                        continue
                    det = self.detect(img)
                    if len(det) >= 1:
                        all_faces.append(self.preprocess(img, det[0]))
                        all_labels.append(label)
                        faces_found += 1
                        if faces_found >= 15:
                            break
                except:
                    continue
            
            if faces_found >= 3:
                self.labels[label] = sid
                self.students[sid] = {'name': name, 'dept': 'Imported', 'fingerprint': BiometricSim.fingerprint(sid), 'enrolled': datetime.now().isoformat()}
                count += 1
                print(f"  + {name}")
        
        if all_faces:
            try:
                if len(self.labels) > count:
                    self.recognizer.update(all_faces, np.array(all_labels))
                else:
                    self.recognizer.train(all_faces, np.array(all_labels))
            except Exception as e:
                return False, str(e)
            self._save()
        
        return True, f"Imported {count} students"


# ============= VIDEO WORKER =============
class CameraWorker(QThread):
    frame_signal = Signal(np.ndarray, list, dict)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.running = False
        self.cap = None
        self.frame = None
    
    def run(self):
        # Try multiple camera indices
        for idx in [0, 1, 2]:
            self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # Use DirectShow on Windows
            if self.cap.isOpened():
                print(f"[OK] Camera {idx} opened")
                break
        
        if not self.cap or not self.cap.isOpened():
            print("[!] No camera found")
            return
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.running = True
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.msleep(30)
                continue
            
            frame = cv2.flip(frame, 1)
            self.frame = frame.copy()
            
            faces = self.db.detect(frame)
            _, blinks, live_ok = self.db.liveness.check(frame)
            
            results = []
            for (x, y, w, h) in faces:
                sid, name, conf = self.db.recognize(frame, (x, y, w, h))
                results.append({'bbox': (x, y, w, h), 'sid': sid, 'name': name, 'conf': conf, 'ok': sid is not None})
            
            self.frame_signal.emit(frame, results, {'blinks': blinks, 'verified': live_ok})
            self.msleep(33)
        
        if self.cap:
            self.cap.release()
    
    def stop(self):
        self.running = False
        self.wait()
    
    def grab(self):
        return self.frame


# ============= UI COMPONENTS =============

class PremiumCard(QFrame):
    """Beautiful card with shadow"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border-radius: 28px;
                border: 1px solid {Colors.BORDER_LIGHT};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(20)


class StatWidget(QFrame):
    """Stat card with large number"""
    def __init__(self, value, label, color=Colors.ORANGE, parent=None):
        super().__init__(parent)
        self.color = color
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.CARD};
                border-radius: 24px;
                border: 1px solid {Colors.BORDER_LIGHT};
                min-width: 160px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)
        
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {color};")
        layout.addWidget(self.value_lbl)
        
        desc = QLabel(label)
        desc.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_SEC}; font-weight: 500;")
        layout.addWidget(desc)
    
    def set_value(self, v):
        self.value_lbl.setText(str(v))


class NavButton(QPushButton):
    """Navigation pill button"""
    def __init__(self, text, active=False, parent=None):
        super().__init__(text, parent)
        self.active = active
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setMinimumWidth(100)
        self._style()
    
    def set_active(self, active):
        self.active = active
        self._style()
    
    def _style(self):
        if self.active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.INPUT};
                    color: {Colors.TEXT};
                    border: none;
                    border-radius: 22px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Colors.TEXT_SEC};
                    border: none;
                    border-radius: 22px;
                    padding: 12px 24px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0, 0, 0, 0.03);
                }}
            """)


class VerifyBadge(QFrame):
    """Verification status badge"""
    def __init__(self, icon, name, points, parent=None):
        super().__init__(parent)
        self.points = points
        self.verified = None
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Icon circle
        icon_frame = QFrame()
        icon_frame.setFixedSize(44, 44)
        icon_frame.setStyleSheet(f"background-color: {Colors.INPUT}; border-radius: 22px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 20px;")
        icon_layout.addWidget(icon_lbl)
        layout.addWidget(icon_frame)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Colors.TEXT};")
        text_layout.addWidget(name_lbl)
        
        pts_lbl = QLabel(f"+{points}% verification")
        pts_lbl.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_MUTED};")
        text_layout.addWidget(pts_lbl)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Status
        self.status = QLabel("--")
        self.status.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Colors.TEXT_MUTED};")
        layout.addWidget(self.status)
        
        self._update()
    
    def set_verified(self, v):
        self.verified = v
        self.status.setText("OK" if v else "X" if v is False else "--")
        self._update()
    
    def reset(self):
        self.verified = None
        self.status.setText("--")
        self._update()
    
    def _update(self):
        if self.verified:
            bg, border = f"rgba(34, 197, 94, 0.08)", Colors.GREEN
            self.status.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Colors.GREEN};")
        elif self.verified is False:
            bg, border = f"rgba(239, 68, 68, 0.08)", Colors.RED
            self.status.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Colors.RED};")
        else:
            bg, border = Colors.INPUT, Colors.BORDER
            self.status.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {Colors.TEXT_MUTED};")
        
        self.setStyleSheet(f"background-color: {bg}; border: 2px solid {border}; border-radius: 16px;")


# ============= MAIN APP =============
class AttendifyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = AttendanceDB()
        self.cam = None
        self.enroll_frames = []
        self.verify_state = {'face': False, 'liveness': False, 'fingerprint': False, 'qr': False}
        self.current_sid = None
        
        self.setWindowTitle("Attendify - Smart Attendance")
        self.setMinimumSize(1500, 900)
        self.setStyleSheet(MAIN_STYLE)
        
        self.build_ui()
    
    def build_ui(self):
        main = QWidget()
        main.setStyleSheet(f"background-color: {Colors.BG};")
        self.setCentralWidget(main)
        
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        layout.addWidget(self._header())
        
        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(48, 36, 48, 36)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self._dashboard())
        self.pages.addWidget(self._monitor())
        self.pages.addWidget(self._verify())
        self.pages.addWidget(self._enroll())
        self.pages.addWidget(self._students())
        
        content_layout.addWidget(self.pages)
        layout.addWidget(content)
        
        self.go_to(0)
    
    def _header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: {Colors.CARD}; border-bottom: 1px solid {Colors.BORDER_LIGHT};")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 0, 40, 0)
        
        # Logo
        logo = QLabel("A  attendify")
        logo.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {Colors.TEXT};")
        layout.addWidget(logo)
        
        layout.addSpacing(48)
        
        # Nav
        nav = QFrame()
        nav.setStyleSheet(f"background-color: {Colors.INPUT}; border-radius: 24px;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(4)
        
        self.nav_btns = []
        for i, txt in enumerate(["Home", "Monitor", "Verify", "Enroll", "Students"]):
            btn = NavButton(txt, i == 0)
            btn.clicked.connect(lambda _, idx=i: self.go_to(idx))
            self.nav_btns.append(btn)
            nav_layout.addWidget(btn)
        
        layout.addWidget(nav)
        layout.addStretch()
        
        # Import button
        import_btn = QPushButton("Import Data")
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.PURPLE};
                color: white;
                border-radius: 20px;
                padding: 12px 24px;
                font-weight: 600;
            }}
        """)
        import_btn.clicked.connect(self.do_import)
        layout.addWidget(import_btn)
        
        return header
    
    def go_to(self, idx):
        self.pages.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.set_active(i == idx)
    
    def do_import(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Face Data", "C:/Users/Ash/Downloads/HackCrypt/Attendify/backend/models/_data-face")
        if folder:
            ok, msg = self.db.import_folder(folder)
            QMessageBox.information(self, "Import", msg)
            self._refresh()
    
    def _refresh(self):
        if hasattr(self, 'stat_enrolled'):
            self.stat_enrolled.set_value(len(self.db.students))
            self.stat_present.set_value(len(self.db.today))
    
    # === PAGES ===
    
    def _dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(28)
        
        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        layout.addWidget(title)
        
        # Stats
        stats = QHBoxLayout()
        stats.setSpacing(20)
        
        self.stat_enrolled = StatWidget(len(self.db.students), "Students", Colors.BLUE)
        self.stat_present = StatWidget(len(self.db.today), "Present", Colors.GREEN)
        self.stat_absent = StatWidget(max(0, len(self.db.students) - len(self.db.today)), "Absent", Colors.RED)
        self.stat_rate = StatWidget("0%", "Rate", Colors.ORANGE)
        
        for s in [self.stat_enrolled, self.stat_present, self.stat_absent, self.stat_rate]:
            stats.addWidget(s)
        
        layout.addLayout(stats)
        
        # Content
        content = QHBoxLayout()
        content.setSpacing(24)
        
        # Actions
        actions = PremiumCard()
        actions.layout.addWidget(QLabel("Quick Actions"))
        
        for txt, clr, idx in [("Start Monitoring", Colors.ORANGE, 1), ("Multi-Factor Verify", Colors.GREEN, 2), ("Enroll Student", Colors.TEXT, 3)]:
            btn = QPushButton(txt)
            btn.setStyleSheet(f"background-color: {clr}; color: white; padding: 18px; border-radius: 16px; font-weight: 600;")
            btn.clicked.connect(lambda _, i=idx: self.go_to(i))
            actions.layout.addWidget(btn)
        
        actions.layout.addStretch()
        content.addWidget(actions)
        
        # Activity
        activity = PremiumCard()
        activity.layout.addWidget(QLabel("Recent Activity"))
        self.home_list = QListWidget()
        self.home_list.setMaximumHeight(320)
        activity.layout.addWidget(self.home_list)
        content.addWidget(activity, 2)
        
        layout.addLayout(content)
        layout.addStretch()
        
        return page
    
    def _monitor(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Live Monitoring")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        title_row.addWidget(title)
        title_row.addStretch()
        
        self.cam_status = QLabel("Offline")
        self.cam_status.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_MUTED}; font-weight: 600;")
        title_row.addWidget(self.cam_status)
        layout.addLayout(title_row)
        
        # Content
        content = QHBoxLayout()
        content.setSpacing(24)
        
        # Video
        video_card = PremiumCard()
        
        self.video_lbl = QLabel("Click 'Start Camera' to begin")
        self.video_lbl.setAlignment(Qt.AlignCenter)
        self.video_lbl.setMinimumSize(800, 520)
        self.video_lbl.setStyleSheet(f"background-color: {Colors.BG}; border-radius: 20px; font-size: 16px; color: {Colors.TEXT_MUTED};")
        video_card.layout.addWidget(self.video_lbl)
        
        # Controls
        ctrl = QHBoxLayout()
        self.cam_btn = QPushButton("Start Camera")
        self.cam_btn.setFixedHeight(56)
        self.cam_btn.clicked.connect(self.toggle_cam)
        ctrl.addWidget(self.cam_btn)
        
        ctrl.addStretch()
        
        self.blink_lbl = QLabel("Blinks: 0/2")
        self.blink_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {Colors.BLUE};")
        ctrl.addWidget(self.blink_lbl)
        
        video_card.layout.addLayout(ctrl)
        content.addWidget(video_card, 2)
        
        # Side
        side = QVBoxLayout()
        side.setSpacing(16)
        
        # Stats
        stats_card = PremiumCard()
        stats_card.layout.addWidget(QLabel("Session"))
        
        stats_row = QHBoxLayout()
        self.vis_stat = StatWidget(0, "Visible", Colors.TEXT)
        self.mark_stat = StatWidget(0, "Marked", Colors.GREEN)
        stats_row.addWidget(self.vis_stat)
        stats_row.addWidget(self.mark_stat)
        stats_card.layout.addLayout(stats_row)
        side.addWidget(stats_card)
        
        # Log
        log_card = PremiumCard()
        log_card.layout.addWidget(QLabel("Activity Log"))
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(280)
        log_card.layout.addWidget(self.log_list)
        side.addWidget(log_card)
        
        side.addStretch()
        content.addLayout(side, 1)
        
        layout.addLayout(content)
        return page
    
    def _verify(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("Multi-Factor Verification")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        layout.addWidget(title)
        
        content = QHBoxLayout()
        content.setSpacing(24)
        
        # Camera
        cam_card = PremiumCard()
        self.verify_video = QLabel("Start camera first")
        self.verify_video.setAlignment(Qt.AlignCenter)
        self.verify_video.setMinimumSize(520, 400)
        self.verify_video.setStyleSheet(f"background-color: {Colors.BG}; border-radius: 20px;")
        cam_card.layout.addWidget(self.verify_video)
        
        self.verify_name = QLabel("No face detected")
        self.verify_name.setAlignment(Qt.AlignCenter)
        self.verify_name.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {Colors.ORANGE};")
        cam_card.layout.addWidget(self.verify_name)
        content.addWidget(cam_card, 2)
        
        # Factors
        factors_card = PremiumCard()
        factors_card.layout.addWidget(QLabel("Verification Factors"))
        
        self.badge_face = VerifyBadge("F", "Face Recognition", 30)
        self.badge_live = VerifyBadge("L", "Liveness (Blink 2x)", 25)
        self.badge_finger = VerifyBadge("P", "Fingerprint", 25)
        self.badge_qr = VerifyBadge("Q", "QR Code", 20)
        
        for b in [self.badge_face, self.badge_live, self.badge_finger, self.badge_qr]:
            factors_card.layout.addWidget(b)
        
        # Buttons
        finger_btn = QPushButton("Scan Fingerprint")
        finger_btn.setStyleSheet(f"background-color: {Colors.BLUE}; color: white; padding: 16px; border-radius: 14px;")
        finger_btn.clicked.connect(self.do_fingerprint)
        factors_card.layout.addWidget(finger_btn)
        
        qr_row = QHBoxLayout()
        qr_show = QPushButton("Show QR")
        qr_show.setStyleSheet(f"background-color: {Colors.PURPLE}; color: white; padding: 14px; border-radius: 14px;")
        qr_show.clicked.connect(self.show_qr)
        qr_row.addWidget(qr_show)
        
        qr_scan = QPushButton("Scan QR")
        qr_scan.setStyleSheet(f"background-color: {Colors.TEXT}; color: white; padding: 14px; border-radius: 14px;")
        qr_scan.clicked.connect(self.do_qr)
        qr_row.addWidget(qr_scan)
        factors_card.layout.addLayout(qr_row)
        
        factors_card.layout.addStretch()
        
        # Score
        self.score_lbl = QLabel("Score: 0%")
        self.score_lbl.setAlignment(Qt.AlignCenter)
        self.score_lbl.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {Colors.ORANGE};")
        factors_card.layout.addWidget(self.score_lbl)
        
        # Submit
        submit = QPushButton("Mark Attendance")
        submit.setStyleSheet(f"background-color: {Colors.GREEN}; color: white; padding: 18px; border-radius: 16px; font-weight: 700; font-size: 16px;")
        submit.clicked.connect(self.do_mark)
        factors_card.layout.addWidget(submit)
        
        reset = QPushButton("Reset")
        reset.setStyleSheet(f"background-color: transparent; border: 2px solid {Colors.BORDER}; color: {Colors.TEXT}; padding: 14px; border-radius: 14px;")
        reset.clicked.connect(self.do_reset)
        factors_card.layout.addWidget(reset)
        
        content.addWidget(factors_card, 1)
        layout.addLayout(content)
        return page
    
    def _enroll(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("Enroll New Student")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        layout.addWidget(title)
        
        content = QHBoxLayout()
        content.setSpacing(24)
        
        # Camera
        cam_card = PremiumCard()
        self.enroll_video = QLabel("Start camera to capture")
        self.enroll_video.setAlignment(Qt.AlignCenter)
        self.enroll_video.setMinimumSize(520, 400)
        self.enroll_video.setStyleSheet(f"background-color: {Colors.BG}; border-radius: 20px;")
        cam_card.layout.addWidget(self.enroll_video)
        
        cap_row = QHBoxLayout()
        cap_btn = QPushButton("Capture Photo")
        cap_btn.clicked.connect(self.do_capture)
        cap_row.addWidget(cap_btn)
        
        self.cap_count = QLabel("0/5")
        self.cap_count.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {Colors.GREEN};")
        cap_row.addWidget(self.cap_count)
        cap_row.addStretch()
        cam_card.layout.addLayout(cap_row)
        
        # Thumbnails
        thumb_row = QHBoxLayout()
        self.thumbs = []
        for _ in range(5):
            t = QLabel()
            t.setFixedSize(64, 64)
            t.setStyleSheet(f"background-color: {Colors.INPUT}; border-radius: 12px; border: 2px solid {Colors.BORDER};")
            self.thumbs.append(t)
            thumb_row.addWidget(t)
        thumb_row.addStretch()
        cam_card.layout.addLayout(thumb_row)
        content.addWidget(cam_card, 2)
        
        # Form
        form_card = PremiumCard()
        form_card.layout.addWidget(QLabel("Student Information"))
        
        for lbl, ph, attr in [("Student ID", "STU001", "enroll_id"), ("Full Name", "John Doe", "enroll_name")]:
            form_card.layout.addWidget(QLabel(lbl))
            inp = QLineEdit()
            inp.setPlaceholderText(ph)
            setattr(self, attr, inp)
            form_card.layout.addWidget(inp)
        
        form_card.layout.addWidget(QLabel("Department"))
        self.enroll_dept = QComboBox()
        self.enroll_dept.addItems(["Computer Science", "Electronics", "Mechanical", "Civil"])
        form_card.layout.addWidget(self.enroll_dept)
        
        form_card.layout.addStretch()
        
        btn_row = QHBoxLayout()
        clear = QPushButton("Clear")
        clear.setStyleSheet(f"background-color: transparent; border: 2px solid {Colors.BORDER}; color: {Colors.TEXT}; padding: 14px 28px; border-radius: 20px;")
        clear.clicked.connect(self.clear_enroll)
        btn_row.addWidget(clear)
        
        save = QPushButton("Enroll & Save")
        save.setStyleSheet(f"background-color: {Colors.GREEN}; color: white; padding: 14px 28px; border-radius: 20px;")
        save.clicked.connect(self.do_enroll)
        btn_row.addWidget(save)
        form_card.layout.addLayout(btn_row)
        
        content.addWidget(form_card, 1)
        layout.addLayout(content)
        return page
    
    def _students(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(24)
        
        title = QLabel("Enrolled Students")
        title.setStyleSheet("font-size: 32px; font-weight: 700;")
        layout.addWidget(title)
        
        card = PremiumCard()
        self.students_list = QListWidget()
        self.students_list.setMinimumHeight(500)
        card.layout.addWidget(self.students_list)
        
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_students)
        card.layout.addWidget(refresh)
        
        layout.addWidget(card)
        self.refresh_students()
        return page
    
    def refresh_students(self):
        self.students_list.clear()
        for sid, data in self.db.students.items():
            self.students_list.addItem(QListWidgetItem(f"{sid} - {data['name']} ({data['dept']})"))
    
    # === CAMERA ===
    def toggle_cam(self):
        if self.cam and self.cam.isRunning():
            self.stop_cam()
        else:
            self.start_cam()
    
    def start_cam(self):
        self.cam = CameraWorker(self.db)
        self.cam.frame_signal.connect(self.on_frame)
        self.cam.start()
        self.cam_btn.setText("Stop Camera")
        self.cam_btn.setStyleSheet(f"background-color: {Colors.RED}; color: white; padding: 16px 32px; border-radius: 25px;")
        self.cam_status.setText("LIVE")
        self.cam_status.setStyleSheet(f"color: {Colors.GREEN}; font-weight: 700;")
    
    def stop_cam(self):
        if self.cam:
            self.cam.stop()
            self.cam = None
        self.cam_btn.setText("Start Camera")
        self.cam_btn.setStyleSheet(f"background-color: {Colors.ORANGE}; color: white; padding: 16px 32px; border-radius: 25px;")
        self.cam_status.setText("Offline")
        self.cam_status.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
    
    def on_frame(self, frame, faces, live):
        verified_mark = " OK" if live['verified'] else ""
        self.blink_lbl.setText(f"Blinks: {live['blinks']}/2{verified_mark}")
        
        for r in faces:
            x, y, w, h = r['bbox']
            color = (34, 197, 94) if r['ok'] else (255, 107, 53)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color[::-1], 3)
            cv2.putText(frame, f"{r['name']} {r['conf']}%", (x, y-12), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color[::-1], 2)
            
            if r['ok']:
                self.current_sid = r['sid']
                self.verify_state['face'] = True
                self.badge_face.set_verified(True)
                self.verify_name.setText(f"{r['name']}")
            
            if live['verified']:
                self.verify_state['liveness'] = True
                self.badge_live.set_verified(True)
        
        self.update_score()
        self.vis_stat.set_value(len(faces))
        self.mark_stat.set_value(len(self.db.today))
        
        self.show_frame(frame, self.video_lbl)
        self.show_frame(frame, self.verify_video)
        self.show_frame(frame, self.enroll_video)
    
    def show_frame(self, frame, lbl):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        lbl.setPixmap(QPixmap.fromImage(img.scaled(lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)))
    
    def update_score(self):
        s = (30 if self.verify_state['face'] else 0) + (25 if self.verify_state['liveness'] else 0) + \
            (25 if self.verify_state['fingerprint'] else 0) + (20 if self.verify_state['qr'] else 0)
        self.score_lbl.setText(f"Score: {s}%")
    
    # === VERIFY ===
    def do_fingerprint(self):
        if not self.current_sid:
            QMessageBox.warning(self, "Error", "Face not recognized!")
            return
        self.verify_state['fingerprint'] = True
        self.badge_finger.set_verified(True)
        self.update_score()
        QMessageBox.information(self, "Fingerprint", "Fingerprint verified!")
    
    def show_qr(self):
        if not self.current_sid:
            QMessageBox.warning(self, "Error", "Face not recognized!")
            return
        
        qr_data, token = BiometricSim.daily_qr(self.current_sid)
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Your QR Code")
        dlg.setStyleSheet(f"background: {Colors.CARD};")
        lay = QVBoxLayout(dlg)
        
        qr_lbl = QLabel()
        qr_lbl.setPixmap(QPixmap.fromImage(QImage.fromData(qr_data)))
        qr_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(qr_lbl)
        
        lay.addWidget(QLabel(f"Student: {self.current_sid}\nToken: {token}\nValid today only"))
        dlg.exec()
    
    def do_qr(self):
        if not self.current_sid:
            QMessageBox.warning(self, "Error", "Face not recognized!")
            return
        self.verify_state['qr'] = True
        self.badge_qr.set_verified(True)
        self.update_score()
        QMessageBox.information(self, "QR", "QR verified!")
    
    def do_mark(self):
        if not self.current_sid:
            QMessageBox.warning(self, "Error", "No face recognized!")
            return
        
        ok, msg = self.db.mark(self.current_sid, self.verify_state)
        if ok:
            name = self.db.students[self.current_sid]['name']
            self.log_list.insertItem(0, QListWidgetItem(f"OK - {name} @ {datetime.now().strftime('%H:%M:%S')}"))
            self.home_list.insertItem(0, QListWidgetItem(f"OK - {name} @ {datetime.now().strftime('%H:%M:%S')}"))
            self.do_reset()
            self._refresh()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Failed", msg)
    
    def do_reset(self):
        self.current_sid = None
        self.verify_state = {'face': False, 'liveness': False, 'fingerprint': False, 'qr': False}
        self.badge_face.reset()
        self.badge_live.reset()
        self.badge_finger.reset()
        self.badge_qr.reset()
        self.db.liveness.reset()
        self.verify_name.setText("No face detected")
        self.update_score()
    
    # === ENROLL ===
    def do_capture(self):
        if not self.cam:
            QMessageBox.warning(self, "Error", "Start camera first!")
            return
        if len(self.enroll_frames) >= 5:
            return
        
        frame = self.cam.grab()
        if frame is not None:
            self.enroll_frames.append(frame)
            self.cap_count.setText(f"{len(self.enroll_frames)}/5")
            
            idx = len(self.enroll_frames) - 1
            small = cv2.resize(frame, (64, 64))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            self.thumbs[idx].setPixmap(QPixmap.fromImage(QImage(rgb.data, 64, 64, 192, QImage.Format_RGB888)))
            self.thumbs[idx].setStyleSheet(f"border-radius: 12px; border: 3px solid {Colors.GREEN};")
    
    def clear_enroll(self):
        self.enroll_frames = []
        self.enroll_id.clear()
        self.enroll_name.clear()
        self.cap_count.setText("0/5")
        for t in self.thumbs:
            t.clear()
            t.setStyleSheet(f"background-color: {Colors.INPUT}; border-radius: 12px; border: 2px solid {Colors.BORDER};")
    
    def do_enroll(self):
        sid, name = self.enroll_id.text().strip(), self.enroll_name.text().strip()
        if not sid or not name:
            QMessageBox.warning(self, "Error", "Fill all fields!")
            return
        if len(self.enroll_frames) < 3:
            QMessageBox.warning(self, "Error", f"Need 3+ photos ({len(self.enroll_frames)})")
            return
        
        ok, msg = self.db.enroll(sid, name, self.enroll_dept.currentText(), self.enroll_frames)
        if ok:
            QMessageBox.information(self, "Enrolled!", msg)
            self._refresh()
            self.refresh_students()
            self.clear_enroll()
        else:
            QMessageBox.critical(self, "Error", msg)
    
    def closeEvent(self, event):
        self.stop_cam()
        event.accept()


if __name__ == "__main__":
    print("=" * 50)
    print("  Attendify - Premium Attendance System")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    
    win = AttendifyApp()
    win.show()
    
    sys.exit(app.exec())
