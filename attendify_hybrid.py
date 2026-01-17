"""
Attendify Hybrid - Web UI + Python Face Recognition
Embeds your React frontend in a Python window with local face recognition

How it works:
1. Python runs a local API server for face recognition
2. PyQt5 WebEngine embeds your React frontend (localhost:5173)
3. React frontend calls Python API for face recognition

Run: python attendify_hybrid.py
Requirements: Your React frontend running on localhost:5173
"""

import sys
import cv2
import numpy as np
import pickle
import base64
import json
from datetime import datetime
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSplashScreen, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter

# ============= FACE RECOGNITION ENGINE =============
class FaceEngine:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Load YOLOv8 for robust person detection
        try:
            from ultralytics import YOLO
            self.yolo = YOLO('yolov8n.pt')
            print("[ENGINE] YOLOv8 (yolov8n.pt) loaded")
        except Exception as e:
            self.yolo = None
            print(f"[WARN] YOLOv8 not available: {e}")

        # Haar Cascade as refined face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        except:
            self.recognizer = None
            print("[!] opencv-contrib-python needed for recognition")
        
        self.labels = {}
        self.students = {}
        self.attendance = {}
        
        self._load()
    
    def _load(self):
        dp = self.data_dir / "hybrid_data.pkl"
        mp = self.data_dir / "hybrid_model.yml"
        
        if dp.exists():
            with open(dp, 'rb') as f:
                d = pickle.load(f)
                self.labels = d.get('labels', {})
                self.students = d.get('students', {})
            print(f"[ENGINE] Loaded {len(self.students)} students")
        
        if self.recognizer and mp.exists():
            try:
                self.recognizer.read(str(mp))
                print("[ENGINE] Model loaded")
            except:
                pass
    
    def _save(self):
        with open(self.data_dir / "hybrid_data.pkl", 'wb') as f:
            pickle.dump({'labels': self.labels, 'students': self.students}, f)
        if self.recognizer and self.labels:
            self.recognizer.write(str(self.data_dir / "hybrid_model.yml"))
        print("[ENGINE] Saved")
    
    def adjust_gamma(self, image, gamma=1.5):
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    def detect_faces_robust(self, img):
        """Hybrid detection: YOLOv8 (Person) -> Haar (Face) + Gamma Correction"""
        faces = []
        h, w = img.shape[:2]
        
        # 1. Try Standard Haar
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        for d in detected: faces.append(d)
        
        # 2. If no faces, try Gamma Correction (Video light compensation)
        if len(faces) == 0:
            gamma_corr = self.adjust_gamma(img, gamma=1.5)
            gray_gamma = cv2.cvtColor(gamma_corr, cv2.COLOR_BGR2GRAY)
            detected_g = self.face_cascade.detectMultiScale(gray_gamma, 1.05, 4, minSize=(60, 60))
            for d in detected_g: faces.append(d)
        
        # 3. If still no faces and YOLO is available, use YOLO to find person ROI then scan ROI
        if len(faces) == 0 and self.yolo:
            results = self.yolo(img, verbose=False, classes=[0]) # class 0 = person
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Crop person
                    person_roi = img[y1:y2, x1:x2]
                    if person_roi.size > 0:
                        gray_p = cv2.cvtColor(person_roi, cv2.COLOR_BGR2GRAY)
                        local_faces = self.face_cascade.detectMultiScale(gray_p, 1.05, 3, minSize=(40, 40))
                        for (fx, fy, fw, fh) in local_faces:
                            faces.append((x1+fx, y1+fy, fw, fh))
        
        return faces

    def train_from_disk(self):
        """Re-train model from all images in data directory"""
        print("[ENGINE] Starting full retraining...")
        faces = []
        labels = []
        self.labels = {}
        self.students = {}
        
        # Walk through all student folders
        # Expected structure: backend/models/_data-face/<student_name>/<images>
        # OR local attendance_data/<student_name>/... if we saved there.
        # But user is importing from 'C:/Users/Ash/Downloads/HackCrypt/Attendify/backend/models/_data-face'
        
        # Let's verify the source folder exists
        source_dir = Path("C:/Users/Ash/Downloads/HackCrypt/Attendify/backend/models/_data-face")
        if not source_dir.exists():
            print(f"[WARN] Source dir {source_dir} not found")
            return False

        label_id = 0
        for person_dir in source_dir.iterdir():
            if not person_dir.is_dir() or person_dir.name.startswith('_'): continue
            
            name = person_dir.name.title()
            sid = name.upper()[:3] + str(label_id + 1).zfill(3)
            
            print(f"  - Processing {name}...")
            
            self.labels[label_id] = sid
            self.students[sid] = {'name': name, 'enrolled_at': datetime.now().isoformat()}
            
            loaded_count = 0
            for img_file in person_dir.glob("*.jpg"):
                try:
                    img = cv2.imread(str(img_file))
                    if img is None: continue
                    
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    detected = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
                    
                    if len(detected) > 0:
                        (x, y, w, h) = detected[0]
                        face = cv2.equalizeHist(cv2.resize(gray[y:y+h, x:x+w], (200, 200)))
                        faces.append(face)
                        labels.append(label_id)
                        loaded_count += 1
                except: pass
            
            print(f"    Loaded {loaded_count} faces")
            label_id += 1
            
        if len(faces) > 0:
            if self.recognizer is None:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.train(faces, np.array(labels))
            self._save()
            print(f"[ENGINE] Retraining complete. {len(faces)} faces trained for {len(self.students)} students.")
            return True
        else:
            print("[WARN] No faces found to train")
            return False

    def base64_to_cv2(self, b64_string):
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        try:
            img_data = base64.b64decode(b64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except:
            return None
    
    # Remove startup training to prevent lag/issues
    # engine.train_from_disk()

    def detect_and_recognize(self, b64_image):
        print(".", end="", flush=True) # Heartbeat
        img = self.base64_to_cv2(b64_image)
        if img is None: return {'success': False, 'error': 'Invalid image'}
        
        # 1. CLAHE Preprocessing (Better than Gamma)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray_clahe = clahe.apply(gray)
        
        faces = []
        
        # 2. Try Haar on CLAHE image (Fastest)
        detected = self.face_cascade.detectMultiScale(gray_clahe, 1.1, 4, minSize=(60, 60))
        for d in detected: faces.append(d)
        
        # 3. If failed, use YOLO (Robust)
        if len(faces) == 0 and self.yolo:
            # conf=0.3 (lower threshold), classes=[0] (person)
            results = self.yolo(img, verbose=False, conf=0.3, classes=[0]) 
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # Crop person and run Haar inside
                    roi_gray = gray_clahe[y1:y2, x1:x2]
                    if roi_gray.size > 0:
                        sub_faces = self.face_cascade.detectMultiScale(roi_gray, 1.05, 3, minSize=(40, 40))
                        for (fx, fy, fw, fh) in sub_faces:
                            faces.append((x1+fx, y1+fy, fw, fh))

        if len(faces) == 0:
            return {'success': True, 'faces': []}
            
        results = []
        for (x, y, w, h) in faces:
             # ... recognition logic ... (keeping existing)
             # NOTE: Re-implementing inner loop to ensure we don't lose logic
            face_data = {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h), 'student_id': None, 'name': 'Unknown', 'confidence': 0}
            
            if self.recognizer and self.labels:
                try:
                    # Use the CLAHE gray image for improved recognition? 
                    # Usually LBPH prefers raw, but uneven lighting kills it. try CLAHE.
                    # Or Histogram Equalization on crop.
                    face_roi = gray[y:y+h, x:x+w]
                    face_resized = cv2.equalizeHist(cv2.resize(face_roi, (200, 200)))
                    label, dist = self.recognizer.predict(face_resized)
                    
                    if dist < 100:
                        confidence = max(0, 100 - dist)
                        if confidence > 25: # Lowered threshold further
                            sid = self.labels.get(label)
                            if sid:
                                face_data['student_id'] = sid
                                face_data['name'] = self.students.get(sid, {}).get('name', 'Unknown')
                                face_data['confidence'] = int(confidence)
                except Exception as e:
                    pass
            results.append(face_data)
        
        return {'success': True, 'faces': results}
    
    def enroll(self, student_id, name, images_b64):
        if student_id in self.students:
            return {'success': False, 'error': 'Student ID already exists'}
        
        label = max(self.labels.keys(), default=-1) + 1
        faces, labels = [], []
        
        for b64 in images_b64:
            img = self.base64_to_cv2(b64)
            if img is None: continue
            
            # Use robust detection for enrollment too
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detected = self.detect_faces_robust(img)
            
            for (x, y, w, h) in detected:
                face = gray[y:y+h, x:x+w]
                face = cv2.equalizeHist(cv2.resize(face, (200, 200)))
                faces.append(face)
                labels.append(label)
                break # Take best face
        
        if len(faces) < 3:
            return {'success': False, 'error': f'Only {len(faces)} valid faces found'}
        
        if self.recognizer:
            try:
                if self.labels:
                    self.recognizer.update(faces, np.array(labels))
                else:
                    self.recognizer.train(faces, np.array(labels))
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        self.labels[label] = student_id
        self.students[student_id] = {'name': name, 'enrolled_at': datetime.now().isoformat()}
        self._save()
        return {'success': True, 'message': f'Enrolled {name}!'}
    
    def mark_attendance(self, student_id):
        """Mark attendance for a student"""
        if student_id not in self.students:
            return {'success': False, 'error': 'Student not found'}
        
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{student_id}_{today}"
        
        if key in self.attendance:
            return {'success': False, 'error': 'Already marked today'}
        
        self.attendance[key] = {
            'student_id': student_id,
            'name': self.students[student_id]['name'],
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': today
        }
        
        return {'success': True, 'message': f"Marked attendance for {self.students[student_id]['name']}"}
    
    def get_students(self):
        """Get all enrolled students"""
        return {'success': True, 'students': [
            {'id': sid, 'name': data['name']} 
            for sid, data in self.students.items()
        ]}
    
    def import_folder(self, folder_path):
        """Import faces from folder structure"""
        path = Path(folder_path)
        if not path.exists():
            return {'success': False, 'error': 'Folder not found'}
        
        count = 0
        all_faces, all_labels = [], []
        
        for person_dir in path.iterdir():
            if not person_dir.is_dir() or person_dir.name.startswith('_'):
                continue
            
            name = person_dir.name.title()
            sid = name.upper()[:3] + str(len(self.students) + 1).zfill(3)
            
            if sid in self.students:
                continue
            
            label = max(self.labels.keys(), default=-1) + 1
            faces_found = 0
            
            for img_file in person_dir.glob("*.jpg"):
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
                        faces_found += 1
                        
                        if faces_found >= 15:
                            break
                except:
                    continue
            
            if faces_found >= 3:
                self.labels[label] = sid
                self.students[sid] = {'name': name, 'enrolled_at': datetime.now().isoformat()}
                count += 1
                print(f"  + Imported {name}")
        
        if all_faces:
            try:
                if len(self.labels) > count:
                    self.recognizer.update(all_faces, np.array(all_labels))
                else:
                    self.recognizer.train(all_faces, np.array(all_labels))
                self._save()
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': True, 'message': f'Imported {count} students'}


