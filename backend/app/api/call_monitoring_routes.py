from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.sql_db import get_db
from app.models import Calls, Targets
from sqlalchemy import func

router = APIRouter(prefix="/api/monitor", tags=["Call Monitoring"])

# 1️⃣ --- Dashboard Summary Metrics ---
@router.get("/stats")
def get_call_stats(db: Session = Depends(get_db)):
    """Aggregate counts for dashboard cards"""
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        stats = {
            "scheduled_overall": db.query(Calls).count(),
            "scheduled_today": db.query(Calls).filter(Calls.Scheduled_Time >= today_start).count(),
            "awaiting_overall": db.query(Calls).filter(Calls.Status == "Awaiting Schedule").count(),
            "awaiting_today": db.query(Calls).filter(
                Calls.Status == "Awaiting Schedule",
                Calls.Scheduled_Time >= today_start
            ).count(),
            "not_conveyed_overall": db.query(Calls).filter(Calls.Status == "Message Not Conveyed").count(),
            "processed_not_conveyed": db.query(Calls).filter(Calls.Status == "Message Conveyed But Not Processed").count(),
            "processed_overall": db.query(Calls).filter(Calls.Status == "Message Conveyed And Processed").count(),
            "failed_overall": db.query(Calls).filter(Calls.Status == "Message Conveyed And Processing Failed").count(),
        }
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# 2️⃣ --- Filtered Call History ---
@router.get("/calls")
def get_filtered_calls(
    db: Session = Depends(get_db),
    batch: str = Query(None),
    department: str = Query(None),
    status: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    """Return filtered calls with optional filters."""
    try:
        query = db.query(Calls, Targets).join(Targets, Calls.Target_Id == Targets.Target_Id)

        if batch and batch.lower() != "all":
            query = query.filter(Targets.Batch == int(batch))
        if department and department.lower() != "all":
            query = query.filter(Targets.Department_Name == department)
        if status and status.lower() != "all":
            query = query.filter(Calls.Status == status)
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Calls.Scheduled_Time >= start)
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Calls.Scheduled_Time < end)

        results = query.all()

        call_data = [
            {
                "Call_Id": call.Call_Id,
                "Target_Name": target.Name,
                "Batch": target.Batch,
                "Department_Name": target.Department_Name,
                "Status": call.Status,
                "Retries_Count": call.Retries_Count,
                "Scheduled_Time": call.Scheduled_Time,
                "Started_Time": call.Started_Time,
                "End_Time": call.End_Time,
                "Duration": call.Duration,
                "Recording_Url": call.Recording_Url
            }
            for call, target in results
        ]

        return call_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching calls: {str(e)}")


# 3️⃣ --- Export as CSV ---
@router.get("/export_csv")
def export_calls_csv(db: Session = Depends(get_db)):
    """Export all calls to CSV format for bulk export."""
    import io, csv
    calls = db.query(Calls).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Call_Id", "Target_Id", "Status", "Retries_Count", "Scheduled_Time", "Started_Time", "End_Time", "Duration", "Recording_Url"])
    for call in calls:
        writer.writerow([
            call.Call_Id, call.Target_Id, call.Status, call.Retries_Count,
            call.Scheduled_Time, call.Started_Time, call.End_Time, call.Duration, call.Recording_Url
        ])
    output.seek(0)
    return {"csv_data": output.getvalue()}
