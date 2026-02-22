# main_exotel.py - FastAPI server with PostgreSQL and Exotel Streaming Integration
from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
import httpx
import requests
import json
import base64
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import uuid
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
import io
from pydub import AudioSegment
import pytz
import os
from app.config import (
    APP_HOST, CONTAINER_NAME,
    MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_ENDPOINT,
    EXOTEL_SID, EXOTEL_API_KEY, EXOTEL_API_TOKEN, JWT_SECRET_KEY,
    EXOTEL_PHONE_NUMBER, MODEL_ID, EXOTEL_WEBHOOK_TOKEN, MIN_RECORDING_DURATION_SECONDS
)
from app.sql_db import get_db
from app.models import Targets, Calls, Emotions, Models, Admins, ErrorLogs, IST
from app.celery_config_exotel import (
    initiate_calls_for_all_targets,
    process_recording_emotion,
)
from app import schemas


# def _extract_call_id_from_custom_field(raw_value: Optional[Any]) -> Optional[str]:
#     """Best-effort extraction of call_id from Exotel CustomField payloads."""
#     if raw_value is None:
#         return None

#     candidate_data: Optional[Dict[str, Any]] = None

#     # Bytes -> str
#     if isinstance(raw_value, (bytes, bytearray)):
#         raw_value = raw_value.decode("utf-8", errors="ignore")

#     # If the payload is already a dict, use it directly
#     if isinstance(raw_value, dict):
#         candidate_data = raw_value
#     elif isinstance(raw_value, str):
#         stripped = raw_value.strip()
#         if not stripped:
#             return None

#         # If it looks like JSON, try parsing
#         if stripped.startswith("{") or stripped.startswith("["):
#             try:
#                 candidate_data = json.loads(stripped)
#             except (TypeError, json.JSONDecodeError):
#                 return stripped
#         else:
#             # Plain string (e.g., UUID) - return as-is
#             return stripped
#     else:
#         # Fallback to string representation
#         return str(raw_value).strip() or None

#     if not isinstance(candidate_data, dict):
#         return None

#     return (  
#         candidate_data.get("CustomField")
#     )


# def _get_call_record_by_call_id(db: Session, call_id_str: Optional[str]) -> Optional[Calls]:
#     if not call_id_str:
#         return None
#     try:
#         call_uuid = uuid.UUID(str(call_id_str))
#     except (ValueError, AttributeError, TypeError):
#         logger.warning(f"----> Invalid call_id provided in CustomField: {call_id_str} <----")
#         return None
#     return db.query(Calls).filter(Calls.Call_Id == call_uuid).first()


def _get_call_record_by_call_sid(db: Session, call_sid: Optional[str]) -> Optional[Calls]:
    if not call_sid:
        return None
    return db.query(Calls).filter(Calls.Call_Sid == str(call_sid)).first()


def _map_exotel_status(exotel_status: Optional[str], duration_seconds: Optional[int]) -> Optional[str]:
    """Map Exotel statuses to internal enum-safe values."""
    if not exotel_status:
        return None

    status_norm = str(exotel_status).strip().lower()

    if status_norm == "completed":
        # If call connected, consider message conveyed; very short calls remain conveyed to avoid enum errors
        if duration_seconds is not None and duration_seconds < int(MIN_RECORDING_DURATION_SECONDS):
            return "Message Not Conveyed"
        return "Message Conveyed But Not Processed"

    if status_norm in {"busy", "no-answer", "failed", "canceled", "timeout"}:
        return "Message Not Conveyed"

    # Unknown statuses are ignored to keep enum integrity
    return None



# --- IMPORT API ROUTERS ---
from app.api.frontend_routes import router as frontend_router
from app.api.auth_routes import router as auth_router
from app.api.database_routes import router as admin_router
from app.api.call_monitoring_routes import router as monitor_router
from app.api.target_monitoring_routes import router as target_monitor_router
from app.api.counsellor_routes import router as counsellor_router
from app.api.ml_routes import router as ml_router

# Exotel API base URL
EXOTEL_BASE_URL = f"https://api.exotel.com/v1/Accounts/{EXOTEL_SID}/"


# Configure logging to always print to terminal (stdout)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not root_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
logger = root_logger

# FastAPI app
app = FastAPI(title="MHealth")

origins = [
    "http://localhost:5173",  # Vite dev server
    os.getenv("FRONTEND_URL", "http://localhost:3000"),  # Production frontend
    "http://10.0.62.206:3000",  # Server IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],      # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],      # Authorization, Content-Type, etc.
)

