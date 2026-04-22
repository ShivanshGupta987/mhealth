"""schemas.py - Pydantic request/response schemas for twilio_service."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Targets ───────────────────────────────────────────────────────────────────

class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone_no: str = Field(..., description="Phone number (E.164 or 10-digit Indian)")
    roll_no: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None

    @field_validator("phone_no")
    @classmethod
    def phone_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("phone_no must not be blank")
        return v.strip()


class TargetOut(BaseModel):
    target_id: uuid.UUID
    name: str
    phone_no: str
    roll_no: Optional[str]
    department: Optional[str]
    program: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Outbound call trigger ─────────────────────────────────────────────────────

class InitiateCallRequest(BaseModel):
    """Body for POST /calls/initiate — triggers a call to a single target."""
    target_id: uuid.UUID = Field(..., description="UUID of the target (Targets.Target_Id)")


class BulkInitiateCallRequest(BaseModel):
    """Body for POST /calls/initiate-bulk — triggers calls to multiple targets."""
    target_ids: List[uuid.UUID] = Field(..., min_length=1)


# ── Response shapes ───────────────────────────────────────────────────────────

class TwilioResponseOut(BaseModel):
    response_id: uuid.UUID
    call_id: uuid.UUID
    question_index: int
    question_text: str
    response_type: str
    response_value: Optional[str]
    twilio_recording_url: Optional[str]
    minio_recording_url: Optional[str]
    recording_playback_url: Optional[str]
    response_label: Optional[str]
    recording_sid: Optional[str]
    recording_duration: Optional[int]
    analysis_score: Optional[float]
    responded_at: datetime

    class Config:
        from_attributes = True


class TwilioCallOut(BaseModel):
    call_id: uuid.UUID
    twilio_call_sid: Optional[str]
    target_id: uuid.UUID
    scheduled_time: datetime
    started_time: Optional[datetime]
    ended_time: Optional[datetime]
    status: str
    total_questions: int
    questions_answered: int
    overall_duration: Optional[int]
    total_response_duration: Optional[int]
    depression_risk: Optional[int] = None
    depression_risk_probability: Optional[float] = None
    depression_risk_level: Optional[str] = None
    depression_risk_confidence: Optional[float] = None
    depression_analysis_timestamp: Optional[datetime] = None
    created_at: datetime
    responses: List[TwilioResponseOut] = []

    class Config:
        from_attributes = True


class InitiateCallResponse(BaseModel):
    message: str
    call_id: uuid.UUID
    target_id: uuid.UUID
