# Smart Campus Attendance System - LAYOUT FIXED
# Run: python attendance_app.py

import cv2
import numpy as np
import os
import pickle
import tkinter as tk
from tkinter import messagebox, font
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk

print("=" * 50)
print("  Smart Campus Attendance System")
print("=" * 50)

# Check LBPH
try:
    test = cv2.face.LBPHFaceRecognizer_create()
    LBPH_AVAILABLE = True
    print("[OK] Face Recognition available")
except:
    LBPH_AVAILABLE = False
    print("[WARN] Need opencv-contrib-python for recognition")


class AttendanceSystem:
    def __init__(self):
        self.data_dir = Path("attendance_data")
        self.data_dir.mkdir(exist_ok=True)
        
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        print(f"[OK] Face detector loaded")
        
        if LBPH_AVAILABLE:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        else:
            self.recognizer = None
        
        self.label_map = {}
        self.student_names = {}
        self.attendance_today = set()
        self._load_data()
    
    def _load_data(self):
        map_path = self.data_dir / "data.pkl"
        model_path = self.data_dir / "model.yml"
        
        if map_path.exists():
            with open(map_path, 'rb') as f:
                data = pickle.load(f)
                self.label_map = data.get('label_map', {})
                self.student_names = data.get('student_names', {})
            print(f"[OK] Loaded {len(self.label_map)} students")
        
        if self.recognizer and model_path.exists():
            try:
                self.recognizer.read(str(model_path))
            except:
                pass
    
    def _save_data(self):
        with open(self.data_dir / "data.pkl", 'wb') as f:
            pickle.dump({'label_map': self.label_map, 'student_names': self.student_names}, f)
        if self.recognizer:
            try:
                self.recognizer.write(str(self.data_dir / "model.yml"))
            except:
                pass
    
    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        return faces
    
    def preprocess_face(self, frame, rect):
        x, y, w, h = rect
        face = frame[y:y+h, x:x+w]
        if len(face.shape) == 3:
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        face = cv2.resize(face, (200, 200))
        face = cv2.equalizeHist(face)
        return face
    
    def enroll(self, student_id, name, frames):
        if not self.recognizer:
            return False, "Recognition not available"
        if len(frames) < 3:
            return False, "Need 3+ photos"
        
        label = max(self.label_map.keys(), default=-1) + 1
        faces, labels = [], []
        
        for img in frames:
            detected = self.detect_faces(img)
            if len(detected) == 1:
                face = self.preprocess_face(img, detected[0])
                faces.append(face)
                labels.append(label)
        
        if len(faces) < 3:
            return False, f"Only {len(faces)} good faces"
        
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
            if label in self.label_map and conf < 80:
                sid = self.label_map[label]
                name = self.student_names.get(sid, "Unknown")
                return sid, name, int(100 - conf)
        except:
            pass
        return None, "Unknown", 0


