"""celery_config_twilio.py - Celery tasks for the Twilio voice call flow service.

Tasks
─────
• initiate_twilio_call_task     – Places an outbound call via Twilio API.
• initiate_calls_for_all_targets – Periodic Celery Beat task: calls all eligible
                                   targets that haven't been called this week.
• archive_call_recordings_task  – Coordinator task that fans out one archival task
                                   per voice response in a call.
• archive_response_recording_task – Archives a single Twilio response recording
                                    to MinIO (idempotent).
• analyze_call_depression_risk_task – Combines all call responses into single audio
                                       and analyzes for depression risk via ML service.
"""
from __future__ import annotations

import io
import json
import logging
import re
import subprocess
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import librosa
import numpy as np
import requests
from celery import Celery
from celery.exceptions import Retry
from celery.schedules import crontab
from sqlalchemy import and_

from app.config import (
    APP_HOST,
    RABBITMQ_URL,
    RETRY_DELAY_MINUTES,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
)
from app.models import Targets, TwilioCalls, TwilioResponses
from app.ml_client import get_client as get_ml_client
from app.sql_db import get_db_session_cm
from app.storage import archive_twilio_recording

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [twilio_celery]: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------
celery_app = Celery(
    "twilio_tasks",
    broker=RABBITMQ_URL,
    backend="rpc://",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_default_delivery_mode="transient",
    timezone="Asia/Kolkata",
    enable_utc=False,
    beat_schedule={
        # Runs every Wednesday at 10:00 AM IST — adjust as needed
        # "twilio-weekly-calls": {
        #     "task": "app.celery_config_twilio.initiate_calls_for_all_targets",
        #     "schedule": crontab(day_of_week="wednesday", hour=10, minute=0),
        # },
    },
)

# ---------------------------------------------------------------------------
# Phone number normalisation (E.164 for Twilio)
# ---------------------------------------------------------------------------

def _normalize_e164(phone: str) -> str:
    """Convert a raw phone string to E.164 format expected by Twilio."""
    if not phone:
        return ""
    phone = str(phone).strip().replace(" ", "")
    phone = re.sub(r"(?!^\+)\D", "", phone)
    if phone.startswith("+"):
        return phone
    phone = phone.lstrip("0")
    if len(phone) == 10:
        return "+91" + phone
    if len(phone) == 12 and phone.startswith("91"):
        return "+" + phone
    if len(phone) == 11 and phone.startswith("1"):
        return "+" + phone
    return phone


# ---------------------------------------------------------------------------
# Task: Initiate a single outbound call
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, max_retries=3, name="app.celery_config_twilio.initiate_twilio_call_task")
def initiate_twilio_call_task(self, target_id: str, phone_number: str, call_id: str):
    """
    Place an outbound call to *phone_number* via the Twilio REST API.

    Args:
        target_id:    UUID string of the target (for logging).
        phone_number: Raw phone number string (will be normalised to E.164).
        call_id:      UUID string of the TwilioCalls record.
    """
    logger.info(
        "Initiating Twilio call: Target=%s, CallID=%s", target_id, call_id
    )

    to_number = _normalize_e164(phone_number)
    from_number = _normalize_e164(TWILIO_PHONE_NUMBER)

    # The webhook URL Twilio will call when the callee answers
    base_url = f"https://{APP_HOST}"
    answer_url = f"{base_url}/voice/answer"
    status_url = f"{base_url}/voice/status"

    with get_db_session_cm() as db:
        call_record = db.query(TwilioCalls).filter(
            TwilioCalls.Call_Id == call_id
        ).first()

        if not call_record:
            logger.error("Call record not found in DB: %s", call_id)
            return

        try:
            from twilio.rest import Client

            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            twilio_call = client.calls.create(
                to=to_number,
                from_=from_number,
                url=answer_url,
                method="POST",
                status_callback=status_url,
                status_callback_method="POST",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                timeout=30,  # seconds to wait for callee to pick up
                time_limit=600,  # max call duration in seconds (10 min)
            )

            call_record.Twilio_Call_Sid = twilio_call.sid
            call_record.Status = "Call Initiated"
            call_record.Started_Time = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                "Twilio call placed: Target=%s, CallSid=%s",
                target_id,
                twilio_call.sid,
            )

        except Exception as exc:
            logger.error(
                "Error initiating Twilio call for Target=%s: %s", target_id, exc
            )
            call_record.Status = "Failed"
            db.commit()
            raise self.retry(exc=exc, countdown=RETRY_DELAY_MINUTES * 60)



