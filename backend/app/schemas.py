from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

# --- Base Schemas (Used for input/output validation) ---

class TargetBase(BaseModel):
    Name: str
    Roll_No: str
    Phone_No: str
    Department_Name: str
    Program: str

class TargetCreate(TargetBase):
    pass # Uses Base structure

class Target(TargetBase):
    Target_Id: uuid.UUID
    
    class Config:
        from_attributes = True # Allows mapping from SQLAlchemy ORM objects

class ModelBase(BaseModel):
    Model_Name: str
    Model_Version: str
    Model_Details: Optional[str] = None

class ModelCreate(ModelBase):
    Model_Id: str # Frontend supplies M001, M002
    pass

class Model(ModelBase):
    Model_Id: str
    
    class Config:
        from_attributes = True

class EmotionBase(BaseModel):
    Emotion: str

class EmotionCreate(EmotionBase):
    Emotion_Id: str

class Emotion(EmotionBase):
    Emotion_Id: str
    
    class Config:
        from_attributes = True

class AdminBase(BaseModel):
    Email: EmailStr
    Password: str

class AdminCreate(AdminBase):
    pass

class Admin(BaseModel):
    Admin_Id: uuid.UUID
    Email: EmailStr
    
    class Config:
        from_attributes = True
        
class ErrorLogBase(BaseModel):
    Error_Type: str
    Error_Message: str

class ErrorLogCreate(ErrorLogBase):
    Timestamp: datetime = datetime.now() # Use Python default for now
    
class ErrorLog(ErrorLogBase):
    Logs_Id: uuid.UUID
    Timestamp: datetime
    
    class Config:
        from_attributes = True