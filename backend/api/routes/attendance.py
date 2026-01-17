"""
Attendance API Routes
Handles marking attendance and fetching attendance history.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
import csv
import os
from pathlib import Path

router = APIRouter()

# Storage file for attendance
ATTENDANCE_FILE = Path(__file__).parent.parent.parent / "data" / "attendance.csv"

class MarkAttendanceRequest(BaseModel):
    name: str
    timestamp: Optional[str] = None

class AttendanceRecord(BaseModel):
    name: str
    date: str
    time: str

@router.post("/mark")
async def mark_attendance(request: MarkAttendanceRequest):
    """Mark attendance for a person."""
    try:
        timestamp = request.timestamp or datetime.now().isoformat()
        # Handle various timestamp formats
        timestamp = timestamp.replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            # Fallback: just use current time if parsing fails
            dt = datetime.now()
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H:%M:%S')
        
        # Ensure data directory exists
        ATTENDANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if already marked today
        existing = []
        if ATTENDANCE_FILE.exists():
            with open(ATTENDANCE_FILE, 'r', newline='') as f:
                reader = csv.DictReader(f)
                existing = list(reader)
        
        already_marked = any(
            r['name'] == request.name and r['date'] == date_str 
            for r in existing
        )
        
        if already_marked:
            return {"success": True, "message": f"{request.name} already marked for today", "duplicate": True}
        
        # Append new record
        file_exists = ATTENDANCE_FILE.exists()
        with open(ATTENDANCE_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'date', 'time'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({'name': request.name, 'date': date_str, 'time': time_str})
        
        return {"success": True, "message": f"Attendance marked for {request.name}", "duplicate": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_attendance_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    name: Optional[str] = None
):
    """Get attendance history with optional filters."""
    if not ATTENDANCE_FILE.exists():
        return {"records": [], "total": 0}
    
    with open(ATTENDANCE_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    # Apply filters
    if start_date:
        records = [r for r in records if r['date'] >= start_date]
    if end_date:
        records = [r for r in records if r['date'] <= end_date]
    if name:
        records = [r for r in records if name.lower() in r['name'].lower()]
    
    # Sort by date descending
    records.sort(key=lambda r: (r['date'], r['time']), reverse=True)
    
    return {"records": records, "total": len(records)}

@router.get("/summary")
async def get_attendance_summary(month: Optional[str] = None):
    """
    Get monthly attendance summary (Excel-like view).
    Returns a pivot table: rows = names, columns = dates.
    """
    if not ATTENDANCE_FILE.exists():
        return {"people": [], "dates": [], "matrix": {}}
    
    # Default to current month
    if not month:
        month = datetime.now().strftime('%Y-%m')
    
    with open(ATTENDANCE_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        records = [r for r in reader if r['date'].startswith(month)]
    
    # Build pivot table
    people = sorted(set(r['name'] for r in records))
    dates = sorted(set(r['date'] for r in records))
    
    matrix = {}
    for person in people:
        matrix[person] = {}
        for d in dates:
            # Check if present on that date
            present = any(r['name'] == person and r['date'] == d for r in records)
            matrix[person][d] = present
    
    return {
        "month": month,
        "people": people,
        "dates": dates,
        "matrix": matrix
    }
