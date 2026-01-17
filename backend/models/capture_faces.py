"""
Face Dataset Capture Script
============================
Captures face images for training the attendance system.

Usage:
    python capture_faces.py

Instructions:
    1. Enter the person's name when prompted
    2. Press SPACE to capture an image
    3. Press Q to quit and save

Images are saved to: _data-face/{person_name}/1.jpg, 2.jpg, 3.jpg, etc.
"""

import cv2
import os
import sys
import traceback
from pathlib import Path


def get_next_image_number(folder_path: Path) -> int:
    """Get the next available image number in the folder.

    Supports common image extensions and ignores non-numeric filenames.
    """
    exts = ("*.jpg", "*.jpeg", "*.png")
    existing = []
    for ext in exts:
        existing.extend(folder_path.glob(ext))

    if not existing:
        return 1

    numbers = []
    for f in existing:
        try:
            num = int(f.stem)
            numbers.append(num)
        except ValueError:
            continue

    return max(numbers, default=0) + 1


def main():
    # Get the data folder path (same directory as this script)
    script_dir = Path(__file__).parent
    data_folder = script_dir / "_data-face"
    
    # Ensure data folder exists
    data_folder.mkdir(parents=True, exist_ok=True)
    
    # Get person name
    print("\n" + "="*50)
    print("  FACE DATASET CAPTURE TOOL")
    print("="*50)
    print("\nExisting people in dataset:")
    
    existing_people = [d.name for d in data_folder.iterdir() if d.is_dir() and not d.name.startswith("unknown")]
    if existing_people:
        for person in sorted(existing_people):
            count = len(list((data_folder / person).glob("*.jpg")))
            print(f"  - {person} ({count} images)")
    else:
        print("  (none)")
    
    print("\n" + "-"*50)
    person_name = input("Enter person's name: ").strip()
    
    if not person_name:
        print("Error: Name cannot be empty!")
        return
    
    # Create person folder (ensure parents)
    person_folder = data_folder / person_name
    person_folder.mkdir(parents=True, exist_ok=True)
    
    # Get starting image number
    image_number = get_next_image_number(person_folder)
    
    print(f"\nSaving images to: {person_folder}")
    print(f"Starting from image #{image_number}")
    print("\n" + "-"*50)
    print("Controls:")
    print("  SPACE - Capture image")
    print("  Q     - Quit")
    print("-"*50 + "\n")
    
    # Initialize webcam (try DirectShow on Windows for better compatibility)
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    except Exception:
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam!")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Load face detector for preview
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    captured_count = 0
    
    print("Camera ready! Position your face and press SPACE to capture.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame!")
            break
        
        # Mirror the frame for natural viewing
        display_frame = cv2.flip(frame, 1)
        
        # Detect faces for preview
        gray = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        # Draw face rectangles
        for (x, y, w, h) in faces:
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Draw info overlay
        cv2.putText(display_frame, f"Person: {person_name}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display_frame, f"Captured: {captured_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "SPACE: Capture | Q: Quit", (10, display_frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Face detection status
        if len(faces) == 0:
            cv2.putText(display_frame, "No face detected", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        elif len(faces) == 1:
            cv2.putText(display_frame, "Face detected - Ready!", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(display_frame, f"Multiple faces ({len(faces)})", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        # Show frame
        cv2.imshow("Face Capture", display_frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # SPACE - capture
            # Save a flipped copy of the original frame so saved image matches preview
            save_frame = cv2.flip(frame, 1)
            filename = person_folder / f"{image_number}.jpg"

            try:
                success = cv2.imwrite(str(filename), save_frame)
            except Exception as e:
                success = False
                print(f"  ✗ Exception while saving: {e}")
                traceback.print_exc()

            if success:
                print(f"  ✓ Captured: {filename.name}")
                captured_count += 1
                image_number += 1
            else:
                print(f"  ✗ Failed to save image to: {filename}")
                # Attempt a fallback write using imencode
                try:
                    ret, buf = cv2.imencode('.jpg', save_frame)
                    if ret:
                        with open(filename, 'wb') as f:
                            f.write(buf.tobytes())
                        print(f"  ✓ Saved via fallback: {filename.name}")
                        captured_count += 1
                        image_number += 1
                    else:
                        print("  ✗ cv2.imencode failed — check write permissions and available disk space")
                except Exception as e:
                    print(f"  ✗ Fallback save exception: {e}")
                    traceback.print_exc()

            # Flash effect
            flash = display_frame.copy()
            cv2.rectangle(flash, (0, 0), (flash.shape[1], flash.shape[0]), (255, 255, 255), -1)
            cv2.addWeighted(flash, 0.3, display_frame, 0.7, 0, display_frame)
            cv2.imshow("Face Capture", display_frame)
            cv2.waitKey(100)
            
        elif key == ord('q') or key == ord('Q'):  # Q - quit
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    # Summary
    print("\n" + "="*50)
    print("  CAPTURE COMPLETE")
    print("="*50)
    print(f"  Person: {person_name}")
    print(f"  Images captured this session: {captured_count}")
    print(f"  Total images in folder: {len(list(person_folder.glob('*.jpg')))}")
    print(f"  Saved to: {person_folder}")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