# ---------------------------------------------------------------------------
# Task: MinIO archival (fan-out)
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=1,
    name="app.celery_config_twilio.archive_call_recordings_task",
)
def archive_call_recordings_task(self, call_id: str):
    """Fan out one archival job per voice response for a call."""
    logger.info("Archive fan-out task started for call_id=%s", call_id)
    try:
        with get_db_session_cm() as db:
            # Convert string to UUID
            try:
                call_uuid = uuid.UUID(call_id)
            except (ValueError, TypeError):
                logger.error("Invalid call_id format: %s", call_id)
                return
            
            call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_uuid).first()
            if not call:
                logger.warning("Call not found for archival fan-out: CallID=%s", call_id)
                return

            responses = (
                db.query(TwilioResponses)
                .filter(
                    TwilioResponses.Call_Id == call_uuid,
                    TwilioResponses.Response_Type == "record",
                )
                .all()
            )
            logger.info("Found %d voice responses for archival in call %s", len(responses), call_id)

            for resp in responses:
                logger.info(
                    "Queueing archival for ResponseID=%s from call %s",
                    resp.Response_Id,
                    call_id,
                )
                archive_response_recording_task.delay(
                    call_id=call_id,
                    response_id=str(resp.Response_Id),
                )

        logger.info(
            "Queued archival fan-out for CallID=%s (%d responses)",
            call_id,
            len(responses),
        )
    except Exception as exc:
        logger.error("Error in archive fan-out for call %s: %s", call_id, exc, exc_info=True)
        raise self.retry(exc=exc, countdown=30)


# ---------------------------------------------------------------------------
# Helper: Extract actual audio duration from file
# ---------------------------------------------------------------------------

