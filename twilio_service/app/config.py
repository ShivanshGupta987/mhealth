"""config.py - Loads configuration from twilio_service's own .env file.

This service is fully standalone. It does NOT share .env or the database
with any other service in the project.
"""
import os
from dotenv import load_dotenv

_here = os.path.dirname(os.path.abspath(__file__))
_service_root = os.path.dirname(_here)   # twilio_service/

# Only load from the service's own .env — no fallback to parent dirs
_dotenv_path = os.path.join(_service_root, ".env")
if os.path.exists(_dotenv_path):
    load_dotenv(_dotenv_path)

# ── Twilio ────────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

# ── Database (service-local PostgreSQL) ───────────────────────────────────────
POSTGRES_DB_URL: str = os.getenv(
    "POSTGRES_DB_URL",
    "postgresql://twilio_user:twilio_pass@localhost:5433/mhealthDB",
)

# PostgreSQL schema used by twilio_service when sharing a single database
# with other services (e.g., backend in public schema).
TWILIO_DB_SCHEMA: str = os.getenv("TWILIO_DB_SCHEMA", "twilio")

# ── Public hostname for Twilio callback URLs ──────────────────────────────────
# No scheme, no trailing slash. e.g. "mhealth.iitgn.ac.in" or "abc.ngrok-free.app"
APP_HOST: str = os.getenv("APP_HOST", "localhost")

# ── Uvicorn bind ──────────────────────────────────────────────────────────────
TWILIO_SERVICE_HOST: str = os.getenv("TWILIO_SERVICE_HOST", "0.0.0.0")
TWILIO_SERVICE_PORT: int = int(os.getenv("TWILIO_SERVICE_PORT", "8002"))

# ── Celery / RabbitMQ (service-local) ─────────────────────────────────────────
RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")

# ── Call management ───────────────────────────────────────────────────────────
RETRY_DELAY_MINUTES: int = int(os.getenv("RETRY_DELAY_MINUTES", "5"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

# ── ML microservice (optional — for voice sentiment analysis) ─────────────────
ML_SERVICE_URL: str = os.getenv("ML_SERVICE_URL", "http://localhost:8001")
ML_SERVICE_TIMEOUT: int = int(os.getenv("ML_SERVICE_TIMEOUT", "30"))

# ── MinIO (optional — archive Twilio recordings) ─────────────────────────────
# Example endpoint values: "localhost:9000" or "http://localhost:9000"
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "twilio-recordings")

# Optional public base URL for generated recording links.
# Example: "https://minio.example.com" or "http://localhost:9000"
MINIO_PUBLIC_BASE_URL: str = os.getenv("MINIO_PUBLIC_BASE_URL", "")

# ── JWT (for admin API routes) ────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change_me_in_production")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "180"))
