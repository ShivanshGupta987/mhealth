"""sql_db.py - SQLAlchemy engine and session setup for twilio_service."""
from contextlib import contextmanager
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import POSTGRES_DB_URL, TWILIO_DB_SCHEMA


_VALID_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _normalize_schema_name(raw_schema: str) -> str:
    schema = (raw_schema or "").strip()
    if not schema:
        return "twilio"
    if not _VALID_SCHEMA_RE.match(schema):
        raise ValueError(
            "Invalid TWILIO_DB_SCHEMA. Use only letters, numbers, and underscores."
        )
    return schema


_SCHEMA = _normalize_schema_name(TWILIO_DB_SCHEMA)

engine = create_engine(
    POSTGRES_DB_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"options": f"-csearch_path={_SCHEMA},public"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session_cm():
    """Context-manager version for use inside Celery tasks."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
