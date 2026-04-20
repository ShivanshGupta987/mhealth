# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from jose.exceptions import JWTError
import secrets
import httpx
from urllib.parse import urlencode
from app.config import (
    JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
    IITGN_CLIENT_ID, IITGN_CLIENT_SECRET, IITGN_REDIRECT_URI, IITGN_ALLOWED_EMAILS,
    FRONTEND_URL,
)
from app.sql_db import get_db
from app.models import Admins, PasswordResetTokens
from app.email_utils import send_password_reset_email

# In-memory CSRF state store (single-server deployment)
_oauth_states: dict = {}

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Use bcrypt_sha256 to match create_admin.py
pwd_ctx = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordIn(BaseModel):
    email: EmailStr
    current_password: str
    new_password: str

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

def get_password_hash(password: str):
    return pwd_ctx.hash(password)

def verify_password(plain, hashed):
    return pwd_ctx.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=1)  # 1 day expiry
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")

@router.post("/signup")
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    existing = db.query(Admins).filter(Admins.Email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already exists")
    admin = Admins(Email=payload.email, Password=get_password_hash(payload.password))
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"ok": True, "admin_id": str(admin.Admin_Id)}

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    admin = db.query(Admins).filter(Admins.Email == payload.email).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if password is already hashed or plain text
    # If verify fails with hash error, check if it's plain text (for backward compatibility)
    try:
        password_valid = verify_password(payload.password, admin.Password)
    except Exception:
        # If password is stored as plain text (old format), check directly
        password_valid = (payload.password == admin.Password)
        
        # If plain text password matches, update to hashed version
        if password_valid:
            admin.Password = get_password_hash(payload.password)
            db.commit()
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(admin.Admin_Id), "email": admin.Email})
    return {"access_token": token, "token_type": "bearer", "admin_id": str(admin.Admin_Id)}

