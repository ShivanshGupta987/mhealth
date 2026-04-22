# app/api/counsellor_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging
import pytz
import uuid
import mimetypes
from urllib.parse import urlparse

import httpx
from minio import Minio
from minio.error import S3Error

from app.sql_db import get_db
from app.models import Targets, Calls, Emotions, FlaggedTargets
from app.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    CONTAINER_NAME,
)

router = APIRouter(prefix="/api/counsellor", tags=["Counsellor"])
logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


def _normalize_endpoint(endpoint: str) -> tuple[str, bool]:
    """Return (host, secure flag) for MinIO style endpoints."""
    if endpoint.startswith("http://"):
        return endpoint[len("http://"):], False
    if endpoint.startswith("https://"):
        return endpoint[len("https://"):], True
    return endpoint, False


def _init_minio_client() -> Optional[Minio]:
    if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY and CONTAINER_NAME):
        return None
    host, secure_flag = _normalize_endpoint(MINIO_ENDPOINT)
    try:
        return Minio(
            host,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=secure_flag,
        )
    except Exception:
        logger.exception("Failed to initialize MinIO client for counsellor routes")
        return None


minio_client = _init_minio_client()


# ---------------------------
# Helper Functions
# ---------------------------
def serialize_row(row):
    """Return a dict of column->value for a SQLAlchemy row."""
    out = {}
    for c in row.__table__.columns.keys():
        val = getattr(row, c)
        # Convert datetime to IST timezone and format
        if isinstance(val, datetime):
            if val.tzinfo:
                val = val.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
            else:
                val = val.strftime("%Y-%m-%d %H:%M:%S")
        out[c] = val
    return out

def _guess_media_type(recording_url: str) -> str:
    media_type, _ = mimetypes.guess_type(recording_url or "")
    return media_type or "audio/mpeg"


def _minio_netloc() -> Optional[str]:
    if not MINIO_ENDPOINT:
        return None
    host, _ = _normalize_endpoint(MINIO_ENDPOINT)
    return host.lower().rstrip("/")


def _is_minio_recording(recording_url: Optional[str]) -> bool:
    if not (recording_url and MINIO_ENDPOINT):
        return False
    parsed = urlparse(recording_url)
    netloc = parsed.netloc.lower().rstrip("/")
    minio_host = _minio_netloc()
    return bool(minio_host and netloc == minio_host)


def _extract_minio_object_name(recording_url: str) -> Optional[str]:
    parsed = urlparse(recording_url)
    path = parsed.path.lstrip("/")
    if not path:
        return None
    if path.startswith(f"{CONTAINER_NAME}/"):
        return path[len(CONTAINER_NAME) + 1 :]
    return path


def _stream_minio_object(minio_obj):
    try:
        for chunk in minio_obj.stream(64 * 1024):
            yield chunk
    finally:
        minio_obj.close()
        minio_obj.release_conn()


def _make_inline_disposition(filename: str) -> str:
    safe_name = filename or "recording.mp3"
    return f'inline; filename="{safe_name}"'


async def _proxy_remote_recording(recording_url: str) -> Response:
    if not recording_url:
        raise HTTPException(status_code=404, detail="Recording not available")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                recording_url,
                follow_redirects=True,
            )
            resp.raise_for_status()
            media_type = resp.headers.get("content-type") or _guess_media_type(recording_url)
            filename = recording_url.rstrip("/").split("/")[-1]
            return Response(
                content=resp.content,
                media_type=media_type,
                headers={"Content-Disposition": _make_inline_disposition(filename)},
            )
    except httpx.HTTPStatusError as exc:
        logger.exception("Remote recording fetch failed: %s", exc)
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Unable to fetch recording",
        )
    except Exception:
        logger.exception("Unexpected error while fetching remote recording")
        raise HTTPException(status_code=502, detail="Unable to fetch recording")


