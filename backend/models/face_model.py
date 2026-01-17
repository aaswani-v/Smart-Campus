"""
Face Detection and Recognition System - With Video Recording
Uses YOLO + Haar + LBPH for face detection and recognition.

Features:
- RECORD VIDEO: Press N to record a video, then auto-extract faces
- WEBCAM CAPTURE: Press A to capture photos one by one
- SELECT VIDEO: Press V to select existing video file
- INCREMENTAL TRAINING: Only retrains when folders change

Controls:
  Q = Quit
  R = Reload/retrain model  
  N = NEW person (record video + extract faces) ← EASY MODE
  A = Add person (webcam photo capture)
  V = Add from existing video file
"""

import os
import cv2
import hashlib
import numpy as np
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pickle

# Try to import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[WARNING] ultralytics not installed, using Haar Cascade only")

# Paths
DATA_FACE_DIR = Path(__file__).parent / "_data-face"
MODEL_CACHE_DIR = Path(__file__).parent / "_model_cache"
VIDEO_DIR = Path(__file__).parent / "_videos"


def get_folder_hash(folder: Path) -> str:
    """Get hash of a folder's contents."""
    files = sorted(folder.glob("*.jpg"))
    content = ",".join(f"{f.name}:{f.stat().st_mtime}" for f in files)
    return hashlib.md5(content.encode()).hexdigest()


