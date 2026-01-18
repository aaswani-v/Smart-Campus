"""
Faces API Routes
Serves face images manifest for frontend face-api.js training.
"""
from fastapi import APIRouter
from pathlib import Path
import os

router = APIRouter()

# Path to face database
FACES_DIR = Path(__file__).parent.parent.parent / "models" / "_data-face"

@router.get("/manifest")
async def get_faces_manifest():
    """
    Returns a manifest of all enrolled people and their image URLs.
    The frontend uses this to train face-api.js.
    """
    people = []
    
    if not FACES_DIR.exists():
        return {"people": []}
    
    for folder in FACES_DIR.iterdir():
        if folder.is_dir() and not folder.name.startswith('_') and not folder.name.startswith('.'):
            images = []
            for img_file in folder.glob('*.jpg'):
                # Return URL path relative to static mount
                images.append(f"/static/faces/{folder.name}/{img_file.name}")
            for img_file in folder.glob('*.png'):
                images.append(f"/static/faces/{folder.name}/{img_file.name}")
            
            if images:
                people.append({
                    "name": folder.name.replace('_', ' ').title(),
                    "folder": folder.name,
                    "images": images
                })
    
    return {"people": people}