# ---------------------------
# DASHBOARD STATISTICS
# ---------------------------
@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics for counsellors:
    - Total targets/students monitored
    - Flagged targets count
    - Total calls made
    - Emotion distribution
    - Call status distribution
    - Department distribution
    """
    try:
        # Total targets
        total_targets = db.query(func.count(Targets.Target_Id)).scalar() or 0
        
        # Flagged targets count
        flagged_count = db.query(func.count(FlaggedTargets.Flag_Id)).scalar() or 0
        
        # Total calls
        total_calls = db.query(func.count(Calls.Call_Id)).scalar() or 0
        
        # Emotion distribution (from calls with emotions)
        emotion_dist = db.query(
            Emotions.Emotion,
            func.count(Calls.Call_Id).label('count')
        ).join(
            Calls, Emotions.Emotion_Id == Calls.Emotion_Id
        ).group_by(Emotions.Emotion).all()
        
        # Call status distribution
        status_dist = db.query(
            Calls.Status,
            func.count(Calls.Call_Id).label('count')
        ).group_by(Calls.Status).all()
        
        # Targets by department
        dept_dist = db.query(
            Targets.Department_Name,
            func.count(Targets.Target_Id).label('count')
        ).group_by(Targets.Department_Name).all()
        
        return {
            "total_targets": total_targets,
            "flagged_count": flagged_count,
            "total_calls": total_calls,
            "emotion_distribution": [{"emotion": e, "count": c} for e, c in emotion_dist],
            "status_distribution": [{"status": s, "count": c} for s, c in status_dist],
            "department_distribution": [{"department": d, "count": c} for d, c in dept_dist]
        }
    except Exception as e:
        logger.exception("Error fetching dashboard stats")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# TARGET LIST WITH FILTERS
# ---------------------------
@router.get("/targets")
def get_targets_with_filters(
    department: Optional[str] = Query(None),
    emotion: Optional[str] = Query(None),
    call_status: Optional[str] = Query(None),
    flagged: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get list of targets with filters and their latest call information.
    """
    try:
        # Subquery to get the latest call for each target
        latest_call_subq = db.query(
            Calls.Target_Id,
            func.max(Calls.Started_Time).label('max_started')
        ).group_by(Calls.Target_Id).subquery()
        
        # Base query with joins
        query = db.query(
            Targets.Target_Id,
            Targets.Name,
            Targets.Roll_No,
            Targets.Phone_No,
            Targets.Department_Name,
            Targets.Program,
            Calls.Status.label("latest_status"),
            Calls.Started_Time.label("last_call_time"),
            Emotions.Emotion.label("latest_emotion"),
            FlaggedTargets.Flag_Id.label("is_flagged")
        ).outerjoin(
            latest_call_subq,
            Targets.Target_Id == latest_call_subq.c.Target_Id
        ).outerjoin(
            Calls,
            (Calls.Target_Id == Targets.Target_Id) & 
            (Calls.Started_Time == latest_call_subq.c.max_started)
        ).outerjoin(
            Emotions, Calls.Emotion_Id == Emotions.Emotion_Id
        ).outerjoin(
            FlaggedTargets, Targets.Target_Id == FlaggedTargets.Target_Id
        )
        
        # Apply filters
        if department and department.lower() != "all":
            query = query.filter(Targets.Department_Name == department)
        if emotion and emotion.lower() != "all":
            query = query.filter(Emotions.Emotion == emotion)
        if call_status and call_status.lower() != "all":
            query = query.filter(Calls.Status == call_status)
        if flagged is not None:
            if flagged:
                query = query.filter(FlaggedTargets.Flag_Id.isnot(None))
            else:
                query = query.filter(FlaggedTargets.Flag_Id.is_(None))
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Targets.Name.ilike(search_filter)) |
                (Targets.Phone_No.ilike(search_filter))
            )
        
        results = query.all()
        
        targets_data = [
            {
                "Target_Id": str(r.Target_Id),
                "Name": r.Name,
                "Roll_No": r.Roll_No,
                "Phone_No": r.Phone_No,
                "Department_Name": r.Department_Name,
                "Program": r.Program,
                "Latest_Status": r.latest_status,
                "Last_Call_Time": r.last_call_time.astimezone(IST).strftime("%Y-%m-%d %H:%M") if r.last_call_time else "N/A",
                "Latest_Emotion": r.latest_emotion,
                "Is_Flagged": r.is_flagged is not None
            }
            for r in results
        ]
        
        return targets_data
    except Exception as e:
        logger.exception("Error fetching targets with filters")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# FLAGGED TARGETS
