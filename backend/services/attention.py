"""
Smart Campus - Attention Tracking Service
Real-time attention monitoring using MediaPipe Face Mesh
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import math

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[AttentionService] MediaPipe not available, using fallback")


@dataclass
class AttentionMetrics:
    """Container for attention metrics"""
    attention_score: float  # 0-100
    head_yaw: float  # Degrees, left/right
    head_pitch: float  # Degrees, up/down
    head_roll: float  # Degrees, tilt
    left_ear: float  # Eye Aspect Ratio
    right_ear: float
    avg_ear: float
    is_drowsy: bool
    is_distracted: bool
    gaze_direction: str  # 'forward', 'left', 'right', 'up', 'down'
    face_detected: bool


class AttentionTracker:
    """Track student attention using facial landmarks"""
    
    # Landmark indices for MediaPipe Face Mesh
    # Face oval points for head pose
    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_LEFT = 33
    LEFT_EYE_RIGHT = 133
    RIGHT_EYE_LEFT = 362
    RIGHT_EYE_RIGHT = 263
    
    # Eye landmarks for EAR calculation
    LEFT_EYE_POINTS = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_POINTS = [362, 385, 387, 263, 373, 380]
    
    # Thresholds
    EAR_THRESHOLD = 0.21  # Below this = eyes closed
    DROWSY_FRAMES = 20  # Consecutive frames with low EAR = drowsy
    YAW_THRESHOLD = 25  # Degrees, looking away left/right
    PITCH_THRESHOLD = 20  # Degrees, looking up/down
    
    def __init__(self):
        self.consecutive_drowsy = 0
        
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=10,  # Track multiple students
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.face_mesh = None
    
    def _calculate_ear(self, eye_points: List[Tuple[float, float]]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR)
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        """
        if len(eye_points) != 6:
            return 0.3  # Default open eye value
        
        p1, p2, p3, p4, p5, p6 = eye_points
        
        # Vertical distances
        v1 = math.sqrt((p2[0] - p6[0])**2 + (p2[1] - p6[1])**2)
        v2 = math.sqrt((p3[0] - p5[0])**2 + (p3[1] - p5[1])**2)
        
        # Horizontal distance
        h = math.sqrt((p1[0] - p4[0])**2 + (p1[1] - p4[1])**2)
        
        if h == 0:
            return 0.3
        
        ear = (v1 + v2) / (2.0 * h)
        return ear
    
    def _estimate_head_pose(
        self,
        landmarks: List,
        image_width: int,
        image_height: int
    ) -> Tuple[float, float, float]:
        """
        Estimate head pose (yaw, pitch, roll) from landmarks
        Returns angles in degrees
        """
        # Key points for pose estimation
        nose = landmarks[self.NOSE_TIP]
        chin = landmarks[self.CHIN]
        left_eye_left = landmarks[self.LEFT_EYE_LEFT]
        right_eye_right = landmarks[self.RIGHT_EYE_RIGHT]
        
        # Convert to pixel coordinates
        nose_2d = (nose.x * image_width, nose.y * image_height)
        chin_2d = (chin.x * image_width, chin.y * image_height)
        left_eye_2d = (left_eye_left.x * image_width, left_eye_left.y * image_height)
        right_eye_2d = (right_eye_right.x * image_width, right_eye_right.y * image_height)
        
        # Calculate yaw (left/right rotation)
        eye_center = ((left_eye_2d[0] + right_eye_2d[0]) / 2, 
                      (left_eye_2d[1] + right_eye_2d[1]) / 2)
        nose_offset = nose_2d[0] - eye_center[0]
        eye_distance = abs(right_eye_2d[0] - left_eye_2d[0])
        
        if eye_distance > 0:
            yaw = math.atan2(nose_offset, eye_distance / 2) * 180 / math.pi
        else:
            yaw = 0
        
        # Calculate pitch (up/down rotation)
        face_height = abs(chin_2d[1] - eye_center[1])
        nose_y_offset = nose_2d[1] - eye_center[1]
        
        if face_height > 0:
            pitch = (nose_y_offset / face_height - 0.5) * 60  # Normalize to degrees
        else:
            pitch = 0
        
        # Calculate roll (tilt)
        delta_y = right_eye_2d[1] - left_eye_2d[1]
        delta_x = right_eye_2d[0] - left_eye_2d[0]
        roll = math.atan2(delta_y, delta_x) * 180 / math.pi
        
        return yaw, pitch, roll
    
    def _determine_gaze_direction(self, yaw: float, pitch: float) -> str:
        """Determine where the person is looking"""
        if abs(yaw) < 10 and abs(pitch) < 10:
            return 'forward'
        elif yaw < -self.YAW_THRESHOLD:
            return 'left'
        elif yaw > self.YAW_THRESHOLD:
            return 'right'
        elif pitch < -self.PITCH_THRESHOLD:
            return 'up'
        elif pitch > self.PITCH_THRESHOLD:
            return 'down'
        else:
            return 'forward'
    
    def _calculate_attention_score(
        self,
        yaw: float,
        pitch: float,
        ear: float,
        is_drowsy: bool
    ) -> float:
        """
        Calculate attention score (0-100)
        100 = fully attentive, 0 = completely distracted
        """
        score = 100.0
        
        # Penalize head rotation
        yaw_penalty = min(abs(yaw) * 1.5, 40)  # Max 40 points penalty
        pitch_penalty = min(abs(pitch) * 1.2, 30)  # Max 30 points penalty
        
        score -= yaw_penalty
        score -= pitch_penalty
        
        # Penalize drowsiness
        if ear < self.EAR_THRESHOLD:
            eye_penalty = (self.EAR_THRESHOLD - ear) * 100  # Up to 20 points
            score -= min(eye_penalty, 20)
        
        if is_drowsy:
            score -= 20  # Additional penalty for sustained drowsiness
        
        return max(0, min(100, score))
    
    def analyze_frame(self, image: np.ndarray) -> List[AttentionMetrics]:
        """
        Analyze a frame and return attention metrics for each detected face
        """
        results = []
        
        if not MEDIAPIPE_AVAILABLE or self.face_mesh is None:
            # Fallback: return dummy data for testing
            return [AttentionMetrics(
                attention_score=75.0,
                head_yaw=0.0,
                head_pitch=0.0,
                head_roll=0.0,
                left_ear=0.28,
                right_ear=0.28,
                avg_ear=0.28,
                is_drowsy=False,
                is_distracted=False,
                gaze_direction='forward',
                face_detected=True
            )]
        
        # Convert BGR to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image.shape[:2]
        
        # Process with MediaPipe
        mp_results = self.face_mesh.process(rgb_image)
        
        if not mp_results.multi_face_landmarks:
            return []
        
        for face_landmarks in mp_results.multi_face_landmarks:
            landmarks = face_landmarks.landmark
            
            # Calculate eye aspect ratios
            left_eye_points = [
                (landmarks[i].x * width, landmarks[i].y * height)
                for i in self.LEFT_EYE_POINTS
            ]
            right_eye_points = [
                (landmarks[i].x * width, landmarks[i].y * height)
                for i in self.RIGHT_EYE_POINTS
            ]
            
            left_ear = self._calculate_ear(left_eye_points)
            right_ear = self._calculate_ear(right_eye_points)
            avg_ear = (left_ear + right_ear) / 2
            
            # Check drowsiness
            if avg_ear < self.EAR_THRESHOLD:
                self.consecutive_drowsy += 1
            else:
                self.consecutive_drowsy = 0
            
            is_drowsy = self.consecutive_drowsy >= self.DROWSY_FRAMES
            
            # Estimate head pose
            yaw, pitch, roll = self._estimate_head_pose(landmarks, width, height)
            
            # Determine gaze and distraction
            gaze = self._determine_gaze_direction(yaw, pitch)
            is_distracted = gaze != 'forward'
            
            # Calculate attention score
            attention = self._calculate_attention_score(yaw, pitch, avg_ear, is_drowsy)
            
            results.append(AttentionMetrics(
                attention_score=round(attention, 1),
                head_yaw=round(yaw, 1),
                head_pitch=round(pitch, 1),
                head_roll=round(roll, 1),
                left_ear=round(left_ear, 3),
                right_ear=round(right_ear, 3),
                avg_ear=round(avg_ear, 3),
                is_drowsy=is_drowsy,
                is_distracted=is_distracted,
                gaze_direction=gaze,
                face_detected=True
            ))
        
        return results
    
    def get_class_attention(self, metrics_list: List[AttentionMetrics]) -> Dict:
        """
        Calculate aggregate attention metrics for a class
        """
        if not metrics_list:
            return {
                'average_attention': 0,
                'attentive_count': 0,
                'distracted_count': 0,
                'drowsy_count': 0,
                'total_detected': 0
            }
        
        total = len(metrics_list)
        avg_attention = sum(m.attention_score for m in metrics_list) / total
        attentive = sum(1 for m in metrics_list if m.attention_score >= 70)
        distracted = sum(1 for m in metrics_list if m.is_distracted)
        drowsy = sum(1 for m in metrics_list if m.is_drowsy)
        
        return {
            'average_attention': round(avg_attention, 1),
            'attentive_count': attentive,
            'distracted_count': distracted,
            'drowsy_count': drowsy,
            'total_detected': total,
            'attention_distribution': {
                'high': sum(1 for m in metrics_list if m.attention_score >= 80),
                'medium': sum(1 for m in metrics_list if 50 <= m.attention_score < 80),
                'low': sum(1 for m in metrics_list if m.attention_score < 50)
            }
        }


# Singleton instance
_attention_tracker = None

def get_attention_tracker() -> AttentionTracker:
    """Get singleton AttentionTracker instance"""
    global _attention_tracker
    if _attention_tracker is None:
        _attention_tracker = AttentionTracker()
    return _attention_tracker