def _extract_audio_duration(file_path: str) -> Optional[int]:
    """
    Extract actual audio duration from a file using ffprobe.
    Returns duration in seconds (rounded), or None if extraction fails.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:novalue=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            duration_float = float(result.stdout.strip())
            return int(round(duration_float))
        else:
            logger.warning(
                "ffprobe failed or returned no output for file: %s", file_path
            )
            return None
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timeout for file: %s", file_path)
        return None
    except Exception as exc:
        logger.warning("Error extracting duration from %s: %s", file_path, exc)
        return None


def _update_total_response_duration(call_id, db):
    """Calculate and update Total_Response_Duration by summing all response durations."""
    # Handle both string and UUID types
    if isinstance(call_id, str):
        try:
            call_uuid = uuid.UUID(call_id)
        except (ValueError, TypeError):
            logger.error("Invalid call_id format for duration update: %s", call_id)
            return
    else:
        call_uuid = call_id
    
    responses = db.query(TwilioResponses).filter(TwilioResponses.Call_Id == call_uuid).all()
    
    duration_sum = sum(
        (r.Recording_Duration or 0) for r in responses
        if r.Recording_Duration is not None
    )
    
    call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_uuid).first()
    if call:
        call.Total_Response_Duration = duration_sum
        db.commit()
        logger.info(
            "Updated Total_Response_Duration for call %s: %d seconds from %d responses",
            call_id, duration_sum, len(responses)
        )


# ---------------------------------------------------------------------------
# Task: Archive a single response recording
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=2,
    name="app.celery_config_twilio.archive_response_recording_task",
)
def archive_response_recording_task(self, call_id: str, response_id: str):
    """Archive one Twilio recording to MinIO and extract actual duration."""
    logger.info("Archive response task started: CallID=%s, ResponseID=%s", call_id, response_id)
    try:
        with get_db_session_cm() as db:
            # Convert string IDs to UUIDs
            try:
                call_uuid = uuid.UUID(call_id)
                response_uuid = uuid.UUID(response_id)
            except (ValueError, TypeError) as e:
                logger.error("Invalid UUID format: call_id=%s, response_id=%s, error=%s", call_id, response_id, e)
                return
            
            resp_record = (
                db.query(TwilioResponses)
                .filter(TwilioResponses.Response_Id == response_uuid)
                .first()
            )
            if not resp_record:
                logger.warning("Response not found for archival: ResponseID=%s", response_id)
                return

            if resp_record.Response_Type != "record":
                logger.info("Response is not a voice recording: ResponseID=%s, Type=%s", response_id, resp_record.Response_Type)
                return

            if resp_record.MinIORecordingUrl:
                logger.info("Recording already archived: ResponseID=%s", response_id)
                return

            recording_url = resp_record.TwilioRecordingUrl
            if not recording_url:
                logger.warning("No Twilio URL for archival: ResponseID=%s", response_id)
                return

            call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_uuid).first()
            
            # Download recording to temp file and extract actual duration
            actual_duration: Optional[int] = None
            try:
                logger.info("Downloading recording from: %s", recording_url)
                resp = requests.get(recording_url, timeout=30)
                resp.raise_for_status()
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp.flush()
                    
                    # Extract actual duration using ffprobe
                    actual_duration = _extract_audio_duration(tmp.name)
                    if actual_duration:
                        logger.info(
                            "Extracted actual duration for ResponseID=%s: %d seconds "
                            "(Twilio reported: %s seconds)",
                            response_id,
                            actual_duration,
                            resp_record.Recording_Duration,
                        )
                        # Update Recording_Duration with actual value
                        resp_record.Recording_Duration = actual_duration
            except Exception as exc:
                logger.warning(
                    "Failed to extract actual duration for ResponseID=%s: %s",
                    response_id,
                    exc,
                )
                # Continue with archival even if duration extraction fails
            
            archived_url = archive_twilio_recording(
                recording_url=recording_url,
                call_sid=(call.Twilio_Call_Sid if call else call_id),
                question_index=resp_record.Question_Index,
                recording_sid=resp_record.Recording_Sid,
                response_id=response_id,
            )
            if not archived_url:
                # Do not fail the pipeline if MinIO is unavailable/full.
                # We can still use Twilio-authenticated URLs for downstream analysis.
                logger.warning(
                    "MinIO archival unavailable for ResponseID=%s. Keeping Twilio URL as fallback.",
                    response_id,
                )
                _update_total_response_duration(call_id, db)
                return

            resp_record.MinIORecordingUrl = archived_url
            db.commit()
            
            # Recalculate total response duration with updated actual durations
            _update_total_response_duration(call_id, db)
            
            logger.info("Recording archived to MinIO for ResponseID=%s", response_id)

    except Exception as exc:
        logger.warning("Archival failed for ResponseID=%s: %s", response_id, exc)
        raise self.retry(exc=exc, countdown=30)


# ---------------------------------------------------------------------------
# Task: Depression risk analysis by combining all call responses
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.celery_config_twilio.analyze_call_depression_risk_task",
)
def analyze_call_depression_risk_task(self, call_id: str):
    """
    Combine all voice responses from a call into a single audio file and
    analyze for depression risk via ML service.
    
    Args:
        call_id: UUID string of the TwilioCalls record
    """
    logger.info("Depression risk analysis task started for call_id=%s", call_id)
    
    try:
        with get_db_session_cm() as db:
            # Convert string to UUID
            try:
                call_uuid = uuid.UUID(call_id)
            except (ValueError, TypeError):
                logger.error("Invalid call_id format for depression analysis: %s", call_id)
                return
            
            call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_uuid).first()
            if not call:
                logger.warning("Call not found for depression analysis: CallID=%s", call_id)
                return
            
            # Query all voice responses for this call, ordered by question index
            responses = (
                db.query(TwilioResponses)
                .filter(
                    TwilioResponses.Call_Id == call_uuid,
                    TwilioResponses.Response_Type == "record",
                )
                .order_by(TwilioResponses.Question_Index)
                .all()
            )
            
            if not responses:
                logger.warning(
                    "No voice responses found for depression analysis: CallID=%s", call_id
                )
                return
            
            logger.info(
                "Found %d voice responses for depression analysis in call %s",
                len(responses),
                call_id,
            )
            
            # Download and concatenate all audio files
            # Use MinIO URLs primarily (archived recordings), fall back to Twilio only if needed
            audio_arrays = []
            sample_rate = None
            
            # MinIO may be unavailable (e.g., storage full). Continue with best available URLs.
            logger.info(
                "Recording source availability for call %s: MinIO=%d/%d, Twilio=%d/%d",
                call_id,
                sum(1 for r in responses if r.MinIORecordingUrl),
                len(responses),
                sum(1 for r in responses if r.TwilioRecordingUrl),
                len(responses),
            )
            
            for resp in responses:
                candidate_urls = []
                if resp.MinIORecordingUrl:
                    candidate_urls.append(resp.MinIORecordingUrl)
                if resp.TwilioRecordingUrl:
                    twilio_base = resp.TwilioRecordingUrl.rstrip("/")
                    candidate_urls.extend([twilio_base, f"{twilio_base}.mp3", f"{twilio_base}.wav"])

                if not candidate_urls:
                    logger.warning(
                        "No recording URL for ResponseID=%s, skipping",
                        resp.Response_Id,
                    )
                    continue

                audio_loaded = False
                for recording_url in candidate_urls:
                    try:
                        logger.info(
                            "Downloading audio for ResponseID=%s from %s",
                            resp.Response_Id,
                            recording_url[:50] + "..." if len(recording_url) > 50 else recording_url,
                        )

                        auth = None
                        if "api.twilio.com" in recording_url:
                            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

                        resp_audio = requests.get(recording_url, timeout=30, auth=auth)
                        resp_audio.raise_for_status()

                        # Load audio with librosa (auto-detects format)
                        audio_data, sr = librosa.load(
                            io.BytesIO(resp_audio.content),
                            sr=None,
                            mono=True,
                        )

                        # Ensure consistent sample rate across all responses
                        if sample_rate is None:
                            sample_rate = sr
                            logger.info("Set sample rate to %d Hz from first response", sample_rate)

                        if sr != sample_rate:
                            logger.info(
                                "Resampling audio for ResponseID=%s from %d Hz to %d Hz",
                                resp.Response_Id,
                                sr,
                                sample_rate,
                            )
                            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=sample_rate)

                        audio_arrays.append(audio_data)
                        logger.info(
                            "Loaded audio for ResponseID=%s: %.2f seconds",
                            resp.Response_Id,
                            len(audio_data) / sample_rate,
                        )
                        audio_loaded = True
                        break
                    except Exception as exc:
                        logger.warning(
                            "Failed to load audio for ResponseID=%s from %s: %s",
                            resp.Response_Id,
                            recording_url,
                            exc,
                        )

                if not audio_loaded:
                    logger.warning(
                        "Could not load audio from any URL for ResponseID=%s",
                        resp.Response_Id,
                    )
            
            if not audio_arrays:
                logger.error(
                    "Failed to load any audio files for depression analysis: CallID=%s",
                    call_id,
                )
                raise self.retry(exc=RuntimeError("No audio could be loaded"), countdown=20)
            
            # Concatenate all audio arrays
            try:
                combined_audio = np.concatenate(audio_arrays)
                logger.info(
                    "Concatenated %d audio responses: %.2f seconds total",
                    len(audio_arrays),
                    len(combined_audio) / sample_rate,
                )
            except Exception as exc:
                logger.error(
                    "Failed to concatenate audio arrays for depression analysis: %s", exc
                )
                return
            
            # Convert combined audio to wav bytes for ML service
            try:
                # Write to BytesIO buffer as wav using soundfile (if available) or scipy
                audio_buffer = io.BytesIO()
                try:
                    # Try soundfile first (usually comes with librosa)
                    import soundfile as sf
                    sf.write(audio_buffer, combined_audio, sample_rate, format='WAV')
                except (ImportError, AttributeError):
                    # Fallback to scipy
                    import scipy.io.wavfile as wavfile
                    wavfile.write(audio_buffer, sample_rate, (combined_audio * 32767).astype(np.int16))
                
                audio_bytes = audio_buffer.getvalue()
                logger.info(
                    "Encoded combined audio to WAV: %d bytes",
                    len(audio_bytes),
                )
            except Exception as exc:
                logger.error(
                    "Failed to encode combined audio for ML service: %s", exc
                )
                return
            
            # Send combined audio to ML service for depression prediction
            try:
                ml_client = get_ml_client()
                prediction_result = ml_client.predict_depression_from_bytes(
                    audio_bytes=audio_bytes,
                    threshold=0.5,
                )
                
                if prediction_result is None:
                    logger.warning(
                        "ML service unavailable or returned None for depression prediction: CallID=%s. Retrying in 30 seconds.",
                        call_id,
                    )
                    raise self.retry(
                        exc=RuntimeError("Depression prediction failed: ML service unavailable"),
                        countdown=30,
                    )
                
                required_keys = {
                    "depression_risk",
                    "risk_probability",
                    "risk_level",
                    "confidence",
                }
                missing_keys = [k for k in required_keys if k not in prediction_result]
                if missing_keys:
                    raise ValueError(
                        f"Invalid ML response shape. Missing required keys: {missing_keys}. "
                        f"Received keys: {list(prediction_result.keys())}"
                    )

                depression_risk = prediction_result["depression_risk"]
                risk_probability = prediction_result["risk_probability"]
                risk_level = prediction_result["risk_level"]
                confidence = prediction_result["confidence"]

                logger.info(
                    "Depression prediction result: CallID=%s, Risk=%d, Probability=%.4f, Level=%s, Confidence=%.4f",
                    call_id,
                    depression_risk,
                    risk_probability,
                    risk_level,
                    confidence,
                )
                
                # Update call record with depression prediction results
                call.Depression_Risk = depression_risk
                call.Depression_Risk_Probability = risk_probability
                call.Depression_Risk_Level = risk_level
                call.Depression_Risk_Confidence = confidence
                call.Depression_Analysis_Timestamp = datetime.now(timezone.utc)
                db.commit()
                
                logger.info(
                    "✓ Depression risk analysis completed and stored for CallID=%s: Risk=%d, Probability=%.4f",
                    call_id,
                    call.Depression_Risk,
                    call.Depression_Risk_Probability,
                )
                
            except Exception as exc:
                logger.error(
                    "ML service call failed for depression analysis: CallID=%s, Error=%s",
                    call_id,
                    exc,
                )
                raise self.retry(exc=exc, countdown=30)
                
    except Retry:
        raise
    except Exception as exc:
        logger.error(
            "Error in depression risk analysis task for call %s: %s",
            call_id,
            exc,
            exc_info=True,
        )
        raise self.retry(exc=exc, countdown=30)
