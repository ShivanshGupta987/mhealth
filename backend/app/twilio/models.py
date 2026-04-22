"""SQLAlchemy models for Twilio call flow tables (public schema)."""
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

from app.twilio.sql_db import Base

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


class TwilioTargets(Base):
    """Call targets managed by the Twilio service."""

    __tablename__ = "Twilio_Targets"

    Target_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = Column(String(255), nullable=False)
    Phone_No = Column(String(20), unique=True, nullable=False)
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

    Twilio_Call_Sid = Column(String(64), nullable=True, index=True)

    Target_Id = Column(UUID(as_uuid=True), ForeignKey("Twilio_Targets.Target_Id"), nullable=False)

    Scheduled_Time = Column(DateTime(timezone=True), nullable=False)
    Started_Time = Column(DateTime(timezone=True), nullable=True)
    Ended_Time = Column(DateTime(timezone=True), nullable=True)

    Status = Column(TWILIO_CALL_STATUS_ENUM, nullable=False, default="Call Scheduled")

    Total_Questions = Column(Integer, nullable=False, default=0)
    Questions_Answered = Column(Integer, nullable=False, default=0)

    Overall_Duration = Column(Integer, nullable=True)
    Total_Response_Duration = Column(Integer, nullable=True, default=0)

    Depression_Risk = Column(Integer, nullable=True)
    Depression_Risk_Probability = Column(Float, nullable=True)
    Depression_Risk_Level = Column(String(32), nullable=True)
    Depression_Risk_Confidence = Column(Float, nullable=True)
    Depression_Analysis_Timestamp = Column(DateTime(timezone=True), nullable=True)

    Created_At = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    target = relationship("TwilioTargets", back_populates="calls")
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

    Call_Id = Column(
        UUID(as_uuid=True),
        ForeignKey("Twilio_Calls.Call_Id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    Question_Index = Column(Integer, nullable=False)
    Question_Text = Column(Text, nullable=False)

    Response_Type = Column(String(8), nullable=False)
    Response_Value = Column(Text, nullable=True)
    Response_Label = Column(String(64), nullable=True)

    Recording_Sid = Column(String(64), nullable=True)
    Recording_Duration = Column(Integer, nullable=True)

    TwilioRecordingUrl = Column(Text, nullable=True)
    MinIORecordingUrl = Column(Text, nullable=True)

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