# ============================================================================
# HEALTH CHECK ENDPOINT (for Docker health checks)
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint for Docker container monitoring"""
    return {
        "status": "healthy",
        "service": "mhealth-backend",
        "timestamp": datetime.utcnow().isoformat()
    }

# --- REGISTER API ROUTERS ---
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(monitor_router)
app.include_router(frontend_router)
app.include_router(target_monitor_router)
app.include_router(counsellor_router)
app.include_router(ml_router)

# MinIO connection setup for storing recordings
try: 
    minio_client = Minio(
        MINIO_ENDPOINT, 
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False  # Use secure=True if using HTTPS
    )
    # Ensure the bucket exists
    if not minio_client.bucket_exists(CONTAINER_NAME):
        minio_client.make_bucket(CONTAINER_NAME)
        logger.info(f"Created '{CONTAINER_NAME}' bucket in MinIO")
    else:
        logger.info(f"'{CONTAINER_NAME}' bucket already exists")
except S3Error as e: 
    logger.exception(f"MinIO client error: {e}")
    minio_client = None 

# JWT authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ============================================================================
# CONFIGURATION CHECK ENDPOINT
# ============================================================================

@app.get("/config-check")
def check_config():
    """Check if configuration is set up correctly for Exotel"""
    return {
        "app_host": APP_HOST,
        "exotel_sid": EXOTEL_SID if EXOTEL_SID else "NOT SET",
        "exotel_phone": EXOTEL_PHONE_NUMBER,
        "minio_endpoint": MINIO_ENDPOINT,
        "minio_bucket": CONTAINER_NAME,
        "minio_connected": minio_client is not None,
        "webhook_urls": {
            # "voice": f"https://{APP_HOST}/voice?token={EXOTEL_WEBHOOK_TOKEN[:8]}...",
            # "call_status": f"https://{APP_HOST}/call_status?token={EXOTEL_WEBHOOK_TOKEN[:8]}...",
            # "stream": f"wss://{APP_HOST}/stream",
            # "recording": f"https://{APP_HOST}/recording_callback?token={EXOTEL_WEBHOOK_TOKEN[:8]}...",
            "passthru": f"https://{APP_HOST}/passthru?token={EXOTEL_WEBHOOK_TOKEN[:8]}..."
        },
        # "recording_setup": {
        #     "status": "enabled",
        #     "note": "Recordings will be downloaded from Exotel and stored in MinIO",
        #     "callback_url": f"https://{APP_HOST}/recording_callback?token={EXOTEL_WEBHOOK_TOKEN[:8]}...",
        #     "storage": "MinIO" if minio_client else "NOT CONFIGURED"
        # },
        # "message": "Ensure these URLs are configured in your Exotel dashboard and flow"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MHealth System is operational", "status": "operational"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return current user"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def validate_exotel_request(request: Request, form_data: dict) -> bool:
    """
    Exotel webhook validation with token-based authentication
    
    For production:
    1. Set EXOTEL_WEBHOOK_TOKEN in .env to a strong random string
    2. Add ?token=YOUR_TOKEN to all Exotel webhook URLs in dashboard
    3. For additional security, also implement IP whitelisting
    
    Example URL: https://your-domain.com/passthru?token=your-secret-token
    """
    # Get token from query params
    token = request.query_params.get("token")
    
    # Validate token
    if not token or token != EXOTEL_WEBHOOK_TOKEN:
        logger.error(f"Invalid webhook token. Expected token, got: {token}")
        return False
    
    return True



# # Recording callback
# @app.post("/recording_callback")
# async def recording_callback(request: Request, db: Session = Depends(get_db)):
#     """
#     Recording callback from Exotel
#     Called when a recording is available after the call
#     """
#     correlation_id = str(uuid.uuid4())
#     logger.info(f"----> Processing /recording_callback, CorrelationID={correlation_id} <----")

#     # Check for token in query params first (skip validation)
#     token = request.query_params.get("token")
#     if token == EXOTEL_WEBHOOK_TOKEN:
#         logger.info(f"----> Valid token provided, skipping signature validation, CorrelationID={correlation_id} <----")
#     else:
#         try:
#             form_data = await request.form()
#             if not validate_exotel_request(request, form_data):
#                 logger.error(f"----> Invalid Exotel signature, CorrelationID={correlation_id} <----")
#                 raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
#         except Exception as e:
#             logger.error(f"----> Validation or form data error: {str(e)}, CorrelationID={correlation_id} <----")
#             return {}

