"""main.py - FastAPI application for the Twilio voice call flow service.

Call flow overview
──────────────────
1.  Celery task calls Twilio API → outbound call placed.
    The call's `url`             → POST /voice/answer
    The call's `status_callback` → POST /voice/status

2.  Callee picks up → Twilio POSTs to /voice/answer
    → App returns TwiML for Question 0.

3.  Depending on question type:
    • gather (DTMF) → <Gather action="/voice/respond/0"> … </Gather>
    • record (voice) → <Record action="/voice/respond/0" …/>

4.  After input Twilio POSTs to POST /voice/respond/{q_index}
    → App stores the response, returns TwiML for next question or closes call.

5.  Twilio posts lifecycle events to POST /voice/status
    → App updates TwilioCalls.Status accordingly.

Security
────────
Every incoming Twilio webhook is validated via X-Twilio-Signature
(twilio.request_validator.RequestValidator).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Gather, VoiceResponse

from app.twilio.config import APP_HOST, TWILIO_AUTH_TOKEN
from app.twilio.models import TwilioTargets, TwilioCalls, TwilioResponses
from app.twilio.question_flow import (
    CLOSING_MESSAGE,
    NO_INPUT_MESSAGE,
    TOTAL_QUESTIONS,
    get_question,
    is_last_question,
)
from app.twilio.schemas import (
    BulkInitiateCallRequest,
    InitiateCallRequest,
    InitiateCallResponse,
    TargetCreate,
    TargetOut,
    TwilioCallOut,
    TwilioResponseOut,
)
from app.twilio.sql_db import get_db
from app.twilio.storage import recording_playback_url

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [twilio_service]: %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Twilio Voice Call Flow Service",
    description=(
        "Standalone outbound call service that asks multiple mental-health "
        "check-in questions using Twilio Voice API and records responses."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Twilio signature validation
# ---------------------------------------------------------------------------
_validator = RequestValidator(TWILIO_AUTH_TOKEN)


async def _validate_twilio_signature(request: Request) -> None:
    """Raise 403 if the request does not carry a valid Twilio signature."""
    signature = request.headers.get("X-Twilio-Signature", "")
    form_data = dict(await request.form())
    url = str(request.url)
    if not _validator.validate(url, form_data, signature):
        logger.warning("Invalid Twilio signature from %s", request.client)
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


# ---------------------------------------------------------------------------
# TwiML builder helpers
# ---------------------------------------------------------------------------
_TTS_VOICE = "Polly.Raveena"
_TTS_LANG = "en-IN"


def _public_base_url(request: Request) -> str:
    """Return the public base URL (scheme + host) seen by Twilio."""
    if APP_HOST and APP_HOST not in ("localhost", "0.0.0.0"):
        return f"https://{APP_HOST}"
    return f"{request.base_url.scheme}://{request.base_url.netloc}"


def _build_question_twiml(question: dict, respond_url: str) -> str:
    """Return TwiML string that reads *question* and collects a response."""
    response = VoiceResponse()

    if question["type"] == "gather":
        gather = Gather(
            action=respond_url,
            method="POST",
            num_digits=question.get("num_digits", 1),
            timeout=question.get("timeout", 10),
            input="dtmf",
        )
        gather.say(question["text"], voice=_TTS_VOICE, language=_TTS_LANG)
        response.append(gather)
        # Fallback when no keypress received within timeout
        response.say(NO_INPUT_MESSAGE, voice=_TTS_VOICE, language=_TTS_LANG)
        response.redirect(respond_url, method="POST")

    elif question["type"] == "record":
        response.say(question["text"], voice=_TTS_VOICE, language=_TTS_LANG)
        response.record(
            action=respond_url,
            method="POST",
            max_length=question.get("max_length", 60),
            timeout=question.get("timeout", 5),
            play_beep=True,
        )

    return str(response)


def _build_closing_twiml() -> str:
    response = VoiceResponse()
    response.say(CLOSING_MESSAGE, voice=_TTS_VOICE, language=_TTS_LANG)
    response.hangup()
    return str(response)


# ===========================================================================
# Health
# ===========================================================================

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "twilio_service"}


# ===========================================================================
# TwilioTargets CRUD
# ===========================================================================

@app.post("/targets", response_model=TargetOut, status_code=201, tags=["Targets"])
def create_target(body: TargetCreate, db: Session = Depends(get_db)):
    """Add a new call target."""
    existing = db.query(TwilioTargets).filter(TwilioTargets.Phone_No == body.phone_no).first()
    if existing:
        raise HTTPException(status_code=409, detail="A target with this phone number already exists")

    target = TwilioTargets(
        Name=body.name,
        Phone_No=body.phone_no,
        Roll_No=body.roll_no,
        Department=body.department,
        Program=body.program,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return _target_to_schema(target)


@app.get("/targets", response_model=List[TargetOut], tags=["Targets"])
def list_targets(db: Session = Depends(get_db)):
    """List all targets."""
    return [_target_to_schema(t) for t in db.query(TwilioTargets).order_by(TwilioTargets.Created_At.desc()).all()]


@app.get("/targets/{target_id}", response_model=TargetOut, tags=["Targets"])
def get_target(target_id: uuid.UUID, db: Session = Depends(get_db)):
    target = db.query(TwilioTargets).filter(TwilioTargets.Target_Id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return _target_to_schema(target)


@app.delete("/targets/{target_id}", status_code=204, tags=["Targets"])
def delete_target(target_id: uuid.UUID, db: Session = Depends(get_db)):
    """Hard-delete a target record."""
    target = db.query(TwilioTargets).filter(TwilioTargets.Target_Id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()


def _target_to_schema(t: TwilioTargets) -> TargetOut:
    return TargetOut(
        target_id=t.Target_Id,
        name=t.Name,
        phone_no=t.Phone_No,
        roll_no=t.Roll_No,
        department=t.Department,
        program=t.Program,
        created_at=t.Created_At,
    )


# ===========================================================================
# Twilio Webhooks
# ===========================================================================

@app.post("/voice/answer", tags=["Twilio Webhooks"])
async def voice_answer(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Called by Twilio when the callee answers.
    Updates call status and returns TwiML for Question 0.
    """
    await _validate_twilio_signature(request)
    logger.info("Call answered: CallSid=%s Status=%s", CallSid, CallStatus)

    call = db.query(TwilioCalls).filter(TwilioCalls.Twilio_Call_Sid == CallSid).first()
    if call:
        call.Status = "In Progress"
        call.Started_Time = datetime.now(timezone.utc)
        db.commit()
    else:
        logger.warning("No TwilioCalls record for CallSid=%s", CallSid)

    base = _public_base_url(request)
    question = get_question(0)
    respond_url = f"{base}/voice/respond/0?call_sid={CallSid}"
    return Response(content=_build_question_twiml(question, respond_url), media_type="text/xml")


