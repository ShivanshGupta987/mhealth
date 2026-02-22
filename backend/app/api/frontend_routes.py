# app/api/frontend_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.sql_db import get_db
from app.models import Targets, Calls, Models, Emotions
from app.config import (
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, CONTAINER_NAME,
    TWILIO_ACCOUNT_SID
)
from minio import Minio
from minio.error import S3Error

router = APIRouter(prefix="/api", tags=["frontend"])

logger = logging.getLogger(__name__)

def make_minio_client():
    # create a MinIO client on demand to avoid circular imports
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=True
    )

# ----------------------------
# Dashboard stats
# ----------------------------
@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    try:
        total_targets = db.query(Targets).count()
        total_calls = db.query(Calls).count()
        pending_retries = db.query(Calls).filter(Calls.Status == "Message Not Conveyed").count()

        # recent call counts by status (last 7 days)
        since = datetime.now() - timedelta(days=7)
        recent = db.query(Calls).filter(Calls.Scheduled_Time >= since).all()
        by_status = {}
        for c in recent:
            by_status[c.Status or "UNKNOWN"] = by_status.get(c.Status or "UNKNOWN", 0) + 1

        return {
            "total_targets": total_targets,
            "total_calls": total_calls,
            "pending_retries": pending_retries,
            "recent_by_status": by_status
        }
    except Exception as e:
        logger.exception("Error building dashboard")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------
# Targets CRUD
# ----------------------------
@router.get("/targets")
def list_targets(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    targets = db.query(Targets).offset(skip).limit(limit).all()
    return [ {
        "Target_Id": str(t.Target_Id),
        "Name": t.Name,
        "Roll_No": t.Roll_No,
        "Phone_No": t.Phone_No,
        "Department_Name": t.Department_Name,
        "Program": t.Program,
    } for t in targets ]

@router.post("/targets")
def create_target(payload: dict, db: Session = Depends(get_db)):
    # payload expected to contain Name, Phone_No, Batch, Department_Name, Program, Semester etc.
    try:
        if not payload.get("Name") or not payload.get("Phone_No") or not payload.get("Roll_No"):
            raise HTTPException(status_code=400, detail="Name, Phone_No, and Roll_No are required")

        existing = db.query(Targets).filter(
            (Targets.Roll_No == payload["Roll_No"]) | (Targets.Phone_No == payload["Phone_No"])
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Target with same Roll_No or Phone_No already exists")

        new = Targets(
            Name=payload.get("Name"),
            Roll_No=payload.get("Roll_No"),
            Phone_No=payload.get("Phone_No"),
            Department_Name=payload.get("Department_Name"),
            Program=payload.get("Program"),
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        return {"ok": True, "Target_Id": str(new.Target_Id)}
    except Exception as e:
        db.rollback()
        logger.exception("Error creating target")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/targets/{target_id}")
def update_target(target_id: str, payload: dict, db: Session = Depends(get_db)):
    t = db.query(Targets).filter(Targets.Target_Id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    for k, v in payload.items():
        if hasattr(t, k):
            setattr(t, k, v)
    try:
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        logger.exception("Error updating target")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/targets/{target_id}")
def delete_target(target_id: str, db: Session = Depends(get_db)):
    t = db.query(Targets).filter(Targets.Target_Id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    try:
        db.delete(t)
        db.commit()
        return {"ok": True}
    except Exception as e:
        db.rollback()
        logger.exception("Error deleting target")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------
# Calls endpoints
# ----------------------------
@router.get("/calls")
def list_calls(skip: int = 0, limit: int = 200, target_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Calls)
    if target_id:
        q = q.filter(Calls.Target_Id == target_id)
    calls = q.order_by(Calls.Scheduled_Time.desc()).offset(skip).limit(limit).all()
    out = []
    for c in calls:
        out.append({
            "Call_Id": str(c.Call_Id),
            "Call_Sid": c.Call_Sid,
            "Target_Id": str(c.Target_Id) if c.Target_Id else None,
            "Model_Id": c.Model_Id,
            "Status": c.Status,
            "Scheduled_Time": c.Scheduled_Time.isoformat() if c.Scheduled_Time else None,
            "Started_Time": c.Started_Time.isoformat() if c.Started_Time else None,
            "Recording_Url": c.Recording_Url
        })
    return out

@router.get("/calls/{call_id}")
def get_call(call_id: str, db: Session = Depends(get_db)):
    c = db.query(Calls).filter(Calls.Call_Id == call_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Call not found")
    return {
        "Call_Id": str(c.Call_Id),
        "Call_Sid": c.Call_Sid,
        "Target_Id": str(c.Target_Id) if c.Target_Id else None,
        "Model_Id": c.Model_Id,
        "Status": c.Status,
        "Scheduled_Time": c.Scheduled_Time.isoformat() if c.Scheduled_Time else None,
        "Started_Time": c.Started_Time.isoformat() if c.Started_Time else None,
        "Recording_Url": c.Recording_Url
    }

# ----------------------------
# Models & Emotions
# ----------------------------
@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    rows = db.query(Models).all()
    return [{"Model_Id": r.Model_Id, "Model_Name": r.Model_Name, "Model_Version": r.Model_Version, "Model_Details": r.Model_Details} for r in rows]

@router.get("/emotions")
def list_emotions(db: Session = Depends(get_db)):
    rows = db.query(Emotions).all()
    return [{"Emotion_Id": r.Emotion_Id, "Emotion": r.Emotion} for r in rows]

# ----------------------------
# Schedule trigger
# ----------------------------
@router.post("/schedule")
def schedule_calls():
    try:
        # uses celery task
        from app.celery_config_exotel import initiate_calls_for_all_targets
        initiate_calls_for_all_targets.delay()
        return {"ok": True}
    except Exception as e:
        logger.exception("Error scheduling calls")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------
# Presigned recording URL
# ----------------------------
@router.get("/recording/{call_sid}")
def get_recording_presigned(call_sid: str):
    # object name pattern: {CallSid}.mp3
    object_name = f"{call_sid}.mp3"
    client = make_minio_client()
    try:
        # ensure object exists (optional)
        client.stat_object(CONTAINER_NAME, object_name)
        url = client.presigned_get_object(CONTAINER_NAME, object_name, expires=timedelta(minutes=60))
        return {"url": url}
    except S3Error as e:
        logger.exception("Recording not found or MinIO error")
        raise HTTPException(status_code=404, detail="Recording not found")
