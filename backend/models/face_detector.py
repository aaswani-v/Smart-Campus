import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import csv
import os
from ultralytics import YOLO
import face_recognition

class FaceAttendanceSystem:
    def __init__(self, data_path, model_path='yolov8n-face.pt'):
        self.data_path = Path(data_path)
        self.model = YOLO(model_path)
        self.known_face_encodings = []
        self.known_face_names = []
        self.attendance_file = 'attendance.csv'
        self.load_database()
    
    def load_database(self):
        """Load faces from the database folder"""
        for person_folder in self.data_path.iterdir():
            if person_folder.is_dir():
                person_name = person_folder.name
                for image_file in person_folder.glob('*.jpg'):
                    image = face_recognition.load_image_file(str(image_file))
                    face_encodings = face_recognition.face_encodings(image)
                    
                    if face_encodings:
                        self.known_face_encodings.append(face_encodings[0])
                        self.known_face_names.append(person_name)
                        print(f"Loaded: {person_name} from {image_file.name}")
    
    def detect_and_mark_attendance(self):
        """Detect faces from webcam and mark attendance"""
        cap = cv2.VideoCapture(0)
        marked_attendance = set()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces using YOLO
            results = self.model(frame)
            
            # Get face locations from YOLO detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=0.6
                )
                name = "Unknown"
                
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                
                # Mark attendance
                if name != "Unknown" and name not in marked_attendance:
                    self.mark_attendance(name)
                    marked_attendance.add(name)
                
                # Draw rectangle and name
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            cv2.imshow('Face Attendance System', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    def mark_attendance(self, name):
        """Mark attendance in CSV file"""
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        
        file_exists = os.path.isfile(self.attendance_file)
        
        with open(self.attendance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Name', 'Timestamp'])
            writer.writerow([name, timestamp])
        
        print(f"Attendance marked for {name} at {timestamp}")

if __name__ == "__main__":
    data_path = r"C:\Users\Ash\Downloads\HackCrypt\Attendify\backend\models\_data-face"
    system = FaceAttendanceSystem(data_path)
    system.detect_and_mark_attendance()