#     # Get form data
#     form_data = await request.form()
    
#     call_sid = form_data.get("CallSid")
#     recording_url = form_data.get("RecordingUrl")
#     user_phone = form_data.get("From")
#     custom_field_raw = (
#         form_data.get("CustomField")
#         or form_data.get("custom_field")
#         or form_data.get("customField")
#         or form_data.get("CustomField1")
#         or form_data.get("custom_field1")
#         or form_data.get("customField1")
#     )
#     call_id_from_custom = _extract_call_id_from_custom_field(custom_field_raw)
    
#     # Log all received data for debugging
#     logger.info(f"----> Recording callback data: CallSid={call_sid}, RecordingUrl={recording_url}, From={user_phone}, CorrelationID={correlation_id} <----")
#     logger.info(f"----> All form data: {dict(form_data)}, CorrelationID={correlation_id} <----")

#     if not call_sid or not recording_url:
#         logger.error(f"----> Missing CallSid or RecordingUrl, CorrelationID={correlation_id} <----")
#         return {"status": "error", "message": "Missing required fields"}

#     if not call_id_from_custom:
#         logger.error(
#             f"----> Recording callback missing call_id for CallSid={call_sid}, CorrelationID={correlation_id} <----"
#         )
#         return {"status": "error", "message": "Missing call_id"}

#     call_record = _get_call_record_by_call_id(db, call_id_from_custom)
#     if not call_record:
#         logger.error(
#             f"----> Recording callback could not find call for CallId={call_id_from_custom}, CorrelationID={correlation_id} <----"
#         )
#         return {"status": "error", "message": "Call record not found"}

#     try:
#         # Download recording from Exotel
#         logger.info(f"----> Downloading recording from: {recording_url}, CorrelationID={correlation_id} <----")
        
#         async with httpx.AsyncClient(timeout=60.0) as client:
#             recording_response = await client.get(
#                 recording_url,
#                 auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN),  # Exotel requires auth for recording download
#                 follow_redirects=True
#             )
#             recording_response.raise_for_status()
#             recording_data = recording_response.content
        
#         logger.info(f"----> Downloaded recording: {len(recording_data)} bytes, CorrelationID={correlation_id} <----")
#         file_name = f"{call_sid}.mp3"

#         # Upload to MinIO
#         if not minio_client:
#             logger.error(f"----> MinIO client not available, CorrelationID={correlation_id} <----")
#             return {"status": "error", "message": "Storage unavailable"}

#         minio_client.put_object(
#             CONTAINER_NAME,
#             file_name,
#             io.BytesIO(recording_data),
#             len(recording_data),
#             content_type="audio/mpeg"
#         )
#         storage_url = f"http://{MINIO_ENDPOINT}/{CONTAINER_NAME}/{file_name}"
#         logger.info(f"----> Recording saved to MinIO: {storage_url} <----")

#         # Update database strictly via call_id
#         call_record.Recording_Url = storage_url
#         if call_record.Status in ["In Progress", "Ringing", None]:
#             call_record.Status = "Message Conveyed But Not Processed"
#         db.commit()
#         logger.info(
#             f"----> Updated recording URL for CallId={call_id_from_custom}, Status={call_record.Status}, CorrelationID={correlation_id} <----"
#         )

#     except Exception as e:
#         logger.exception(f"----> FATAL ERROR processing recording {call_sid}, CorrelationID={correlation_id} <-----")
#         db.rollback()
        
#         # Log error to database
#         error_log = ErrorLogs(
#             Error_Type="Recording Processing Error",
#             Error_Message=f"CallSid={call_sid}, Error={str(e)}, CorrelationID={correlation_id}"
#         )
#         db.add(error_log)
#         db.commit()
        
#         raise HTTPException(status_code=500, detail="Internal server error while processing recording.")

#     return {"status": "success", "call_sid": call_sid, "correlation_id": correlation_id}



# ---------------------------------------------------------------------------
# New StatusCallback endpoint for simplified Greeting -> Voicemail -> Passthru -> Hangup flow
# ---------------------------------------------------------------------------


