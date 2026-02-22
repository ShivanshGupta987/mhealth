from passlib.context import CryptContext
import pytz 
from datetime import datetime, timedelta, timezone
from app.config import (JWT_SECRET_KEY)
from sqlalchemy.orm import Session
from app.models import *
from typing import Optional
import jwt

# Define the IST timezone object
IST = pytz.timezone('Asia/Kolkata') 

# Password Hashing and JWT Setup - use bcrypt_sha256 to match create_admin.py
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 1 day = 24 hours * 60 minutes

def get_password_hash(password):
    """Hashes the plain text password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generates a new JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    # Use HS256 algorithm for signing
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256") 
    return encoded_jwt

def authenticate_admin(db: Session, email: str, password: str):
    """Finds admin by email and verifies password."""
    admin = db.query(Admins).filter(Admins.Email == email).first()
    if not admin:
        return None
    
    # Verify the password hash stored in the database
    if not verify_password(password, admin.Password):
        return None
    
    return admin