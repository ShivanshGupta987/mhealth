# celery_config_exotel.py - Celery configuration with PostgreSQL and Exotel API
import logging
import json
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from celery import Celery
import requests
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import pytz
import numpy as np
import librosa
from joblib import dump, load
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from app.config import (
    EXOTEL_SID, EXOTEL_API_KEY, EXOTEL_API_TOKEN, EXOTEL_PHONE_NUMBER,
    APP_HOST, RABBITMQ_URL, MODEL_ID, RETRY_DELAY_MINUTES, MAX_RETRIES,
    MIN_RECORDING_DURATION_SECONDS, EXOTEL_WEBHOOK_TOKEN, EXOTEL_APP_ID
)
from app.sql_db import SessionLocal, get_db_session_cm
from app.models import Targets, Calls, Emotions, Models, FlaggedTargets, ErrorLogs, IST, CALL_STATUS_ENUM
from celery.schedules import crontab

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Celery configuration with RabbitMQ
celery_app = Celery(
    "tasks",
    broker=RABBITMQ_URL,
    backend="rpc://"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_default_delivery_mode='transient',
    timezone="Asia/Kolkata",
    enable_utc=False,
    beat_schedule={
        'weekly-calls' : {
            'task' : 'app.celery_config_exotel.initiate_calls_for_all_targets',
            # 'schedule': crontab(day_of_week='wednesday', hour=9, minute=0)
            'schedule': crontab(minute='*/5'),
        },
        # 'daily-calls': {
        #     'task': 'app.celery_config_exotel.initiate_calls_for_all_targets',
        #     'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM IST
        # },
        # 'retry-failed-calls': {
        #     'task': 'app.celery_config_exotel.retry_failed_calls',
        #     'schedule': crontab(minute='*/30'),  # Check every 30 minutes
        # }
    }
)

# Exotel API base URL
EXOTEL_BASE_URL = f"https://api.exotel.com/v1/Accounts/{EXOTEL_SID}/"

# Log configuration on startup (without sensitive data)
logger.info(f"Celery Config Loaded - Exotel_SID: {EXOTEL_SID}, EXOTEL_APP_ID: {EXOTEL_APP_ID},  EXOTEL_BASE_URL: {EXOTEL_BASE_URL}")
logger.info(f"APP_HOST: {APP_HOST}, EXOTEL_PHONE: {EXOTEL_PHONE_NUMBER}")

# Utility: normalize phone to digits, return last 10 digits for matching
def _normalize_last10(phone: str) -> str:
    if not phone:
        return ""
    # keep digits only
    digits = "".join([c for c in str(phone) if c.isdigit()])
    return digits[-10:]


EMOTION_LABELS = ["NEGATIVE", "POSITIVE", "NEUTRAL"]
EMOTION_MODEL_PATH = Path(__file__).resolve().parent / "emotion_model.joblib"
EMOTION_EXECUTOR = ThreadPoolExecutor(max_workers=50)


class EmotionModelService:
    """Lazy loader for an sklearn pipeline that predicts call emotions."""

    def __init__(self):
        self._model = None
        self._feature_len = None

    def _train_fallback_model(self, feature_len: int) -> Pipeline:
        rng = np.random.default_rng(7)
        samples = 600
        X = rng.normal(loc=0.0, scale=1.0, size=(samples, feature_len))
        y = rng.integers(low=0, high=len(EMOTION_LABELS), size=samples)

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=200, multi_class="auto"))
        ])
        pipeline.fit(X, y)
        return pipeline

    def _load_or_train(self, feature_len: int) -> Pipeline:
        if EMOTION_MODEL_PATH.exists():
            try:
                bundle = load(EMOTION_MODEL_PATH)
                pipeline = bundle.get("pipeline")
                stored_len = bundle.get("feature_len")
                if pipeline is not None and stored_len == feature_len:
                    self._feature_len = stored_len
                    logger.info("Loaded cached emotion model from disk")
                    return pipeline
            except Exception as exc:
                logger.warning(f"Failed to load cached emotion model: {exc}")

        logger.info("Training fallback emotion model for feature length %s", feature_len)
        pipeline = self._train_fallback_model(feature_len)
        dump({"pipeline": pipeline, "feature_len": feature_len}, EMOTION_MODEL_PATH)
        self._feature_len = feature_len
        return pipeline

    def predict(self, feature_vector: np.ndarray):
        feature_len = feature_vector.shape[0]
        if self._model is None or self._feature_len != feature_len:
            self._model = self._load_or_train(feature_len)
        probs = self._model.predict_proba([feature_vector])[0]
        idx = int(np.argmax(probs))
        return EMOTION_LABELS[idx], float(probs[idx])