# ============= LOCAL API SERVER =============
engine = FaceEngine()

class APIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/api/health':
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'engine': 'python'}).encode())
        
        elif parsed.path == '/api/students':
            self._set_headers()
            result = engine.get_students()
            self.wfile.write(json.dumps(result).encode())
        
        elif parsed.path == '/api/import':
            self._set_headers()
            # Default import path
            result = engine.import_folder("C:/Users/Ash/Downloads/HackCrypt/Attendify/backend/models/_data-face")
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        if self.path == '/api/recognize':
            # Recognize faces in image
            image = data.get('image', '')
            if not image:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'No image provided'}).encode())
                return
            
            result = engine.detect_and_recognize(image)
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif self.path == '/api/enroll':
            # Enroll new student
            student_id = data.get('student_id', '')
            name = data.get('name', '')
            images = data.get('images', [])
            
            if not student_id or not name or not images:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Missing data'}).encode())
                return
            
            result = engine.enroll(student_id, name, images)
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif self.path == '/api/attendance':
            # Mark attendance
            student_id = data.get('student_id', '')
            result = engine.mark_attendance(student_id)
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


def run_api_server(port=8765):
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"[API] Server running on http://localhost:{port}")
    server.serve_forever()


# ============= CUSTOM WEB PAGE =============
class CustomPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, msg, line, source):
        print(f"[JS] {msg}")
    
    def featurePermissionRequested(self, securityOrigin, feature):
        # Auto-grant camera and microphone permissions
        if feature in [QWebEnginePage.MediaAudioVideoCapture, QWebEnginePage.MediaVideoCapture, QWebEnginePage.MediaAudioCapture]:
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionGrantedByUser)
        else:
            self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionDeniedByUser)