@app.post("/status_callback")
async def status_callback(request: Request, db: Session = Depends(get_db)):
    """
    Exotel StatusCallback handler: updates call status and saves recording if provided.
    This coexists with legacy passthru/voicebot code (kept intact for manual cleanup).
    """
    correlation_id = str(uuid.uuid4())
    form_data = await request.form()

    logger.info(
        "----> /status_callback payload: %s, CorrelationID=%s <----",
        {k: v for k, v in form_data.items()},
        correlation_id,
    )

    if not validate_exotel_request(request, form_data):
        logger.error("Invalid Exotel signature, CorrelationID=%s", correlation_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    call_sid = form_data.get("CallSid") or form_data.get("CallSID")
    exotel_status = form_data.get("Status") or form_data.get("CallStatus")
    recording_url = form_data.get("RecordingUrl") or form_data.get("RecordingURL")
    
    print("---FORM DATA OF STATUS CALLBACK---\n")
    print(form_data)
    print("------------------------------------")

    call_record = _get_call_record_by_call_sid(db, call_sid)

    if not call_record:
        logger.error(
            "StatusCallback could not find call (CallSid=%s, CallId=%s), CorrelationID=%s",
            call_sid,
            correlation_id,
        )
        return {"status": "ignored", "reason": "unknown call"}


    # Only update status for failed, busy, no-answer
    if exotel_status:
        if exotel_status in {"failed", "busy", "no-answer"}:
            call_record.Status = exotel_status
        elif exotel_status == "completed":
            # Do not update here; passthru will handle
            pass
        else:
            logger.warning(
                "Unmapped Exotel status '%s' for CallSid=%s; leaving status unchanged",
                exotel_status,
                call_sid,
            )


    storage_url = None

    # If no recording_url in callback, fallback to Exotel Call Details API
    if not recording_url and call_sid:
        try:
            api_url = f"{EXOTEL_BASE_URL}Calls/{call_sid}.json"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(api_url, auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN))
                resp.raise_for_status()
                call_data = resp.json().get('Call', {})
                recording_url = call_data.get('RecordingUrl') 
                print(resp)
                print(call_data)
        except Exception as exc:
            logger.error("Fallback to Call Details API failed for CallSid=%s, CorrelationID=%s: %s", call_sid, correlation_id, exc)

    db.commit()

    logger.info(
        "StatusCallback processed: CallId=%s, CallSid=%s, Status=%s,  CorrelationID=%s",
        call_record.Call_Id,
        call_record.Call_Sid,
        call_record.Status,
        correlation_id,
    )

    return {
        "status": "ok",
        "call_id": str(call_record.Call_Id),
        "call_sid": call_record.Call_Sid,
        "exotel_status": exotel_status,
        "recording_saved": bool(storage_url),
    }