@app.post("/voice/respond/{question_index}", tags=["Twilio Webhooks"])
async def voice_respond(
    question_index: int,
    request: Request,
    call_sid: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Called by Twilio after the callee responds to a question.
    Stores the response and returns TwiML for the next question (or closing).
    """
    await _validate_twilio_signature(request)

    form = dict(await request.form())
    call_sid_form: str = form.get("CallSid", call_sid or "")
    digits: Optional[str] = form.get("Digits")
    recording_url: Optional[str] = form.get("RecordingUrl")
    recording_sid: Optional[str] = form.get("RecordingSid")
    raw_duration = form.get("RecordingDuration")
    recording_duration: Optional[int] = int(raw_duration) if raw_duration else None

    logger.info(
        "Response: CallSid=%s Q=%d Digits=%s RecordingUrl=%s",
        call_sid_form, question_index, digits, recording_url,
    )

    if question_index < 0 or question_index >= TOTAL_QUESTIONS:
        return Response(content=_build_closing_twiml(), media_type="text/xml")

    question = get_question(question_index)
    response_type: str = question["type"]
    response_value: Optional[str] = None
    response_label: Optional[str] = None

    if response_type == "gather":
        response_value = digits or ""
        response_label = question.get("label_map", {}).get(response_value, response_value)
    elif response_type == "record":
        # Voice responses store URLs in dedicated fields, not in Response_Value.
        response_value = None

    call = db.query(TwilioCalls).filter(TwilioCalls.Twilio_Call_Sid == call_sid_form).first()
    if call:
        already_saved = (
            db.query(TwilioResponses)
            .filter(
                TwilioResponses.Call_Id == call.Call_Id,
                TwilioResponses.Question_Index == question_index,
            )
            .first()
        )
        if not already_saved:
            resp_record = TwilioResponses(
                Call_Id=call.Call_Id,
                Question_Index=question_index,
                Question_Text=question["text"],
                Response_Type=response_type,
                Response_Value=response_value,
                Response_Label=response_label,
                Recording_Sid=recording_sid,
                Recording_Duration=recording_duration,
                TwilioRecordingUrl=recording_url,
                Responded_At=datetime.now(timezone.utc),
            )
            db.add(resp_record)
            call.Questions_Answered = (call.Questions_Answered or 0) + 1
            db.commit()
            
            # Calculate total response duration from all responses
            total_duration = (
                db.query(TwilioResponses)
                .filter(TwilioResponses.Call_Id == call.Call_Id)
                .all()
            )
            duration_sum = sum(
                (r.Recording_Duration or 0) for r in total_duration
                if r.Recording_Duration is not None
            )
            call.Total_Response_Duration = duration_sum
            db.commit()
            logger.info(
                "Updated Total_Response_Duration for call %s: %d seconds",
                call.Call_Id, duration_sum
            )
            
            # Check if total response time exceeds 3 minutes (180 seconds)
            if duration_sum >= 180:
                logger.info(
                    "Total response duration reached limit: %d seconds >= 180 seconds. Ending call for CallID=%s",
                    duration_sum, call.Call_Id
                )
                call.Status = "Completed"
                call.Ended_Time = datetime.now(timezone.utc)
                db.commit()
                _trigger_call_recording_archival(str(call.Call_Id))
                _trigger_depression_analysis(str(call.Call_Id))
                return Response(content=_build_closing_twiml(), media_type="text/xml")

            # Only depression analysis is used after call completion.
    else:
        logger.warning("No TwilioCalls record for CallSid=%s", call_sid_form)

    # At this point we've processed the response and checked if 3-min limit was reached
    # If we're here, we can proceed to next question or closing
    
    if is_last_question(question_index):
        # Last question answered - close call
        if call:
            call.Status = "Completed"
            call.Ended_Time = datetime.now(timezone.utc)
            db.commit()
            _trigger_call_recording_archival(str(call.Call_Id))
            _trigger_depression_analysis(str(call.Call_Id))
        return Response(content=_build_closing_twiml(), media_type="text/xml")

    # Not last question - offer next question if available
    # (3-minute check already done above, so if we're here we haven't hit the limit)
    base = _public_base_url(request)
    next_index = question_index + 1
    if next_index < TOTAL_QUESTIONS:
        next_question = get_question(next_index)
        next_url = f"{base}/voice/respond/{next_index}?call_sid={call_sid_form}"
        return Response(content=_build_question_twiml(next_question, next_url), media_type="text/xml")
    else:
        # No more questions available - close call
        if call:
            call.Status = "Completed"
            call.Ended_Time = datetime.now(timezone.utc)
            db.commit()
            _trigger_call_recording_archival(str(call.Call_Id))
            _trigger_depression_analysis(str(call.Call_Id))
        return Response(content=_build_closing_twiml(), media_type="text/xml")


@app.post("/voice/status", tags=["Twilio Webhooks"])
async def voice_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Receives Twilio call lifecycle events and updates status in DB."""
    await _validate_twilio_signature(request)
    logger.info("Status callback: CallSid=%s Status=%s", CallSid, CallStatus)

    _STATUS_MAP = {
        "completed": "Completed",
        "no-answer": "No Answer",
        "failed": "Failed",
        "busy": "Busy",
        "canceled": "Cancelled",
        "in-progress": "In Progress",
        "queued": "Call Initiated",
        "ringing": "Call Initiated",
        "initiated": "Call Initiated",
    }
    mapped = _STATUS_MAP.get(CallStatus.lower(), "Call Initiated")

    call = db.query(TwilioCalls).filter(TwilioCalls.Twilio_Call_Sid == CallSid).first()
    if call:
        if call.Status != "Completed" or mapped == "Completed":
            call.Status = mapped
        if CallDuration:
            call.Overall_Duration = int(CallDuration)
        if mapped in ("Completed", "No Answer", "Failed", "Busy", "Cancelled"):
            call.Ended_Time = datetime.now(timezone.utc)
        db.commit()

        if mapped == "Completed":
            _trigger_call_recording_archival(str(call.Call_Id))

    return PlainTextResponse("", status_code=204)


# ===========================================================================
# Admin: trigger calls
# ===========================================================================

@app.post(
    "/calls/initiate",
    response_model=InitiateCallResponse,
    status_code=202,
    tags=["Admin"],
)
def initiate_call(body: InitiateCallRequest, db: Session = Depends(get_db)):
    """Trigger an outbound Twilio call for a single target."""
    from app.twilio.celery_config_twilio import initiate_twilio_call_task

    target = db.query(TwilioTargets).filter(TwilioTargets.Target_Id == body.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    if not target.Phone_No:
        raise HTTPException(status_code=422, detail="Target has no phone number")

    call_record = TwilioCalls(
        Target_Id=target.Target_Id,
        Scheduled_Time=datetime.now(timezone.utc),
        Status="Call Scheduled",
        Total_Questions=TOTAL_QUESTIONS,
        Questions_Answered=0,
    )
    db.add(call_record)
    db.commit()
    db.refresh(call_record)

    initiate_twilio_call_task.delay(
        target_id=str(target.Target_Id),
        phone_number=target.Phone_No,
        call_id=str(call_record.Call_Id),
    )

    return InitiateCallResponse(
        message="Call scheduled",
        call_id=call_record.Call_Id,
        target_id=target.Target_Id,
    )


@app.post("/calls/initiate-bulk", status_code=202, tags=["Admin"])
def initiate_bulk_calls(body: BulkInitiateCallRequest, db: Session = Depends(get_db)):
    """Trigger outbound calls for multiple targets."""
    from app.twilio.celery_config_twilio import initiate_twilio_call_task

    dispatched, skipped = [], []

    for tid in body.target_ids:
        target = db.query(TwilioTargets).filter(TwilioTargets.Target_Id == tid).first()
        if not target or not target.Phone_No:
            skipped.append(str(tid))
            continue

        call_record = TwilioCalls(
            Target_Id=target.Target_Id,
            Scheduled_Time=datetime.now(timezone.utc),
            Status="Call Scheduled",
            Total_Questions=TOTAL_QUESTIONS,
            Questions_Answered=0,
        )
        db.add(call_record)
        db.commit()
        db.refresh(call_record)

        initiate_twilio_call_task.delay(
            target_id=str(target.Target_Id),
            phone_number=target.Phone_No,
            call_id=str(call_record.Call_Id),
        )
        dispatched.append(str(tid))

    return {
        "message": f"{len(dispatched)} calls scheduled, {len(skipped)} skipped",
        "dispatched": dispatched,
        "skipped_no_phone": skipped,
    }


@app.get("/targets/{target_id}/calls", response_model=List[TwilioCallOut], tags=["Admin"])
def list_calls_for_target(target_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return all calls for a target, newest first."""
    target = db.query(TwilioTargets).filter(TwilioTargets.Target_Id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    calls = (
        db.query(TwilioCalls)
        .filter(TwilioCalls.Target_Id == target_id)
        .order_by(TwilioCalls.Scheduled_Time.desc())
        .all()
    )
    return [
        TwilioCallOut(
            call_id=c.Call_Id,
            twilio_call_sid=c.Twilio_Call_Sid,
            target_id=c.Target_Id,
            scheduled_time=c.Scheduled_Time,
            started_time=c.Started_Time,
            ended_time=c.Ended_Time,
            status=c.Status,
            total_questions=c.Total_Questions,
            questions_answered=c.Questions_Answered,
            overall_duration=c.Overall_Duration,
            total_response_duration=c.Total_Response_Duration,
            depression_risk=c.Depression_Risk,
            depression_risk_probability=c.Depression_Risk_Probability,
            depression_risk_level=c.Depression_Risk_Level,
            depression_risk_confidence=c.Depression_Risk_Confidence,
            depression_analysis_timestamp=c.Depression_Analysis_Timestamp,
            created_at=c.Created_At,
            responses=[
                {
                    "response_id": r.Response_Id,
                    "call_id": r.Call_Id,
                    "question_index": r.Question_Index,
                    "question_text": r.Question_Text,
                    "response_type": r.Response_Type,
                    "response_value": r.Response_Value,
                    "twilio_recording_url": r.TwilioRecordingUrl,
                    "minio_recording_url": r.MinIORecordingUrl,
                    "recording_playback_url": recording_playback_url(r.MinIORecordingUrl, r.TwilioRecordingUrl),
                    "response_label": r.Response_Label,
                    "recording_sid": r.Recording_Sid,
                    "recording_duration": r.Recording_Duration,
                    "analysis_score": r.Analysis_Score,
                    "responded_at": r.Responded_At,
                }
                for r in sorted(c.responses, key=lambda x: x.Question_Index)
            ],
        )
        for c in calls
    ]


@app.get("/calls", response_model=List[TwilioCallOut], tags=["Admin"])
def list_all_calls(db: Session = Depends(get_db)):
    """Return every call record, newest first."""
    calls = db.query(TwilioCalls).order_by(TwilioCalls.Scheduled_Time.desc()).all()
    return [
        TwilioCallOut(
            call_id=c.Call_Id,
            twilio_call_sid=c.Twilio_Call_Sid,
            target_id=c.Target_Id,
            scheduled_time=c.Scheduled_Time,
            started_time=c.Started_Time,
            ended_time=c.Ended_Time,
            status=c.Status,
            total_questions=c.Total_Questions,
            questions_answered=c.Questions_Answered,
            overall_duration=c.Overall_Duration,
            total_response_duration=c.Total_Response_Duration,
            depression_risk=c.Depression_Risk,
            depression_risk_probability=c.Depression_Risk_Probability,
            depression_risk_level=c.Depression_Risk_Level,
            depression_risk_confidence=c.Depression_Risk_Confidence,
            depression_analysis_timestamp=c.Depression_Analysis_Timestamp,
            created_at=c.Created_At,
            responses=[
                {
                    "response_id": r.Response_Id,
                    "call_id": r.Call_Id,
                    "question_index": r.Question_Index,
                    "question_text": r.Question_Text,
                    "response_type": r.Response_Type,
                    "response_value": r.Response_Value,
                    "twilio_recording_url": r.TwilioRecordingUrl,
                    "minio_recording_url": r.MinIORecordingUrl,
                    "recording_playback_url": recording_playback_url(r.MinIORecordingUrl, r.TwilioRecordingUrl),
                    "response_label": r.Response_Label,
                    "recording_sid": r.Recording_Sid,
                    "recording_duration": r.Recording_Duration,
                    "analysis_score": r.Analysis_Score,
                    "responded_at": r.Responded_At,
                }
                for r in sorted(c.responses, key=lambda x: x.Question_Index)
            ],
        )
        for c in calls
    ]


@app.delete("/calls/{call_id}", status_code=204, tags=["Admin"])
def delete_call(call_id: uuid.UUID, db: Session = Depends(get_db)):
    """Hard-delete a call record (cascades to responses)."""
    call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    db.delete(call)
    db.commit()


@app.get("/responses", response_model=List[TwilioResponseOut], tags=["Admin"])
def list_all_responses(db: Session = Depends(get_db)):
    """Return every response record, newest first."""
    from app.twilio.models import TwilioResponses
    rows = db.query(TwilioResponses).order_by(TwilioResponses.Responded_At.desc()).all()
    return [
        TwilioResponseOut(
            response_id=r.Response_Id,
            call_id=r.Call_Id,
            question_index=r.Question_Index,
            question_text=r.Question_Text,
            response_type=r.Response_Type,
            response_value=r.Response_Value,
            twilio_recording_url=r.TwilioRecordingUrl,
            minio_recording_url=r.MinIORecordingUrl,
            recording_playback_url=recording_playback_url(r.MinIORecordingUrl, r.TwilioRecordingUrl),
            response_label=r.Response_Label,
            recording_sid=r.Recording_Sid,
            recording_duration=r.Recording_Duration,
            analysis_score=r.Analysis_Score,
            responded_at=r.Responded_At,
        )
        for r in rows
    ]


@app.delete("/responses/{response_id}", status_code=204, tags=["Admin"])
def delete_response(response_id: uuid.UUID, db: Session = Depends(get_db)):
    """Hard-delete a single response record."""
    from app.twilio.models import TwilioResponses
    row = db.query(TwilioResponses).filter(TwilioResponses.Response_Id == response_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Response not found")
    db.delete(row)
    db.commit()


@app.get("/calls/{call_id}", response_model=TwilioCallOut, tags=["Admin"])
def get_call(call_id: uuid.UUID, db: Session = Depends(get_db)):
    """Return full call details including all question responses."""
    call = db.query(TwilioCalls).filter(TwilioCalls.Call_Id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return TwilioCallOut(
        call_id=call.Call_Id,
        twilio_call_sid=call.Twilio_Call_Sid,
        target_id=call.Target_Id,
        scheduled_time=call.Scheduled_Time,
        started_time=call.Started_Time,
        ended_time=call.Ended_Time,
        status=call.Status,
        total_questions=call.Total_Questions,
        questions_answered=call.Questions_Answered,
        overall_duration=call.Overall_Duration,
        total_response_duration=call.Total_Response_Duration,
        depression_risk=call.Depression_Risk,
        depression_risk_probability=call.Depression_Risk_Probability,
        depression_risk_level=call.Depression_Risk_Level,
        depression_risk_confidence=call.Depression_Risk_Confidence,
        depression_analysis_timestamp=call.Depression_Analysis_Timestamp,
        created_at=call.Created_At,
        responses=[
            {
                "response_id": r.Response_Id,
                "call_id": r.Call_Id,
                "question_index": r.Question_Index,
                "question_text": r.Question_Text,
                "response_type": r.Response_Type,
                "response_value": r.Response_Value,
                "twilio_recording_url": r.TwilioRecordingUrl,
                "minio_recording_url": r.MinIORecordingUrl,
                "recording_playback_url": recording_playback_url(r.MinIORecordingUrl, r.TwilioRecordingUrl),
                "response_label": r.Response_Label,
                "recording_sid": r.Recording_Sid,
                "recording_duration": r.Recording_Duration,
                "analysis_score": r.Analysis_Score,
                "responded_at": r.Responded_At,
            }
            for r in sorted(call.responses, key=lambda x: x.Question_Index)
        ],
    )


# ===========================================================================
# Internal helpers
# ===========================================================================

def _trigger_call_recording_archival(call_id: str):
    """Dispatch Celery fan-out task to archive all call recordings to MinIO."""
    from app.twilio.celery_config_twilio import archive_call_recordings_task

    logger.info("Triggering archival for call %s", call_id)
    result = archive_call_recordings_task.delay(call_id=call_id)
    logger.info("Archival task queued with task_id=%s", result.id)


def _trigger_depression_analysis(call_id: str):
    """Dispatch Celery task to analyze call for depression risk by combining all responses."""
    from app.twilio.celery_config_twilio import analyze_call_depression_risk_task

    logger.info("Triggering depression risk analysis for call %s", call_id)
    result = analyze_call_depression_risk_task.delay(call_id=call_id)
    logger.info("Depression analysis task queued with task_id=%s", result.id)