EMOTION_MODEL_SERVICE = EmotionModelService()


def _download_recording_to_temp(recording_url: str) -> str:
    suffix = Path(recording_url).suffix if recording_url else ".wav"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_file.close()

    response = requests.get(recording_url, stream=True, timeout=120)
    response.raise_for_status()

    with open(tmp_file.name, "wb") as out:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                out.write(chunk)
    return tmp_file.name


def _extract_audio_features(file_path: str) -> np.ndarray:
    y, sr = librosa.load(file_path, sr=16000)
    if y.size == 0:
        raise ValueError("Audio file is empty")

    features = [
        float(np.mean(np.abs(y))),
        float(np.std(y)),
        float(librosa.feature.zero_crossing_rate(y).mean()),
        float(librosa.feature.spectral_centroid(y=y, sr=sr).mean()),
        float(librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()),
        float(librosa.feature.spectral_rolloff(y=y, sr=sr).mean()),
    ]

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features.extend([float(v) for v in mfcc.mean(axis=1)])

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features.extend([float(v) for v in chroma.mean(axis=1)])

    return np.array(features, dtype=np.float32)

# ============================================================================
# CELERY TASKS
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def initiate_call(self, target_id: str, phone_number: str, call_id: str):
    """
    Initiate outbound call to a single target using Exotel API
    
    Args:
        target_id: UUID of the target
        phone_number: Phone number to call
        call_id: UUID of the call record
    """
    correlation_id = str(uuid.uuid4())
    logger.info(f"Initiating call for Target={target_id}, CallID={call_id}, CorrelationID={correlation_id}")
    
    with get_db_session_cm() as db:
        try:
            # Get call record
            call_record = db.query(Calls).filter(Calls.Call_Id == call_id).first()
            
            if not call_record:
                logger.error(f"Call record not found: {call_id}")
                return
            
            # Update call to started
            call_record.Started_Time = datetime.now(IST)
            db.commit()
            
            # Prepare Exotel API call
            # Format phone number for Exotel (remove + or 0)
            # Exotel expects format: 91XXXXXXXXXX (without + or 0 prefix)
            # formatted_phone = phone_number.lstrip('+').lstrip('0')
            formatted_phone = _normalize_last10(phone_number)
            formatted_exotel_phone = EXOTEL_PHONE_NUMBER.lstrip('+').lstrip('0')
            
            # Use the mhealth flow configured in Exotel dashboard
            call_data = {
                'From': formatted_phone,
                # 'To': formatted_phone,
                'CallerId': formatted_exotel_phone,
                'CallType': 'trans',  # Transactional call
                # 'Url': f'https://{APP_HOST}/voice?token={EXOTEL_WEBHOOK_TOKEN}',
                'Url': f'http://my.exotel.com/{EXOTEL_SID}/exoml/start_voice/{EXOTEL_APP_ID}',
                # 'StatusCallback': f"https://{APP_HOST}/call_status?token={EXOTEL_WEBHOOK_TOKEN}",
                # 'RecordingStatusCallback': f"https://{APP_HOST}/recording_callback?token={EXOTEL_WEBHOOK_TOKEN}",
                'Record': 'true',
                'TimeLimit': 3,
                'CallerName': 'MHealth IIT Gandhinagar',
                'CustomField': call_id
            }
            
            logger.info(
                f"Calling Exotel API: From={call_data['From']}, Url=/voice, CorrelationID={correlation_id}"
            )
            
            # Make API call to Exotel (use .json endpoint)
            api_url = f"{EXOTEL_BASE_URL}Calls/connect.json"
            exotel_response = requests.post(
                api_url,
                auth=(EXOTEL_API_KEY, EXOTEL_API_TOKEN),
                data=call_data,
                timeout=30
            )
            
            # Log response for debugging
            logger.info(f"Exotel Response Status: {exotel_response.status_code}, CorrelationID={correlation_id}")
            logger.info(f"Exotel Response Body: {exotel_response.text[:500]}, CorrelationID={correlation_id}")
            
            exotel_response.raise_for_status()
            
            # Parse response
            try:
                response_data = exotel_response.json()
            except ValueError as json_err:
                logger.error(f"Failed to parse Exotel JSON response: {json_err}, CorrelationID={correlation_id}")
                logger.error(f"Raw Response: {exotel_response.text}, CorrelationID={correlation_id}")
                raise Exception(f"Invalid JSON response from Exotel API: {exotel_response.text[:200]}")
            
            call_sid = response_data.get('Call', {}).get('Sid')
            # print(f"ccall_sid is :{call_sid}")
            if not call_sid:
                logger.error(f"Exotel API response did not contain CallSid: {response_data}, CorrelationID={correlation_id}")
                raise Exception("Invalid Exotel API response - no CallSid")
            
            # Update call record with Call_Sid
            call_record.Call_Sid = call_sid
            db.commit()
            
            logger.info(f"Call initiated successfully: Target={target_id}, CallSid={call_sid}, CorrelationID={correlation_id}")
            
        except requests.exceptions.HTTPError as err:
            logger.error(f"Exotel API error: {err}, CorrelationID={correlation_id}")
            logger.error(f"Response Body: {err.response.text if err.response else 'No response'}")
            
            # Update call status to failed
            call_record.Status = "Message Not Conveyed"
            db.commit()
            
            # Log error
            error_log = ErrorLogs(
                Error_Type="Exotel API Error",
                Error_Message=f"Target={target_id}, CallID={call_id}, Error={str(err)}, CorrelationID={correlation_id}"
            )
            db.add(error_log)
            db.commit()
            
            # Retry task
            raise self.retry(exc=err, countdown=60)
            
        except Exception as e:
            logger.error(f"Error initiating call for Target={target_id}: {str(e)}, CorrelationID={correlation_id}")
            
            # Update call status
            call_record.Status = "Message Not Conveyed"
            db.commit()
            
            # Log error
            error_log = ErrorLogs(
                Error_Type="Call Initiation Error",
                Error_Message=f"Target={target_id}, CallID={call_id}, Error={str(e)}, CorrelationID={correlation_id}"
            )
            db.add(error_log)
            db.commit()
            
            raise