# Passthru callback - Exotel passthru applet (rewritten for Exotel docs compliance)
@app.get("/passthru")
async def passthru(request: Request):
    """
    Exotel Passthru applet endpoint (GET only).
    Receives call details as query parameters, validates token, logs, stores recording in MinIO if present, and returns 200 OK.
    """
    correlation_id = str(uuid.uuid4())
    params = dict(request.query_params)

    # Validate token (required for security)
    token = params.get("token")
    exotel_token = os.getenv("EXOTEL_WEBHOOK_TOKEN")
    if exotel_token and token != exotel_token:
        logger.warning(f"Invalid token in passthru request, CorrelationID={correlation_id}")
        raise HTTPException(status_code=403, detail="Forbidden")

    # Extract key Exotel params
    call_sid = params.get("CallSid")
    call_from = params.get("CallFrom")
    call_to = params.get("CallTo")
    call_status = params.get("CallStatus")
    direction = params.get("Direction")
    created = params.get("Created")
    start_time = params.get("StartTime")
    end_time = params.get("EndTime")
    recording_url = params.get("RecordingUrl")
    custom_field = params.get("CustomField")

    logger.info(f"[Passthru] CallSid={call_sid}, From={call_from}, To={call_to}, Status={call_status}, RecordingUrl={recording_url}, CustomField={custom_field}, CorrelationID={correlation_id}")
    logger.info(f"[Passthru] Full params: {params}, CorrelationID={correlation_id}")

    storage_url = None
    voicemail_duration = None

    # Update call status for completed calls after voicemail duration extraction
    # (status logic moved to after recording download below)

    # Only download if recording_url is a valid http(s) URL
    if (
        recording_url
        and isinstance(recording_url, str)
        and recording_url.lower().startswith("http")
        and call_sid
    ):
        file_name = f"{call_sid}.mp3"
        # Idempotency: check if file already exists in MinIO
        try:
            if minio_client and minio_client.bucket_exists(CONTAINER_NAME):
                found = minio_client.stat_object(CONTAINER_NAME, file_name)
                storage_url = f"http://{MINIO_ENDPOINT}/{CONTAINER_NAME}/{file_name}"
                logger.info(f"[Passthru] Recording already exists in MinIO: {storage_url}, CorrelationID={correlation_id}")
                return {"status": "ok", "correlation_id": correlation_id, "recording_storage_url": storage_url, "voicemail_duration_seconds": None, "idempotent": True}
        except Exception:
            pass  # Not found, proceed to download
        try:
            logger.info(f"[Passthru] Downloading recording from {recording_url}, CorrelationID={correlation_id}")
            exotel_api_key = os.getenv("EXOTEL_API_KEY")
            exotel_api_token = os.getenv("EXOTEL_API_TOKEN")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    recording_url,
                    auth=(exotel_api_key, exotel_api_token),
                    follow_redirects=True
                )
                response.raise_for_status()
                recording_data = response.content
            # Always save to MinIO first
            import io as _io
            if not minio_client:
                logger.error(f"[Passthru] MinIO client not available, CorrelationID={correlation_id}")
                raise HTTPException(status_code=500, detail="Storage unavailable")
            minio_client.put_object(
                CONTAINER_NAME,
                file_name,
                _io.BytesIO(recording_data),
                len(recording_data),
                content_type="audio/mpeg"
            )
            storage_url = f"http://{MINIO_ENDPOINT}/{CONTAINER_NAME}/{file_name}"
            logger.info(f"[Passthru] Recording saved to MinIO: {storage_url}, CorrelationID={correlation_id}")
            # Now extract duration and update DB/status/trigger emotion
            try:
                audio = AudioSegment.from_file(_io.BytesIO(recording_data), format="mp3")
                voicemail_duration = int(audio.duration_seconds)
                logger.info(f"[Passthru] Actual voicemail duration: {voicemail_duration}s, CorrelationID={correlation_id}")
                try:
                    db2 = next(get_db())
                    call_record2 = None
                    if call_sid:
                        call_record2 = db2.query(Calls).filter(Calls.Call_Sid == call_sid).first()
                    if call_record2:
                        call_record2.Duration = voicemail_duration
                        # Update status based on voicemail duration
                        if voicemail_duration < int(MIN_RECORDING_DURATION_SECONDS):
                            call_record2.Status = "Message Not Conveyed"
                        elif voicemail_duration == int(MIN_RECORDING_DURATION_SECONDS):
                            call_record2.Status = "Message Conveyed But Not Processed"
                            db2.commit()
                            # Trigger emotion processing for this call
                            try:
                                from app.celery_config_exotel import process_recording_emotion
                                process_recording_emotion(str(call_record2.Call_Id))
                                # After successful processing, status will be updated to 'Message Conveyed And Processed' in emotion processing
                            except Exception as emo_e:
                                logger.warning(f"[Passthru] Could not trigger emotion processing: {emo_e}, CorrelationID={correlation_id}")
                        else:
                            db2.commit()
                except Exception as db_e:
                    logger.warning(f"[Passthru] Could not update Duration/Status in DB: {db_e}, CorrelationID={correlation_id}")
                finally:
                    if 'db2' in locals() and db2:
                        db2.close()
            except Exception as dur_e:
                logger.warning(f"[Passthru] Could not determine voicemail duration: {dur_e}, CorrelationID={correlation_id}")
        except Exception as e:
            logger.exception(f"[Passthru] Error saving recording: {e}, CorrelationID={correlation_id}")
            raise HTTPException(status_code=500, detail="Failed to process recording")
    else:
        logger.info(f"[Passthru] No valid recording URL to download, CorrelationID={correlation_id}")

    return {"status": "ok", "correlation_id": correlation_id, "recording_storage_url": storage_url, "voicemail_duration_seconds": voicemail_duration}