# ============= MAIN WINDOW =============
class HybridApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Attendify - Smart Attendance System")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("background-color: #1a1a2e;")
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view
        self.web = QWebEngineView()
        self.web.setPage(CustomPage(self.web))
        
        # Enable local storage and media
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        
        # Load the React frontend
        self.web.setUrl(QUrl("http://localhost:5173"))
        
        layout.addWidget(self.web)
        
        # Status bar
        self.statusBar().showMessage("Python Face Recognition Engine Active | API: http://localhost:8765")
        self.statusBar().setStyleSheet("color: #22C55E; background: #16213e; padding: 8px;")
    
    def closeEvent(self, event):
        event.accept()


# ============= MAIN =============
def main():
    print("=" * 60)
    print("  Attendify Hybrid")
    print("  Web UI + Python Face Recognition")
    print("=" * 60)
    
    # Start API server in background
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Import and RETRAIN existing data automatically
    print("\n[INIT] Retraining model from disk ensure consistency...")
    # Run in BACKGROUND thread to not block UI startup
    train_thread = Thread(target=engine.train_from_disk, daemon=True)
    train_thread.start()
    
    # Enable camera access flags
    sys.argv.append("--enable-media-stream")
    sys.argv.append("--use-fake-ui-for-media-stream")
    sys.argv.append("--enable-usermedia-screen-capturing")
    
    # Start Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("Attendify Hybrid")
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))
    
    window = HybridApp()
    window.show()
    
    print("\n[READY] Application started!")
    print("[INFO] Make sure your React frontend is running on http://localhost:5173")
    print("[API] Python recognition API available at http://localhost:8765")
    print("\nAPI Endpoints:")
    print("  GET  /api/health     - Check API status")
    print("  GET  /api/students   - Get enrolled students")
    print("  GET  /api/import     - Import from default folder")
    print("  POST /api/recognize  - Recognize faces {image: base64}")
    print("  POST /api/enroll     - Enroll student {student_id, name, images[]}")
    print("  POST /api/attendance - Mark attendance {student_id}")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