class App:
    def __init__(self):
        self.system = AttendanceSystem()
        self.cap = None
        self.running = False
        self.frames = []
        self.mode = "recognition"
        
        self.root = tk.Tk()
        self.root.title("Smart Campus - Attendance System")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a2e')
        self.root.resizable(True, True)
        
        self.setup_ui()
    
    def setup_ui(self):
        title_font = font.Font(family='Helvetica', size=20, weight='bold')
        label_font = font.Font(family='Helvetica', size=11)
        btn_font = font.Font(family='Helvetica', size=10, weight='bold')
        
        # HEADER
        header = tk.Frame(self.root, bg='#1a1a2e')
        header.pack(fill='x', padx=20, pady=10)
        tk.Label(header, text="🎓 Smart Campus Attendance", font=title_font, 
                fg='#ff6b35', bg='#1a1a2e').pack(side='left')
        
        # MAIN CONTAINER
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(fill='both', expand=True, padx=20, pady=10)
        
        # LEFT SIDE - Camera (takes most space)
        left = tk.Frame(main, bg='#16213e', relief='ridge', bd=2)
        left.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Video Canvas (fixed size, centered)
        video_frame = tk.Frame(left, bg='#0f0f1a')
        video_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.video_label = tk.Label(video_frame, bg='#0f0f1a')
        self.video_label.pack(fill='both', expand=True)
        
        # Controls below video
        ctrl = tk.Frame(left, bg='#16213e')
        ctrl.pack(fill='x', pady=10, padx=10)
        
        self.cam_btn = tk.Button(ctrl, text="▶ START CAMERA", font=btn_font,
                                  bg='#22c55e', fg='white', command=self.toggle_camera,
                                  width=18, height=2, cursor='hand2')
        self.cam_btn.pack(side='left', padx=10)
        
        mode_frame = tk.Frame(ctrl, bg='#16213e')
        mode_frame.pack(side='left', padx=20)
        
        self.mode_var = tk.StringVar(value="recognition")
        tk.Radiobutton(mode_frame, text="Recognition", variable=self.mode_var, 
                       value="recognition", bg='#16213e', fg='white',
                       selectcolor='#16213e', font=label_font, activebackground='#16213e',
                       command=self.change_mode).pack(side='left', padx=5)
        tk.Radiobutton(mode_frame, text="Enrollment", variable=self.mode_var,
                       value="enrollment", bg='#16213e', fg='white',
                       selectcolor='#16213e', font=label_font, activebackground='#16213e',
                       command=self.change_mode).pack(side='left', padx=5)
        
        # RIGHT SIDE - Panels (fixed width)
        right = tk.Frame(main, bg='#1a1a2e', width=320)
        right.pack(side='right', fill='y')
        right.pack_propagate(False)
        
        # ENROLL PANEL
        enroll_panel = tk.LabelFrame(right, text=" 📝 Enroll Student ", font=label_font,
                                      bg='#16213e', fg='#ff6b35', labelanchor='n')
        enroll_panel.pack(fill='x', pady=5, padx=5)
        
        form = tk.Frame(enroll_panel, bg='#16213e')
        form.pack(fill='x', padx=10, pady=10)
        
        tk.Label(form, text="Student ID:", bg='#16213e', fg='white', font=label_font).grid(row=0, column=0, sticky='w', pady=5)
        self.id_entry = tk.Entry(form, font=label_font, width=25)
        self.id_entry.grid(row=0, column=1, pady=5, padx=5)
        
        tk.Label(form, text="Name:", bg='#16213e', fg='white', font=label_font).grid(row=1, column=0, sticky='w', pady=5)
        self.name_entry = tk.Entry(form, font=label_font, width=25)
        self.name_entry.grid(row=1, column=1, pady=5, padx=5)
        
        self.count_label = tk.Label(enroll_panel, text="Photos: 0/5", bg='#16213e', 
                                     fg='#22c55e', font=('Helvetica', 12, 'bold'))
        self.count_label.pack(pady=5)
        
        btn_row = tk.Frame(enroll_panel, bg='#16213e')
        btn_row.pack(pady=10)
        
        tk.Button(btn_row, text="📸 Capture", font=btn_font, bg='#3b82f6', fg='white',
                  command=self.capture, width=9, cursor='hand2').pack(side='left', padx=3)
        tk.Button(btn_row, text="✅ Enroll", font=btn_font, bg='#22c55e', fg='white',
                  command=self.enroll, width=9, cursor='hand2').pack(side='left', padx=3)
        tk.Button(btn_row, text="🗑 Clear", font=btn_font, bg='#ef4444', fg='white',
                  command=self.clear, width=9, cursor='hand2').pack(side='left', padx=3)
        
        # LOG PANEL
        log_panel = tk.LabelFrame(right, text=" 📋 Attendance Log ", font=label_font,
                                   bg='#16213e', fg='#22c55e', labelanchor='n')
        log_panel.pack(fill='both', expand=True, pady=5, padx=5)
        
        self.log_list = tk.Listbox(log_panel, bg='#0f0f1a', fg='white', 
                                    font=('Consolas', 11), height=12,
                                    selectbackground='#ff6b35')
        self.log_list.pack(fill='both', expand=True, padx=10, pady=10)
        
        # STATUS
        self.status = tk.Label(right, text=f"Enrolled: {len(self.system.label_map)} | Ready",
                                bg='#1a1a2e', fg='#888', font=label_font)
        self.status.pack(pady=10)
    
    def change_mode(self):
        self.mode = self.mode_var.get()
        self.status.config(text=f"Mode: {self.mode.upper()}")
    
    def toggle_camera(self):
        if self.running:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera!")
            return
        self.running = True
        self.cam_btn.config(text="⏹ STOP CAMERA", bg='#ef4444')
        self.update_video()
    
    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.cam_btn.config(text="▶ START CAMERA", bg='#22c55e')
    
    def update_video(self):
        if not self.running:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(30, self.update_video)
            return
        
        frame = cv2.flip(frame, 1)
        self.current_frame = frame.copy()
        
        faces = self.system.detect_faces(frame)
        
        for (x, y, w, h) in faces:
            if self.mode == "recognition":
                sid, name, conf = self.system.recognize(frame, (x, y, w, h))
                if sid:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(frame, f"{name} ({conf}%)", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    if sid not in self.system.attendance_today:
                        self.system.attendance_today.add(sid)
                        time_str = datetime.now().strftime("%H:%M:%S")
                        self.log_list.insert(0, f"✅ {name} - {time_str}")
                        with open(self.system.data_dir / f"log_{datetime.now().strftime('%Y%m%d')}.txt", 'a') as f:
                            f.write(f"{time_str},{sid},{name}\n")
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 165, 255), 3)
                    cv2.putText(frame, "Unknown", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 107, 53), 3)
                cv2.putText(frame, "ENROLLMENT MODE", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 107, 53), 2)
        
        # Convert and resize to fit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Get label size and resize proportionally
        label_w = self.video_label.winfo_width()
        label_h = self.video_label.winfo_height()
        
        if label_w > 100 and label_h > 100:
            # Maintain aspect ratio
            img_ratio = img.width / img.height
            label_ratio = label_w / label_h
            
            if img_ratio > label_ratio:
                new_w = label_w
                new_h = int(label_w / img_ratio)
            else:
                new_h = label_h
                new_w = int(label_h * img_ratio)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)
        
        self.root.after(30, self.update_video)
    
    def capture(self):
        if not self.running:
            messagebox.showwarning("Warning", "Start camera first!")
            return
        if len(self.frames) >= 5:
            messagebox.showinfo("Info", "Already have 5 photos!")
            return
        if hasattr(self, 'current_frame'):
            self.frames.append(self.current_frame.copy())
            self.count_label.config(text=f"Photos: {len(self.frames)}/5")
            self.status.config(text=f"Captured #{len(self.frames)}")
    
    def clear(self):
        self.frames = []
        self.id_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.count_label.config(text="Photos: 0/5")
        self.status.config(text="Cleared")
    
    def enroll(self):
        sid = self.id_entry.get().strip()
        name = self.name_entry.get().strip()
        if not sid or not name:
            messagebox.showwarning("Warning", "Enter ID and Name!")
            return
        if len(self.frames) < 3:
            messagebox.showwarning("Warning", f"Need 3+ photos, have {len(self.frames)}")
            return
        
        ok, msg = self.system.enroll(sid, name, self.frames)
        if ok:
            messagebox.showinfo("Success", msg)
            self.status.config(text=f"Enrolled: {len(self.system.label_map)}")
            self.clear()
        else:
            messagebox.showerror("Error", msg)
    
    def run(self):
        self.root.mainloop()
        if self.cap:
            self.cap.release()


if __name__ == "__main__":
    print("\nStarting...")
    app = App()
    app.run()