# Schedule calls
@app.post("/schedule_calls")
async def schedule_calls(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Schedule calls for all targets
    Triggers Celery Beat to initiate calls
    """
    correlation_id = str(uuid.uuid4())
    logger.info(f"----> Scheduling calls by {current_user}, CorrelationID={correlation_id} <----")
    
    try:
        # Get all targets
        targets = db.query(Targets)
        
        target_count = len(targets)
        
        if target_count == 0:
            logger.warning(f"----> No targets found in database, CorrelationID={correlation_id} <----")
            raise HTTPException(status_code=400, detail="No targets found in database")
        
        # Trigger Celery task to initiate calls
        initiate_calls_for_all_targets.delay()
        
        logger.info(f"----> Scheduled calls for {target_count} targets, CorrelationID={correlation_id} <----")
        return {
            "message": f"Scheduled calls for {target_count} targets",
            "correlation_id": correlation_id,
            "target_count": target_count
        }
    
    except Exception as e:
        logger.error(f"----> Error scheduling calls: {str(e)}, CorrelationID={correlation_id} <----")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Token endpoint for admin authentication
@app.post("/token")
async def login_for_access_token(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Login endpoint for admin users
    Returns JWT token for authentication
    """
    correlation_id = str(uuid.uuid4())
    logger.info(f"----> Login attempt for {username}, CorrelationID={correlation_id} <----")
    
    # Query admin user
    admin = db.query(Admins).filter(Admins.Email == username).first()
    
    if not admin:
        logger.error(f"----> Admin not found: {username}, CorrelationID={correlation_id} <----")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password (in production, use proper password hashing like bcrypt)
    # For now, assuming passwords are hashed in the database
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    if not pwd_context.verify(password, admin.Password):
        logger.error(f"----> Invalid password for {username}, CorrelationID={correlation_id} <----")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token_data = {
        "sub": username,
        "admin_id": str(admin.Admin_Id),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")
    
    logger.info(f"----> Token generated for {username}, CorrelationID={correlation_id} <----")
    return {
        "access_token": token,
        "token_type": "bearer",
        "correlation_id": correlation_id
    }


# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        # Check MinIO connection
        minio_status = "connected" if minio_client and minio_client.bucket_exists(CONTAINER_NAME) else "disconnected"
        
        return {
            "status": "healthy",
            "database": "connected",
            "minio": minio_status,
            "timestamp": datetime.now(IST).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(IST).isoformat()
        }



# Debug endpoint to manually fetch recording for a call
@app.post("/debug/fetch-recording/{call_sid}")
async def debug_fetch_recording(call_sid: str, db: Session = Depends(get_db)):
    """Manually fetch recording for a specific CallSid from Exotel"""
    correlation_id = str(uuid.uuid4())
    logger.info(f"----> Manual recording fetch for CallSid={call_sid}, CorrelationID={correlation_id} <----")
    
    try:
        # Get call details from Exotel API
        api_url = f"{EXOTEL_BASE_URL}Calls/{call_sid}.json"
        
        logger.info(f"----> Fetching call details from: {api_url} <----")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                api_url,
                auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN)
            )
            response.raise_for_status()
            call_data = response.json()
        
        logger.info(f"----> Call data: {json.dumps(call_data, indent=2)} <----")
        
        # Extract recording URL from call data
        call_info = call_data.get('Call', {})
        recording_url = call_info.get('RecordingUrl')
        
        if not recording_url:
            return {
                "status": "no_recording",
                "message": "No recording URL found in Exotel call data",
                "call_data": call_data,
                "correlation_id": correlation_id
            }
        
        logger.info(f"----> Found recording URL: {recording_url} <----")
        
        # Download recording
        async with httpx.AsyncClient(timeout=60.0) as client:
            recording_response = await client.get(
                recording_url,
                auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN),
                follow_redirects=True
            )
            recording_response.raise_for_status()
            recording_data = recording_response.content
        
        logger.info(f"----> Downloaded recording: {len(recording_data)} bytes <----")
        
        # Save to MinIO
        if minio_client:
            file_name = f"{call_sid}.mp3"
            minio_client.put_object(
                CONTAINER_NAME,
                file_name,
                io.BytesIO(recording_data),
                len(recording_data),
                content_type="audio/mpeg"
            )
            storage_url = f"http://{MINIO_ENDPOINT}/{CONTAINER_NAME}/{file_name}"
            logger.info(f"----> Recording saved to MinIO: {storage_url} <----")
            
            # Update database
            call_record = db.query(Calls).filter(Calls.Call_Sid == call_sid).first()
            if call_record:
                call_record.Recording_Url = storage_url
                if call_record.Status in ["In Progress", "Ringing", None]:
                    call_record.Status = "Message Conveyed But Not Processed"
                db.commit()
                logger.info(f"----> Updated database for CallSid={call_sid} <----")
            
            return {
                "status": "success",
                "message": "Recording fetched and stored successfully",
                "recording_url": recording_url,
                "storage_url": storage_url,
                "size_bytes": len(recording_data),
                "correlation_id": correlation_id
            }
        else:
            return {
                "status": "error",
                "message": "MinIO client not available",
                "correlation_id": correlation_id
            }
    
    except Exception as e:
        logger.exception(f"----> Error fetching recording: {e}, CorrelationID={correlation_id} <----")
        raise HTTPException(status_code=500, detail=str(e))