@celery_app.task
def initiate_calls_for_all_targets():
    """
    Celery Beat task to schedule calls for all active targets
    Creates call records and initiates Exotel API calls
    """
    logger.info("Celery Beat task: Initiating calls for all targets.")
    
    with get_db_session_cm() as db:
        try:
            current_time = datetime.now(IST)
            
            # Get all targets that are not flagged
            flagged_target_ids = db.query(FlaggedTargets.Target_Id).all()
            flagged_ids = [ft.Target_Id for ft in flagged_target_ids]
            
            targets = db.query(Targets).filter(
                ~Targets.Target_Id.in_(flagged_ids)
            ).all()
            
            if not targets:
                logger.warning("No targets found to schedule calls for.")
                return
            
            logger.info(f"Found {len(targets)} targets for calling")
            
            # Get or create model record
            model = db.query(Models).filter(Models.Model_Id == MODEL_ID).first()
            if not model:
                logger.error(f"Model {MODEL_ID} not found in database")
                return
            
            # Create call records and initiate calls
            initiated_count = 0
            
            for target in targets:
                try:
                    # Check if there's already a pending call for today
                    existing_call = db.query(Calls).filter(
                        and_(
                            Calls.Target_Id == target.Target_Id,
                            Calls.Scheduled_Time >= current_time.replace(hour=0, minute=0, second=0),
                            Calls.Status == "Awaiting Schedule"  # Only check truly pending calls
                        )
                    ).first()
                    
                    if existing_call:
                        logger.info(f"Call already scheduled for Target={target.Target_Id}, Status={existing_call.Status}")
                        continue
                    
                    # Create new call record
                    new_call = Calls(
                        Target_Id=target.Target_Id,
                        Model_Id=MODEL_ID,
                        Scheduled_Time=current_time,
                        Status="Awaiting Schedule"
                    )
                    
                    db.add(new_call)
                    db.flush()  # Get the Call_Id
                    
                    # Initiate call asynchronously
                    initiate_call.delay(
                        str(target.Target_Id),
                        target.Phone_No,
                        str(new_call.Call_Id)
                    )
                    
                    initiated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error creating call for Target={target.Target_Id}: {e}")
                    db.rollback()
                    continue
            
            db.commit()
            logger.info(f"Initiated {initiated_count} calls successfully")
            
        except Exception as e:
            logger.error(f"Error in initiate_calls_for_all_targets: {str(e)}")
            db.rollback()



