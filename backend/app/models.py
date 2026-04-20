from sqlalchemy import Column, Float, Integer, String, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship 
from datetime import datetime , timezone 
from app.sql_db import Base  
from sqlalchemy.dialects.postgresql import UUID 
import uuid 
import pytz

# IST Timezone object 
IST = pytz.timezone('Asia/Kolkata')

# --- ENUM Definitions ---
# Target.Department_Name now uses a plain string (no enum)
# Enum for Calls.Status
CALL_STATUS_ENUM = Enum(
    "Call Scheduled",    # 1: Initial status when scheduling
    "failed",            # 2: Exotel status from status_callback
    "busy",              # 3: Exotel status from status_callback
    "no-answer",         # 4: Exotel status from status_callback
    "Message Not Conveyed",                # 5: Passthru, completed but no recording
    "Message Conveyed But Not Processed",  # 6: Passthru, completed with recording, before emotion
    "Message Conveyed And Processed",      # 7: After emotion processing
    name='call_status_enum'
)

class Targets(Base):
    __tablename__ = 'Targets'

    # Map directly to your ERD 
    Target_Id = Column(UUID(as_uuid=True), primary_key=True, default = uuid.uuid4) 
    Name = Column(String, nullable=False)
    Roll_No = Column(String, unique=True, nullable=False)
    Phone_No = Column(String, unique=True, nullable=True)
    Department_Name = Column(String, nullable=False)
    Program = Column(String, nullable=False)

    # one to many relationship with 'Calls' Table 
    calls = relationship("Calls", back_populates="target") 


class Calls(Base):
    __tablename__ = 'Calls'

    # Primary Key 
    Call_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Call_Sid nullable initially to support placeholder/claim insertion
    Call_Sid = Column(String(100), nullable=True)
    
    # Foreign Key 
    Target_Id = Column(UUID(as_uuid=True), ForeignKey('Targets.Target_Id'))
    Model_Id = Column(String(10), ForeignKey('Models.Model_Id'))

    # Time Celery beat initiated the task(Intent)
    Scheduled_Time = Column(DateTime(timezone=True))
    # Time Celery Worker started execution (reality)
    Started_Time = Column(DateTime(timezone=True)) 
    # Foreign Key 
    Emotion_Id = Column(String(10), ForeignKey('Emotions.Emotion_Id'), nullable=True) 
    Status = Column(CALL_STATUS_ENUM)
    Duration = Column(Integer)
    Recording_Url = Column(String(512), nullable=True)
    Analysis_Score = Column(Float, nullable=True)

    # Relationships 
    target = relationship("Targets", back_populates="calls")
    model = relationship("Models", back_populates="calls")
    emotion = relationship("Emotions", back_populates="calls")
    
    __table_args__ = (
        # prevent duplicate claims for the same target + scheduled time
        UniqueConstraint('Target_Id', 'Scheduled_Time', name='uq_target_scheduled_time'),
    )


class Emotions(Base):
    __tablename__ = 'Emotions'
    
    # Primary Key : Enter Emotion_Id manually
    Emotion_Id = Column(String(10), primary_key=True)
    Emotion = Column(String(20), unique=True)
    
    calls = relationship("Calls", back_populates="emotion")

class Models(Base):
    __tablename__ = 'Models'
    
    # PK: Enter Model_Id manually
    Model_Id = Column(String(10), primary_key=True)
    Model_Name = Column(String)
    Model_Version = Column(String)
    Model_Details = Column(Text)
    
    calls = relationship("Calls", back_populates="model")

class Admins(Base):
    __tablename__ = 'Admins'
    
    # PK
    Admin_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Email = Column(String(255), unique=True)
    Password = Column(String(255))

class PasswordResetTokens(Base):
    __tablename__ = 'Password_Reset_Tokens'
    
    # PK
    Token_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Admin_Id = Column(UUID(as_uuid=True), ForeignKey('Admins.Admin_Id'), nullable=False)
    Token = Column(String(255), unique=True, nullable=False)
    Created_At = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    Expires_At = Column(DateTime(timezone=True), nullable=False)
    Used = Column(Integer, default=0)  # 0 = not used, 1 = used

class ErrorLogs(Base):
    __tablename__ = 'Error_Logs'
    
    # PK
    Logs_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Timestamp = Column(DateTime(timezone=True), default=lambda : datetime.now(IST))
    Error_Type = Column(String)
    Error_Message = Column(Text)

class FlaggedTargets(Base):
    __tablename__ = "FlaggedTargets"

    Flag_Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    Target_Id = Column(UUID(as_uuid=True), ForeignKey("Targets.Target_Id"), nullable=False)
    Call_Scheduled_DateTime = Column(DateTime(timezone=True), default=lambda: datetime.now(IST))