# ---------------------------
@router.get("/flagged-targets")
def get_flagged_targets(db: Session = Depends(get_db)):
    """
    Get all flagged targets with their details.
    """
    try:
        # Subquery: latest call per target with Emotion_Id = E003
        latest_call_sq = (
            db.query(
                Calls.Target_Id.label("Target_Id"),
                func.max(Calls.Scheduled_Time).label("max_time"),
            )
            .filter(Calls.Emotion_Id == "E003")
            .group_by(Calls.Target_Id)
            .subquery()
        )

        flagged = db.query(
            FlaggedTargets.Flag_Id,
            FlaggedTargets.Call_Scheduled_DateTime,
            Targets.Target_Id,
            Targets.Name,
            Targets.Roll_No,
            Targets.Phone_No,
            Targets.Department_Name,
            Targets.Program,
            Calls.Analysis_Score,
        ).join(
            Targets, FlaggedTargets.Target_Id == Targets.Target_Id
        ).outerjoin(
            latest_call_sq, latest_call_sq.c.Target_Id == Targets.Target_Id
        ).outerjoin(
            Calls,
            (Calls.Target_Id == Targets.Target_Id) &
            (Calls.Scheduled_Time == latest_call_sq.c.max_time) &
            (Calls.Emotion_Id == "E003")
        ).order_by(desc(FlaggedTargets.Call_Scheduled_DateTime)).all()
        
        flagged_data = [
            {
                "Flag_Id": str(f.Flag_Id),
                "Target_Id": str(f.Target_Id),
                "Name": f.Name,
                "Roll_No": f.Roll_No,
                "Phone_No": f.Phone_No,
                "Department_Name": f.Department_Name,
                "Program": f.Program,
                "Call_Scheduled_DateTime": f.Call_Scheduled_DateTime.astimezone(IST).strftime("%Y-%m-%d %H:%M") if f.Call_Scheduled_DateTime else None,
                "Analysis_Score": f.Analysis_Score,
            }
            for f in flagged
        ]
        
        return flagged_data
    except Exception as e:
        logger.exception("Error fetching flagged targets")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# POTENTIAL CASES EXPORT (Calls + Targets)
# ---------------------------
@router.get("/potential-cases/export")
def export_potential_cases(
    range: str = Query(
        "7d",
        description="Time window to export. Allowed: 24h, 7d, 30d, all.",
        regex="^(24h|7d|30d|all)$",
    ),
    db: Session = Depends(get_db),
):
    """Export potential cases (high analysis) from Calls + Targets, not from flagged table.

    Returns JSON rows; frontend converts to XLSX.
    Fields: Name, Roll_No, Phone_No, Department_Name, Program, Call_Made_DateTime.
    Use range='all' to export all data without any time filter.
    """
    try:
        # Use scheduled time only per requirement
        call_time_expr = Calls.Scheduled_Time.label("call_time")

        query = (
            db.query(
                Targets.Name,
                Targets.Roll_No,
                Targets.Phone_No,
                Targets.Department_Name,
                Targets.Program,
                call_time_expr,
                Calls.Analysis_Score,
            )
            .join(Calls, Calls.Target_Id == Targets.Target_Id)
            .filter(Calls.Emotion_Id == "E003")
            .order_by(desc(call_time_expr))
        )

        if range != "all":
            window_map = {
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
            }
            delta = window_map.get(range, timedelta(days=7))
            now_ist = datetime.now(IST)
            start_time = now_ist - delta
            query = query.filter(call_time_expr >= start_time)

        rows = []
        for row in query.all():
            call_time = row.call_time
            if isinstance(call_time, datetime):
                if call_time.tzinfo:
                    call_time = call_time.astimezone(IST)
                else:
                    call_time = call_time.replace(tzinfo=IST)
                call_time_str = call_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                call_time_str = None

            rows.append(
                {
                    "Name": row.Name,
                    "Roll_No": row.Roll_No,
                    "Phone_No": row.Phone_No,
                    "Department_Name": row.Department_Name,
                    "Program": row.Program,
                    "Call_Made_DateTime": call_time_str,
                    "Analysis_Score": row.Analysis_Score,
                }
            )

        return rows
    except Exception as e:
        logger.exception("Error exporting potential cases")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# LIVE CALL FEED