class FaceDetector:
    """Face detection and recognition with video recording support."""
    
    def __init__(self, max_distance: float = 80.0, detection_scale: float = 0.5,
                 skip_frames: int = 2):
        self.max_distance = max_distance
        self.detection_scale = detection_scale
        self.skip_frames = skip_frames
        self.known_face_labels: Dict[int, str] = {}
        self.label_counter = 0
        
        self.frame_count = 0
        self.cached_faces = []
        self.cached_results = []
        self.folder_hashes: Dict[str, str] = {}
        
        print("[INFO] Loading cascades...")
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.alt_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
        )
        
        self.yolo_model = None
        if YOLO_AVAILABLE:
            print("[INFO] Loading YOLO...")
            try:
                self.yolo_model = YOLO('yolov8n.pt')
                print("[INFO] YOLO loaded")
            except Exception as e:
                print(f"[WARNING] YOLO failed: {e}")
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=200.0
        )
        self.is_trained = False
        
        DATA_FACE_DIR.mkdir(parents=True, exist_ok=True)
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        
        self.load_model()
    
    def preprocess_face(self, face_roi: np.ndarray) -> np.ndarray:
        face = cv2.resize(face_roi, (100, 100))
        face = cv2.equalizeHist(face)
        return face
    
    def load_model(self) -> bool:
        model_path = MODEL_CACHE_DIR / "lbph_model.yml"
        labels_path = MODEL_CACHE_DIR / "labels.pkl"
        hashes_path = MODEL_CACHE_DIR / "folder_hashes.pkl"
        
        if hashes_path.exists():
            with open(hashes_path, 'rb') as f:
                self.folder_hashes = pickle.load(f)
        
        current_folders = {}
        changed = []
        
        for folder in DATA_FACE_DIR.iterdir():
            if not folder.is_dir() or folder.name.startswith('unknown'):
                continue
            h = get_folder_hash(folder)
            current_folders[folder.name] = h
            if folder.name not in self.folder_hashes or self.folder_hashes[folder.name] != h:
                changed.append(folder.name)
        
        deleted = set(self.folder_hashes.keys()) - set(current_folders.keys())
        if deleted:
            changed.extend(deleted)
        
        if not changed and model_path.exists() and labels_path.exists():
            print("[INFO] No changes, loading cache...")
            try:
                self.recognizer.read(str(model_path))
                with open(labels_path, 'rb') as f:
                    d = pickle.load(f)
                self.known_face_labels = d['labels']
                self.label_counter = d['counter']
                self.is_trained = True
                print(f"[INFO] Loaded {len(self.known_face_labels)} persons")
                return True
            except:
                pass
        
        if changed:
            print(f"[INFO] {len(changed)} folder(s) changed")
        return self._train_all(current_folders)
    
    def _train_all(self, hashes: Dict[str, str]) -> bool:
        self.known_face_labels = {}
        self.label_counter = 0
        faces = []
        labels = []
        name_to_label = {}
        
        for folder in DATA_FACE_DIR.iterdir():
            if not folder.is_dir() or folder.name.startswith('unknown'):
                continue
            
            name = folder.name.replace('_', ' ').title()
            if name not in name_to_label:
                name_to_label[name] = self.label_counter
                self.known_face_labels[self.label_counter] = name
                self.label_counter += 1
            
            label = name_to_label[name]
            count = 0
            
            for img_path in folder.iterdir():
                if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                    continue
                try:
                    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        continue
                    rects = self.face_cascade.detectMultiScale(img, 1.1, 3, minSize=(20, 20))
                    if len(rects) > 0:
                        x, y, w, h = max(rects, key=lambda r: r[2]*r[3])
                        roi = img[y:y+h, x:x+w]
                    else:
                        roi = img
                    faces.append(self.preprocess_face(roi))
                    labels.append(label)
                    count += 1
                except:
                    pass
            
            if count > 0:
                print(f"[INFO] {folder.name}: {count} images")
        
        if faces:
            self.recognizer.train(faces, np.array(labels))
            self.is_trained = True
            print(f"[TRAINED] {len(faces)} faces, {len(name_to_label)} persons")
            self._save_cache(hashes)
            return True
        return False
    
    def _save_cache(self, hashes):
        try:
            self.recognizer.save(str(MODEL_CACHE_DIR / "lbph_model.yml"))
            with open(MODEL_CACHE_DIR / "labels.pkl", 'wb') as f:
                pickle.dump({'labels': self.known_face_labels, 'counter': self.label_counter}, f)
            with open(MODEL_CACHE_DIR / "folder_hashes.pkl", 'wb') as f:
                pickle.dump(hashes, f)
            self.folder_hashes = hashes
        except:
            pass
    
    def force_retrain(self):
        hashes = {}
        for folder in DATA_FACE_DIR.iterdir():
            if folder.is_dir() and not folder.name.startswith('unknown'):
                hashes[folder.name] = get_folder_hash(folder)
        self._train_all(hashes)
    
    def detect_faces_fast(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        scale = self.detection_scale
        small = cv2.resize(frame, None, fx=scale, fy=scale)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        all_faces = []
        
        if self.yolo_model:
            # Lower confidence slightly to ensure detection
            results = self.yolo_model(small, verbose=False, classes=[0], conf=0.4)
            for r in results:
                for box in r.boxes:
                    px1, py1, px2, py2 = map(int, box.xyxy[0])
                    px1, py1 = max(0, px1), max(0, py1)
                    px2, py2 = min(small.shape[1], px2), min(small.shape[0], py2)
                    
                    if px2 <= px1 or py2 <= py1:
                        continue
                        
                    # TRUST YOLO DIRECTLY - significantly faster and more reliable
                    # Scale back up to original frame coordinates
                    original_x = int(px1 / scale)
                    original_y = int(py1 / scale)
                    original_w = int((px2 - px1) / scale)
                    original_h = int((py2 - py1) / scale)
                    
                    all_faces.append((original_x, original_y, original_w, original_h))
        
        # Fallback to Haar only if YOLO found nothing (or isn't loaded)
        if not all_faces:
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            for (x, y, w, h) in faces:
                all_faces.append((int(x/scale), int(y/scale), int(w/scale), int(h/scale)))
        
        return all_faces
    
    def recognize_face(self, frame, rect) -> Tuple[str, float, float]:
        if not self.is_trained:
            return "Unknown", 0.0, 999.0
        x, y, w, h = rect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        x, y = max(0, x), max(0, y)
        x2, y2 = min(gray.shape[1], x+w), min(gray.shape[0], y+h)
        if x2 <= x or y2 <= y:
            return "Unknown", 0.0, 999.0
            
        roi = self.preprocess_face(gray[y:y2, x:x2])
        try:
            label, dist = self.recognizer.predict(roi)
            conf = max(0, min(100, 100 - dist * 0.7))
            
            # Debug info to understand why detection might fail
            name = self.known_face_labels.get(label, "Unknown")
            print(f"[DEBUG] Predicted: {name} (ID:{label}) | Dist: {dist:.1f} | Conf: {conf:.1f}")
            
            if dist <= self.max_distance:
                return name, conf, dist
            else:
                # pass
                print(f"[DEBUG] REJECTED: {name} - Dist {dist:.1f} > {self.max_distance}")
                
        except Exception as e:
            # print(f"[ERROR] Recognition error: {e}")
            pass
            
        return "Unknown", 0.0, 999.0
    
    def get_folder(self, name: str) -> Path:
        folder_name = name.lower().strip().replace(' ', '_')
        folder_name = ''.join(c for c in folder_name if c.isalnum() or c == '_')
        folder = DATA_FACE_DIR / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    def get_next_num(self, folder: Path) -> int:
        nums = []
        for f in folder.glob("*.jpg"):
            try:
                nums.append(int(f.stem))
            except:
                pass
        return max(nums, default=0) + 1
    
    def record_and_extract(self, person_name: str, duration: int = 10, camera_index: int = 0) -> int:
        """
        Record a video of the person, then extract faces from it.
        
        Args:
            person_name: Name of the person
            duration: Recording duration in seconds
            camera_index: Camera to use
            
        Returns:
            Number of faces extracted
        """
        print(f"\n{'='*50}")
        print(f"RECORDING: {person_name}")
        print(f"Duration: {duration} seconds")
        print(f"{'='*50}")
        print("\nTips for best results:")
        print("  - Move your head left/right slowly")
        print("  - Look up/down")
        print("  - Show different expressions")
        print("  - Move closer/farther from camera")
        print(f"{'='*50}\n")
        
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print("[ERROR] Cannot open camera")
            return 0
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Video file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = VIDEO_DIR / f"{person_name}_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 20.0
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (1280, 720))
        
        window = f'Recording: {person_name} [{duration}s]'
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 800, 600)
        
        print("[INFO] Recording starting in 3 seconds...")
        
        # Countdown
        for i in range(3, 0, -1):
            ret, frame = cap.read()
            if ret:
                display = frame.copy()
                cv2.putText(display, str(i), (frame.shape[1]//2 - 50, frame.shape[0]//2 + 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 10)
                cv2.imshow(window, display)
            cv2.waitKey(1000)
        
        print("[RECORDING] Started! Move your head around...")
        
        start_time = time.time()
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            elapsed = time.time() - start_time
            remaining = max(0, duration - elapsed)
            
            if elapsed >= duration:
                break
            
            # Write to video
            out.write(frame)
            frame_count += 1
            
            # Display
            display = frame.copy()
            
            # Timer bar
            progress = int((elapsed / duration) * frame.shape[1])
            cv2.rectangle(display, (0, 0), (progress, 30), (0, 255, 0), -1)
            cv2.rectangle(display, (0, 0), (frame.shape[1], 30), (255, 255, 255), 2)
            
            cv2.putText(display, f"Recording: {remaining:.1f}s left", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(display, f"Person: {person_name}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display, "Move head: left/right, up/down", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            cv2.imshow(window, display)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        out.release()
        cap.release()
        cv2.destroyWindow(window)
        
        print(f"\n[SAVED] Video: {video_path}")
        print(f"[INFO] Frames recorded: {frame_count}")
        
        # Now extract faces
        print("\n[EXTRACTING] Processing video for faces...")
        extracted = self.extract_from_video(str(video_path), person_name)
        
        return extracted
    
    def extract_from_video(self, video_path: str, person_name: str, 
                           max_frames: int = 100, interval: int = 3) -> int:
        """Extract faces from a video file."""
        folder = self.get_folder(person_name)
        img_num = self.get_next_num(folder)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[ERROR] Cannot open: {video_path}")
            return 0
        
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[VIDEO] {total} frames")
        
        cv2.namedWindow("Extracting", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Extracting", 640, 480)
        
        extracted = 0
        idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            idx += 1
            if idx % interval != 0:
                continue
            
            faces = self.detect_faces_fast(frame)
            
            if len(faces) == 1:
                x, y, w, h = faces[0]
                pad = 30
                H, W = frame.shape[:2]
                x1, y1 = max(0, x-pad), max(0, y-pad)
                x2, y2 = min(W, x+w+pad), min(H, y+h+pad)
                
                face_img = frame[y1:y2, x1:x2]
                
                if face_img.shape[0] >= 80 and face_img.shape[1] >= 80:
                    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
                    
                    if blur > 50:
                        cv2.imwrite(str(folder / f"{img_num}.jpg"), face_img)
                        extracted += 1
                        img_num += 1
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            progress = int((idx / total) * 100)
            cv2.putText(frame, f"{progress}% - Extracted: {extracted}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Extracting", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q') or extracted >= max_frames:
                break
        
        cap.release()
        cv2.destroyWindow("Extracting")
        
        print(f"\n[DONE] Extracted {extracted} faces for {person_name}")
        return extracted
    
    def capture_photos(self, person_name: str, camera_index: int = 0) -> int:
        """Capture individual photos."""
        folder = self.get_folder(person_name)
        img_num = self.get_next_num(folder)
        
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return 0
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        window = f'Capture: {person_name} [SPACE=snap Q=done]'
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 800, 600)
        
        captured = 0
        print(f"\n[CAPTURE] {person_name}")
        print("[INFO] SPACE=capture, Q=done\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            display = frame.copy()
            faces = self.detect_faces_fast(frame)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            cv2.putText(display, f"{person_name} - Captured: {captured}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            cv2.imshow(window, display)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') and faces:
                x, y, w, h = max(faces, key=lambda r: r[2]*r[3])
                pad = 30
                H, W = frame.shape[:2]
                x1, y1 = max(0, x-pad), max(0, y-pad)
                x2, y2 = min(W, x+w+pad), min(H, y+h+pad)
                cv2.imwrite(str(folder / f"{img_num}.jpg"), frame[y1:y2, x1:x2])
                captured += 1
                img_num += 1
                print(f"  [+] {img_num-1}.jpg")
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyWindow(window)
        return captured
    
    def run(self, camera_index: int = 0):
        """Main loop."""
        print("\n" + "=" * 50)
        print("Face Detection & Recognition")
        print("=" * 50)
        
        print(f"[INFO] Known People: {', '.join(sorted(self.known_face_labels.values()))}")
        
        print("Controls:")
        print("  N = NEW person (record video - EASY)")
        print("  A = Add person (photo capture)")
        print("  V = Add from video file")
        print("  R = Retrain model")
        print("  Q = Quit")
        print("=" * 50 + "\n")
        
        # Robust Camera Discovery
        cap = None
        for idx in range(4):
            print(f"[INFO] Trying camera index {idx}...")
            temp_cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not temp_cap.isOpened():
                temp_cap = cv2.VideoCapture(idx)
            
            if temp_cap.isOpened():
                ret, _ = temp_cap.read()
                if ret:
                    print(f"[SUCCESS] Connected to camera {idx}")
                    cap = temp_cap
                    camera_index = idx
                    break
                else:
                    temp_cap.release()
        
        if cap is None:
            print("[ERROR] No valid camera found (tried indices 0-3)")
            return
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print("[INFO] Camera ready!")
        
        window = 'Face Detection [N:new A:add V:video R:retrain Q:quit]'
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 800, 600)
        
        fps_start = time.time()
        fps_count = 0
        fps = 0
        
        # Text input state
        input_mode = False
        input_text = ""
        input_action = ""  # "record", "capture", "video"
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            fps_count += 1
            if time.time() - fps_start >= 1.0:
                fps = fps_count
                fps_count = 0
                fps_start = time.time()
            
            display = frame.copy()
            
            if input_mode:
                # Show text input overlay
                overlay = display.copy()
                cv2.rectangle(overlay, (0, 0), (display.shape[1], 120), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.8, display, 0.2, 0, display)
                
                action_text = {"record": "Record Video", "capture": "Photo Capture", "video": "Video Path"}
                cv2.putText(display, f"[{action_text.get(input_action, '')}] Enter name:", (10, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(display, input_text + "_", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                cv2.putText(display, "ENTER=confirm  ESC=cancel", (10, display.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            else:
                # Detection
                self.frame_count += 1
                if self.frame_count % self.skip_frames == 0:
                    self.cached_faces = self.detect_faces_fast(frame)
                    self.cached_results = [self.recognize_face(frame, r) for r in self.cached_faces]
                
                for i, (x, y, w, h) in enumerate(self.cached_faces):
                    if i < len(self.cached_results):
                        name, conf, _ = self.cached_results[i]
                    else:
                        name, conf = "Unknown", 0
                    
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    label = f"{name} ({conf:.0f}%)" if name != "Unknown" else "Unknown"
                    
                    cv2.rectangle(display, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(display, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                cv2.putText(display, f"FPS: {fps}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display, f"Persons: {len(self.known_face_labels)}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow(window, display)
            key = cv2.waitKey(1) & 0xFF
            
            if input_mode:
                if key == 27:  # ESC
                    input_mode = False
                    input_text = ""
                elif key == 13:  # ENTER
                    if input_text.strip():
                        name = input_text.strip()
                        cv2.destroyWindow(window)
                        cap.release()
                        
                        if input_action == "record":
                            # Ask for duration
                            print(f"\nRecording for: {name}")
                            print("Enter duration in seconds (default 10): ", end="")
                            try:
                                dur_input = input().strip()
                                duration = int(dur_input) if dur_input else 10
                            except:
                                duration = 10
                            
                            count = self.record_and_extract(name, duration, camera_index)
                        elif input_action == "capture":
                            count = self.capture_photos(name, camera_index)
                        elif input_action == "video":
                            print(f"\nEnter full path to video file: ", end="")
                            video_path = input().strip()
                            if video_path and os.path.exists(video_path):
                                count = self.extract_from_video(video_path, name)
                            else:
                                print("[ERROR] File not found")
                                count = 0
                        else:
                            count = 0
                        
                        if count > 0:
                            print("\n[INFO] Retraining...")
                            self.force_retrain()
                        
                        # Reopen camera
                        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                        if not cap.isOpened():
                            cap = cv2.VideoCapture(camera_index)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
                        cv2.resizeWindow(window, 800, 600)
                    
                    input_mode = False
                    input_text = ""
                elif key == 8:  # BACKSPACE
                    input_text = input_text[:-1]
                elif 32 <= key <= 126:
                    input_text += chr(key)
            else:
                if key == ord('q') or key == ord('Q'):
                    break
                elif key == ord('r') or key == ord('R'):
                    self.force_retrain()
                elif key == ord('n') or key == ord('N'):
                    input_mode = True
                    input_text = ""
                    input_action = "record"
                elif key == ord('a') or key == ord('A'):
                    input_mode = True
                    input_text = ""
                    input_action = "capture"
                elif key == ord('v') or key == ord('V'):
                    input_mode = True
                    input_text = ""
                    input_action = "video"
        
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Done")


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Face Recognition System")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            for f in sorted(DATA_FACE_DIR.iterdir()):
                if f.is_dir() and not f.name.startswith('unknown'):
                    print(f"  {f.name}: {len(list(f.glob('*.jpg')))} images")
            sys.exit(0)
        elif sys.argv[1] == "--record" and len(sys.argv) >= 3:
            d = FaceDetector()
            dur = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            d.record_and_extract(sys.argv[2], dur)
            d.force_retrain()
            sys.exit(0)
        elif sys.argv[1] == "--video" and len(sys.argv) >= 4:
            d = FaceDetector()
            d.extract_from_video(sys.argv[2], sys.argv[3])
            d.force_retrain()
            sys.exit(0)
    
    print("\nCommands:")
    print("  python face_model.py                    # Run detection")
    print("  python face_model.py --list             # List persons")
    print("  python face_model.py --record 'Name' 10 # Record 10s video")
    print("  python face_model.py --video path 'Name'# Extract from video")
    print("\nControls: N=new(record) A=add(photos) V=video R=retrain Q=quit")
    print("=" * 50 + "\n")
    
    FaceDetector().run()
