from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, extract, case
from datetime import datetime, timedelta
import pytz

from app.sql_db import get_db
from app.models import Calls, FlaggedTargets, Targets

# ✅ Use your requested router name and prefix
router = APIRouter(prefix="/api/target_monitoring", tags=["Target Monitoring"])

# Indian timezone
IST = pytz.timezone("Asia/Kolkata")

# 🧠 1️⃣ Function to check and flag target automatically
def auto_flag_targets(db: Session):
    """
    Checks last 3 consecutive calls per target.
    If all have Emotion E001 (negative), flag the target.
    """
    try:
        target_ids = db.query(Calls.Target_Id).distinct().all()

        for (target_id,) in target_ids:
            recent_calls = (
                db.query(Calls)
                .filter(Calls.Target_Id == target_id)
                .order_by(desc(Calls.Started_Time))
                .limit(3)
                .all()
            )

            if len(recent_calls) == 3:
                if all(getattr(c, "Emotion_Id", None) == "E001" for c in recent_calls):
                    existing = (
                        db.query(FlaggedTargets)
                        .filter(FlaggedTargets.Target_Id == target_id)
                        .first()
                    )
                    if not existing:
                        new_flag = FlaggedTargets(
                            Target_Id=target_id,
                            Call_Scheduled_DateTime=datetime.now(IST)
                        )
                        db.add(new_flag)
                        db.commit()
                        db.refresh(new_flag)
        return {"message": "Auto-flagging completed successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error in flagging: {str(e)}")


# 🔁 2️⃣ Manual trigger endpoint (can be run via Celery too)
@router.post("/check_and_flag")
def trigger_flagging(db: Session = Depends(get_db)):
    return auto_flag_targets(db)


# 📋 3️⃣ Get all flagged targets (joined with Target details)
@router.get("/flagged_targets")
def get_flagged_targets(db: Session = Depends(get_db)):
    try:
        # Auto-run flagging before returning data
        auto_flag_targets(db)

        flagged = (
            db.query(
                FlaggedTargets.Flag_Id,
                FlaggedTargets.Call_Scheduled_DateTime,
                Targets.Target_Id,
                Targets.Name,
                Targets.Batch,
                Targets.Department_Name,
                Targets.Phone_No,
            )
            .join(Targets, Targets.Target_Id == FlaggedTargets.Target_Id)
            .all()
        )

        data = [
            {
                "Flag_Id": f.Flag_Id,
                "Target_Id": f.Target_Id,
                "Name": f.Name,
                "Batch": f.Batch,
                "Department_Name": f.Department_Name,
                "Phone_No": f.Phone_No,
                "Call_Scheduled_DateTime": f.Call_Scheduled_DateTime.astimezone(IST).strftime("%Y-%m-%d %H:%M"),
            }
            for f in flagged
        ]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📊 4️⃣ Summary Stats for top section
@router.get("/stats")
def get_flagged_stats(db: Session = Depends(get_db)):
    try:
        total_screened = db.query(Targets).count()
        total_flagged = db.query(FlaggedTargets).count()

        recent_24h = datetime.now(IST) - timedelta(hours=24)
        new_flagged_24h = (
            db.query(FlaggedTargets)
            .filter(FlaggedTargets.Call_Scheduled_DateTime >= recent_24h)
            .count()
        )

        return {
            "total_screened": total_screened,
            "total_flagged": total_flagged,
            "new_flagged_24h": new_flagged_24h,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 📈 5️⃣ Emotion trend data 
@router.get("/trends")
def get_emotion_trends(
    db: Session = Depends(get_db),
    range_days: int = Query(None, description="Number of days (7 or 30)"),
    month: int = Query(None, ge=1, le=12),
    year: int = Query(None, ge=2000)
):
    """Return % negative (E001) calls grouped by date."""
    try:
        neg_id = "E001"
        now = datetime.now(IST);
        # ✅ Default to current month/year if not provided
        if not month:
            month = now.month
        if not year:
            year = now.year

        query = db.query(
            func.date(Calls.Started_Time).label("date"),
            func.sum(case((Calls.Emotion_Id == neg_id, 1), else_=0)).label("neg_count"),
            func.count(Calls.Call_Id).label("total_count"),
        )
        query = db.query(
            func.date(Calls.Started_Time).label("date"),
            func.sum(case((Calls.Emotion_Id == neg_id, 1), else_=0)).label("neg_count"),
            func.count(Calls.Call_Id).label("total_count"),
        )

        # Apply filters
        if range_days:
            start = datetime.now(IST) - timedelta(days=range_days)
            query = query.filter(Calls.Started_Time >= start)
        if month:
            query = query.filter(extract("month", Calls.Started_Time) == month)
        if year:
            query = query.filter(extract("year", Calls.Started_Time) == year)

        results = (
            query.group_by(func.date(Calls.Started_Time))
            .order_by(func.date(Calls.Started_Time))
            .all()
        )
        trends = [
            {
                "date": str(r.date),
                "negative_percentage": round((r.neg_count / r.total_count * 100), 2)
                if r.total_count else 0,
            }
            for r in results
        ]
        # ✅ Add metadata (month, year, label)
        month_name = datetime(1900, month, 1).strftime("%B")
        response = {
            "month": month,
            "month_name": month_name,
            "year": year,
            "range_days": range_days or None,
            "data": trends,
        }

        print(f"📊 Trends Response: {response}")
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

# 🧹 6️⃣ Unflag a target manually
@router.delete("/unflag/{target_id}")
def unflag_target(target_id: str, db: Session = Depends(get_db)):
    try:
        flag_entry = (
            db.query(FlaggedTargets)
            .filter(FlaggedTargets.Target_Id == target_id)
            .first()
        )
        if not flag_entry:
            raise HTTPException(status_code=404, detail="Target not flagged.")
        db.delete(flag_entry)
        db.commit()
        return {"message": f"Target {target_id} unflagged successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    