@celery_app.task
def process_recording_emotion(call_id: str):
    """
    Celery task to process recording and detect emotion using AI/ML model
    This would integrate with your emotion detection model
    
    Args:
        call_id: UUID of the call record
    """
    logger.info(f"Processing recording for emotion detection: Call={call_id}")
    future = EMOTION_EXECUTOR.submit(_process_recording_emotion_job, call_id)
    return future.result()


def _process_recording_emotion_job(call_id: str):
    temp_path = None
    try:
        with get_db_session_cm() as db:
            call_record = db.query(Calls).filter(Calls.Call_Id == call_id).first()

            if not call_record or not call_record.Recording_Url:
                raise ValueError(f"Call record or recording not found for {call_id}")

            temp_path = _download_recording_to_temp(call_record.Recording_Url)
            feature_vector = _extract_audio_features(temp_path)
            emotion_label, confidence = EMOTION_MODEL_SERVICE.predict(feature_vector)

            emotion_row = db.query(Emotions).filter(
                func.lower(Emotions.Emotion) == emotion_label.lower()
            ).first()

            if emotion_row:
                call_record.Emotion_Id = emotion_row.Emotion_Id
                print(f"Emotion_ID is :{emotion_row.Emotion_Id}")
            else:
                logger.warning("Predicted emotion %s not present in database", emotion_label)

            call_record.Status = "Message Conveyed And Processed"
            if call_record.Duration and call_record.Duration < int(MIN_RECORDING_DURATION_SECONDS):
                logger.warning(
                    "Recording too short for Call=%s, Duration=%ss",
                    call_id,
                    call_record.Duration
                )
                call_record.Status = "Message Conveyed But Not Processed"
                call_record.Emotion_id = "E001"

            db.commit()
            print(f"Emotion label is  : {emotion_label}")
            logger.info(
                "Emotion processing completed for Call=%s -> %s (confidence %.2f)",
                call_id,
                emotion_label,
                confidence
            )
    except Exception as exc:
        logger.error(f"Error processing recording emotion for Call={call_id}: {exc}", exc_info=True)
        with get_db_session_cm() as db:
            call_record = db.query(Calls).filter(Calls.Call_Id == call_id).first()
            if call_record:
                call_record.Status = "Message Conveyed And Processing Failed"
                db.commit()

            error_log = ErrorLogs(
                Error_Type="Emotion Processing Error",
                Error_Message=f"CallID={call_id}, Error={str(exc)}"
            )
            db.add(error_log)
            db.commit()
        raise
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
