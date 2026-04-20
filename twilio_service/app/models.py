"""models.py - SQLAlchemy models for the Twilio call flow service.

This service is fully standalone: it owns its own PostgreSQL database.
All four tables below are created by this service's Alembic migrations.
"""
import uuid
from datetime import datetime, timezone

import pytz
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.sql_db import Base

IST = pytz.timezone("Asia/Kolkata")

# ── Status Enum ───────────────────────────────────────────────────────────────
TWILIO_CALL_STATUS_ENUM = Enum(
    "Call Scheduled",   # Created in DB, not yet sent to Twilio
    "Call Initiated",   # Twilio API call placed, awaiting pickup
    "In Progress",      # Call answered, questions being asked
    "Completed",        # All questions answered; call ended normally
    "No Answer",        # Callee did not pick up
    "Busy",             # Line was busy
    "Failed",           # Twilio reported a failure
    "Cancelled",        # Call cancelled before answer
    name="twilio_call_status_enum",
)


class Targets(Base):
    """People to be called by the Twilio service.

    This table is owned exclusively by twilio_service and is managed via
    the admin API (POST /targets) or by bulk-importing a CSV.
    """

    __tablename__ = "Targets"

    Target_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = Column(String(255), nullable=False)
    # Must be in E.164 or local format; normalised before calling
    Phone_No = Column(String(20), unique=True, nullable=False)
    # Optional metadata
    Roll_No = Column(String(50), unique=True, nullable=True)
    Department = Column(String(100), nullable=True)
    Program = Column(String(100), nullable=True)

    Created_At = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    calls = relationship("TwilioCalls", back_populates="target", cascade="all, delete-orphan")


class TwilioCalls(Base):
    """Tracks each outbound call initiated via the Twilio Voice API."""

    __tablename__ = "Twilio_Calls"

    Call_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Filled once Twilio API returns a CallSid
    Twilio_Call_Sid = Column(String(64), nullable=True, index=True)

    # Foreign key to the local Targets table (owned by this service)
    Target_Id = Column(UUID(as_uuid=True), ForeignKey("Targets.Target_Id"), nullable=False)

    Scheduled_Time = Column(DateTime(timezone=True), nullable=False)
    Started_Time = Column(DateTime(timezone=True), nullable=True)
    Ended_Time = Column(DateTime(timezone=True), nullable=True)

    Status = Column(TWILIO_CALL_STATUS_ENUM, nullable=False, default="Call Scheduled")

    # Total number of questions in the flow at the time of the call
    Total_Questions = Column(Integer, nullable=False, default=0)
    # How many questions were actually answered
    Questions_Answered = Column(Integer, nullable=False, default=0)

    # Duration of the call in seconds (from Twilio callback)
    Overall_Duration = Column(Integer, nullable=True)
    # Sum of durations of all question responses in seconds
    Total_Response_Duration = Column(Integer, nullable=True, default=0)

    # Depression risk prediction from ML service
    Depression_Risk = Column(Integer, nullable=True)  # 0 or 1
    Depression_Risk_Probability = Column(Float, nullable=True)  # 0.0-1.0
    Depression_Risk_Level = Column(String(32), nullable=True)  # "High" or "Low"
    Depression_Risk_Confidence = Column(Float, nullable=True)
    Depression_Analysis_Timestamp = Column(DateTime(timezone=True), nullable=True)

    Created_At = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    target = relationship("Targets", back_populates="calls")
    responses = relationship(
        "TwilioResponses", back_populates="call", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "Target_Id", "Scheduled_Time", name="uq_twilio_target_scheduled_time"
        ),
    )


class TwilioResponses(Base):
    """Stores each individual question response within a TwilioCalls session."""

    __tablename__ = "Twilio_Responses"

    Response_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Parent call
    Call_Id = Column(
        UUID(as_uuid=True),
        ForeignKey("Twilio_Calls.Call_Id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 0-based question index matching question_flow.QUESTIONS
    Question_Index = Column(Integer, nullable=False)
    Question_Text = Column(Text, nullable=False)

    # 'dtmf' for keypress responses, 'voice' for recorded audio
    Response_Type = Column(String(8), nullable=False)

    # For dtmf: the digit(s) pressed; for voice: Twilio RecordingUrl
    Response_Value = Column(Text, nullable=True)

    # Human-readable label for DTMF responses (e.g. "Good", "Yes")
    Response_Label = Column(String(64), nullable=True)

    # Twilio recording identifiers (voice questions only)
    Recording_Sid = Column(String(64), nullable=True)
    Recording_Duration = Column(Integer, nullable=True)

    # Recording URLs — both Twilio and MinIO (if configured)
    # TwilioRecordingUrl: always stored (permanent backup, survives storage migration)
    # MinIORecordingUrl: populated when archival to MinIO succeeds
    TwilioRecordingUrl = Column(Text, nullable=True)
    MinIORecordingUrl = Column(Text, nullable=True)

    # Generic analysis score at response level (reserved for future use)
    Analysis_Score = Column(Float, nullable=True)

    Responded_At = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    call = relationship("TwilioCalls", back_populates="responses")

    __table_args__ = (
        UniqueConstraint(
            "Call_Id", "Question_Index", name="uq_twilio_call_question"
        ),
    )
