"""
Photo Organization Script (Google Photos Style)
Organizes unassigned/scattered face images into person clusters.

Features:
1. Scans 'unknown/' and 'unknown_person_*/' folders
2. Uses "Single Linkage" clustering:
   - A face belongs to a cluster if it matches ANY face in that cluster
   - This fixes the issue where a face might not match the "representative" but matches another face
3. Moves organized photos into clean 'clustered_person_X/' folders
"""

import cv2
import numpy as np
import shutil
from pathlib import Path
from typing import List, Dict, Set, Tuple
import os

# Define paths
BASE_DIR = Path(__file__).parent / "_data-face"
UNKNOWN_DIR = BASE_DIR / "unknown"

# Clustering settings
CLUSTER_THRESHOLD = 90.0  # Relaxed threshold (standard is ~80)

class FaceImage:
    """Represents a single face image."""
    def __init__(self, path: Path):
        self.path = path
        self.face_roi = None
        self.hist_face = None
        self.load_image()
    
    def load_image(self):
        """Load and preprocess image."""
        try:
            img = cv2.imread(str(self.path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                return
            
            # Resize for consistent LBPH grid calculation
            self.face_roi = cv2.resize(img, (100, 100))
            self.face_roi = cv2.equalizeHist(self.face_roi)
            
        except Exception as e:
            print(f"[ERROR] Loading {self.path.name}: {e}")

class PhotoOrganizer:
    def __init__(self):
        self.cluster_map: Dict[int, List[FaceImage]] = {}

    def compute_distance(self, face1: FaceImage, face2: FaceImage) -> float:
        """Compute LBPH distance between two faces."""
        if face1.face_roi is None or face2.face_roi is None:
            return 999.0
            
        # To compare two faces, we train on one and predict the other
        try:
            # Create fresh recognizer with high threshold to ensure we get a distance
            rec = cv2.face.LBPHFaceRecognizer_create(
                radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=1000.0
            )
            rec.train([face1.face_roi], np.array([1]))
            label, distance = rec.predict(face2.face_roi)
            return distance
        except Exception:
            return 999.0

    def collect_unnorganized_images(self) -> List[FaceImage]:
        """Collect images from unknown/ and unknown_person_*/ folders."""
        images = []
        
        # 1. Check unknown/
        if UNKNOWN_DIR.exists():
            for p in UNKNOWN_DIR.glob("*.jpg"):
                images.append(FaceImage(p))
                
        # 2. Check unknown_person_*/
        for folder in BASE_DIR.iterdir():
            if folder.is_dir() and folder.name.startswith("unknown_person"):
                for p in folder.glob("*.jpg"):
                    images.append(FaceImage(p))
                    
        print(f"[INFO] Found {len(images)} unorganized images.")
        return images

    def cluster_images(self):
        """Run clustering algorithm."""
        images = self.collect_unnorganized_images()
        if not images:
            print("[INFO] No images to organize.")
            return

        # Simple clustering algorithm
        # For each image:
        #   Compare with all existing clusters
        #   Find "Single Linkage" distance (min distance to ANY face in cluster)
        #   If min_dist < threshold, add to that cluster
        #   Else create new cluster
        
        clusters = [] # List of lists of FaceImages
        
        print("[INFO] Starting clustering (this may take a moment)...")
        total = len(images)
        
        for i, img in enumerate(images):
            print(f"\r[INFO] Processing image {i+1}/{total}...", end="")
            
            if img.face_roi is None:
                continue
                
            best_cluster_idx = -1
            min_dist = 999.0
            
            # Check against existing clusters
            for c_idx, cluster_imgs in enumerate(clusters):
                # Find distance to this cluster (Single Linkage: min distance to any node)
                for cluster_img in cluster_imgs:
                    dist = self.compute_distance(cluster_img, img)
                    if dist < min_dist:
                        min_dist = dist
            
            if min_dist < CLUSTER_THRESHOLD:
                # Add to best cluster
                # We need to find which cluster gave the min_dist
                # Re-looping isn't efficient, but for <1000 images it's fine
                # Let's optimize: maintain best_cluster_idx updated in loop above
                
                # Optimized loop:
                # Reset
                best_cluster_idx = -1
                min_dist = 999.0
                
                for c_idx, cluster_imgs in enumerate(clusters):
                    for cluster_img in cluster_imgs:
                        dist = self.compute_distance(cluster_img, img)
                        if dist < min_dist:
                            min_dist = dist
                            best_cluster_idx = c_idx
                
                if min_dist < CLUSTER_THRESHOLD and best_cluster_idx != -1:
                    clusters[best_cluster_idx].append(img)
                else:
                    clusters.append([img])
            else:
                # New cluster
                clusters.append([img])
                
        print(f"\n[INFO] Clustering complete. Found {len(clusters)} clusters.")
        self.save_results(clusters)

    def save_results(self, clusters: List[List[FaceImage]]):
        """Move files to new folder structure."""
        print("[INFO] Organizing files...")
        
        # Create temporary 'organized' folder to avoid conflicts during move
        org_dir = BASE_DIR / "organized_temp"
        if org_dir.exists():
            shutil.rmtree(org_dir)
        org_dir.mkdir()
        
        for idx, cluster in enumerate(clusters):
            # Sort by cluster size - maybe filter out noise (single images)?
            # Keep everything for now.
            
            cluster_name = f"person_{idx+1}"
            cluster_dir = org_dir / cluster_name
            cluster_dir.mkdir()
            
            for i, img in enumerate(cluster):
                # Copy file to new location
                src = img.path
                dst = cluster_dir / f"{i+1}.jpg"
                shutil.copy2(src, dst)
        
        print(f"[INFO] Files prepared in: {org_dir}")
        print("[ACTION REQUIRED] Verify the 'organized_temp' folder.")
        print("To apply changes, delete old 'unknown' folders and rename 'organized_temp' to your liking.")
        print(f"Or run with --apply to auto-replace old unknown folders.")

def apply_changes():
    """Destructive: deletes old unknown folders and moves organized_temp to split folders."""
    temp_dir = BASE_DIR / "organized_temp"
    if not temp_dir.exists():
        print("[ERROR] Run clustering first.")
        return

    # Delete old unknown folders
    if UNKNOWN_DIR.exists():
        shutil.rmtree(UNKNOWN_DIR)
    
    for folder in BASE_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith("unknown_person"):
            shutil.rmtree(folder)
            
    # Move clusters to main dir
    for folder in temp_dir.iterdir():
        if folder.is_dir():
            shutil.move(str(folder), str(BASE_DIR / f"unknown_{folder.name}"))
            
    shutil.rmtree(temp_dir)
    print("[SUCCESS] Applied organization. Check _data-face/unknown_person_*/ folders.")

if __name__ == "__main__":
    import sys
    print("="*50)
    print("Face Organizer")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_changes()
    else:
        organizer = PhotoOrganizer()
        organizer.cluster_images()
