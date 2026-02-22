# app/api/database_routes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Any, Dict, List, Type
from sqlalchemy.orm import Session
import csv, io, logging

from app.sql_db import get_db
from app import models

router = APIRouter(prefix="/api", tags=["database"])
logger = logging.getLogger(__name__)


# ---------------------------
# Helpers
# ---------------------------
def serialize_row(row):
    """Return a dict of column->value for a SQLAlchemy row (exclude _sa_instance_state)."""
    out = {}
    for c in row.__table__.columns.keys():
        out[c] = getattr(row, c)
    return out


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

def fetch_all_records(db: Session, model: Type) -> List[Dict[str, Any]]:
    try:
        rows = db.query(model).all()
        return [serialize_row(r) for r in rows]
    except Exception as e:
        logger.exception(f"Error fetching {model.__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def commit_or_500(db: Session):
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("DB commit failed")
        raise HTTPException(status_code=500, detail=str(e))

def apply_patch(db: Session, model: Type, id_field: str, id_value: Any, changes: Dict[str, Any]):
    """
    Case-insensitive partial update. changes is a dict of field:value.
    """
    record = db.query(model).filter(getattr(model, id_field) == id_value).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")

    logger.info(f"PATCH {model.__name__}({id_value}) payload: {changes}")

    updated = False
    cols = list(record.__table__.columns.keys())
    for k, v in changes.items():
        # match column case-insensitively
        for col in cols:
            if k.lower() == col.lower():
                old = getattr(record, col)
                try:
                    setattr(record, col, v)
                except Exception:
                    # try simple type coercion for common types (int)
                    try:
                        col_type = type(old)
                        setattr(record, col, col_type(v))
                    except Exception:
                        setattr(record, col, v)
                logger.info(f"Updated {model.__name__}.{col}: {old} -> {getattr(record, col)}")
                updated = True
                break

    if not updated:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    commit_or_500(db)
    db.refresh(record)
    return serialize_row(record)

def delete_record(db: Session, model: Type, id_field: str, id_value: Any):
    record = db.query(model).filter(getattr(model, id_field) == id_value).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    try:
        db.delete(record)
        commit_or_500(db)
        return {"message": f"{model.__name__} deleted"}
    except Exception as e:
        logger.exception("Delete failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# TARGETS
# ---------------------------
@router.get("/targets")
def list_targets(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.Targets)

@router.post("/targets", status_code=status.HTTP_201_CREATED)
def create_target(payload: Dict[str, Any], db: Session = Depends(get_db)):
    # Accepts arbitrary dict; will set attributes that exist on model
    t = models.Targets()
    for k, v in payload.items():
        # case-insensitive set of columns
        for col in t.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(t, col, v)
                break
    db.add(t)
    commit_or_500(db)
    db.refresh(t)
    return serialize_row(t)

@router.get("/targets/{target_id}")
def get_target(target_id: str, db: Session = Depends(get_db)):
    rec = db.query(models.Targets).filter(models.Targets.Target_Id == target_id).first()
    if not rec:
        raise HTTPException(404, "Target not found")
    return serialize_row(rec)

@router.patch("/targets/{target_id}")
def patch_target(target_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    return apply_patch(db, models.Targets, "Target_Id", target_id, changes)

@router.delete("/targets/{target_id}")
def remove_target(target_id: str, db: Session = Depends(get_db)):
    return delete_record(db, models.Targets, "Target_Id", target_id)

@router.post("/targets/import")
def import_targets(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts CSV with header like: Name,Roll_No,Phone_No,Department_Name,Program
    """
    try:
        content = file.file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)
        created, skipped = 0, 0

        for row in reader:
            roll_no = _clean_str(row.get("Roll_No", ""))
            phone_no = _clean_str(row.get("Phone_No", ""))
            name = _clean_str(row.get("Name", ""))
            if not roll_no or not phone_no or not name:
                continue  # skip invalid rows

            existing = db.query(models.Targets).filter(
                (models.Targets.Roll_No == roll_no) | (models.Targets.Phone_No == phone_no)
            ).first()
            if existing:
                skipped += 1
                continue  # skip duplicates

            t = models.Targets()
            for k, v in row.items():
                for col in t.__table__.columns.keys():
                    if k.strip().lower() == col.lower():
                        value = v.strip() if isinstance(v, str) and v.strip() else None
                        setattr(t, col, value)
                        break
            db.add(t)
            created += 1
        commit_or_500(db)
        print(f"skipped {skipped} targets while importing ")
        return {"message": f"Imported {created} new targets, skipped {skipped} duplicates"}

    except Exception as e:
        logger.exception("Import failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/targets/bulk")
def bulk_import_targets(payload: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Accept JSON list of targets (from UI upload) and insert non-duplicate rows."""
    if not payload:
        raise HTTPException(status_code=400, detail="No target data provided")

    created, duplicates, skipped = 0, 0, 0

    try:
        for row in payload:
            if not isinstance(row, dict):
                skipped += 1
                continue

            roll_no = _clean_str(row.get("Roll_No"))
            phone_no = _clean_str(row.get("Phone_No"))
            name = _clean_str(row.get("Name"))
            if not roll_no or not phone_no or not name:
                skipped += 1
                continue

            existing = db.query(models.Targets).filter(
                (models.Targets.Roll_No == roll_no) | (models.Targets.Phone_No == phone_no)
            ).first()
            if existing:
                duplicates += 1
                continue

            target = models.Targets()
            for k, v in row.items():
                for col in target.__table__.columns.keys():
                    if k.lower() == col.lower():
                        value = None
                        if isinstance(v, str):
                            value = v.strip() or None
                        else:
                            value = v
                        setattr(target, col, value)
                        break

            if not target.Name or not target.Phone_No:
                skipped += 1
                continue

            db.add(target)
            created += 1

        commit_or_500(db)
        return {
            "inserted": created,
            "duplicates": duplicates,
            "skipped": skipped
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Bulk import failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# MODELS
# ---------------------------
@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.Models)

@router.post("/models", status_code=status.HTTP_201_CREATED)
def create_model(payload: Dict[str, Any], db: Session = Depends(get_db)):
    m = models.Models()
    for k, v in payload.items():
        for col in m.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(m, col, v)
                break
    db.add(m)
    commit_or_500(db)
    db.refresh(m)
    return serialize_row(m)

@router.patch("/models/{model_id}")
def patch_model(model_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    return apply_patch(db, models.Models, "Model_Id", model_id, changes)

@router.delete("/models/{model_id}")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    return delete_record(db, models.Models, "Model_Id", model_id)


# ---------------------------
# EMOTIONS
# ---------------------------
@router.get("/emotions")
def list_emotions(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.Emotions)

@router.post("/emotions", status_code=status.HTTP_201_CREATED)
def create_emotion(payload: Dict[str, Any], db: Session = Depends(get_db)):
    e = models.Emotions()
    for k, v in payload.items():
        for col in e.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(e, col, v)
                break
    db.add(e)
    commit_or_500(db)
    db.refresh(e)
    return serialize_row(e)

@router.patch("/emotions/{emotion_id}")
def patch_emotion(emotion_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    return apply_patch(db, models.Emotions, "Emotion_Id", emotion_id, changes)

@router.delete("/emotions/{emotion_id}")
def delete_emotion(emotion_id: str, db: Session = Depends(get_db)):
    return delete_record(db, models.Emotions, "Emotion_Id", emotion_id)


# ---------------------------
# ADMINS
# ---------------------------
@router.get("/admins")
def list_admins(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.Admins)

@router.post("/admins", status_code=status.HTTP_201_CREATED)
def create_admin(payload: Dict[str, Any], db: Session = Depends(get_db)):
    a = models.Admins()
    for k, v in payload.items():
        for col in a.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(a, col, v)
                break
    db.add(a)
    commit_or_500(db)
    db.refresh(a)
    return serialize_row(a)

@router.patch("/admins/{admin_id}")
def patch_admin(admin_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    return apply_patch(db, models.Admins, "Admin_Id", admin_id, changes)

@router.delete("/admins/{admin_id}")
def delete_admin(admin_id: str, db: Session = Depends(get_db)):
    return delete_record(db, models.Admins, "Admin_Id", admin_id)


# ---------------------------
# ERROR LOGS
# ---------------------------
@router.get("/error_logs")
def list_error_logs(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.ErrorLogs)

@router.post("/error_logs", status_code=status.HTTP_201_CREATED)
def create_error_log(payload: Dict[str, Any], db: Session = Depends(get_db)):
    e = models.ErrorLogs()
    for k, v in payload.items():
        for col in e.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(e, col, v)
                break
    db.add(e)
    commit_or_500(db)
    db.refresh(e)
    return serialize_row(e)

@router.delete("/error_logs/{log_id}")
def delete_error_log(log_id: str, db: Session = Depends(get_db)):
    # Note: model primary key is Logs_Id in your models.py
    return delete_record(db, models.ErrorLogs, "Logs_Id", log_id)



# ---------------------------
# CALLS
# ---------------------------
@router.get("/calls")
def list_calls(db: Session = Depends(get_db)):
    return fetch_all_records(db, models.Calls)

@router.get("/calls/{call_id}")
def get_call(call_id: str, db: Session = Depends(get_db)):
    rec = db.query(models.Calls).filter(models.Calls.Call_Id == call_id).first()
    if not rec:
        raise HTTPException(404, "Call not found")
    return serialize_row(rec)

@router.post("/calls", status_code=status.HTTP_201_CREATED)
def create_call(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Create a new Call record.
    Payload should include: Target_Id, Model_Id, Scheduled_Time, Status, etc.
    """
    c = models.Calls()
    for k, v in payload.items():
        for col in c.__table__.columns.keys():
            if k.lower() == col.lower():
                setattr(c, col, v)
                break
    db.add(c)
    commit_or_500(db)
    db.refresh(c)
    return serialize_row(c)

@router.patch("/calls/{call_id}")
def patch_call(call_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    return apply_patch(db, models.Calls, "Call_Id", call_id, changes)

@router.delete("/calls/{call_id}")
def delete_call(call_id: str, db: Session = Depends(get_db)):
    return delete_record(db, models.Calls, "Call_Id", call_id)

# ---------------------------
# FLAGGED TARGETS
# ---------------------------
@router.get("/flagged_targets")
def list_flagged_targets(db: Session = Depends(get_db)):
    """Return all flagged targets."""
    return fetch_all_records(db, models.FlaggedTargets)


@router.post("/flagged_targets", status_code=status.HTTP_201_CREATED)
def create_flagged_target(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Create a new flagged target record.
    Payload must include 'Target_Id'.
    """
    try:
        target_id = payload.get("Target_Id")
        if not target_id:
            raise HTTPException(status_code=400, detail="Target_Id is required.")

        # Check if already flagged
        existing = db.query(models.FlaggedTargets).filter(models.FlaggedTargets.Target_Id == target_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Target already flagged.")

        # Create record
        f = models.FlaggedTargets()
        for k, v in payload.items():
            for col in f.__table__.columns.keys():
                if k.lower() == col.lower():
                    setattr(f, col, v)
                    break
        db.add(f)
        commit_or_500(db)
        db.refresh(f)
        return serialize_row(f)
    except Exception as e:
        db.rollback()
        logger.exception("Create FlaggedTarget failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/flagged_targets/{flag_id}")
def patch_flagged_target(flag_id: str, changes: Dict[str, Any], db: Session = Depends(get_db)):
    """Partial update (PATCH) for flagged target record."""
    return apply_patch(db, models.FlaggedTargets, "Flag_Id", flag_id, changes)


@router.delete("/flagged_targets/{flag_id}")
def delete_flagged_target(flag_id: str, db: Session = Depends(get_db)):
    """Delete a flagged target (unflag)."""
    return delete_record(db, models.FlaggedTargets, "Flag_Id", flag_id)



# ---------------------------
# SCHEDULE TRIGGER
# ---------------------------
@router.post("/schedule_calls")
def schedule_calls_trigger():
    try:
        from app.celery_config_exotel import initiate_calls_for_all_targets
        initiate_calls_for_all_targets.delay()
        return {"message": "Scheduled call initiation task"}
    except Exception as e:
        logger.exception("Failed to trigger schedule")
        raise HTTPException(status_code=500, detail=str(e))