@router.post("/change-password")
def change_password(payload: ChangePasswordIn, db: Session = Depends(get_db)):
    """Change password for logged-in users (requires current password)"""
    admin = db.query(Admins).filter(Admins.Email == payload.email).first()
    if not admin:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    try:
        password_valid = verify_password(payload.current_password, admin.Password)
    except Exception:
        password_valid = (payload.current_password == admin.Password)
    
    if not password_valid:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Update to new password
    admin.Password = get_password_hash(payload.new_password)
    db.commit()
    
    return {"ok": True, "message": "Password changed successfully"}

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordIn, db: Session = Depends(get_db)):
    """Request password reset - sends email with reset link"""
    admin = db.query(Admins).filter(Admins.Email == payload.email).first()
    
    # Don't reveal if user exists for security
    if not admin:
        return {"ok": True, "message": "If the email exists, a password reset link has been sent"}
    
    # Generate secure random token
    reset_token = secrets.token_urlsafe(32)
    
    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    
    # Invalidate any existing unused tokens for this admin
    db.query(PasswordResetTokens).filter(
        PasswordResetTokens.Admin_Id == admin.Admin_Id,
        PasswordResetTokens.Used == 0
    ).update({"Used": 1})
    
    # Create new reset token record
    token_record = PasswordResetTokens(
        Admin_Id=admin.Admin_Id,
        Token=reset_token,
        Expires_At=expires_at,
        Used=0
    )
    db.add(token_record)
    db.commit()
    
    # Send email with reset link
    email_sent = send_password_reset_email(admin.Email, reset_token)
    
    if not email_sent:
        # Log the token for development if email fails
        print(f"DEV MODE - Reset token for {admin.Email}: {reset_token}")
    
    return {"ok": True, "message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    """Reset password using token from email"""
    # Find the token
    token_record = db.query(PasswordResetTokens).filter(
        PasswordResetTokens.Token == payload.token,
        PasswordResetTokens.Used == 0
    ).first()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    if datetime.now(timezone.utc) > token_record.Expires_At:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    # Get the admin
    admin = db.query(Admins).filter(Admins.Admin_Id == token_record.Admin_Id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    admin.Password = get_password_hash(payload.new_password)
    
    # Mark token as used
    token_record.Used = 1
    
    db.commit()
    
    return {"ok": True, "message": "Password reset successfully"}

@router.get("/verify-reset-token/{token}")
def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """Verify if a reset token is valid"""
    token_record = db.query(PasswordResetTokens).filter(
        PasswordResetTokens.Token == token,
        PasswordResetTokens.Used == 0
    ).first()
    
    if not token_record:
        return {"valid": False, "message": "Invalid token"}
    
    if datetime.now(timezone.utc) > token_record.Expires_At:
        return {"valid": False, "message": "Token has expired"}
    
    # Get admin email for display
    admin = db.query(Admins).filter(Admins.Admin_Id == token_record.Admin_Id).first()
    
    return {
        "valid": True,
        "email": admin.Email if admin else None
    }


# ────────────────────────────────────────────────────────────
# IITGN SSO (Keycloak / OpenID Connect)
# ────────────────────────────────────────────────────────────

IITGN_AUTH_BASE = "https://auth.iitgn.ac.in/realms/iitgnsso/protocol/openid-connect"


@router.get("/sso/login")
def sso_login():
    """Redirect user to IITGN SSO (Keycloak) consent screen."""
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = True
    params = {
        "client_id": IITGN_CLIENT_ID,
        "redirect_uri": IITGN_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    url = f"{IITGN_AUTH_BASE}/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/sso/callback")
def sso_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Handle IITGN SSO callback, issue JWT, redirect to frontend."""
    frontend_login = f"{FRONTEND_URL}/login"

    if error:
        return RedirectResponse(f"{frontend_login}?error=SSO+sign-in+was+cancelled")

    if not state or state not in _oauth_states:
        return RedirectResponse(f"{frontend_login}?error=Invalid+SSO+state")
    _oauth_states.pop(state, None)

    if not code:
        return RedirectResponse(f"{frontend_login}?error=No+authorisation+code+received")

    # Exchange authorisation code for tokens
    try:
        token_resp = httpx.post(
            f"{IITGN_AUTH_BASE}/token",
            data={
                "code": code,
                "client_id": IITGN_CLIENT_ID,
                "client_secret": IITGN_CLIENT_SECRET,
                "redirect_uri": IITGN_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except Exception:
        return RedirectResponse(f"{frontend_login}?error=Failed+to+exchange+token+with+IITGN+SSO")

    # Fetch user info from Keycloak
    try:
        info_resp = httpx.get(
            f"{IITGN_AUTH_BASE}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        info_resp.raise_for_status()
        user_info = info_resp.json()
    except Exception:
        return RedirectResponse(f"{frontend_login}?error=Failed+to+fetch+user+info+from+IITGN+SSO")

    email: str = user_info.get("email", "")
    if not email:
        return RedirectResponse(f"{frontend_login}?error=No+email+returned+by+IITGN+SSO")

    # Validate email allowlist if configured
    if IITGN_ALLOWED_EMAILS:
        email_lower = email.strip().lower()
        is_allowed = any(
            email_lower.endswith(allowed_item)
            if allowed_item.startswith('@')
            else email_lower == allowed_item
            for allowed_item in IITGN_ALLOWED_EMAILS
        )

        if not is_allowed:
            return RedirectResponse(f"{frontend_login}?error=Your+email+is+not+authorized+to+access+this+application")

    # Find or auto-create admin for this SSO account
    admin = db.query(Admins).filter(Admins.Email == email).first()
    if not admin:
        admin = Admins(Email=email, Password="")  # SSO-only, no local password
        db.add(admin)
        db.commit()
        db.refresh(admin)

    jwt_token = create_access_token({"sub": str(admin.Admin_Id), "email": admin.Email})
    return RedirectResponse(
        f"{frontend_login}?token={jwt_token}&admin_id={str(admin.Admin_Id)}"
    )

