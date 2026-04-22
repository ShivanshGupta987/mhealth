from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

from app.api.auth_routes import router as auth_router
from app.api.call_monitoring_routes import router as call_monitoring_router
from app.api.counsellor_routes import router as counsellor_router
from app.api.database_routes import router as database_router
from app.api.ml_routes import router as ml_router
from app.api.target_monitoring_routes import router as target_monitoring_router
from app.config import APP_HOST, CONTAINER_NAME, MINIO_ACCESS_KEY, MINIO_ENDPOINT, MINIO_SECRET_KEY
from app.twilio.config import TWILIO_ACCOUNT_SID
from app.twilio.main import app as twilio_app
from app.twilio.main import voice_answer, voice_respond, voice_status

logger = logging.getLogger(__name__)

app = FastAPI(title="MHealth")

frontend_urls = os.getenv("FRONTEND_URL", "http://localhost:3000")
origins = [
    "http://localhost:5173",
    "https://localhost:5173",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost",
    "https://localhost",
]

if frontend_urls:
    for url in frontend_urls.split(","):
        cleaned = url.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend-owned routers
app.include_router(auth_router)
app.include_router(ml_router)
app.include_router(database_router)
app.include_router(call_monitoring_router)
app.include_router(target_monitoring_router)
app.include_router(counsellor_router)

# Twilio admin/data APIs under /twilio/*
app.include_router(twilio_app.router, prefix="/twilio")

# Twilio webhook callbacks at root paths expected by Twilio
app.add_api_route("/voice/answer", voice_answer, methods=["POST"], tags=["Twilio Webhooks"])
app.add_api_route(
    "/voice/respond/{question_index}",
    voice_respond,
    methods=["POST"],
    tags=["Twilio Webhooks"],
)
app.add_api_route("/voice/status", voice_status, methods=["POST"], tags=["Twilio Webhooks"])


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mhealth-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root():
    return {
        "message": "MHealth System is operational",
        "status": "operational",
    }


def _is_minio_connected() -> bool:
    if not (MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY and CONTAINER_NAME):
        return False

    endpoint = MINIO_ENDPOINT
    secure = False
    if endpoint.startswith("https://"):
        endpoint = endpoint[len("https://") :]
        secure = True
    elif endpoint.startswith("http://"):
        endpoint = endpoint[len("http://") :]

    try:
        client = Minio(
            endpoint,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=secure,
        )
        # A successful bucket_exists call proves connectivity/auth.
        client.bucket_exists(CONTAINER_NAME)
        return True
    except Exception:
        logger.warning("MinIO connectivity check failed", exc_info=True)
        return False


@app.get("/config-check")
def check_config():
    host = (APP_HOST or "").strip()
    webhook_urls = {}
    if host:
        webhook_urls = {
            "voice_answer": f"https://{host}/voice/answer",
            "voice_status": f"https://{host}/voice/status",
            "twilio_admin": f"https://{host}/twilio",
        }

    return {
        "app_host": APP_HOST,
        "twilio_account_sid": TWILIO_ACCOUNT_SID if TWILIO_ACCOUNT_SID else "NOT SET",
        "minio_endpoint": MINIO_ENDPOINT,
        "minio_bucket": CONTAINER_NAME,
        "minio_connected": _is_minio_connected(),
        "webhook_urls": webhook_urls,
    }