# ---------------------------
@router.get("/live-calls")
def get_live_calls(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Return the latest call activity with emotion and recording info."""
    try:
        recent_calls = db.query(
            Calls.Call_Id,
            Calls.Started_Time,
            Calls.Status,
            Calls.Recording_Url,
            Targets.Name.label("target_name"),
            Targets.Phone_No.label("target_phone"),
            Emotions.Emotion.label("emotion")
        ).outerjoin(
            Targets, Calls.Target_Id == Targets.Target_Id
        ).outerjoin(
            Emotions, Calls.Emotion_Id == Emotions.Emotion_Id
        ).order_by(desc(Calls.Started_Time)).limit(limit).all()

        feed = []
        for row in recent_calls:
            feed.append({
                "call_id": str(row.Call_Id),
                "target_name": row.target_name,
                "target_phone": row.target_phone,
                "started_time": row.Started_Time.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S") if row.Started_Time else None,
                "status": row.Status,
                "emotion": row.emotion,
                "recording_url": row.Recording_Url,
                "recording_proxy_url": f"/api/counsellor/recordings/{row.Call_Id}" if row.Recording_Url else None,
            })
        return feed
    except Exception as e:
        logger.exception("Error fetching live calls")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recordings/{call_id}")
async def stream_call_recording(call_id: str, db: Session = Depends(get_db)):
    """Stream a call recording from MinIO or Twilio."""
    try:
        call_uuid = uuid.UUID(call_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid call_id format")

    call = db.query(Calls).filter(Calls.Call_Id == call_uuid).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    recording_url = call.Recording_Url
    if not recording_url:
        raise HTTPException(status_code=404, detail="Recording not available")

    if _is_minio_recording(recording_url):
        if not minio_client:
            raise HTTPException(status_code=503, detail="Recording storage unavailable")
        object_name = _extract_minio_object_name(recording_url)
        if not object_name:
            raise HTTPException(status_code=404, detail="Recording not available")
        try:
            minio_obj = minio_client.get_object(CONTAINER_NAME, object_name)
        except S3Error as exc:
            logger.exception("Failed to fetch recording %s from MinIO: %s", object_name, exc)
            raise HTTPException(status_code=502, detail="Unable to fetch recording")

        media_type = minio_obj.headers.get("Content-Type") or _guess_media_type(recording_url)
        filename = object_name.split("/")[-1]
        return StreamingResponse(
            _stream_minio_object(minio_obj),
            media_type=media_type,
            headers={"Content-Disposition": _make_inline_disposition(filename)},
        )

    # Default to server-side proxy fetch for any non-MinIO URL.
    return await _proxy_remote_recording(recording_url)


@router.get("/recordings/by-sid/{call_sid}")
async def stream_call_recording_by_sid(call_sid: str):
    """Stream a call recording from MinIO using CallSid-based filenames ({CallSid}.mp3)."""
    if not minio_client:
        raise HTTPException(status_code=503, detail="Recording storage unavailable")

    object_name = f"{call_sid}.mp3"
    try:
        minio_obj = minio_client.get_object(CONTAINER_NAME, object_name)
    except S3Error as exc:
        logger.exception("Failed to fetch recording %s from MinIO: %s", object_name, exc)
        raise HTTPException(status_code=404, detail="Recording not found")

    media_type = minio_obj.headers.get("Content-Type") or _guess_media_type(object_name)
    filename = object_name.split("/")[-1]
    return StreamingResponse(
        _stream_minio_object(minio_obj),
        media_type=media_type,
        headers={"Content-Disposition": _make_inline_disposition(filename)},
    )


# ---------------------------
# TARGET DETAILS & HISTORY
# ---------------------------
@router.get("/target/{target_id}")
def get_target_details(target_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific target including call history.
    """
    try:
        # Get target
        target = db.query(Targets).filter(Targets.Target_Id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        
        # Get call history with emotion details
        calls = db.query(
                Calls.Call_Id,
                Calls.Call_Sid,
                Calls.Scheduled_Time,
                Calls.Started_Time,
                Calls.Status,
                Calls.Duration,
                Calls.Recording_Url,
                Calls.Analysis_Score,
                Emotions.Emotion,
                Emotions.Emotion_Id
            ).outerjoin(
                Emotions, Calls.Emotion_Id == Emotions.Emotion_Id
            ).filter(
                Calls.Target_Id == target_id
            ).order_by(desc(Calls.Started_Time)).all()
        
        # Check if flagged
        flagged_info = db.query(FlaggedTargets).filter(
            FlaggedTargets.Target_Id == target_id
        ).first()
        
        call_history = [
            {
                "Call_Id": str(c.Call_Id),
                "Call_Sid": c.Call_Sid,
                "Scheduled_Time": c.Scheduled_Time.astimezone(IST).strftime("%d-%m-%Y %H:%M:%S.%f")[:-4] if c.Scheduled_Time else None,
                "Started_Time": c.Started_Time.astimezone(IST).strftime("%d-%m-%Y %H:%M:%S.%f")[:-4] if c.Started_Time else None,
                "Status": c.Status,
                "Duration": c.Duration,
                "Attempts": 0,
                "Recording_Url": c.Recording_Url,
                "Recording_Proxy_Url": (
                    f"/api/counsellor/recordings/by-sid/{c.Call_Sid}" if c.Call_Sid else (
                        f"/api/counsellor/recordings/{c.Call_Id}" if c.Recording_Url else None
                    )
                ),
                "Emotion": c.Emotion,
                "Emotion_Id": c.Emotion_Id,
                "Analysis_Score": c.Analysis_Score,
            }
            for c in calls
        ]
        
        return {
            "Target_Id": str(target.Target_Id),
            "Name": target.Name,
            "Phone_No": target.Phone_No,
            "Department_Name": target.Department_Name,
            "Program": target.Program,
            "Is_Flagged": flagged_info is not None,
            "Call_Scheduled_DateTime": flagged_info.Call_Scheduled_DateTime.astimezone(IST).strftime("%Y-%m-%d %H:%M") if flagged_info else None,
            "Total_Calls": len(call_history),
            "Call_History": call_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching target details for {target_id}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# FILTER OPTIONS
# ---------------------------
@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    """
    Get available options for filters.
    """
    try:
        departments = db.query(Targets.Department_Name).distinct().order_by(Targets.Department_Name).all()
        emotions = db.query(Emotions.Emotion).distinct().order_by(Emotions.Emotion).all()
        statuses = db.query(Calls.Status).distinct().all()

        return {
            "departments": [d[0] for d in departments if d[0]],
            "emotions": [e[0] for e in emotions if e[0]],
            "statuses": [s[0] for s in statuses if s[0]],
        }
    except Exception as e:
        logger.exception("Error fetching filter options")
        raise HTTPException(status_code=500, detail=str(e))
